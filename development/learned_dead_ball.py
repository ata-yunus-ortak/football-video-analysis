"""External-data learned dead/live evidence, separate from team ownership.

Pure NumPy training and inference. No provider state, events, match clock,
player names or team identity may enter features. Parameters require external
selection; class probability does not assert independent ground truth.
"""
import warnings
import numpy as np
from .continuity import pair_masks
from .dead_ball_features import extract
from .sequence_possession import FIELDS, SequenceConfig, decode


BASE_NAMES = ('signed_edge', 'ball_speed', 'nearest_player', 'player_speed_q25',
              'player_speed_median', 'player_speed_q75', 'player_spread_x', 'player_spread_y')
FEATURE_NAMES = [f'{name}_{window}s' for window in (0., .4, 1.6) for name in BASE_NAMES]


def temporal_mean(values, period, frame, radius):
    out = np.full_like(values, np.nan)
    boundaries = np.r_[0, np.flatnonzero((period[1:] != period[:-1]) | (np.diff(frame) != 1)) + 1, len(values)]
    for a,b in zip(boundaries[:-1],boundaries[1:]):
        block = values[a:b]; valid = np.isfinite(block)
        sums = np.vstack((np.zeros((1,values.shape[1])), np.cumsum(np.where(valid,block,0.),axis=0)))
        counts = np.vstack((np.zeros((1,values.shape[1])), np.cumsum(valid,axis=0)))
        index = np.arange(b-a); left = np.maximum(0,index-radius); right = np.minimum(b-a,index+radius+1)
        count = counts[right]-counts[left]
        np.divide(sums[right]-sums[left], count, out=out[a:b], where=count>0)
    return out


def features(inputs):
    if set(inputs)-FIELDS: raise ValueError('Only registered measurement fields allowed')
    measured = extract(inputs)
    b,p = np.asarray(inputs['ball'],float), np.array(inputs['players'],float,copy=True)
    n,fps = len(b),float(inputs['fps'])
    detected = np.asarray(inputs.get('player_detected',np.isfinite(p).all(2)))
    p[~detected] = np.nan
    _, pp = pair_masks(inputs)
    speed = np.full(p.shape[:2],np.nan)
    speed[1:] = np.linalg.norm(np.diff(p,axis=0),axis=2)*fps
    speed[~pp] = np.nan
    distance = np.linalg.norm(p-b[:,None],axis=2)
    distance[~measured['ball_present']] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        nearest = np.nanmin(distance,axis=1)
        quantiles = np.nanquantile(speed,[.25,.5,.75],axis=1).T
        spread = np.nanstd(p,axis=1)
    margin = measured['ball_edge_margin_m']
    base = np.column_stack((np.sign(margin)*np.log1p(np.abs(margin)),
                            np.log1p(measured['ball_speed_mps']),np.log1p(nearest),
                            np.log1p(quantiles),np.log1p(spread)))
    blocks = [base]
    # Native-source discontinuities cannot be bridged by time summaries.
    frame = np.array(inputs['frame'],copy=True)
    if 'ball_pair_valid' in inputs:
        frame += np.cumsum(~np.asarray(inputs['ball_pair_valid']))
    for window in (.4,1.6):
        blocks.append(temporal_mean(base,inputs['period'],frame,int(round(window*fps/2))))
    coverage = np.sum(np.isfinite(p).all(2),axis=1)
    # Absent evidence is not a dead-ball claim. Coverage threshold is a fixed
    # input validity guard (not selected from the supplied fixture).
    usable = np.isin(inputs['period'],(1,2)) & (coverage >= 4)
    return np.column_stack(blocks), usable


def corrupt(inputs, seed, ball_fraction=.2, player_fraction=.2):
    """Label-independent block dropout; never alters targets."""
    rng = np.random.default_rng(seed)
    x = {k:np.array(v,copy=True) for k,v in inputs.items()}
    width = max(1,round(2*float(x['fps'])))
    n = len(x['ball']); count = (n+width-1)//width
    ball_drop = np.repeat(rng.random(count)<ball_fraction,width)[:n]
    person_drop = np.repeat(rng.random((count,x['players'].shape[1]))<player_fraction,width,axis=0)[:n]
    x['ball'][ball_drop] = np.nan; x['ball_observed'][ball_drop] = False
    x['players'][person_drop] = np.nan; x['player_detected'][person_drop] = False
    return x


def design(raw, median, scale):
    missing = ~np.isfinite(raw)
    z = np.clip((np.where(missing,median,raw)-median)/scale,-10.,10.)
    return np.column_stack((np.ones(len(z)),z,missing.astype(float)))


def sigmoid(z):
    z = np.clip(z,-40.,40.)
    return 1/(1+np.exp(-z))


def fit(raw, target, weights, l2):
    if not np.isfinite(l2) or l2 <= 0: raise ValueError('Positive regularization required')
    if raw.ndim != 2 or target.shape != (len(raw),) or weights.shape != target.shape or not np.isin(target,(0,1)).all():
        raise ValueError('Aligned binary training targets required')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        median = np.nanmedian(raw,axis=0)
        scale = np.nanstd(raw,axis=0)
    median = np.nan_to_num(median); scale = np.where(np.isfinite(scale)&(scale>1e-6),scale,1.)
    z = design(raw,median,scale)
    weights = weights/weights.sum()
    beta = np.zeros(z.shape[1]); penalty = np.full(len(beta),l2); penalty[0] = 0.
    def objective(v):
        scores = z@v
        return float(np.sum(weights*(np.logaddexp(0,scores)-target*scores)) + .5*np.sum(penalty*v*v))
    converged = False
    for iteration in range(50):
        prob = sigmoid(z@beta)
        gradient = z.T@(weights*(prob-target)) + penalty*beta
        curvature = weights*prob*(1-prob)
        hessian = z.T@(curvature[:,None]*z) + np.diag(penalty+1e-9)
        delta = np.linalg.solve(hessian,gradient)
        step,old = 1.,objective(beta)
        while objective(beta-step*delta)>old and step>1e-6: step *= .5
        beta -= step*delta
        if np.max(np.abs(gradient))<1e-7:
            converged = True; break
    if not converged: raise ValueError('Logistic fit did not converge')
    return {'median':median.tolist(),'scale':scale.tolist(),'coefficients':beta.tolist(),
            'feature_names':FEATURE_NAMES,'l2':l2,'iterations':iteration+1,'converged':converged}


def probability(raw, model):
    if model['feature_names'] != FEATURE_NAMES: raise ValueError('Feature schema mismatch')
    return sigmoid(design(raw,np.asarray(model['median']),np.asarray(model['scale']))@np.asarray(model['coefficients']))


def classify(probability_dead, usable, inputs, threshold, switch_cost):
    if not 0<threshold<1: raise ValueError('Probability threshold must lie in (0,1)')
    score = np.clip((np.asarray(probability_dead)-threshold)/max(threshold,1-threshold),-1,1)
    score[~usable] = 0
    # The generic two-state decoder's H means dead here, A means live.
    cfg = SequenceConfig(1.,1.,.001,switch_cost,'geometry')
    state = decode(score,usable,inputs['period'],inputs['frame'],float(inputs['fps']),cfg)
    return np.where(state=='H','D',np.where(state=='A','L','X'))


def boundary_score(target, state, period, fps, tolerance_s=1.):
    """One-to-one onset/restart matching within each period, no X bridging."""
    target,state,period = map(np.asarray,(target,state,period))
    known = np.isin(target,('H','A','D')) & np.isin(period,(1,2))
    gt = target=='D'; pred = state=='D'
    pair = known[1:] & known[:-1] & (period[1:]==period[:-1])
    pred_pair = pair & (state[1:]!='X') & (state[:-1]!='X')
    hits = ng = npred = 0; errors = []
    for half in (1,2):
        for direction in (-1,1):
            a = np.flatnonzero(pair & (period[1:]==half) & (np.diff(gt.astype(int))==direction))+1
            b = np.flatnonzero(pred_pair & (period[1:]==half) & (np.diff(pred.astype(int))==direction))+1
            ng += len(a); npred += len(b)
            edges = [(abs(int(i)-int(j)),int(i),int(j)) for i in a for j in b if abs(i-j)<=fps*tolerance_s]
            used_a,used_b = set(),set()
            for error,i,j in sorted(edges):
                if i not in used_a and j not in used_b:
                    hits += 1; used_a.add(i); used_b.add(j); errors.append(error/fps)
    return {'f1':2*hits/max(1,ng+npred),'matched':hits,'target_boundaries':ng,'predicted_boundaries':npred,
            'matched_median_error_s':float(np.median(errors)) if errors else None,
            'tolerance_s':tolerance_s}
