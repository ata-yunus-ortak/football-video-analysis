"""Input position smoothing for possession v2.3 (candidate).

NaN-aware centred moving average of every player and ball coordinate over 2*half+1 frames,
computed inside each play block; a frame that is missing stays missing (no gap filling).
Applied identically to corrupted training copies and to the provided tracking at inference.
"""
import numpy as np
from .features import play_blocks


def _smooth2d(a, half):
    """a: (n, k) with NaN; centred NaN-aware mean over +-half rows; NaN rows stay NaN."""
    n = len(a)
    f = np.isfinite(a)
    z = np.where(f, a, 0.0)
    cs = np.vstack([np.zeros((1, a.shape[1])), np.cumsum(z, 0)])
    cc = np.vstack([np.zeros((1, a.shape[1])), np.cumsum(f, 0, dtype=np.float64)])
    lo = np.clip(np.arange(n) - half, 0, n)
    hi = np.clip(np.arange(n) + half + 1, 0, n)
    s, c = cs[hi] - cs[lo], cc[hi] - cc[lo]
    with np.errstate(invalid='ignore', divide='ignore'):
        out = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    return np.where(f, out, np.nan)


def smooth_positions(match, half=2):
    """Copy of `match` with smoothed ball and player positions (float32), per play block."""
    ball = np.asarray(match['ball'], np.float64).copy()
    players = np.asarray(match['players'], np.float64).copy()
    n, s, _ = players.shape
    for a, b in play_blocks(match['period']):
        ball[a:b] = _smooth2d(ball[a:b], half)
        players[a:b] = _smooth2d(players[a:b].reshape(b - a, s * 2), half).reshape(b - a, s, 2)
    out = dict(match)
    out.update(ball=ball.astype(np.float32), players=players.astype(np.float32))
    return out
