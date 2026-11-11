"""High-frequency position noise of a tracking input (possession v2.4 gate; candidate).

sigma_hat = 1.4826 * MAD(d2) / sqrt(6), d2 = x[t+1] - 2 x[t] + x[t-1] over frames where the three
positions exist (x and y pooled), inside the play blocks. For i.i.d. noise of s.d. sigma the second
difference has s.d. sqrt(6) * sigma, while real motion at 25 fps adds well under 1 cm, and kicks or
short false detections are rare outliers that the median ignores. Slowly varying bias and smoothed
(temporally correlated) tracker error are NOT seen by this estimator.
"""
import numpy as np
from .features import play_blocks

THRESHOLD_M = 0.30      # upper end of the ball/player noise v2.1 was trained with (degrade.RANGES)
MIN_VALUES = 500


def high_freq_sd(xy, min_n=MIN_VALUES):
    """xy: (n, 2) positions with NaN for missing frames."""
    d2 = xy[2:] - 2 * xy[1:-1] + xy[:-2]
    v = d2[np.isfinite(d2).all(1)].ravel()
    if len(v) < min_n:
        return float('nan')
    return float(1.4826 * np.median(np.abs(v - np.median(v))) / np.sqrt(6))


def _blocks(a, blocks):
    """Concatenate the play blocks of a, separated by one missing row (no difference across a gap)."""
    pad = np.full((1,) + a.shape[1:], np.nan)
    return np.concatenate([np.concatenate([a[s:e], pad]) for s, e in blocks]) if blocks else a[:0]


def estimate_noise(match):
    blocks = list(play_blocks(match['period']))
    ball = _blocks(np.asarray(match['ball'], np.float64), blocks)
    players = _blocks(np.asarray(match['players'], np.float64), blocks)
    per_slot = [high_freq_sd(players[:, j]) for j in range(players.shape[1])]
    per_slot = [s for s in per_slot if np.isfinite(s)]
    return {'ball_m': high_freq_sd(ball), 'players_m': float(np.median(per_slot)) if per_slot else float('nan'),
            'player_slots_used': len(per_slot)}


def choose_path(noise, threshold=THRESHOLD_M):
    """'v2.3' if either measured noise exceeds the threshold, else 'v2.1' (missing estimates do not trigger)."""
    hi = [k for k in ('players_m', 'ball_m') if np.isfinite(noise[k]) and noise[k] > threshold]
    return ('v2.3' if hi else 'v2.1'), hi
