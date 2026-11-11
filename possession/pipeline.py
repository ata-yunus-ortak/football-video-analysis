"""features -> frame probabilities -> H/A/D labels, with a frozen model bundle."""
import numpy as np
from .features import features, play_blocks
from .trees import predict_proba
from .decode import emissions, decode_blocks


def frame_probabilities(match, bundle):
    """Symmetrised P(dead) and P(home | alive) for every frame (NaN-free, 0.5 outside blocks)."""
    X, names = features(match)
    Xs, names_s = features(match, swap=True)
    if names != bundle['feature_names'] or names_s != names:
        raise ValueError('feature layout differs from the frozen model')
    n = len(X)
    ok = np.zeros(n, bool)
    for a, b in play_blocks(match['period']):
        ok[a:b] = True
    pd_ = np.full(n, 0.5)
    ph = np.full(n, 0.5)
    pd_[ok] = 0.5 * (predict_proba(bundle['dead'], X[ok]) + predict_proba(bundle['dead'], Xs[ok]))
    ph[ok] = 0.5 * (predict_proba(bundle['home'], X[ok]) + 1.0 - predict_proba(bundle['home'], Xs[ok]))
    # 6 decimals: removes platform-level floating noise before the discrete decoder
    return np.round(pd_, 6), np.round(ph, 6)


def stacked_probabilities(pd_, ph, match, bundle):
    """Optional second stage (temporal stacking) when the bundle carries it."""
    from .stack import stack_features
    S, cols = stack_features(pd_, ph, match['period'], match['fps'])
    Sw, _ = stack_features(pd_, ph, match['period'], match['fps'], swap=True)
    if cols != bundle['stack_feature_names']:
        raise ValueError('stack feature layout differs from the frozen model')
    ok = np.zeros(len(S), bool)
    for a, b in play_blocks(match['period']):
        ok[a:b] = True
    d2 = np.full(len(S), 0.5)
    h2 = np.full(len(S), 0.5)
    d2[ok] = 0.5 * (predict_proba(bundle['stack_dead'], S[ok]) + predict_proba(bundle['stack_dead'], Sw[ok]))
    h2[ok] = 0.5 * (predict_proba(bundle['stack_home'], S[ok]) + 1.0 - predict_proba(bundle['stack_home'], Sw[ok]))
    return np.round(d2, 6), np.round(h2, 6)


def predict_labels(match, bundle, outside='D'):
    pd_, ph = frame_probabilities(match, bundle)
    if 'stack_dead' in bundle:
        pd_, ph = stacked_probabilities(pd_, ph, match, bundle)
    return decode_blocks(emissions(pd_, ph), match['period'], bundle['decoder'], outside=outside), pd_, ph
