"""v2.12 development experiment, shared helpers (imported by the other scripts in /home/claude/work/v212).

What it provides: the fixed development split (ONLY the four DFL training matches J03WOH, J03WOY, J03WPY,
J03WQQ), the corruption seeds (training seeds 1, 2, 3 for training rows and held-out copies; extra held-out
development seeds 9001-9008, two per match, used only as held-out copies), cached baseline feature arrays
(first 227 columns of the verified /home/claude/work/cache/{name}_s{seed}_w{swap}_f4.npy, or recomputed with the
frozen possession.features.features into /home/claude/work/v212/cache for the extra seeds), cached touch features
(possession.touch.touch_features), training rows exactly as possession.train.training_rows (every sixth frame
starting at seed % 6, labelled H/A/D only, both team views), HistGradientBoosting fits with the
possession-v2-config.json hyperparameters, symmetrised frame probabilities as possession.train.frame_probs, the
frozen decoder, the organisers' metric through possession.evaluate.score, and short-spell recall at IoU 0.3 as in
experiments/possession_v2/err_spells.py. Validation/reserved matches are never loaded here.
"""
import sys, os, json, hashlib, pickle
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')

ROOT = '/home/claude/work/v212/'
VC = ROOT + 'cache/'
OLD = '/home/claude/work/cache/'
MATCHES = ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ']
FORBIDDEN = {'J03WN1', 'J03WR9', 'MET1', 'MET2', 'MET3', 'J03WMX'}
TRAIN_SEEDS = [1, 2, 3]
EXTRA_SEEDS = {'J03WOH': [9001, 9002], 'J03WOY': [9003, 9004], 'J03WPY': [9005, 9006], 'J03WQQ': [9007, 9008]}
CFG = json.load(open('/home/claude/sc/possession-v2-config.json'))
HP, STEP = CFG['hyperparameters'], CFG['step']
HP2, STEP2 = CFG['stack']['hyperparameters'], CFG['stack']['step']
DEC = dict(CFG['decoder'])
NB = 227                       # v2 (feature_version 2) columns


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def guard(name):
    if name in FORBIDDEN or name not in MATCHES:
        raise RuntimeError(f'{name} is not a development match of this experiment')


def held_seeds(name):
    return TRAIN_SEEDS + EXTRA_SEEDS[name]


def load(name):
    guard(name)
    from harness import load as hload
    return hload(name)


def degraded(name, seed):
    guard(name)
    from harness import degraded as hdeg
    return hdeg(name, seed)


def base_path(name, seed, swap):
    if seed in TRAIN_SEEDS:
        return f'{OLD}{name}_s{seed}_w{int(swap)}_f4.npy'
    return f'{VC}base_{name}_s{seed}_w{int(swap)}.npy'


def touch_path(name, seed, swap):
    return f'{VC}touch_{name}_s{seed}_w{int(swap)}.npy'


def base(name, seed, swap, rows=None):
    guard(name)
    a = np.load(base_path(name, seed, swap), mmap_mode='r')
    return np.asarray(a[:, :NB] if rows is None else a[rows, :NB], np.float32)


def touch(name, seed, swap, rows=None):
    guard(name)
    a = np.load(touch_path(name, seed, swap), mmap_mode='r')
    return np.asarray(a if rows is None else a[rows], np.float32)


def feats(name, seed, swap, fset, rows=None):
    X = base(name, seed, swap, rows)
    if fset == 'touch':
        X = np.concatenate([X, touch(name, seed, swap, rows)], 1)
    return X


def row_index(lab, seed, step):
    idx = np.arange(seed % step, len(lab), step)
    return idx[np.isin(lab[idx], ('H', 'A', 'D'))]


def targets(lab, idx, swap):
    yd = (lab[idx] == 'D').astype(np.int8)
    h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
    yh = (np.where(h >= 0, 1 - h, -1) if swap else h).astype(np.int8)
    return yd, yh


def train_rows(names, fset):
    """Stage-1 rows of the given matches (seeds 1-3, both views), cached per match in rows_{name}.npz."""
    Xs, yds, yhs = [], [], []
    for name in names:
        z = np.load(f'{VC}rows_{name}.npz')
        X = z['X'] if fset == 'touch' else z['X'][:, :NB]
        Xs.append(X); yds.append(z['yd']); yhs.append(z['yh'])
    return np.concatenate(Xs), np.concatenate(yds), np.concatenate(yhs)


def fit(X, yd, yh, hp):
    from sklearn.ensemble import HistGradientBoostingClassifier
    md = HistGradientBoostingClassifier(random_state=0, early_stopping=False, **hp).fit(X, yd)
    alive = yh >= 0
    mh = HistGradientBoostingClassifier(random_state=0, early_stopping=False, **hp).fit(X[alive], yh[alive])
    return md, mh


def blocks_mask(period):
    from possession.features import play_blocks
    ok = np.zeros(len(period), bool)
    for a, b in play_blocks(period):
        ok[a:b] = True
    return ok


def probs(md, mh, X, Xs, period):
    """Symmetrised stage-1 probabilities over the play blocks, as possession.train.frame_probs."""
    ok = blocks_mask(period)
    n = len(X)
    pd_, ph = np.full(n, 0.5), np.full(n, 0.5)
    pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1.0 - mh.predict_proba(Xs[ok])[:, 1])
    return np.round(pd_, 6), np.round(ph, 6)


def stack_probs(sd, sh, pd_, ph, period, fps):
    """Second stage as possession.pipeline.stacked_probabilities (sklearn models instead of exported trees)."""
    from possession.stack import stack_features
    S, _ = stack_features(pd_, ph, period, fps)
    Sw, _ = stack_features(pd_, ph, period, fps, swap=True)
    ok = blocks_mask(period)
    d2, h2 = np.full(len(S), 0.5), np.full(len(S), 0.5)
    d2[ok] = 0.5 * (sd.predict_proba(S[ok])[:, 1] + sd.predict_proba(Sw[ok])[:, 1])
    h2[ok] = 0.5 * (sh.predict_proba(S[ok])[:, 1] + 1.0 - sh.predict_proba(Sw[ok])[:, 1])
    return np.round(d2, 6), np.round(h2, 6)


BINS = [('<1s', 0, 25), ('1-2s', 25, 50), ('2-5s', 50, 125), ('5-10s', 125, 250), ('>10s', 250, 10 ** 9)]


def evaluate(lab, period, pd_, ph):
    """Frozen decoder + organisers' metric + spell recall by length (IoU 0.3, as err_spells.py)."""
    from possession.decode import emissions, decode_blocks
    from possession.evaluate import score, _with_separators
    from possession import official_metrics as pm
    pred = decode_blocks(emissions(pd_, ph), period, DEC)
    s = score(lab, pred, period)
    g, p = pm.label_codes(_with_separators(lab, period)), pm.label_codes(_with_separators(pred, period))
    runs = pm.valid_runs(g)
    gs, ps = pm.possession_spells(g, runs), pm.possession_spells(p, runs)
    ov = pm.spell_overlaps(gs, ps)
    hit = pm.matched_gt_flags(ov, len(gs), 0.3)
    L = np.array([b - a for a, b, _ in gs])
    out = {'spell_f1': s['spell_f1_mean'], 'macro_f1': s['macro_f1'], 'n_gt': s['n_gt_spells'],
           'n_pred': s['n_pred_spells'], 'short_n': int((L < 50).sum()), 'short_hit': int(hit[L < 50].sum()),
           'trans_f1_12': s['trans_f1_12'], 'trans_f1_25': s['trans_f1_25']}
    for nm, a, b in BINS:
        sel = (L >= a) & (L < b)
        out[f'n_{nm}'] = int(sel.sum()); out[f'hit_{nm}'] = int(hit[sel].sum())
    Lp = np.array([b - a for a, b, _ in ps])
    out['pred_short_n'] = int((Lp < 50).sum())
    return out


def save_pickle(obj, path):
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(obj, f)
    os.replace(tmp, path)


def load_pickle(path):
    with open(path, 'rb') as f:
        return pickle.load(f)
