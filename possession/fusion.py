"""Broadcast ball fill behind an accuracy gate (possession v2.5 candidate, experimental).

The v4 module (possession/broadcast.py) aligns the broadcast tracking to the tactical timeline and
was shown to fill tactical ball gaps correctly, but a broadcast ball with about 1 m of error made
the possession output worse. Here the fill is used only when the two cameras agree closely where
both see the ball: median tactical-broadcast distance <= 0.50 m over at least 120 s of overlap,
with at least 5% of the broadcast frames accepted by the alignment. That distance includes the
tactical error, so it bounds the broadcast error from above. Only missing tactical balls are filled
(tactical balls are never replaced), with the v4 plausibility check against nearby tactical balls.
Thresholds are fixed constants registered in possession-v25-plan.json; nothing is fitted to the
provided match.
"""
import numpy as np

GATE_MEDIAN_M = 0.50
MIN_OVERLAP_S = 120.0
MIN_ACCEPTED = 0.05
VMAX = 35.0          # m/s, as in v4
MARGIN_M = 2.0       # as in v4


def project(bro_ball, t_of_b, T):
    """Broadcast ball on the tactical timeline (NaN where no accepted broadcast frame has a ball)."""
    bb = np.full((T, 2), np.nan)
    acc = np.flatnonzero(t_of_b >= 0)
    has = np.isfinite(bro_ball[acc]).all(1)
    bb[t_of_b[acc[has]]] = bro_ball[acc[has]]
    return bb


def accuracy_gate(tac_ball, bb, t_of_b, fps):
    both = np.isfinite(tac_ball).all(1) & np.isfinite(bb).all(1)
    dist = np.linalg.norm(tac_ball[both] - bb[both], axis=1)
    med = float(np.median(dist)) if len(dist) else float('nan')
    accepted = float(np.mean(t_of_b >= 0)) if len(t_of_b) else 0.0
    checks = {'overlap_frames': int(both.sum()), 'overlap_ok': bool(len(dist) >= MIN_OVERLAP_S * fps),
              'accepted_fraction': round(accepted, 4), 'accepted_ok': bool(accepted >= MIN_ACCEPTED),
              'median_distance_m': round(med, 4) if np.isfinite(med) else None,
              'median_ok': bool(np.isfinite(med) and med <= GATE_MEDIAN_M)}
    return checks['overlap_ok'] and checks['accepted_ok'] and checks['median_ok'], checks


def fill(tac_ball, bb, fps):
    """Fill missing tactical balls with bb where plausible (v4 rule). Returns (ball, filled mask)."""
    T = len(tac_ball)
    tf = np.isfinite(tac_ball).all(1)
    cand = ~tf & np.isfinite(bb).all(1)
    h = int(round(0.5 * fps))
    t = np.arange(T)
    prev = np.maximum.accumulate(np.where(tf, t, -1))
    nxt = np.minimum.accumulate(np.where(tf, t, T)[::-1])[::-1]
    ok = cand.copy()
    for ref in (prev, nxt):
        r = np.clip(ref, 0, T - 1)
        near = (ref >= 0) & (ref < T) & (np.abs(ref - t) <= h)
        dd = np.linalg.norm(bb - tac_ball[r], axis=1)
        lim = VMAX * np.abs(ref - t) / fps + MARGIN_M
        ok &= ~(near & cand & (dd > lim))
    out = tac_ball.copy()
    out[ok] = bb[ok]
    return out, ok


def fuse_gated(tac_ball, bro_ball, t_of_b, fps, graded_mask=None):
    """Gate + fill. Returns (ball for the possession pipeline, report)."""
    T = len(tac_ball)
    bb = project(bro_ball, t_of_b, T)
    used, rep = accuracy_gate(tac_ball, bb, t_of_b, fps)
    rep['used'] = bool(used)
    if not used:
        rep['filled'] = 0
        return tac_ball.copy(), rep
    out, ok = fill(tac_ball, bb, fps)
    cand = ~np.isfinite(tac_ball).all(1) & np.isfinite(bb).all(1)
    rep.update(filled=int(ok.sum()), rejected_implausible=int((cand & ~ok).sum()))
    if graded_mask is not None and graded_mask.any():
        rep['ball_visible_graded_before'] = round(float(np.isfinite(tac_ball[graded_mask]).all(1).mean()), 4)
        rep['ball_visible_graded_after'] = round(float(np.isfinite(out[graded_mask]).all(1).mean()), 4)
    return out, rep


# ---- v2.5b candidate: alignment anchored on the on-screen clock (possession/clocksync.py) ----------
CLOCK_SEARCH_F = 40     # +-1.6 s around the clock lag (clock whole seconds + drift)


def _ball_cost(bro_ball, tac_ball, bs, lag, T):
    t = bs + lag
    ok = (t >= 0) & (t < T)
    b, t = bs[ok], t[ok]
    fin = np.isfinite(bro_ball[b]).all(1) & np.isfinite(tac_ball[t]).all(1)
    if fin.sum() < 200:
        return np.inf
    return float(np.median(np.linalg.norm(bro_ball[b[fin]] - tac_ball[t[fin]], axis=1)))


def orient_at(tac, bro, bro_valid, fps, pitch, halves, lags):
    """Axis flips and team mapping of the broadcast tracking at known per-half lags (no lag search)."""
    from . import broadcast as bc
    T = len(tac['ball'])
    best = None
    for fx, fy in bc.FLIPS:
        b, _ = bc._flip(bro['ball'], bro['players'][:1], pitch, fx, fy)
        costs = []
        for per, a, e in halves:
            if per not in lags:
                continue
            bs = np.flatnonzero(bro_valid)
            bs = bs[(bs + lags[per] >= a) & (bs + lags[per] <= e)][::5]
            costs.append(min(_ball_cost(b, tac['ball'], bs, lags[per] + dd, T)
                             for dd in range(-CLOCK_SEARCH_F, CLOCK_SEARCH_F + 1, 5)))
        c = float(np.mean(costs)) if costs else np.inf
        if best is None or c < best[0]:
            best = (c, fx, fy)
    c, fx, fy = best
    b, p = bc._flip(bro['ball'], bro['players'], pitch, fx, fy)
    out = dict(bro, ball=b, players=p)
    scores = []
    for team in (out['team'], (1 - out['team']).astype(out['team'].dtype)):
        fr = []
        for per, a, e in halves:
            if per not in lags:
                continue
            bs = np.flatnonzero(bro_valid)
            bs = bs[(bs + lags[per] >= a) & (bs + lags[per] <= e)][::25]
            med, cnt = bc._team_nn(out['players'][bs], team, tac['players'][bs + lags[per]], tac['team'])
            fr.append((med <= bc.MATCH_M) & (cnt >= bc.MIN_PLAYERS))
        scores.append(float(np.mean(np.concatenate(fr))) if fr and sum(len(x) for x in fr) else 0.0)
    swap = scores[1] > scores[0]
    if swap:
        out['team'] = (1 - out['team']).astype(out['team'].dtype)
    return out, {'flip_x': fx, 'flip_y': fy, 'ball_cost_m': round(c, 4) if np.isfinite(c) else None,
                 'team_swapped': bool(swap), 'match_fraction': [round(x, 4) for x in scores]}


def align_at(tac, bro, bro_valid, fps, halves, lags):
    """As broadcast.align, but the coarse lag of each half comes from the clock and the window
    refinement searches +-CLOCK_SEARCH_F frames around it."""
    from . import broadcast as bc
    B, T = len(bro['ball']), len(tac['ball'])
    bball = np.where(bro_valid[:, None], bro['ball'], np.nan)
    t_of_b = np.full(B, -1, np.int64)
    report = {'halves': []}
    for per, a, e in halves:
        rep = {'period': int(per)}
        if per not in lags:
            rep['status'] = 'no clock lag'
            report['halves'].append(rep)
            continue
        d = int(lags[per])
        rep['clock_lag'] = d
        b0, b1 = max(0, a - d - CLOCK_SEARCH_F), min(B, e + 1 - d + CLOCK_SEARCH_F)
        win, step = int(bc.WIN_S * fps), int(bc.STEP_S * fps)
        centers, picks = [], []
        for w0 in range(b0, b1, step):
            w1 = min(b1, w0 + win)
            sel = np.arange(w0, w1)
            sel = sel[bro_valid[sel]]
            if len(sel) < 50:
                continue
            bsel = sel[np.isfinite(bball[sel]).all(1)]
            psel = sel[::5]
            def cost(dd):
                tb = bsel + dd
                okb = (tb >= a) & (tb <= e)
                tb, bb_ = tb[okb], bsel[okb]
                fin = np.isfinite(tac['ball'][tb]).all(1)
                cb = np.minimum(np.linalg.norm(bball[bb_[fin]] - tac['ball'][tb[fin]], axis=1), 5.0)
                tp = psel + dd
                okp = (tp >= a) & (tp <= e)
                med, cnt = bc._team_nn(bro['players'][psel[okp]], bro['team'], tac['players'][tp[okp]], tac['team'])
                cp = np.minimum(med[cnt >= bc.MIN_PLAYERS], 5.0)
                k = len(cb) + len(cp)
                return (float((cb.sum() + 0.5 * cp.sum()) / max(len(cb) + 0.5 * len(cp), 1e-9)) if k >= 20
                        else np.inf, dd)
            # coarse-to-fine: every 4th lag over +-CLOCK_SEARCH_F, then +-3 frames around the best
            c0, bd = min(cost(dd) for dd in range(d - CLOCK_SEARCH_F, d + CLOCK_SEARCH_F + 1, 4))
            if np.isfinite(c0):
                c0, bd = min(cost(dd) for dd in range(bd - 3, bd + 4))
            if np.isfinite(c0) and c0 < 2.5:
                centers.append((w0 + w1) / 2.0)
                picks.append(bd)
        nwin = max(1, len(range(b0, b1, step)))
        rep['windows_locked_fraction'] = round(len(picks) / nwin, 4)
        if not picks:
            rep['status'] = 'no window locked'
            report['halves'].append(rep)
            continue
        pk = np.array(picks, float)
        sm = np.array([np.median(pk[max(0, i - 2):i + 3]) for i in range(len(pk))])
        idx = np.arange(b0, b1)
        lag = np.interp(idx, np.array(centers), sm)
        t = np.round(idx + lag).astype(np.int64)
        okt = (t >= a) & (t <= e) & bro_valid[idx]
        med, cnt = np.full(len(idx), np.nan), np.zeros(len(idx), int)
        if okt.any():
            med[okt], cnt[okt] = bc._team_nn(bro['players'][idx[okt]], bro['team'], tac['players'][t[okt]], tac['team'])
        acc = okt & (med <= bc.MATCH_M) & (cnt >= bc.MIN_PLAYERS) & (t_of_b[idx] < 0)
        t_of_b[idx[acc]] = t[acc]
        rep.update(status='ok', accepted_frames=int(acc.sum()), lag_min=int(np.min(lag)), lag_max=int(np.max(lag)))
        report['halves'].append(rep)
    report['accepted_fraction'] = round(float((t_of_b >= 0).mean()), 4)
    return t_of_b, report


def align_auto(tac, bro, bro_valid, fps, pitch, halves, clock_lags=None):
    """Clock-anchored alignment when every half has a clock lag, otherwise the v4 alignment."""
    from . import broadcast as bc
    if clock_lags and all(per in clock_lags for per, _, _ in halves):
        bro2, orep = orient_at(tac, bro, bro_valid, fps, pitch, halves, clock_lags)
        t_of_b, arep = align_at(tac, bro2, bro_valid, fps, halves, clock_lags)
        mode = 'clock'
    else:
        bro2, orep = bc.orient(tac, bro, bro_valid, fps, pitch)
        t_of_b, arep = bc.align(tac, bro2, bro_valid, fps, halves)
        mode = 'tracking'
    return bro2, t_of_b, {'mode': mode, 'orient': orep, 'align': arep}
