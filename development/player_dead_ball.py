"""Player-only dead/live ablation: no ball position or ball velocity features."""
import warnings
import numpy as np
from . import learned_dead_ball as core
from .continuity import pair_masks
from .sequence_possession import FIELDS

BASE_NAMES=('player_speed_q25','player_speed_median','player_speed_q75','player_spread_x','player_spread_y')
FEATURE_NAMES=[f'{name}_{window}s' for window in (0.,.4,1.6) for name in BASE_NAMES]
corrupt=core.corrupt
classify=core.classify
boundary_score=core.boundary_score


def features(inputs):
    if set(inputs)-FIELDS: raise ValueError('Only registered measurement fields allowed')
    p=np.array(inputs['players'],float,copy=True);n=len(p);fps=float(inputs['fps'])
    period=np.asarray(inputs['period']);frame=np.asarray(inputs['frame'])
    if not np.isfinite(fps) or fps<=0 or not n: raise ValueError('Positive FPS and measurements required')
    _,pair=pair_masks(inputs)
    detected=np.asarray(inputs.get('player_detected',np.isfinite(p).all(2)))
    p[~detected]=np.nan
    speed=np.full(p.shape[:2],np.nan)
    speed[1:]=np.linalg.norm(np.diff(p,axis=0),axis=2)*fps
    speed[~pair]=np.nan
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        q=np.nanquantile(speed,[.25,.5,.75],axis=1).T
        spread=np.nanstd(p,axis=1)
    base=np.log1p(np.column_stack((q,spread)))
    blocks=[base]
    if 'player_pair_valid' in inputs:
        frame=frame+np.cumsum(~np.any(inputs['player_pair_valid'],axis=1))
    for window in (.4,1.6):
        blocks.append(core.temporal_mean(base,period,frame,int(round(window*fps/2))))
    usable=np.isin(period,(1,2)) & (np.sum(np.isfinite(p).all(2),axis=1)>=4)
    return np.column_stack(blocks),usable


def fit(raw,target,weights,l2):
    # Reuse only the numerical optimizer; export this adapter's own schema.
    model=core.fit(raw,target,weights,l2)
    model['feature_names']=FEATURE_NAMES
    model['model_family']='player-only-dead-live-v1'
    return model


def probability(raw,model):
    if model.get('model_family')!='player-only-dead-live-v1' or model['feature_names']!=FEATURE_NAMES:
        raise ValueError('Player-only model schema required')
    z=core.design(raw,np.asarray(model['median']),np.asarray(model['scale']))
    return core.sigmoid(z@np.asarray(model['coefficients']))
