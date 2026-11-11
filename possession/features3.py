"""Feature version 3 (candidate, possession v2.7): v2 features plus gap-bridging ball features.

The v2 features describe a missing ball only through the last-seen and next-seen positions.
Here the ball is linearly bridged across every gap of at most BRIDGE_S seconds and the team
geometry is measured against the bridged position; in addition the player who was nearest when
the ball disappeared is followed to the frame where it reappears (a dribble keeps him close, a
pass does not), and vice versa. Nothing is filled into the tracking itself; these are features.
`possession/features.py` is frozen and is called unchanged.
"""
import numpy as np
from .features import features, play_blocks, wsum, wfrac, wmin, since, until

BRIDGE_S = 6.0
FEATURE_VERSION = 3


def _extra_block(ball, players, team, fps):
    m = len(ball)
    T = lambda sec: int(round(sec * fps))
    ball = ball.astype(np.float64); players = players.astype(np.float64)
    vis = np.isfinite(ball).all(1)
    t = np.arange(m)
    il = np.maximum.accumulate(np.where(vis, t, -1))
    nx = np.minimum.accumulate(np.where(vis, t, m)[::-1])[::-1]
    ok = (il >= 0) & (nx < m)
    a, b = np.clip(il, 0, m - 1), np.clip(nx, 0, m - 1)
    gap = np.where(ok, (nx - il) / fps, np.nan)
    frac = np.where(nx > il, (t - il) / np.maximum(nx - il, 1), 0.0)
    bridged = ok & (np.nan_to_num(gap, nan=1e9) <= BRIDGE_S)
    bi = ball[a] + (ball[b] - ball[a]) * frac[:, None]
    bi[~bridged] = np.nan
    F = {'gap_len': gap, 'gap_frac': np.where(ok, frac, np.nan)}
    with np.errstate(invalid='ignore', divide='ignore'):
        F['gap_speed'] = np.where(ok & (nx > il), np.linalg.norm(ball[b] - ball[a], axis=1) / np.maximum(gap, 1 / fps), np.where(ok, 0.0, np.nan))
    d = np.linalg.norm(players - bi[:, None], axis=2); d[~np.isfinite(d)] = np.inf
    dr = np.linalg.norm(players - ball[:, None], axis=2); dr[~np.isfinite(dr)] = np.inf
    near, jraw = [], []
    for k in (0, 1):
        dk = np.where((team == k)[None], d, np.inf).min(1)
        near.append(np.where(np.isfinite(dk), dk, np.nan))
        jraw.append(np.argmin(np.where((team == k)[None], dr, np.inf), 1))
    persp = []
    for k in (0, 1):
        P = {}
        dk, do = near[k], near[1 - k]
        P['di'] = dk
        P['di_minus_opp'] = dk - do
        nearest = bridged & (np.nan_to_num(dk, nan=99) < np.nan_to_num(do, nan=99))
        ctrl = bridged & (np.nan_to_num(dk, nan=99) < 1.5)
        for nm, (x, y) in {'p1': (-T(1), 0), 'f1': (0, T(1)), 'p3': (-T(3), 0), 'f3': (0, T(3))}.items():
            P[f'inearfrac_{nm}'] = wfrac(nearest, bridged, x, y)
        for nm, (x, y) in {'p1': (-T(1), 0), 'f1': (0, T(1))}.items():
            P[f'ictrl_{nm}'] = wsum(ctrl.astype(float), x, y)
            P[f'idmin_{nm}'] = wmin(dk, x, y) if (x + y) % 2 == 0 else wmin(dk, x - 1, y)
        P['t_since_ictrl'] = since(ctrl, fps, 20.0)
        P['t_until_ictrl'] = until(ctrl, fps, 20.0)
        # follow the player nearest at the last-seen frame to the next-seen frame, and the reverse
        jh, jn = jraw[k][a], jraw[k][b]
        with np.errstate(invalid='ignore'):
            ce = np.linalg.norm(players[b, jh] - ball[b], axis=1)
            cs = np.linalg.norm(players[a, jn] - ball[a], axis=1)
            hd = np.linalg.norm(players[t, jh] - bi, axis=1)
        P['carry_end_d'] = np.where(ok, ce, np.nan)
        P['carry_start_d'] = np.where(ok, cs, np.nan)
        P['hold_di'] = np.where(bridged, hd, np.nan)
        persp.append(P)
    return F, persp


def features3(match, swap=False):
    """(n, k) float32: the v2 columns followed by the gap-bridging columns; names likewise."""
    import warnings
    base, names = features(match, swap=swap)
    fps = float(match['fps'])
    team = np.asarray(match['team']).astype(np.int8)
    if swap:
        team = 1 - team
    n = len(match['ball'])
    extra, enames = None, None
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        for a, b in play_blocks(match['period']):
            F, persp = _extra_block(np.asarray(match['ball'][a:b]), np.asarray(match['players'][a:b]), team, fps)
            cols = [(f'x_{k}', v) for k, v in F.items()]
            for i, P in enumerate(persp):
                cols += [(f'{"hk"[i]}_x_{k}', v) for k, v in P.items()]
            cols += [(f'diff_x_{k}', persp[0][k] - persp[1][k]) for k in persp[0]]
            if extra is None:
                enames = [c for c, _ in cols]
                extra = np.full((n, len(enames)), np.nan, np.float32)
            extra[a:b] = np.stack([np.asarray(v, np.float32) for _, v in cols], 1)
    return np.concatenate([base, extra], 1), names + enames
