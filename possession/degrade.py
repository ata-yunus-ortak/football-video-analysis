"""Make clean external tracking resemble automatic, uncorrected tracking (domain randomisation).

The competition ATD is automatic: the ball is missing on ~41% of graded frames (DATA.md), player
tracks have gaps/duplicates and positions are noisier than corrected optical data. Exact
characteristics of the supplied match are NOT measured or tuned here (that would be calibration
on the provided data). Instead each training/validation copy samples its corruption parameters
from broad ranges around the published aggregate statistics, so the selected model must work
across them. Labels are never altered.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d

RANGES = {
    'ball_miss_alive': (0.12, 0.40),     # marginal missing rate while play is live
    'ball_miss_dead_extra': (0.0, 0.55), # extra missing while the ball is dead (unknown coupling)
    'ball_miss_tau_s': (0.3, 2.0),       # temporal correlation of missingness
    'ball_out_miss': (0.4, 1.0),         # P(missing) when ball is >1 m outside the lines
    'ball_crowd_logit': (0.0, 1.5),      # extra missing logit per nearby (<1.5 m) player
    'ball_fast_logit': (0.0, 1.5),       # extra missing logit for fast balls (>15 m/s)
    'ball_sigma_m': (0.05, 0.3),
    'ball_fp_rate': (0.0, 0.004),        # false ball detections (bursts) per frame
    'player_miss': (0.02, 0.12),
    'player_miss_tau_s': (0.5, 4.0),
    'player_sigma_m': (0.03, 0.3),
    'team_flip_rate': (0.0, 0.002),      # per-frame start rate of short wrong-team tracklets
}


# possession-v2.2 training profile: wider ball noise plus a slowly varying ball bias (applied after
# every v2.1 draw, so the v2.1 profile and its random draws are unchanged).
RANGES_V22 = dict(RANGES, ball_sigma_m=(0.05, 0.6), ball_bias_sd_m=(0.0, 0.6), ball_bias_tau_s=(1.0, 10.0))
# possession-v2.3 training profile: v2.2 ball ranges plus wider player noise.
RANGES_V23 = dict(RANGES_V22, player_sigma_m=(0.03, 0.6))
PROFILES = {'v2': RANGES, 'v2.2': RANGES_V22, 'v2.3': RANGES_V23}


def sample_params(rng, fixed=None, ranges=None):
    p = {k: float(rng.uniform(a, b)) for k, (a, b) in (ranges or RANGES).items()}
    if fixed:
        p.update(fixed)
    return p


def _corr_noise(rng, n, tau_frames):
    z = rng.standard_normal(n)
    if tau_frames > 0.5:
        z = gaussian_filter1d(z, tau_frames, mode='nearest')
        z /= max(z.std(), 1e-9)
    return z


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def degrade(match, labels, rng, params=None, profile='v2'):
    """Return a corrupted copy of `match` (labels used only to modulate dead-ball missingness)."""
    from scipy.stats import norm
    p = params or sample_params(rng, ranges=PROFILES[profile])
    fps = match['fps']
    L, W = match['pitch']
    ball = match['ball'].astype(np.float32).copy()
    players = match['players'].astype(np.float32).copy()
    team = match['team'].copy()
    n, s, _ = players.shape
    dead = np.asarray(labels) == 'D' if labels is not None else np.zeros(n, bool)
    # --- ball missingness: thresholded correlated Gaussian with frame-varying marginal
    d = np.linalg.norm(players - ball[:, None], axis=2)
    crowd = np.nansum(d < 1.5, axis=1)
    v = np.full(n, np.nan)
    v[1:-1] = np.linalg.norm(ball[2:] - ball[:-2], axis=1) * fps / 2
    fast = np.nan_to_num(v) > 15
    logit = _logit(p['ball_miss_alive']) + p['ball_crowd_logit'] * np.clip(crowd - 1, 0, 3) \
        + p['ball_fast_logit'] * fast
    pm = 1 / (1 + np.exp(-logit))
    pm = np.where(dead, pm + (1 - pm) * p['ball_miss_dead_extra'], pm)
    outside = (ball[:, 0] < -1) | (ball[:, 0] > L + 1) | (ball[:, 1] < -1) | (ball[:, 1] > W + 1)
    pm = np.where(outside, np.maximum(pm, p['ball_out_miss']), pm)
    z = _corr_noise(rng, n, p['ball_miss_tau_s'] * fps)
    miss = z < norm.ppf(np.clip(pm, 1e-4, 1 - 1e-4))
    ball[miss] = np.nan
    ball += rng.normal(0, p['ball_sigma_m'], ball.shape).astype(np.float32)
    # false detections: short bursts at a random pitch location or a random player's feet
    starts = np.flatnonzero(rng.random(n) < p['ball_fp_rate'])
    for a in starts:
        b = min(n, a + int(rng.integers(2, 12)))
        if rng.random() < 0.5:
            pos = rng.uniform([0, 0], [L, W])
        else:
            j = int(rng.integers(0, s))
            pos = players[a, j] if np.isfinite(players[a, j]).all() else rng.uniform([0, 0], [L, W])
        ball[a:b] = pos + rng.normal(0, 0.3, (b - a, 2))
    # --- players: correlated dropouts + extra occlusion dropouts + noise
    for j in range(s):
        z = _corr_noise(rng, n, p['player_miss_tau_s'] * fps)
        drop = z < norm.ppf(p['player_miss'])
        players[drop, j] = np.nan
    close = np.zeros((n, s), bool)
    for a in range(0, n, 8000):
        q = players[a:a + 8000]
        pd_ = np.linalg.norm(q[:, :, None] - q[:, None], axis=3)
        pd_[:, np.arange(s), np.arange(s)] = np.inf
        close[a:a + 8000] = np.nanmin(np.where(np.isnan(pd_), np.inf, pd_), axis=2) < 0.8
    occl = close & (rng.random((n, s)) < 0.25)
    players[occl] = np.nan
    players += rng.normal(0, p['player_sigma_m'], players.shape).astype(np.float32)
    # --- wrong-team tracklets: copy a player into an extra slot of the other team for 1-6 s
    flips = np.flatnonzero(rng.random(n) < p['team_flip_rate'])
    extra = []
    for a in flips:
        j = int(rng.integers(0, s))
        b = min(n, a + int(rng.integers(fps, 6 * fps)))
        col = np.full((n, 2), np.nan, np.float32)
        col[a:b] = players[a:b, j]
        players[a:b, j] = np.nan
        extra.append((col, 1 - team[j]))
    if extra:
        players = np.concatenate([players, np.stack([c for c, _ in extra], 1)], 1)
        team = np.r_[team, np.array([t for _, t in extra], np.int8)]
    # --- v2.2 profile only: slowly varying ball position bias (calibration / height errors)
    if p.get('ball_bias_sd_m', 0.0) > 0:
        tau = p.get('ball_bias_tau_s', 3.0) * fps
        bias = np.stack([_corr_noise(rng, n, tau), _corr_noise(rng, n, tau)], 1) * p['ball_bias_sd_m']
        ball += bias.astype(np.float32)
    out = dict(match)
    out.update(ball=ball, players=players, team=team.astype(np.int8), degrade_params=p)
    return out
