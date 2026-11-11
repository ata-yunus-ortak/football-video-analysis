"""Second-stage temporal features computed from first-stage frame probabilities.

Stage 1 sees one frame's measurement context; stage 2 sees how the stage-1 probabilities evolve
over the surrounding seconds (onsets, plateaus, sustained changes), which is what possession
boundaries look like. Trained on out-of-fold stage-1 outputs of external matches only.
"""
import numpy as np
from .features import wmean, wmax, wmin, play_blocks


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def stack_features(pd_, ph, period, fps=25.0, swap=False):
    pd_ = np.asarray(pd_, float)
    ph = np.asarray(ph, float)
    if swap:
        ph = 1.0 - ph
    n = len(pd_)
    cols = None
    out = None
    T = lambda s: int(round(s * fps))
    for a, b in play_blocks(period):
        d, h = pd_[a:b], ph[a:b]
        hl = _logit(h)
        F = {'pd': d, 'ld': _logit(d), 'ph': h, 'lh': hl}
        for sec in (0.2, 0.5, 1, 2, 5, 10):
            F[f'd_p{sec}'] = wmean(d, -T(sec), 0)
            F[f'd_f{sec}'] = wmean(d, 0, T(sec))
            F[f'h_p{sec}'] = wmean(hl, -T(sec), 0)
            F[f'h_f{sec}'] = wmean(hl, 0, T(sec))
            F[f'h_df{sec}'] = F[f'h_f{sec}'] - F[f'h_p{sec}']
            F[f'd_df{sec}'] = F[f'd_f{sec}'] - F[f'd_p{sec}']
        for sec in (1, 3):
            F[f'd_max{sec}'] = wmax(d, -T(sec), T(sec))
            F[f'd_min{sec}'] = wmin(d, -T(sec), T(sec))
            F[f'h_max{sec}'] = wmax(hl, -T(sec), T(sec))
            F[f'h_min{sec}'] = wmin(hl, -T(sec), T(sec))
        if cols is None:
            cols = list(F)
            out = np.full((n, len(cols)), np.nan, np.float64)
        out[a:b] = np.stack([F[c] for c in cols], 1)
    return out, cols
