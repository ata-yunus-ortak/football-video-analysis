"""Touch and control-change evidence per frame (possession v2.12 candidate; DEVELOPMENT ONLY, not released).

Nothing in the frozen possession-v2.11 chain imports this module, and it imports nothing from it: numpy only.

Why. Diagnosis K007: most missed possessions are shorter than 2 s and the stage-1 probabilities barely show
them. In the DFL development labels a team spell starts when a player of that team plays the ball (at every
team-to-team start of DFL J03WOH, clean tracking, a player of the new team is within 1.5 m of the ball). The
features below try to detect such touches in corrupted tracking (noisy ball, ball missing for runs of frames)
and to say which team made them, without filling the ball track.

Input: the match dict of possession.data (fps, ball (n,2) m with NaN = missing, players (n,S,2) m,
team (S,) 0 = home / 1 = away, period (n,)). Only measured positions are used: no labels, events, video or
provider ownership flags. Everything is computed inside each play block (same blocks as
possession.features.play_blocks), so nothing crosses halftime; rows outside the blocks are NaN, as in
features(). swap=True exchanges the team ids exactly like features(m, swap=True): the h_ and k_ columns
exchange, diff_ columns change sign, common columns are unchanged. The function is deterministic.

Ball kinematics (K = FIT_HALF_S * fps = 7 frames at 25 fps). For every frame t two straight-line fits
(constant velocity) are made by least squares through the VISIBLE ball positions of [t-K, t] (left) and of
[t, t+K] (right); each needs MIN_PTS visible frames, so a few missing frames inside a window are tolerated
and a frame inside a short gap still gets both fits. The ball noise sigma is estimated per block from second
differences of three consecutive visible frames (robust median, floor SIGMA_FLOOR). A one-sided fit is kept
only if its points lie on a line within the noise (residual RMS per coordinate <= RES_K * sigma; a touch or a
false detection inside the window fails this) and its speed is at most VMAX_MS. Touch score
z(t) = |v_right - v_left| / (sigma * sqrt(1/Sxx_left + 1/Sxx_right)), i.e. the velocity change in units of its
own noise standard error. z is set to NaN when the two fits do not meet (|p_left - p_right| > JUMP_M +
3 sigma: a tracking jump or a false detection, not a touch).
Gaps (1..GAP_MAX_S * fps missing frames between visible frames a and b): the left fit ending at a and the
right fit starting at b are compared the same way; if the velocity changed, the touch time is put where the
incoming and the (backwards) outgoing lines pass closest, and the touch position at the middle of the two
lines there. This is an inferred event (kind 1), not a filled ball: no ball coordinate is written anywhere.
Touch events: frames (kind 0) and gaps (kind 1) with z >= Z_TOUCH and |dv| >= DV_TOUCH, thinned by
non-maximum suppression over +-K frames. Each event is attributed to the team of the nearest player
(positions averaged over +-2 frames, so a player missing for 1-2 frames still counts) when that player is
within REACH_M of the touch position; otherwise the event is unattributed.

Columns (common; name prefix tc_):
  tc_z            touch score z at the frame (inside an inferred gap: the gap's score); NaN if not computable
  tc_dv           |v_right - v_left| in m/s at the frame; NaN if not computable
  tc_zmax_c1      max of tc_z over the centred 1 s window [t-W, t+W] (W = WIN_S * fps); NaN if none
  tc_since_any    seconds since the latest touch event of any kind (capped at STATE_CAP_S)
  tc_last_z       z of that event; NaN if none within STATE_CAP_S
  tc_last_dmin    distance (m) of the nearest player to that event's position; NaN if none / no player
  tc_last_gap     1 if that event was inferred across a gap, 0 if seen; NaN if none
  tc_since_change seconds since the latest attributed event whose team differs from the previous attributed
                  event (a control change); capped at STATE_CAP_S
  tc_nchange_p1   number of such changes in the last 1 s (causal window [t - fps, t])
Per team (h_tc_*, k_tc_* for home / away, diff_tc_* = h - k):
  since    seconds since the latest event attributed to the team (capped at STATE_CAP_S)
  last     1 if the latest attributed event (within STATE_CAP_S) is the team's, else 0
  d_last   distance (m) of the team's nearest player to the latest event's position; NaN if none
  n_p1     events attributed to the team in the last 1 s (causal)
  zt_c1    max touch score over [t-W, t+W] among frames whose touch position has the team's player as the
           nearest player within REACH_M (continuous evidence, no event threshold); NaN if none
  cm_p     co-movement over the past window [t-W, t]: |ball displacement - displacement of the team's player
           nearest to the ball at the last visible frame| / elapsed time (m/s), between the first and last
           visible ball frames of the window (at least MIN_SPAN frames apart); NaN otherwise
  cm_f     the same over the future window [t, t+W], player nearest at the first visible frame
  press    opponents within PRESS_M of the team's player nearest to the ball, where the ball is the last
           visible ball position within the past W frames; NaN if there is none
  opp_gap  distance (m) from that player to the nearest opponent; NaN as press
Missing values follow features.py: NaN where a quantity is not measurable, the cap for "since" features.

Time reach (at 25 fps). Window statistics span at most 1 s (centred [t-12, t+12] or causal [t-25, t]).
Look-ahead (latest frame of ball or player data used for frame t): event-state columns (since, last, d_last,
n_p1, since_change, nchange_p1, last_*) t + 22 (an event at or before t may be inferred across a gap of at most
15 frames and confirmed by a 7-frame fit after it); tc_z t + 7 in seen frames, t + 22 inside a gap; tc_dv
t + 7; tc_zmax_c1 and zt_c1 t + 34 (a centred 12-frame window over such scores); cm_f t + 14; cm_p, press,
opp_gap t + 2 (player positions averaged over +-2 frames). Look-back: windows at most 1 s plus a 7-frame fit;
the event-state columns are causal and carry the latest event for at most STATE_CAP_S = 10 s.
"""
import numpy as np

FEATURE_SET = 'touch-v1'
FIT_HALF_S = 0.28      # s; one-sided fit windows [t-K, t] and [t, t+K], K = 7 frames at 25 fps
MIN_PTS = 3            # visible ball frames needed in a one-sided fit
GAP_MAX_S = 0.6        # s; longest run of missing ball frames across which a touch is inferred (15 at 25 fps)
Z_TOUCH = 3.0          # normalised velocity change needed for a touch event
DV_TOUCH = 1.0         # m/s; velocity change needed for a touch event
JUMP_M = 1.0           # m (+ 3 sigma): position discontinuity above this is a jump / false detection
REACH_M = 2.0          # m; an event is attributed to the nearest player only within this distance
SIGMA_FLOOR = 0.03     # m; lower bound of the per-block ball noise estimate
SIGMA_DEFAULT = 0.15   # m; used when a block has too few consecutive visible ball frames
STATE_CAP_S = 10.0     # s; event-age features saturate (causal look-back limit)
WIN_S = 0.5            # s; half-length of centred windows, length of the co-movement windows
PRESS_M = 2.0          # m; opponents counted around the player nearest to the ball
MIN_SPAN = 5           # frames; shortest ball displacement used for co-movement
RES_K = 3.0            # a one-sided fit is valid only if its residual RMS per coordinate <= RES_K * sigma
VMAX_MS = 40.0         # m/s; faster one-sided fits are tracking errors (same cap as features.py)
COMMON = ('z', 'dv', 'zmax_c1', 'since_any', 'last_z', 'last_dmin', 'last_gap', 'since_change', 'nchange_p1')
PERSP = ('since', 'last', 'd_last', 'n_p1', 'zt_c1', 'cm_p', 'cm_f', 'press', 'opp_gap')


# ----------------------------------------------------------------------------- helpers (numpy only)
def play_blocks(period):
    """Contiguous period-1 / period-2 runs; identical logic to possession.features.play_blocks."""
    p = np.asarray(period)
    ok = np.isin(p, (1, 2))
    edges = np.flatnonzero(np.diff(np.r_[0, ok.astype(np.int8), 0]))
    blocks = []
    for a, b in zip(edges[::2], edges[1::2]):
        cuts = np.flatnonzero(np.diff(p[a:b])) + 1 + a
        bounds = np.r_[a, cuts, b]
        blocks += [(int(u), int(v)) for u, v in zip(bounds[:-1], bounds[1:])]
    return blocks


def _shift(x, off, fill):
    """y[t] = x[t + off] where t + off is inside the array, else fill (along axis 0)."""
    m = len(x)
    y = np.full(x.shape, fill, dtype=x.dtype)
    if off >= 0:
        if off < m:
            y[:m - off] = x[off:]
    elif -off < m:
        y[-off:] = x[:m + off]
    return y


def _wsum(x, a, b):
    """Sum of x over [t+a, t+b], clipped to the array."""
    n = len(x)
    c = np.concatenate(([0.0], np.cumsum(x, dtype=np.float64)))
    lo = np.clip(np.arange(n) + a, 0, n)
    hi = np.clip(np.arange(n) + b + 1, 0, n)
    return c[hi] - c[lo]


def _wmax(x, a, b):
    """NaN-aware max over [t+a, t+b]; NaN where the window has no finite value."""
    y = np.where(np.isfinite(x), x, -np.inf)
    out = np.full(len(x), -np.inf)
    for o in range(a, b + 1):
        np.maximum(out, _shift(y, o, -np.inf), out=out)
    return np.where(np.isfinite(out), out, np.nan)


def _smooth_players(P, h=2):
    """Centred NaN-aware mean over +-h frames (a player missing for <= h frames gets a position)."""
    f = np.isfinite(P).all(2)
    z = np.where(f[..., None], P, 0.0)
    s = np.zeros_like(z)
    k = np.zeros(f.shape)
    for o in range(-h, h + 1):
        s += _shift(z, o, 0.0)
        k += _shift(f, o, False)
    out = s / np.maximum(k, 1)[..., None]
    out[k == 0] = np.nan
    return out


def _noise(B, vis):
    """Robust per-block ball noise (m): MAD of second differences of three consecutive visible frames."""
    if len(B) < 3:
        return SIGMA_DEFAULT
    tri = vis[:-2] & vis[1:-1] & vis[2:]
    if tri.sum() < 50:
        return SIGMA_DEFAULT
    d2 = (B[2:] - 2.0 * B[1:-1] + B[:-2])[tri]
    return float(max(SIGMA_FLOOR, 1.4826 * np.median(np.abs(d2)) / np.sqrt(6.0)))


def _side_fit(B, vis, K, side, sigma, fps):
    """Least-squares line through the visible ball frames of [t-K, t] (side -1) or [t, t+K] (side +1).

    Returns position at t (m), velocity (m/frame) and Sxx (sum of squared offsets about their mean).
    NaN where fewer than MIN_PTS frames are visible, where the points are not a straight line within the noise
    (residual RMS per coordinate > RES_K * sigma: a touch or a jump inside the window) or where the speed
    exceeds VMAX_MS (as features.py, faster is a tracking error).
    """
    m = len(B)
    Bz = np.where(vis[:, None], B, 0.0)
    S0 = np.zeros(m); S1 = np.zeros(m); S2 = np.zeros(m)
    Sx = np.zeros((m, 2)); Sxo = np.zeros((m, 2))
    for o in range(K + 1):
        off = side * o
        w = _shift(vis, off, False).astype(np.float64)
        x = _shift(Bz, off, 0.0)
        S0 += w; S1 += w * off; S2 += w * (off * off)
        Sx += x; Sxo += x * off
    den = S0 * S2 - S1 * S1
    ok = (S0 >= MIN_PTS) & (den > 0)
    dd = np.where(ok, den, 1.0)
    s0 = np.where(ok, S0, 1.0)
    v = (S0[:, None] * Sxo - S1[:, None] * Sx) / dd[:, None]
    p = (Sx - v * S1[:, None]) / s0[:, None]
    rss = np.zeros(m)
    for o in range(K + 1):
        off = side * o
        w = _shift(vis, off, False)
        r = _shift(Bz, off, 0.0) - p - v * off
        rss += np.where(w, (r * r).sum(1), 0.0)
    ok &= rss <= 2.0 * np.maximum(S0 - 2.0, 1.0) * (RES_K * sigma) ** 2
    ok &= np.linalg.norm(v, axis=1) * fps <= VMAX_MS
    sxx = np.where(ok, dd / s0, np.nan)
    v[~ok] = np.nan
    p[~ok] = np.nan
    return p, v, sxx


def _latest(et, mask_e, m):
    """Index (into the time-sorted events) of the latest masked event at or before each frame; -1 if none."""
    arr = np.full(m, -1, np.int64)
    sel = np.flatnonzero(mask_e)
    arr[et[sel]] = sel
    return np.maximum.accumulate(arr) if m else arr


def _take(values, li, fill=np.nan):
    out = np.full(len(li), fill, np.float64)
    ok = li >= 0
    if ok.any():
        out[ok] = np.asarray(values, np.float64)[li[ok]]
    return out


# ----------------------------------------------------------------------------- one play block
def _events(B, vis, P, tm, fps, K, G):
    """Touch score per frame and attributed touch events of one block."""
    m = len(B)
    anyteam = (tm == 0) | (tm == 1)
    sigma = _noise(B, vis)
    pL, vL, sL = _side_fit(B, vis, K, -1, sigma, fps)
    pR, vR, sR = _side_fit(B, vis, K, +1, sigma, fps)
    se = sigma * np.sqrt(1.0 / sL + 1.0 / sR)
    dvn = np.linalg.norm(vR - vL, axis=1)
    z = dvn / se
    cont = np.isfinite(z) & (np.linalg.norm(pR - pL, axis=1) <= JUMP_M + 3.0 * sigma)
    zf = np.where(cont, z, np.nan)
    dvms = np.where(cont, dvn * fps, np.nan)
    pt = 0.5 * (pL + pR)
    zfill = zf.copy()
    # --- inferred events across gaps of 1..G missing frames
    iv = np.flatnonzero(vis)
    tg = np.zeros(0, np.int64); zg = np.zeros(0); pg = np.zeros((0, 2))
    if len(iv) >= 2:
        g = np.diff(iv) - 1
        sel = (g >= 1) & (g <= G)
        a, b = iv[:-1][sel], iv[1:][sel]
        ok = np.isfinite(vL[a]).all(1) & np.isfinite(vR[b]).all(1)
        a, b = a[ok], b[ok]
        if len(a):
            va, vb, pa, pb = vL[a], vR[b], pL[a], pR[b]
            seg = sigma * np.sqrt(1.0 / sL[a] + 1.0 / sR[b])
            dg = np.linalg.norm(vb - va, axis=1)
            zgap = dg / seg
            span = (b - a).astype(np.float64)
            c = pa - pb + vb * span[:, None]          # incoming minus outgoing line at u = 0 (u = t - a)
            e = va - vb
            ee = (e * e).sum(1)
            u = np.where(ee > 0, -(c * e).sum(1) / np.where(ee > 0, ee, 1.0), 0.5 * span)
            u = np.clip(u, 0.0, span)
            pin = pa + va * u[:, None]
            pout = pb + vb * (u - span)[:, None]
            miss = np.linalg.norm(pin - pout, axis=1)
            fit_ok = miss <= JUMP_M + 3.0 * sigma + 3.0 * seg * span / 2.0
            for i in np.flatnonzero(fit_ok):
                w = zfill[a[i] + 1:b[i]]
                zfill[a[i] + 1:b[i]] = np.where(np.isfinite(w), w, zgap[i])
            good = fit_ok & (zgap >= Z_TOUCH) & (dg * fps >= DV_TOUCH)
            tg = np.rint(a[good] + u[good]).astype(np.int64)
            zg = zgap[good]
            pg = 0.5 * (pin + pout)[good]
    # --- frame candidates + gap candidates, non-maximum suppression over +-K frames
    cf = np.flatnonzero(np.isfinite(zf) & (zf >= Z_TOUCH) & (dvms >= DV_TOUCH))
    T = np.r_[cf, tg].astype(np.int64)
    Z = np.r_[zf[cf], zg]
    PP = np.concatenate([pt[cf], pg], 0)
    KIND = np.r_[np.zeros(len(cf)), np.ones(len(tg))]
    taken = np.zeros(m, bool)
    keep = []
    for i in np.lexsort((T, -Z)):
        t = T[i]
        if taken[t]:
            continue
        keep.append(i)
        taken[max(0, t - K):t + K + 1] = True
    keep = np.array(keep, np.int64)
    if len(keep):
        keep = keep[np.argsort(T[keep], kind='stable')]
    et, ez, ep, ek = T[keep], Z[keep], PP[keep].reshape(-1, 2), KIND[keep]
    # --- attribution to the nearest player of either team
    E = len(et)
    if E:
        dd = np.linalg.norm(P[et] - ep[:, None], axis=2)
        dd = np.where(np.isfinite(dd) & anyteam[None], dd, np.inf)
        j = np.argmin(dd, 1)
        d1 = dd[np.arange(E), j]
        att = np.where(d1 <= REACH_M, tm[j], -1).astype(np.int64)
        dk = [np.where((tm == k)[None], dd, np.inf).min(1) for k in (0, 1)]
        dk = [np.where(np.isfinite(x), x, np.nan) for x in dk]
        d1 = np.where(np.isfinite(d1), d1, np.nan)
    else:
        att = np.zeros(0, np.int64); d1 = np.zeros(0); dk = [np.zeros(0), np.zeros(0)]
    # --- continuous per-team touch evidence at every frame with a score
    dpt = np.linalg.norm(P - pt[:, None], axis=2)
    dpt = np.where(np.isfinite(dpt) & anyteam[None], dpt, np.inf)
    j1 = np.argmin(dpt, 1)
    dn = dpt[np.arange(m), j1]
    k1 = np.where(np.isfinite(dn) & (dn <= REACH_M), tm[j1], -1)
    zt = [np.where(np.isfinite(zf) & (k1 == k), zf, np.nan) for k in (0, 1)]
    for i in np.flatnonzero((ek == 1) & (att >= 0)):     # inferred gap events count at their touch frame
        k, t = int(att[i]), int(et[i])
        zt[k][t] = ez[i] if not np.isfinite(zt[k][t]) else max(zt[k][t], ez[i])
    return dict(zfill=zfill, dvms=dvms, et=et, ez=ez, ek=ek, att=att, d1=d1, dk=dk, zt=zt, sigma=sigma)


def _block(ball, players, team, fps):
    m = len(ball)
    K = max(2, int(round(FIT_HALF_S * fps)))
    G = max(1, int(round(GAP_MAX_S * fps)))
    W = max(1, int(round(WIN_S * fps)))
    T1 = max(1, int(round(fps)))
    cap = STATE_CAP_S
    B = np.asarray(ball, np.float64).copy()
    vis = np.isfinite(B).all(1)
    B[~vis] = np.nan
    P = _smooth_players(np.asarray(players, np.float64), 2)
    tm = np.asarray(team)
    ev = _events(B, vis, P, tm, fps, K, G)
    et, ez, ek, att, d1, dk = ev['et'], ev['ez'], ev['ek'], ev['att'], ev['d1'], ev['dk']
    idx = np.arange(m)
    F = {'z': ev['zfill'], 'dv': ev['dvms'], 'zmax_c1': _wmax(ev['zfill'], -W, W)}
    # --- event state (causal)
    li = _latest(et, np.ones(len(et), bool), m)
    age = np.where(li >= 0, (idx - _take(et, li, 0)) / fps, np.inf)
    rec = li.copy()
    rec[age > cap] = -1
    F['since_any'] = np.minimum(age, cap)
    F['last_z'] = _take(ez, rec)
    F['last_dmin'] = _take(d1, rec)
    F['last_gap'] = _take(ek, rec)
    ia = np.flatnonzero(att >= 0)
    chg = np.zeros(len(et), bool)
    if len(ia) > 1:
        chg[ia[1:][att[ia[1:]] != att[ia[:-1]]]] = True
    lc = _latest(et, chg, m)
    F['since_change'] = np.minimum(np.where(lc >= 0, (idx - _take(et, lc, 0)) / fps, np.inf), cap)
    ind = np.zeros(m)
    ind[et[chg]] = 1.0
    F['nchange_p1'] = _wsum(ind, -T1, 0)
    la = _latest(et, att >= 0, m)
    agea = np.where(la >= 0, (idx - _take(et, la, 0)) / fps, np.inf)
    lat = np.where((la >= 0) & (agea <= cap), _take(att, la, -1), -1)
    # --- ball reference frames for co-movement and pressure (a play block has at least one frame)
    last = m - 1
    lastvis = np.maximum.accumulate(np.where(vis, idx, -1))
    nextvis = np.minimum.accumulate(np.where(vis, idx, m)[::-1])[::-1]
    db = np.linalg.norm(P - B[:, None], axis=2)
    db = np.where(np.isfinite(db), db, np.inf)
    s1p = lastvis
    s0p = nextvis[np.clip(idx - W, 0, last)]
    okp = (s1p >= 0) & (s1p >= idx - W) & (s1p - s0p >= MIN_SPAN)
    s0f = nextvis
    s1f = lastvis[np.clip(idx + W, 0, last)]
    okf = (s0f < m) & (s0f <= idx + W) & (s1f - s0f >= MIN_SPAN)
    href = (s1p >= 0) & (s1p >= idx - W)
    bref = np.where(href[:, None], B[np.clip(s1p, 0, last)], np.nan)
    dref = np.linalg.norm(P - bref[:, None], axis=2)
    dref = np.where(np.isfinite(dref), dref, np.inf)
    persp = []
    for k in (0, 1):
        mk = tm == k
        mo = tm == 1 - k
        Q = {}
        lk = _latest(et, att == k, m)
        Q['since'] = np.minimum(np.where(lk >= 0, (idx - _take(et, lk, 0)) / fps, np.inf), cap)
        Q['last'] = (lat == k).astype(np.float64)
        Q['d_last'] = _take(dk[k], rec)
        indk = np.zeros(m)
        indk[et[att == k]] = 1.0
        Q['n_p1'] = _wsum(indk, -T1, 0)
        Q['zt_c1'] = _wmax(ev['zt'][k], -W, W)
        dbk = np.where(mk[None], db, np.inf)
        jk = np.argmin(dbk, 1)
        hask = np.isfinite(dbk[idx, jk])
        cm = []
        for ok, r0, r1, ref in ((okp, s0p, s1p, s1p), (okf, s0f, s1f, s0f)):
            r0c, r1c, refc = (np.clip(r, 0, last) for r in (r0, r1, ref))
            j = jk[refc]
            dB = B[r1c] - B[r0c]
            dPj = P[r1c, j] - P[r0c, j]
            v = np.linalg.norm(dB - dPj, axis=1) / np.maximum(r1c - r0c, 1) * fps
            cm.append(np.where(ok & hask[refc] & np.isfinite(v), v, np.nan))
        Q['cm_p'], Q['cm_f'] = cm
        drk = np.where(mk[None], dref, np.inf)
        jr = np.argmin(drk, 1)
        okr = np.isfinite(drk[idx, jr])
        pj = P[idx, jr]
        dop = np.linalg.norm(P - pj[:, None], axis=2)
        dop = np.where(np.isfinite(dop) & mo[None], dop, np.inf)
        npress = (dop < PRESS_M).sum(1).astype(np.float64)
        gap = dop.min(1)
        Q['press'] = np.where(okr, npress, np.nan)
        Q['opp_gap'] = np.where(okr & np.isfinite(gap), gap, np.nan)
        persp.append(Q)
    return F, persp, ev


def touch_features(match, swap=False):
    """(n, k) float32 touch/control-change features and their names; NaN outside play blocks.

    swap=True exchanges home and away exactly like possession.features.features(match, swap=True).
    """
    with np.errstate(invalid='ignore', divide='ignore', over='ignore'):
        return _touch_features(match, swap)


def _names():
    names = [f'tc_{c}' for c in COMMON]
    names += [f'{"hk"[i]}_tc_{c}' for i in (0, 1) for c in PERSP]
    names += [f'diff_tc_{c}' for c in PERSP]
    return names


def _touch_features(match, swap):
    fps = float(match['fps'])
    team = np.asarray(match['team']).astype(np.int8)
    if swap:
        team = 1 - team
    n = len(match['ball'])
    names = _names()
    out = np.full((n, len(names)), np.nan, np.float32)
    for a, b in play_blocks(match['period']):
        F, persp, _ = _block(np.asarray(match['ball'][a:b]), np.asarray(match['players'][a:b]), team, fps)
        cols = [F[c] for c in COMMON]
        cols += [persp[i][c] for i in (0, 1) for c in PERSP]
        cols += [persp[0][c] - persp[1][c] for c in PERSP]
        out[a:b] = np.stack([np.asarray(v, np.float32) for v in cols], 1)
    return out, names


def touch_events(match, swap=False):
    """Detected touch events over the whole match (absolute frames), for diagnostics and tests.

    Returns a dict of arrays: frame, team (0/1, -1 = unattributed), z, kind (0 seen, 1 inferred across a gap),
    dmin (distance of the nearest player, m), and the per-block ball noise estimates.
    """
    fps = float(match['fps'])
    team = np.asarray(match['team']).astype(np.int8)
    if swap:
        team = 1 - team
    K = max(2, int(round(FIT_HALF_S * fps)))
    G = max(1, int(round(GAP_MAX_S * fps)))
    parts = {'frame': [], 'team': [], 'z': [], 'kind': [], 'dmin': []}
    sig = []
    with np.errstate(invalid='ignore', divide='ignore', over='ignore'):
        for a, b in play_blocks(match['period']):
            B = np.asarray(match['ball'][a:b], np.float64).copy()
            vis = np.isfinite(B).all(1)
            B[~vis] = np.nan
            P = _smooth_players(np.asarray(match['players'][a:b], np.float64), 2)
            ev = _events(B, vis, P, np.asarray(team), fps, K, G)
            parts['frame'].append(ev['et'] + a); parts['team'].append(ev['att']); parts['z'].append(ev['ez'])
            parts['kind'].append(ev['ek']); parts['dmin'].append(ev['d1']); sig.append(ev['sigma'])
    out = {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in parts.items()}
    out['frame'] = out['frame'].astype(np.int64)
    out['team'] = out['team'].astype(np.int64)
    out['sigma'] = np.array(sig)
    return out
