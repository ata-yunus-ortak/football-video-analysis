"""Shared helpers for the v2.6 switch-hazard experiment."""
import numpy as np
from possession.features import features
from possession.stack import stack_features

K_FRAMES = 12   # +-0.5 s


def switch_target(lab, k=K_FRAMES):
    """1 where a direct H<->A change of the provider labels lies within +-k frames."""
    lab = np.asarray(lab)
    alive = np.isin(lab, ('H', 'A'))
    ch = np.zeros(len(lab), bool)
    ch[1:] = alive[1:] & alive[:-1] & (lab[1:] != lab[:-1])
    c = np.r_[0, np.cumsum(ch)]
    n = len(lab)
    lo = np.clip(np.arange(n) - k, 0, n)
    hi = np.clip(np.arange(n) + k + 1, 0, n)
    return ((c[hi] - c[lo]) > 0).astype(np.int8)


def hazard_matrix(m_deg, period, p1, q1, swap, idx=None):
    X, _ = features(m_deg, swap=swap)
    S, _ = stack_features(p1, q1, period, swap=swap)
    if idx is not None:
        X, S = X[idx], S[idx]
    return np.hstack([X, S])


def hazard_prob(model, m_deg, period, p1, q1):
    """Team-symmetric hazard: mean of both team views; 0 outside play blocks."""
    out = np.zeros(len(period))
    ok = period > 0
    acc = []
    for sw in (False, True):
        Z = hazard_matrix(m_deg, period, p1, q1, sw)
        v = np.zeros(len(period))
        fin = ok & np.isfinite(Z).any(1)
        v[fin] = model.predict_proba(Z[fin])[:, 1]
        acc.append(v)
        del Z
    out[:] = 0.5 * (acc[0] + acc[1])
    return out
