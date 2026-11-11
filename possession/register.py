"""Broadcast ball registered to the tactical frame through the players (possession v2.9 candidate).

The broadcast homography has a calibration error that changes from shot to shot. Players that both
cameras see give a direct measurement of it: after the time alignment, a broadcast player and the
tactical player of the same team at the same place are the same person, and the difference of
their positions is the local error of the broadcast mapping. For every accepted broadcast frame
the error at the ball is estimated from the matched players (those near the ball weigh more), the
estimate is median-filtered over +-0.5 s, and it is subtracted from the broadcast ball. The ball is
then smoothed over +-2 frames (as possession/smooth.py does for the tactical positions). Frames
without a usable estimate get no broadcast ball. The accuracy gate of possession/fusion.py is
applied afterwards, on ball positions that this step never used, so it remains an independent check.

Fixed constants (possession-v29-plan.json); nothing is fitted to the provided match.
"""
import numpy as np

MATCH_R_M = 3.0        # a broadcast player is matched to the mutually nearest tactical player within this
TRIM_M = 1.0           # matches farther than this from the median residual are dropped
MIN_MATCHES = 3
WEIGHT_SIGMA_M = 12.0  # Gaussian weight of a match by its distance to the broadcast ball
MEDIAN_HALF_S = 0.5
SMOOTH_HALF = 2        # frames, ball smoothing after the correction


def frame_offsets(bro_players, bro_team, bro_ball, tac_players, tac_team, t_of_b, chunk=2000):
    """(B, 2) estimated broadcast-minus-tactical offset at the ball; NaN where not estimable."""
    B = len(t_of_b)
    off = np.full((B, 2), np.nan)
    acc = np.flatnonzero(t_of_b >= 0)
    bro_team = np.asarray(bro_team); tac_team = np.asarray(tac_team)
    for s in range(0, len(acc), chunk):
        idx = acc[s:s + chunk]
        res_all, w_all = [], []
        for k in (0, 1):
            bp = bro_players[idx][:, bro_team == k].astype(np.float64)       # (n, nb, 2)
            tp = tac_players[t_of_b[idx]][:, tac_team == k].astype(np.float64)  # (n, nt, 2)
            if bp.shape[1] == 0 or tp.shape[1] == 0:
                continue
            d = np.linalg.norm(bp[:, :, None] - tp[:, None], axis=3)
            d[~np.isfinite(d)] = np.inf
            jb = d.argmin(2)                                   # nearest tactical for each broadcast player
            ib = d.argmin(1)                                   # nearest broadcast for each tactical player
            n, nb = jb.shape
            rows = np.arange(n)[:, None]
            dmin = d[rows, np.arange(nb)[None], jb]
            mutual = ib[rows, jb] == np.arange(nb)[None]
            ok = mutual & (dmin <= MATCH_R_M)
            r = bp - tp[rows, jb]
            r[~ok] = np.nan
            db = np.linalg.norm(bp - bro_ball[idx][:, None], axis=2)
            w = np.where(np.isfinite(db), np.exp(-0.5 * (db / WEIGHT_SIGMA_M) ** 2), 1.0)
            w[~ok] = 0.0
            res_all.append(r); w_all.append(w)
        if not res_all:
            continue
        r = np.concatenate(res_all, 1); w = np.concatenate(w_all, 1)
        with np.errstate(all='ignore'):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                med = np.nanmedian(r, axis=1)
        keep = (w > 0) & (np.linalg.norm(np.nan_to_num(r, nan=1e9) - np.nan_to_num(med, nan=0.0)[:, None], axis=2) <= TRIM_M)
        w = np.where(keep, w, 0.0)
        cnt = keep.sum(1); sw = w.sum(1)
        est = (np.nan_to_num(r) * w[..., None]).sum(1) / np.maximum(sw, 1e-12)[:, None]
        good = (cnt >= MIN_MATCHES) & (sw > 1e-9)
        est[~good] = np.nan
        off[idx] = est
    return off


def _nan_window(x, half, fn):
    """Centred NaN-aware window statistic over +-half rows of an (n, 2) array (NaN stays NaN where all are NaN)."""
    import warnings
    n = len(x)
    pad = np.full((half, x.shape[1]), np.nan)
    xp = np.concatenate([pad, x, pad])
    win = np.lib.stride_tricks.sliding_window_view(xp, 2 * half + 1, axis=0)   # (n, 2, 2*half+1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        return fn(win, axis=2)


def register_ball(bro, tac, t_of_b, fps):
    """Broadcast ball corrected by the player-based offset and smoothed. Returns (ball, report)."""
    ball = np.asarray(bro['ball'], np.float64)
    off = frame_offsets(np.asarray(bro['players']), bro['team'], ball, np.asarray(tac['players']), tac['team'], t_of_b)
    sm = _nan_window(off, int(round(MEDIAN_HALF_S * fps)), np.nanmedian)
    sm[t_of_b < 0] = np.nan
    out = ball - sm                                   # NaN offset -> no ball
    fin = np.isfinite(out).all(1)
    out[~fin] = np.nan
    sm_ball = _nan_window(out, SMOOTH_HALF, np.nanmean)
    sm_ball[~fin] = np.nan
    had = np.isfinite(ball).all(1) & (t_of_b >= 0)
    mag = np.linalg.norm(sm[fin], axis=1)
    rep = {'accepted_ball_frames': int(had.sum()), 'registered_ball_frames': int(fin.sum()),
           'median_offset_m': round(float(np.median(mag)), 4) if len(mag) else None,
           'p90_offset_m': round(float(np.percentile(mag, 90)), 4) if len(mag) else None}
    return sm_ball, rep
