"""Pooling of the two model families' frame probabilities (possession v2.15).

The v2 models give P(dead) and P(home | alive) per frame; the temporal convolution network gives [home, away, dead]
per frame. Both are turned into three classes, pooled with a fixed weight, and turned back into P(dead) and
P(home | alive), which then go through the unchanged v2 decoder (possession/decode.py with the constants of the model
bundle). Nothing else of the v2 flow changes.

POOL and WEIGHT were chosen on external matches only and fixed in possession-v215-plan.json before the validation.
NumPy only; the result is rounded to 6 decimals, like the v2 probabilities, so that platform-level floating-point
noise cannot reach the discrete decoder unless a value sits exactly on a rounding boundary.
"""
import numpy as np

POOL = 'arithmetic'             # 'arithmetic' or 'geometric'
WEIGHT = 0.2                    # weight of the temporal convolution network
FLOOR = 1e-4                    # smallest probability inside the geometric pool (the v2 decoder clips at the same value)


def three_class(p_dead, p_home):
    """[home, away, dead] from P(dead) and P(home | alive)."""
    p_dead = np.asarray(p_dead, np.float64)
    p_home = np.asarray(p_home, np.float64)
    return np.stack([(1.0 - p_dead) * p_home, (1.0 - p_dead) * (1.0 - p_home), p_dead], axis=1)


def pool(tcn, p_dead, p_home, weight=None, kind=None):
    """tcn: (n, 3) probabilities [home, away, dead] on the frame grid; p_dead, p_home: (n,) of the v2 models.

    Returns pooled P(dead) and P(home | alive), each (n,), rounded to 6 decimals.
    """
    w = WEIGHT if weight is None else weight
    kind = POOL if kind is None else kind
    tcn = np.asarray(tcn, np.float64)
    v2 = three_class(p_dead, p_home)
    if kind == 'arithmetic':
        mixed = w * tcn + (1.0 - w) * v2
    elif kind == 'geometric':
        mixed = np.exp(w * np.log(np.clip(tcn, FLOOR, 1.0)) + (1.0 - w) * np.log(np.clip(v2, FLOOR, 1.0)))
    else:
        raise ValueError('unknown pool: %r' % (kind,))
    alive = mixed[:, 0] + mixed[:, 1]
    total = np.maximum(alive + mixed[:, 2], 1e-12)
    return np.round(mixed[:, 2] / total, 6), np.round(mixed[:, 0] / np.maximum(alive, 1e-12), 6)
