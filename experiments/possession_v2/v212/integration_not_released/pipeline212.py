"""Possession v2.12: frame probabilities and labels with the touch columns (possession/touch.py).

The stage-1 input is the 227 frozen possession.features columns followed by the 36 touch columns. The base columns are
computed on `match` (the tracking the models see, which may carry the broadcast ball fill); the touch columns on
`touch_match`, the tactical tracking before any fill (same frames, same play blocks, same team ids). Symmetrisation,
rounding, the second stage and the decoder are those of possession/pipeline.py, unchanged.
"""
import numpy as np
from .features import features, play_blocks
from .touch import touch_features
from .trees import predict_proba
from .decode import emissions, decode_blocks
from .pipeline import stacked_probabilities


def frame_probabilities(match, touch_match, bundle):
    """Symmetrised P(dead) and P(home | alive) for every frame (0.5 outside the play blocks), as pipeline.py."""
    if len(touch_match['ball']) != len(match['ball']) or not np.array_equal(touch_match['period'], match['period']):
        raise ValueError('the touch input and the base input differ in frames or play blocks')
    if not np.array_equal(np.asarray(touch_match['team']), np.asarray(match['team'])):
        raise ValueError('the touch input and the base input carry different team ids')
    X, names = features(match)
    Xs, names_s = features(match, swap=True)
    T, tnames = touch_features(touch_match)
    Ts, tnames_s = touch_features(touch_match, swap=True)
    if names + tnames != bundle['feature_names'] or names_s + tnames_s != names + tnames:
        raise ValueError('feature layout differs from the frozen model')
    X = np.concatenate([X, T], 1)
    Xs = np.concatenate([Xs, Ts], 1)
    del T, Ts
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


def predict_labels(match, touch_match, bundle, outside='D'):
    pd_, ph = frame_probabilities(match, touch_match, bundle)
    if 'stack_dead' in bundle:
        pd_, ph = stacked_probabilities(pd_, ph, match, bundle)
    return decode_blocks(emissions(pd_, ph), match['period'], bundle['decoder'], outside=outside), pd_, ph
