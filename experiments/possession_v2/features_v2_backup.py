"""Per-frame features for dead-ball and team-possession inference.

Only measurements are used: player/ball positions (metres) and team membership of track slots.
No labels, events, video or provider ownership flags enter here. Everything is computed inside
contiguous play blocks (period 1 / period 2) so nothing leaks across halftime.
"""
import numpy as np
from scipy.ndimage import maximum_filter1d, minimum_filter1d

CAP_T = 30.0
FEATURE_VERSION = 2


# ----------------------------------------------------------------------------- window helpers
def _cum(x):
    return np.concatenate(([0.0], np.cumsum(x, dtype=np.float64)))


def wsum(x, a, b):
    """Sum of x over [t+a, t+b] (clipped to the array)."""
    n = len(x)
    c = _cum(x)
    lo = np.clip(np.arange(n) + a, 0, n)
    hi = np.clip(np.arange(n) + b + 1, 0, n)
    return c[hi] - c[lo]


def wmean(x, a, b):
    """NaN-aware mean over [t+a, t+b]; NaN where the window has no finite value."""
    f = np.isfinite(x)
    s = wsum(np.where(f, x, 0.0), a, b)
    k = wsum(f.astype(np.float64), a, b)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(k > 0, s / np.maximum(k, 1), np.nan)


def wfrac(mask, valid, a, b):
    k = wsum(valid.astype(np.float64), a, b)
    s = wsum((mask & valid).astype(np.float64), a, b)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(k > 0, s / np.maximum(k, 1), np.nan)


def _shifted(arr, off):
    n = len(arr)
    idx = np.clip(np.arange(n) + off, 0, n - 1)
    return arr[idx]


def wmax(x, a, b):
    """NaN-aware max over [t+a, t+b] (a+b must be even)."""
    size = b - a + 1
    y = maximum_filter1d(np.where(np.isfinite(x), x, -np.inf), size, mode='nearest')
    y = _shifted(y, (a + b) // 2)
    return np.where(np.isfinite(y), y, np.nan)


def wmin(x, a, b):
    size = b - a + 1
    y = minimum_filter1d(np.where(np.isfinite(x), x, np.inf), size, mode='nearest')
    y = _shifted(y, (a + b) // 2)
    return np.where(np.isfinite(y), y, np.nan)


def since(mask, fps, cap=CAP_T):
    n = len(mask)
    idx = np.where(mask, np.arange(n), -1)
    last = np.maximum.accumulate(idx)
    out = (np.arange(n) - last) / fps
    out[last < 0] = cap
    return np.minimum(out, cap)


def until(mask, fps, cap=CAP_T):
    return since(mask[::-1], fps, cap)[::-1]


def ffill(x, valid):
    n = len(valid)
    idx = np.where(valid, np.arange(n), -1)
    last = np.maximum.accumulate(idx)
    out = x[np.maximum(last, 0)].copy()
    out[last < 0] = np.nan
    return out


def bfill(x, valid):
    return ffill(x[::-1], valid[::-1])[::-1]


def nan_rolling_mean(a, half):
    """Centred NaN-aware rolling mean along axis 0 (works for (n,...) arrays)."""
    f = np.isfinite(a)
    z = np.where(f, a, 0.0)
    n = a.shape[0]
    c = np.concatenate([np.zeros((1,) + a.shape[1:]), np.cumsum(z, 0)])
    k = np.concatenate([np.zeros((1,) + a.shape[1:]), np.cumsum(f, 0)])
    lo = np.clip(np.arange(n) - half, 0, n)
    hi = np.clip(np.arange(n) + half + 1, 0, n)
    s, m = c[hi] - c[lo], k[hi] - k[lo]
    with np.errstate(invalid='ignore', divide='ignore'):
        out = np.where(m > 0, s / np.maximum(m, 1), np.nan)
    return np.where(f, out, np.nan)


# ----------------------------------------------------------------------------- geometry
def out_dist(pos, L, W):
    """Signed distance to the pitch boundary: positive outside, negative inside."""
    x, y = pos[:, 0], pos[:, 1]
    inside = np.minimum(np.minimum(x, L - x), np.minimum(y, W - y))
    return -inside


def boundary_feats(pos, L, W, tag):
    x, y = pos[:, 0], pos[:, 1]
    d_touch = np.minimum(y, W - y)
    d_goal = np.minimum(x, L - x)
    corner = np.sqrt(d_touch ** 2 + d_goal ** 2)
    center = np.sqrt((x - L / 2) ** 2 + (y - W / 2) ** 2)
    in_box = (d_goal < 16.5) & (np.abs(y - W / 2) < 20.16)
    in_six = (d_goal < 5.5) & (np.abs(y - W / 2) < 9.16)
    f = {f'{tag}_out': out_dist(pos, L, W), f'{tag}_dtouch': d_touch, f'{tag}_dgoal': d_goal,
         f'{tag}_dcorner': corner, f'{tag}_dcenter': center,
         f'{tag}_inbox': np.where(np.isfinite(x), in_box, np.nan),
         f'{tag}_insix': np.where(np.isfinite(x), in_six, np.nan)}
    return f


# ----------------------------------------------------------------------------- blocks
def play_blocks(period):
    p = np.asarray(period)
    ok = np.isin(p, (1, 2))
    edges = np.flatnonzero(np.diff(np.r_[0, ok.astype(np.int8), 0]))
    blocks = []
    for a, b in zip(edges[::2], edges[1::2]):
        # split if the period id changes inside an ok run
        cuts = np.flatnonzero(np.diff(p[a:b])) + 1 + a
        bounds = np.r_[a, cuts, b]
        blocks += [(int(u), int(v)) for u, v in zip(bounds[:-1], bounds[1:])]
    return blocks


def attack_dirs(players, team, L):
    """+1 if the team attacks towards x=L in this block, judged by mean team x over the block."""
    mx = [np.nanmean(players[:, team == k, 0]) for k in (0, 1)]
    if not np.all(np.isfinite(mx)):
        return 1, -1
    return (1, -1) if mx[0] < mx[1] else (-1, 1)


def _block_features(ball, players, team, fps, L, W):
    m, s, _ = players.shape
    F = {}
    T = lambda sec: int(round(sec * fps))
    vis = np.isfinite(ball).all(1)
    pvis = np.isfinite(players).all(2)
    # --- kinematics
    ps = nan_rolling_mean(players.astype(np.float64), 2)
    pv = np.full_like(ps, np.nan)
    pv[2:-2] = (ps[4:] - ps[:-4]) * fps / 4.0
    psp = np.linalg.norm(pv, axis=2)
    psp[psp > 11.0] = np.nan
    pv[~np.isfinite(psp)] = np.nan
    bs = nan_rolling_mean(ball.astype(np.float64), 2)
    bv = np.full((m, 2), np.nan)
    bv[2:-2] = (bs[4:] - bs[:-4]) * fps / 4.0
    one = np.isnan(bv[:, 0])
    alt = np.full((m, 2), np.nan)
    alt[1:-1] = (bs[2:] - bs[:-2]) * fps / 2.0
    bv[one] = alt[one]
    bsp = np.linalg.norm(bv, axis=1)
    bad = bsp > 40.0
    bsp[bad] = np.nan
    bv[bad] = np.nan
    # --- ball visibility / position context
    F['vis'] = vis.astype(float)
    for nm, (a, b) in {'p1': (-T(1), 0), 'f1': (0, T(1)), 'p5': (-T(5), 0), 'f5': (0, T(5)),
                       'c05': (-T(.5), T(.5)), 'c15': (-T(15), T(15))}.items():
        F[f'visfrac_{nm}'] = wsum(vis.astype(float), a, b) / (b - a + 1)
    F['t_since_vis'] = since(vis, fps)
    F['t_until_vis'] = until(vis, fps)
    bh = np.stack([ffill(ball[:, 0], vis), ffill(ball[:, 1], vis)], 1)
    bn = np.stack([bfill(ball[:, 0], vis), bfill(ball[:, 1], vis)], 1)
    F.update(boundary_feats(bh, L, W, 'bh'))
    F.update(boundary_feats(bn, L, W, 'bn'))
    F['bh_bn_dist'] = np.linalg.norm(bh - bn, axis=1)
    F['bsp'] = bsp
    F['bsp_max_p1'] = wmax(bsp, -T(1), 0) if T(1) % 2 == 0 else wmax(bsp, -T(1) - 1, 0)
    F['bsp_max_f1'] = wmax(bsp, 0, T(1) + (T(1) % 2))
    F['bsp_mean_p05'] = wmean(bsp, -T(.5), 0)
    F['bsp_mean_f05'] = wmean(bsp, 0, T(.5))
    moving = np.nan_to_num(bsp) > 2.0
    still = vis & (np.nan_to_num(bsp, nan=99) < 0.7)
    F['t_since_bmove'] = since(moving, fps)
    F['t_until_bmove'] = until(moving, fps)
    F['still_frac_p2'] = wfrac(still, vis, -T(2), 0)
    F['still_frac_f2'] = wfrac(still, vis, 0, T(2))
    F['t_since_fast'] = since(np.nan_to_num(bsp) > 10.0, fps)
    F['t_until_fast'] = until(np.nan_to_num(bsp) > 10.0, fps)
    # --- player kinematics (all players)
    with np.errstate(invalid='ignore'):
        ms = np.nanmean(psp, 1)
        F['ms'] = ms
        npv = np.isfinite(psp).sum(1)
        F['frac_gt2'] = np.where(npv > 0, (psp > 2).sum(1) / np.maximum(npv, 1), np.nan)
        F['frac_gt4'] = np.where(npv > 0, (psp > 4).sum(1) / np.maximum(npv, 1), np.nan)
        F['maxsp'] = np.where(npv > 0, np.nanmax(np.where(np.isfinite(psp), psp, -1), 1), np.nan)
    for nm, (a, b) in {'p1': (-T(1), 0), 'f1': (0, T(1)), 'p3': (-T(3), 0), 'f3': (0, T(3)),
                       'p10': (-T(10), 0), 'f10': (0, T(10))}.items():
        F[f'ms_{nm}'] = wmean(ms, a, b)
        F[f'gt4_{nm}'] = wmean(F['frac_gt4'], a, b)
    F['ms_diff3'] = F['ms_f3'] - F['ms_p3']
    F['ms_diff1'] = F['ms_f1'] - F['ms_p1']
    F['n_players'] = pvis.sum(1).astype(float)
    F['n_players_p5'] = wmean(F['n_players'], -T(5), 0)
    # --- ball impulses (kicks/touches): change of smoothed ball velocity over +-3 frames
    acc = np.full(m, np.nan)
    acc[3:-3] = np.linalg.norm(bv[6:] - bv[:-6], axis=1)
    F['bacc'] = acc
    loc = np.nan_to_num(acc) >= np.nan_to_num(wmax(acc, -3, 3))
    kick = loc & (np.nan_to_num(acc) > 6.0)
    F['t_since_kick'] = since(kick, fps)
    F['t_until_kick'] = until(kick, fps)
    F['kicks_c3'] = wsum(kick.astype(float), -T(3), T(3))
    with np.errstate(invalid='ignore'):
        F['frac_stand'] = np.where(np.isfinite(psp).sum(1) > 0,
                                   (psp < 1.0).sum(1) / np.maximum(np.isfinite(psp).sum(1), 1), np.nan)
    F['stand_p3'] = wmean(F['frac_stand'], -T(3), 0)
    F['stand_f3'] = wmean(F['frac_stand'], 0, T(3))
    # --- formation / dead-ball context
    dh = np.linalg.norm(players - bh[:, None], axis=2)  # distance to last-seen ball
    with np.errstate(invalid='ignore'):
        F['n_within9'] = np.where(np.isfinite(bh[:, 0]), np.nansum(dh < 9.15, 1), np.nan)
        F['n_within3'] = np.where(np.isfinite(bh[:, 0]), np.nansum(dh < 3.0, 1), np.nan)
        F['mean_dist_ball'] = np.nanmean(dh, 1)
    x, y = players[:, :, 0], players[:, :, 1]
    boxl = (x < 16.5) & (np.abs(y - W / 2) < 20.16)
    boxr = (x > L - 16.5) & (np.abs(y - W / 2) < 20.16)
    F['n_box_max'] = np.maximum(boxl.sum(1), boxr.sum(1)).astype(float)
    with np.errstate(invalid='ignore'):
        cx = [np.nanmean(np.where(team[None] == k, x, np.nan), 1) for k in (0, 1)]
        cy = [np.nanmean(np.where(team[None] == k, y, np.nan), 1) for k in (0, 1)]
    F['centroid_gap'] = np.sqrt((cx[0] - cx[1]) ** 2 + (cy[0] - cy[1]) ** 2)
    # --- distances ball <-> players (current frame, raw ball)
    d = np.linalg.norm(players - ball[:, None], axis=2)
    d[~np.isfinite(d)] = np.inf
    dirs = attack_dirs(players, team, L)
    persp = []
    near = []
    for k in (0, 1):
        mk = team == k
        dk_all = np.where(mk[None], d, np.inf)
        jk = np.argmin(dk_all, 1)
        dk = dk_all[np.arange(m), jk]
        dk = np.where(np.isfinite(dk), dk, np.nan)
        near.append(dk)
    for k in (0, 1):
        P = {}
        mk = team == k
        dk = near[k]
        do = near[1 - k]
        dk_all = np.where(mk[None], d, np.inf)
        jk = np.argmin(dk_all, 1)
        P['d'] = dk
        P['d_minus_opp'] = dk - do
        for r in (1.5, 3.0, 5.0):
            P[f'n{r:g}'] = np.where(vis, (dk_all < r).sum(1), np.nan)
        rv = np.linalg.norm(bv - pv[np.arange(m), jk], axis=1)
        P['relv'] = np.where(np.isfinite(dk), rv, np.nan)
        P['nearsp'] = np.where(np.isfinite(dk), psp[np.arange(m), jk], np.nan)
        ctrl = vis & (np.nan_to_num(dk, nan=99) < 1.2) & (np.nan_to_num(rv, nan=99) < 3.0)
        touch = vis & (np.nan_to_num(dk, nan=99) < 0.8)
        nearest = vis & (np.nan_to_num(dk, nan=99) < np.nan_to_num(do, nan=99))
        for nm, (a, b) in {'p05': (-T(.5), 0), 'f05': (0, T(.5)), 'p2': (-T(2), 0), 'f2': (0, T(2)),
                           'c5': (-T(5), T(5))}.items():
            P[f'ctrl_{nm}'] = wsum(ctrl.astype(float), a, b)
        for nm, (a, b) in {'p1': (-T(1), 0), 'f1': (0, T(1)), 'p3': (-T(3), 0), 'f3': (0, T(3)),
                           'p10': (-T(10), 0), 'f10': (0, T(10))}.items():
            P[f'nearfrac_{nm}'] = wfrac(nearest, vis, a, b)
        for nm, (a, b) in {'p05': (-T(.5), 0), 'f05': (0, T(.5)), 'p2': (-T(2), 0), 'f2': (0, T(2))}.items():
            P[f'dmin_{nm}'] = wmin(dk, a, b) if (a + b) % 2 == 0 else wmin(dk, a - 1, b)
        kk = kick & (np.nan_to_num(wmin(dk, -2, 2), nan=99) < 2.0) & \
            (np.nan_to_num(wmin(dk, -2, 2), nan=99) <= np.nan_to_num(wmin(do, -2, 2), nan=99))
        P['t_since_kick'] = since(kk, fps, 20.0)
        P['t_until_kick'] = until(kk, fps, 20.0)
        P['kicks_p2'] = wsum(kk.astype(float), -T(2), 0)
        P['kicks_f2'] = wsum(kk.astype(float), 0, T(2))
        P['kicks_c6'] = wsum(kk.astype(float), -T(6), T(6))
        bfwd = bv[:, 0] * dirs[k]
        P['ball_fwd_p1'] = wmean(bfwd, -T(1), 0)
        P['ball_fwd_f1'] = wmean(bfwd, 0, T(1))
        P['t_since_ctrl'] = since(ctrl, fps, 20.0)
        P['t_until_ctrl'] = until(ctrl, fps, 20.0)
        P['t_since_touch'] = since(touch, fps, 20.0)
        P['t_until_touch'] = until(touch, fps, 20.0)
        P['t_since_near'] = since(nearest, fps, 20.0)
        P['t_until_near'] = until(nearest, fps, 20.0)
        P['d_held'] = ffill(dk, vis)
        P['d_next'] = bfill(dk, vis)
        # team shape in own attacking direction
        dir_k = dirs[k]
        xa = x if dir_k > 0 else L - x
        with np.errstate(invalid='ignore'):
            cxa = np.nanmean(np.where(mk[None], xa, np.nan), 1)
            P['cxa'] = cxa
            P['spread_x'] = np.nanstd(np.where(mk[None], x, np.nan), 1)
            P['spread_y'] = np.nanstd(np.where(mk[None], y, np.nan), 1)
            P['n_vis'] = (pvis & mk[None]).sum(1).astype(float)
            fwd = pv[:, :, 0] * dir_k
            P['fwd_v'] = np.nanmean(np.where(mk[None], fwd, np.nan), 1)
            P['sp'] = np.nanmean(np.where(mk[None], psp, np.nan), 1)
            own_half = np.where(mk[None] & pvis, (xa < L / 2), False).sum(1)
            P['own_half_frac'] = own_half / np.maximum(P['n_vis'], 1)
        P['fwd_v_p1'] = wmean(P['fwd_v'], -T(1), 0)
        P['fwd_v_f1'] = wmean(P['fwd_v'], 0, T(1))
        P['fwd_v_f3'] = wmean(P['fwd_v'], 0, T(3))
        P['fwd_v_p3'] = wmean(P['fwd_v'], -T(3), 0)
        P['spread_x_c2'] = wmean(P['spread_x'], -T(2), T(2))
        P['spread_y_c2'] = wmean(P['spread_y'], -T(2), T(2))
        bxa = bh[:, 0] if dir_k > 0 else L - bh[:, 0]
        P['bxa'] = bxa
        P['bxa_rel'] = bxa - cxa
        dk_held = np.linalg.norm(players - bh[:, None], axis=2)
        with np.errstate(invalid='ignore'):
            P['n5_held'] = np.where(np.isfinite(bh[:, 0]), np.nansum(np.where(mk[None], dk_held < 5, False), 1), np.nan)
        persp.append(P)
    F['kickoff_own_half'] = (persp[0]['own_half_frac'] + persp[1]['own_half_frac']) / 2
    return F, persp


COMMON = None
PERSP = None


def features(match, swap=False, tags=None):
    """(n, k) float32 feature matrix and names. NaN outside play blocks.

    swap=True computes the same features with home/away exchanged (for symmetric team models).
    tags: optional Smart Tagging list (possession.tags); adds tag columns when given.
    """
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        return _features(match, swap, tags)


def _features(match, swap, tags=None):
    global COMMON, PERSP
    fps = float(match['fps'])
    L, W = [float(v) for v in match['pitch']]
    team = np.asarray(match['team']).astype(np.int8)
    if swap:
        team = 1 - team
    n = len(match['ball'])
    out = None
    names = None
    for a, b in play_blocks(match['period']):
        F, persp = _block_features(match['ball'][a:b], match['players'][a:b], team, fps, L, W)
        if tags is not None:
            from .tags import tag_features
            local = [dict(t, start=t['start'] - a, end=t['end'] - a,
                          team=(None if t['team'] is None else (1 - t['team'] if swap else t['team'])))
                     for t in tags if t['end'] > a and t['start'] < b]
            C, TP = tag_features(local, b - a, None, fps)
            F.update({f'tag_{k}': v for k, v in C.items()})
            for i in (0, 1):
                persp[i].update({f'tag_{k}': v for k, v in TP[i].items()})
        cols = [(k, v) for k, v in F.items()]
        for i, P in enumerate(persp):
            cols += [(f'{"hk"[i]}_{k}', v) for k, v in P.items()]
        cols += [(f'diff_{k}', persp[0][k] - persp[1][k]) for k in persp[0]]
        if names is None:
            names = [c for c, _ in cols]
            out = np.full((n, len(names)), np.nan, np.float32)
            COMMON = [c for c in F]
            PERSP = list(persp[0])
        out[a:b] = np.stack([np.asarray(v, np.float32) for _, v in cols], 1)
    return out, names
