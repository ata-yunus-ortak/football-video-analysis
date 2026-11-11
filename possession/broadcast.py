"""Broadcast tracking as a second ball source (experimental, possession v4 candidate).

The broadcast recording has its own timeline (cuts, replays, close-ups) and no mapping to the
tactical video. Both are real-time 25 fps recordings, so live broadcast frames sit at a nearly
constant offset from the tactical frames within a half. This module:

- align():  finds that offset per half from the ball trajectories (masked normalised
            cross-correlation, FFT), refines it in 60 s windows (slow drift) by matching the
            visible broadcast players to the tactical players of the same team, and accepts a
            broadcast frame only when its players match the tactical ones at the mapped frame
            (replays and close-ups fail this check).
- fuse():   fills tactical ball gaps with the aligned broadcast ball, behind a global agreement
            gate (where both cameras see the ball they must agree) and a local plausibility check.

Nothing here was fitted to the provided match; thresholds are fixed constants (see V4 plan).
"""
import numpy as np
from .features import play_blocks

NMIN_OVERLAP_S = 120.0     # minimum overlapping ball frames for a coarse offset
MATCH_M = 2.0              # median player match distance for an accepted broadcast frame
MIN_PLAYERS = 3
WIN_S, STEP_S, DRIFT_F = 60.0, 30.0, 12
GATE_AGREE, GATE_M, MIN_ACCEPTED = 0.70, 2.0, 0.05
VMAX = 35.0                # m/s, plausibility of a filled ball against nearby tactical balls


def read_homography(path, n):
    """valid (bool) and reprojection error per frame from an organiser homography CSV."""
    import csv
    valid = np.zeros(n, bool)
    err = np.full(n, np.nan)
    with open(path, newline='', encoding='utf-8-sig') as fh:
        for row in csv.DictReader(fh):
            try:
                f = int(row['frame'])
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= f < n:
                valid[f] = str(row.get('valid', '0')).strip() in ('1', 'True', 'true')
                try:
                    err[f] = float(row.get('reprojection_error', 'nan'))
                except ValueError:
                    pass
    return valid, err


def _xcorr(u, v, nfft):
    """c[d] = sum_b u[b] v[b+d] for d in (-(len(u)-1) .. len(v)-1), as a dict-free array + offset."""
    U = np.fft.rfft(u, nfft)
    V = np.fft.rfft(v, nfft)
    return np.fft.irfft(np.conj(U) * V, nfft)


def coarse_offset(bro_ball, tac_ball, tac_mask, fps):
    """Lag d (tactical = broadcast + d) maximising the masked NCC of ball x and y.

    tac_mask selects the tactical frames of one half. Returns (d, score, second_best_score).
    """
    B, T = len(bro_ball), len(tac_ball)
    nfft = 1 << int(np.ceil(np.log2(B + T)))
    mg = np.isfinite(bro_ball).all(1).astype(float)
    mf = (np.isfinite(tac_ball).all(1) & tac_mask).astype(float)
    n = _xcorr(mg, mf, nfft)
    total = np.zeros(nfft)
    for j in (0, 1):
        g = np.where(mg > 0, bro_ball[:, j], 0.0)
        f = np.where(mf > 0, tac_ball[:, j], 0.0)
        Sf, Sg = _xcorr(mg, f, nfft), _xcorr(g, mf, nfft)
        Sfg = _xcorr(g, f, nfft)
        Sff, Sgg = _xcorr(mg, f * f, nfft), _xcorr(g * g, mf, nfft)
        with np.errstate(invalid='ignore', divide='ignore'):
            nn = np.maximum(n, 1.0)
            cov = Sfg - Sf * Sg / nn
            var = (Sff - Sf ** 2 / nn) * (Sgg - Sg ** 2 / nn)
            total += np.where(var > 0, cov / np.sqrt(np.maximum(var, 1e-12)), 0.0)
    total[n < NMIN_OVERLAP_S * fps] = -np.inf
    lags = np.arange(nfft)
    lags = np.where(lags < T, lags, lags - nfft)   # circular index -> signed lag (nfft >= B + T)
    ok = (lags > -B) & (lags < T)
    total[~ok] = -np.inf
    i = int(np.argmax(total))
    best, d = float(total[i]), int(lags[i])
    far = np.abs(lags - d) > 5 * fps
    second = float(np.max(np.where(far, total, -np.inf)))
    return d, best, second


def _team_nn(bp, bt, tp, tt):
    """Median distance from visible broadcast players to the nearest tactical player of their team."""
    out = np.full(len(bp), np.nan)
    cnt = np.zeros(len(bp), int)
    for i in range(len(bp)):
        ds = []
        for k in (0, 1):
            a = bp[i][bt == k]
            a = a[np.isfinite(a).all(1)]
            c = tp[i][tt == k]
            c = c[np.isfinite(c).all(1)]
            if len(a) and len(c):
                ds.append(np.min(np.linalg.norm(a[:, None] - c[None], axis=2), axis=1))
        if ds:
            d = np.concatenate(ds)
            out[i], cnt[i] = np.median(d), len(d)
    return out, cnt


FLIPS = ((False, False), (True, False), (False, True), (True, True))


def _flip(ball, players, pitch, fx, fy):
    b, p = ball.copy(), players.copy()
    for j, f in ((0, fx), (1, fy)):
        if f:
            b[:, j] = pitch[j] - b[:, j]
            p[..., j] = pitch[j] - p[..., j]
    return b, p


def orient(tac, bro, bro_valid, fps, pitch):
    """Choose the axis orientation (identity or flips) and team-index mapping of the broadcast
    tracking that best matches the tactical one: by ball NCC over the whole match, then by player
    matching at that lag. Returns (bro oriented, report)."""
    allm = np.ones(len(tac['ball']), bool)
    best = None
    for fx, fy in FLIPS:
        b, _ = _flip(bro['ball'], bro['players'][:1], pitch, fx, fy)
        d, sc, _ = coarse_offset(np.where(bro_valid[:, None], b, np.nan), tac['ball'], allm, fps)
        if best is None or sc > best[0]:
            best = (sc, fx, fy, d)
    sc, fx, fy, d = best
    b, p = _flip(bro['ball'], bro['players'], pitch, fx, fy)
    out = dict(bro, ball=b, players=p)
    bs = np.flatnonzero(bro_valid)
    bs = bs[(bs + d >= 0) & (bs + d < len(tac['ball']))][::25]
    scores = []
    for team in (out['team'], (1 - out['team']).astype(out['team'].dtype)):
        med, cnt = _team_nn(out['players'][bs], team, tac['players'][bs + d], tac['team'])
        scores.append(float(np.mean((med <= MATCH_M) & (cnt >= MIN_PLAYERS))) if len(bs) else 0.0)
    swap = scores[1] > scores[0]
    if swap:
        out['team'] = (1 - out['team']).astype(out['team'].dtype)
    return out, {'flip_x': fx, 'flip_y': fy, 'global_lag': d, 'ncc': round(float(sc), 4),
                 'team_swapped': bool(swap), 'match_fraction': [round(x, 4) for x in scores]}


def align(tac, bro, bro_valid, fps, halves):
    """Map broadcast frames to tactical frames.

    tac/bro: match dicts (ball (n,2), players (n,S,2), team (S,)) in metres on the same pitch.
    halves: [(period, first_tactical_frame, last_tactical_frame)].
    Returns (t_of_b int array, -1 = not accepted; report).
    """
    B, T = len(bro['ball']), len(tac['ball'])
    bball = np.where(bro_valid[:, None], bro['ball'], np.nan)
    t_of_b = np.full(B, -1, np.int64)
    report = {'halves': []}
    for per, a, e in halves:
        tm = np.zeros(T, bool)
        tm[a:e + 1] = True
        d, sc, sc2 = coarse_offset(bball, tac['ball'], tm, fps)
        rep = {'period': int(per), 'coarse_lag': d, 'ncc': round(sc, 4), 'ncc_second': round(sc2, 4)}
        if not np.isfinite(sc) or sc <= 0:
            rep['status'] = 'no overlap'
            report['halves'].append(rep)
            continue
        b0, b1 = max(0, a - d), min(B, e + 1 - d)
        win, step = int(WIN_S * fps), int(STEP_S * fps)
        lag = np.full(B, np.nan)
        centers, picks = [], []
        for w0 in range(b0, b1, step):
            w1 = min(b1, w0 + win)
            sel = np.arange(w0, w1)
            sel = sel[bro_valid[sel]]
            if len(sel) < 50:
                continue
            bsel = sel[np.isfinite(bball[sel]).all(1)]
            psel = sel[::5]
            costs = []
            for dd in range(d - DRIFT_F, d + DRIFT_F + 1):
                # ball term: frames where both cameras see the ball (sharp: the ball moves fast)
                tb = bsel + dd
                okb = (tb >= a) & (tb <= e)
                tb, bb_ = tb[okb], bsel[okb]
                fin = np.isfinite(tac['ball'][tb]).all(1)
                cb = np.minimum(np.linalg.norm(bball[bb_[fin]] - tac['ball'][tb[fin]], axis=1), 5.0)
                # player term on every 5th frame
                tp = psel + dd
                okp = (tp >= a) & (tp <= e)
                med, cnt = _team_nn(bro['players'][psel[okp]], bro['team'], tac['players'][tp[okp]], tac['team'])
                cp = np.minimum(med[cnt >= MIN_PLAYERS], 5.0)
                k = len(cb) + len(cp)
                costs.append((float((cb.sum() + 0.5 * cp.sum()) / max(len(cb) + 0.5 * len(cp), 1e-9)) if k >= 20
                              else np.inf, dd, len(cb), len(cp)))
            c0, bd, nb, npl = min(costs)
            if np.isfinite(c0) and c0 < 2.5:
                centers.append((w0 + w1) / 2.0)
                picks.append(bd)
        if picks:
            pk = np.array(picks, float)
            sm = np.array([np.median(pk[max(0, i - 2):i + 3]) for i in range(len(pk))])   # robust smoothing
            idx = np.arange(b0, b1)
            lag[b0:b1] = np.interp(idx, np.array(centers), sm)
        nwin = max(1, len(range(b0, b1, step)))
        rep['windows_locked_fraction'] = round(len(picks) / nwin, 4)
        if not picks:
            rep['status'] = 'no window locked'
            report['halves'].append(rep)
            continue
        idx = np.arange(b0, b1)
        t = np.round(idx + lag[b0:b1]).astype(np.int64)
        okt = (t >= a) & (t <= e) & bro_valid[idx]
        med, cnt = np.full(len(idx), np.nan), np.zeros(len(idx), int)
        if okt.any():
            med[okt], cnt[okt] = _team_nn(bro['players'][idx[okt]], bro['team'], tac['players'][t[okt]], tac['team'])
        acc = okt & (med <= MATCH_M) & (cnt >= MIN_PLAYERS)
        t_of_b[idx[acc]] = t[acc]
        rep.update(status='ok', accepted_frames=int(acc.sum()), lag_min=int(np.nanmin(lag[b0:b1])),
                   lag_max=int(np.nanmax(lag[b0:b1])))
        report['halves'].append(rep)
    report['accepted_fraction'] = round(float((t_of_b >= 0).mean()), 4)
    return t_of_b, report


def fuse(tac_ball, bro_ball, t_of_b, fps, graded_mask=None):
    """Fill tactical ball gaps with aligned broadcast balls behind agreement and plausibility checks."""
    T = len(tac_ball)
    acc = np.flatnonzero(t_of_b >= 0)
    rep = {'accepted_broadcast_frames': int(len(acc))}
    bb = np.full((T, 2), np.nan)
    has = np.isfinite(bro_ball[acc]).all(1)
    bb[t_of_b[acc[has]]] = bro_ball[acc[has]]
    tf = np.isfinite(tac_ball).all(1)
    both = tf & np.isfinite(bb).all(1)
    dist = np.linalg.norm(tac_ball[both] - bb[both], axis=1)
    agree = float(np.mean(dist <= GATE_M)) if len(dist) else 0.0
    rep.update(overlap_frames=int(both.sum()), agreement=round(agree, 4),
               median_distance_m=round(float(np.median(dist)), 3) if len(dist) else None)
    if len(acc) < MIN_ACCEPTED * len(t_of_b) or len(dist) < NMIN_OVERLAP_S * fps or agree < GATE_AGREE:
        rep.update(used=False, filled=0)
        return tac_ball.copy(), rep
    cand = ~tf & np.isfinite(bb).all(1)
    # plausibility against the nearest tactical ball within +-0.5 s
    h = int(round(0.5 * fps))
    idx = np.where(tf, np.arange(T), -1)
    prev = np.maximum.accumulate(idx)
    nxt = np.where(tf, np.arange(T), T)
    nxt = np.minimum.accumulate(nxt[::-1])[::-1]
    ok = cand.copy()
    for ref in (prev, nxt):
        r = np.clip(ref, 0, T - 1)
        near = (ref >= 0) & (ref < T) & (np.abs(ref - np.arange(T)) <= h)
        dd = np.linalg.norm(bb - tac_ball[r], axis=1)
        lim = VMAX * np.abs(ref - np.arange(T)) / fps + GATE_M
        ok &= ~(near & cand & (dd > lim))
    out = tac_ball.copy()
    out[ok] = bb[ok]
    rep.update(used=True, filled=int(ok.sum()), rejected_implausible=int((cand & ~ok).sum()))
    if graded_mask is not None:
        rep['ball_visible_graded_before'] = round(float(tf[graded_mask].mean()), 4)
        rep['ball_visible_graded_after'] = round(float(np.isfinite(out[graded_mask]).all(1).mean()), 4)
    return out, rep
