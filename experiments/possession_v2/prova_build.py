"""Full-size 'provided-like' rehearsal bundle. Development only; nothing of the provided match is used.

Content: Metrica sample game 3 (both halves) with pieces of sample game 2 appended to fill the published
graded windows; everything outside play is synthesised (people wandering, a warm-up ball). The tracking is
corrupted with possession.degrade, a few duplicated tracks are added, and the tracklets are packed into 46
anonymous slots ('Track 1'..'Track 46') written in Metrica's EPTS layout under the file names of the
competition bundle. A broadcast stream (51 slots, homography validity file) and clock readings of both
recordings are simulated from the same content. Aggregate properties are trimmed to the facts DATA.md
publishes (record counts, slots, frames with a ball, mean tracked objects, usable homography share), so
that possession.inputs_check has a file on which every check should pass.

Usage: prova_build.py OUT_DIR [--seed N] [--profile good|hard]
"""
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade
from possession.features import play_blocks
import synth_clock as sc
from synth_broadcast import _markov

N = 199319
W1 = (11185, 90652)             # [first play frame, end) of the first-half graded window
LEAD = (110808, 113742)         # graded, stated to be all D in FAQ.md
W2 = (113742, 190198)           # second-half play (kick-off frame published in FAQ.md)
GRADED = ((11185, 90652), (110808, 190198))
PITCH = np.array([105.0, 68.0])
FPS = 25.0
PUB = {'ball_total': 113488, 'ball_graded': 94214, 'tracked': 20.5, 'bro_n': 164488, 'bro_ball': 0.505,
       'bro_valid': 0.658, 'bro_invalid_stretches': 122}
PROFILES = {
    # tactical corruption (possession.degrade parameters) and broadcast quality
    'good': ({'ball_miss_alive': 0.06, 'ball_miss_dead_extra': 0.0, 'ball_miss_tau_s': 1.0, 'ball_out_miss': 0.5,
              'ball_crowd_logit': 0.3, 'ball_fast_logit': 0.3, 'ball_sigma_m': 0.15, 'ball_fp_rate': 0.002,
              'player_miss': 0.03, 'player_miss_tau_s': 2.0, 'player_sigma_m': 0.12, 'team_flip_rate': 0.001},
             {'bias_sd': 0.12, 'b_sd': 0.15, 'p_sd': 0.15}),
    'hard': ({'ball_miss_alive': 0.06, 'ball_miss_dead_extra': 0.0, 'ball_miss_tau_s': 1.5, 'ball_out_miss': 0.5,
              'ball_crowd_logit': 0.3, 'ball_fast_logit': 0.3, 'ball_sigma_m': 0.28, 'ball_fp_rate': 0.003,
              'player_miss': 0.03, 'player_miss_tau_s': 3.0, 'player_sigma_m': 0.45, 'team_flip_rate': 0.0015},
             {'bias_sd': 0.45, 'b_sd': 0.35, 'p_sd': 0.35}),
}


def runs(mask):
    d = np.diff(np.r_[0, np.asarray(mask, np.int8), 0])
    return np.flatnonzero(d == 1), np.flatnonzero(d == -1)


def wander(rng, T, base, amp, tau_s, env):
    """base (k,2) plus smooth random offsets of s.d. amp metres, scaled by env (T,) in 0..1."""
    z = rng.standard_normal((T, len(base), 2)).astype(np.float32)
    z = gaussian_filter1d(z, tau_s * FPS, axis=0, mode='nearest')
    z /= z.std(axis=0, keepdims=True) + 1e-9
    out = base[None] + amp * env[:, None, None] * z
    return np.clip(out, -2.0, PITCH + 2.0).astype(np.float32)


def warmup_ball(rng, P):
    """A ball hopping between whoever is on the pitch (P (T,k,2), NaN = absent)."""
    T = len(P)
    out = np.full((T, 2), np.nan, np.float32)
    t, pos = 0, PITCH / 2
    while t < T:
        act = np.flatnonzero(np.isfinite(P[t]).all(1))
        hold = int(rng.uniform(0.5, 3.0) * FPS)
        if len(act):
            target = P[t, rng.choice(act)].astype(float)
            fly = max(1, int(np.linalg.norm(target - pos) / rng.uniform(6, 14) * FPS))
            seg = pos + (target - pos) * np.linspace(0, 1, fly, endpoint=False)[:, None]
            out[t:t + fly] = seg[:T - t]
            t += fly
            pos = target
        out[t:t + hold] = pos
        t += hold
    return out


def assemble(rng):
    """Clean assembled match (wide slot layout: game 3 columns then game 2 columns), labels, play period."""
    m3, l3 = load('MET3')
    m3 = dict(m3, ball=m3['ball'].copy(), players=m3['players'].copy()); l3 = np.asarray(l3).copy()
    m2, l2 = load('MET2')
    S3, S2 = m3['players'].shape[1], m2['players'].shape[1]
    S = S3 + S2
    ball = np.full((N, 2), np.nan, np.float32)
    players = np.full((N, S, 2), np.nan, np.float32)
    lab = np.full(N, 'D', dtype='<U1')
    team = np.r_[m3['team'], m2['team']].astype(np.int8)
    c3, c2 = slice(0, S3), slice(S3, S)
    (a31, b31), (a32, b32) = play_blocks(m3['period'])
    (a21, b21), (a22, b22) = play_blocks(m2['period'])
    src = {}

    def place(dst, m, l, a, k, cols, name):
        ball[dst:dst + k] = m['ball'][a:a + k]
        players[dst:dst + k, cols] = m['players'][a:a + k]
        lab[dst:dst + k] = l[a:a + k]
        src[name] = {'to': [int(dst), int(dst + k)], 'from': [int(a), int(a + k)]}

    for (w, (a3, b3), a2, tag) in ((W1, (a31, b31), a21, 'first half'), (W2, (a32, b32), a22, 'second half')):
        k3 = b3 - a3
        fill = (w[1] - w[0]) - k3
        assert fill > 0
        place(w[0], m3, l3, a3, k3, c3, f'game 3 {tag}')
        place(w[0] + k3, m2, l2, a2, fill, c2, f'game 2 {tag} (start), appended')
        # same side of the pitch for the home team in both pieces
        side = [np.nanmean(players[x:y][:, team == 0, 0]) - np.nanmean(players[x:y][:, team == 1, 0])
                for x, y in ((w[0], w[0] + k3), (w[0] + k3, w[1]))]
        assert side[0] * side[1] > 0, side
    period = np.zeros(N, np.int8)
    period[W1[0]:W1[1]] = 1
    period[W2[0]:W2[1]] = 2

    def segment(a, b, cols_frame, mode):
        """People of the adjacent play frame wander; 'in' = arrive and converge to it, 'out' = start there and leave."""
        T = b - a
        cols = np.flatnonzero(np.isfinite(players[cols_frame]).all(1))
        base = players[cols_frame, cols].astype(np.float32)
        t = np.arange(T)
        if mode == 'in':
            env = np.clip((T - t) / (15 * FPS), 0, 1)
            gone = t[:, None] < (rng.uniform(0, min(100.0, T / FPS / 3), len(cols)) * FPS)[None]
        else:
            env = np.clip(t / (15 * FPS), 0, 1)
            gone = t[:, None] > (rng.uniform(20, min(300.0, T / FPS), len(cols)) * FPS)[None]
        P = wander(rng, T, base, 9.0, 6.0, env)
        P[gone] = np.nan
        players[a:b, cols] = P
        return P

    balls = {}
    P = segment(0, W1[0], W1[0], 'in'); balls[(0, W1[0])] = warmup_ball(rng, P)                    # before the match
    ht0, ht1 = W1[1], LEAD[0]
    P = segment(ht0, ht0 + 2500, W1[1] - 1, 'out'); b1 = warmup_ball(rng, P)                       # walking off
    P = segment(ht1 - 3000, W2[0], W2[0], 'in'); b2 = warmup_ball(rng, P)                          # back, then lining up
    mid = np.full((ht1 - 3000 - (ht0 + 2500), 2), np.nan, np.float32)
    mid[:] = b1[-1]                                                                                # a ball left lying on the pitch
    balls[(ht0, ht1)] = np.concatenate([b1, mid, b2[:3000]])
    lead = b2[3000:].copy()
    spot = int(30 * FPS)
    lead[-spot:] = PITCH / 2                                                                       # on the centre spot
    lead[:-spot][~_markov(len(lead) - spot, 0.3, 50, rng)] = np.nan
    lead[-spot:][~_markov(spot, 0.9, 100, rng)] = np.nan
    ball[LEAD[0]:LEAD[1]] = lead
    P = segment(W2[1], N, W2[1] - 1, 'out'); balls[(W2[1], N)] = warmup_ball(rng, P)               # after the match
    for (a, b), bb in balls.items():
        bb[~_markov(b - a, 0.68, 75, rng)] = np.nan
        ball[a:b] = bb
    m = {'fps': FPS, 'pitch': PITCH.copy(), 'ball': ball, 'players': players, 'team': team, 'period': period}
    return m, lab, src


def drop_runs(present, excess, rng, mean_run):
    """Clear `excess` True cells of a 1-D mask in random runs; returns the cleared mask."""
    present = present.copy()
    while excess > 0:
        idx = np.flatnonzero(present)
        a = int(rng.choice(idx))
        k = min(int(excess), int(rng.geometric(1.0 / mean_run)))
        sel = np.arange(a, min(len(present), a + k))
        sel = sel[present[sel]]
        present[sel] = False
        excess -= len(sel)
    return present


def graded_mask():
    g = np.zeros(N, bool)
    for a, b in GRADED:
        g[a:b] = True
    return g


def trim_ball(ball, rng):
    """Ball frames exactly as published: on graded frames and in total."""
    g = graded_mask()
    fin = np.isfinite(ball).all(1)
    stats = {'graded_before': int(fin[g].sum()), 'other_before': int(fin[~g].sum())}
    for mask, target in ((g, PUB['ball_graded']), (~g, PUB['ball_total'] - PUB['ball_graded'])):
        have = int(fin[mask].sum())
        if have < target:
            raise RuntimeError(f'not enough ball frames: {have} < {target}')
        idx = np.flatnonzero(mask)
        keep = drop_runs(fin[idx], have - target, rng, 12)
        ball[idx[~keep]] = np.nan
    fin = np.isfinite(ball).all(1)
    stats.update(graded=int(fin[g].sum()), total=int(fin.sum()))
    return stats


def duplicates(players, team, rng, rate):
    """Extra tracklets that copy a tracked player for 1-8 s at a small offset (same team 4 times in 5)."""
    n, s, _ = players.shape
    out = []
    fin = np.isfinite(players).all(2)
    for a in np.flatnonzero(rng.random(n) < rate):
        act = np.flatnonzero(fin[a])
        if not len(act):
            continue
        j = int(rng.choice(act))
        b = min(n, a + int(rng.uniform(1, 8) * FPS))
        e = a + int(np.argmin(np.r_[fin[a:b, j], False]))        # until the copied track ends
        off = rng.normal(0, 0.6, 2).astype(np.float32)
        xy = players[a:e, j] + off + rng.normal(0, 0.05, (e - a, 2)).astype(np.float32)
        t = int(team[j]) if rng.random() < 0.8 else 1 - int(team[j])
        out.append((int(a), int(e), t, xy))
    return out


def trim_tracked(players, dups, rng):
    """Mean number of tracked objects on graded frames as published (players and duplicated tracks)."""
    g = graded_mask()
    fin = np.isfinite(players).all(2)
    extra = sum(int(g[a:b].sum()) for a, b, _, _ in dups)
    have = int(fin[g].sum()) + extra
    target = int(round(PUB['tracked'] * g.sum()))
    before = have / g.sum()
    if have < target:
        raise RuntimeError(f'not enough tracked objects: {before:.2f}')
    gi = np.flatnonzero(g)
    cols = np.flatnonzero(fin[g].any(0))
    while have > target:
        j = int(rng.choice(cols))
        a = int(rng.choice(gi))
        k = int(rng.uniform(0.5, 4.0) * FPS)
        sel = np.arange(a, min(N, a + k))
        sel = sel[g[sel] & fin[sel, j]][:have - target]
        fin[sel, j] = False
        players[sel, j] = np.nan
        have -= len(sel)
    return {'before': round(before, 3), 'after': round(have / g.sum(), 4)}


def tracklets(P, team):
    """[(start, end, team, key, xy)] of every run of finite positions of every column."""
    fin = np.isfinite(P).all(2)
    out = []
    for j in range(P.shape[1]):
        s, e = runs(fin[:, j])
        out += [(int(a), int(b), int(team[j]), j, P[a:b, j]) for a, b in zip(s, e)]
    return out


def pack(n, items, slot_team, policy='sticky', gap=25):
    """Tracklets into anonymous slots of their team.

    sticky: a track that reappears within `gap` frames returns to its slot if that is still free, otherwise
            the slot that has been free the longest (identity mostly kept over short losses);
    lru:    always the slot that has been free the longest (identity never kept);
    swap:   always the slot that became free last (a new person follows directly in the same slot)."""
    out = np.full((n, len(slot_team), 2), np.nan, np.float32)
    free_at = np.zeros(len(slot_team), np.int64)
    last = {}
    slots_of = [np.flatnonzero(slot_team == k) for k in (0, 1)]
    peak = [0, 0]
    for a, b, t, key, xy in sorted(items, key=lambda r: (r[0], r[3] if isinstance(r[3], int) else -1)):
        sl = slots_of[t]
        free = sl[free_at[sl] <= a]
        peak[t] = max(peak[t], len(sl) - len(free) + 1)
        if not len(free):
            raise RuntimeError('more simultaneous tracks than slots')
        slot = None
        if policy == 'sticky' and key in last and a - last[key][1] <= gap and free_at[last[key][0]] <= a:
            slot = last[key][0]
        if slot is None:
            slot = free[np.argmax(free_at[free])] if policy == 'swap' else free[np.argmin(free_at[free])]
        out[a:b, slot] = xy
        free_at[slot] = b
        last[key] = (slot, b)
    return out, peak


def speeds(P):
    v = np.zeros(P.shape[:-1], np.float32)
    d = np.linalg.norm(P[2:] - P[:-2], axis=-1) * FPS / 2
    v[1:-1] = np.nan_to_num(d)
    return v


def write_epts(folder, stem, P, ball, slot_team, names=('FC Barcelona', 'Athletic Club')):
    """Metrica EPTS pair in the documented layout of the provided ATD (see tests/test_possession_reader_reference.py)."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    n, slots, _ = P.shape
    X = P / PITCH.astype(np.float32)
    Bn = ball / PITCH.astype(np.float32)
    sp, bs = speeds(P), speeds(ball)
    seen = np.isfinite(X).all(2)
    bseen = np.isfinite(Bn).all(1)
    with open(folder / f'{stem}_atd.txt', 'w', encoding='ascii', newline='\n') as fh:
        for a in range(0, n, 4000):
            xs, ss, oks = X[a:a + 4000].tolist(), sp[a:a + 4000].tolist(), seen[a:a + 4000].tolist()
            bn, bsp, bok = Bn[a:a + 4000].tolist(), bs[a:a + 4000].tolist(), bseen[a:a + 4000].tolist()
            lines = []
            for i, (xi, si, ok) in enumerate(zip(xs, ss, oks)):
                groups = [f'{xy[0]:.5f},{xy[1]:.5f},{v:.3f}' if o else 'NaN,NaN,NaN' for xy, v, o in zip(xi, si, ok)]
                b = f'{bn[i][0]:.5f},{bn[i][1]:.5f},{bsp[i]:.3f}' if bok[i] else 'NaN,NaN,NaN'
                lines.append(f'{a + i + 1}:' + ';'.join(groups) + ':' + b + '\n')
            fh.write(''.join(lines))
    ids = [str(k + 1) for k in range(slots)]
    players = ''.join(f'<Player id="{ids[j]}" teamId="{"TA" if slot_team[j] == 0 else "TB"}"><Name>Track {j + 1}</Name>'
                      f'<ShirtNumber>{j + 1}</ShirtNumber></Player>' for j in range(slots))
    channels = ''.join(f'<PlayerChannel channelId="{c}" id="player{ids[j]}_{c}" playerId="{ids[j]}"/>' for j in range(slots) for c in 'xys')
    refs = ''.join('<SplitRegister separator=",">' + ''.join(f'<PlayerChannelRef playerChannelId="player{ids[j]}_{c}"/>' for c in 'xys')
                   + '</SplitRegister>' for j in range(slots))
    (folder / f'{stem}_atd.xml').write_text(
        '<?xml version="1.0" encoding="utf-8"?><main><Metadata><GlobalConfig><ProviderName>Metrica Sports</ProviderName>'
        '<FrameRate>25</FrameRate><ProviderGlobalParameters>'
        + ''.join(f'<ProviderParameter><Name>{k}</Name><Value>{v}</Value></ProviderParameter>' for k, v in
                  (('first_half_start', 1), ('first_half_end', n // 2), ('second_half_start', n // 2 + 1), ('second_half_end', n)))
        + '</ProviderGlobalParameters></GlobalConfig><Sessions><Session id="session1"><SessionType>Match</SessionType>'
        f'<FieldSize><Width>{PITCH[0]:g}</Width><Height>{PITCH[1]:g}</Height></FieldSize></Session></Sessions>'
        f'<Teams><Team id="TA"><Name>{names[0]}</Name></Team><Team id="TB"><Name>{names[1]}</Name></Team></Teams>'
        f'<Players>{players}</Players><Devices><Device id="device1"><Name>Device 1</Name><Sensors>'
        '<Sensor id="position"><Name>Position</Name><Channels><Channel id="x"><Name>position_x</Name><Unit>normalized</Unit></Channel>'
        '<Channel id="y"><Name>position_y</Name><Unit>normalized</Unit></Channel></Channels></Sensor>'
        '<Sensor id="speed"><Name>Speed</Name><Channels><Channel id="s"><Name>speed</Name><Unit>m/s</Unit></Channel></Channels></Sensor>'
        f'</Sensors></Device></Devices><PlayerChannels>{channels}</PlayerChannels></Metadata>'
        f'<DataFormatSpecifications><DataFormatSpecification endFrame="{n}" separator=":" startFrame="1">'
        f'<StringRegister name="frameCount"/><SplitRegister separator=";">{refs}</SplitRegister>'
        '<SplitRegister separator=","><BallChannelRef channelId="x"/><BallChannelRef channelId="y"/><BallChannelRef channelId="s"/>'
        '</SplitRegister></DataFormatSpecification></DataFormatSpecifications></main>', encoding='utf-8')


def simulate_broadcast(m, lab, rng, q):
    """As work/synth_broadcast3.simulate_warp, with the length of the stream and the unusable stretches
    (count, share, mostly over stoppages) following DATA.md."""
    fps, n = FPS, N
    ball, players, team = m['ball'], m['players'], m['team']
    S = players.shape[1]
    segs, replays = [], []
    for h, (a, e) in enumerate((W1, W2)):
        t0 = max(0, a - int(q['pre_frames'])); t1 = min(n, e + int(q['post_s'] * fps))
        seg_c = list(range(t0, t1)); seg_l = [True] * (t1 - t0)
        steps = int(abs(q['drift']) * (t1 - t0))
        if steps:
            pos = np.sort(rng.choice(np.arange(1, t1 - t0 - 1), steps, replace=False))
            for p in pos[::-1]:
                if q['drift'] > 0:
                    del seg_c[p]; del seg_l[p]
                else:
                    seg_c.insert(p, seg_c[p]); seg_l.insert(p, True)
        seg_clock = list(seg_c)
        labs = lab[t0:t1]
        s_, e_ = runs(labs == 'D')
        for x, y in zip(s_, e_):
            if y - x < 4 * fps or rng.random() > 0.5 or x < a - t0:        # no replays before the kick-off
                continue
            start = x + int(fps)
            dur = int(rng.uniform(4, 12) * fps)
            back = int(rng.uniform(6, 15) * fps)
            slow = rng.random() < 0.5
            for j in range(dur):
                k = start + j
                if k >= len(seg_c):
                    break
                src = start - back + (j // 2 if slow else j)
                seg_c[k] = t0 + max(0, src); seg_l[k] = False
        segs.append((seg_c, seg_l, seg_clock))
    gap = PUB['bro_n'] - sum(len(s[0]) for s in segs)
    assert gap > 250, gap
    content = np.array(segs[0][0] + [-1] * gap + segs[1][0])
    live = np.array(segs[0][1] + [False] * gap + segs[1][1])
    clock = np.array(segs[0][2] + [-1] * gap + segs[1][2])
    B = len(content)
    c = np.where(content >= 0, content, 0)
    # --- unusable stretches: studio, most replays, and close-ups laid over the longest stoppages without a ball
    invalid = content < 0
    rs, re_ = runs(~live & (content >= 0))
    for x, y in zip(rs, re_):
        if rng.random() < 0.85:
            invalid[x:y] = True
    target = int(round((1 - PUB['bro_valid']) * B))
    need = target - int(invalid.sum())
    assert need > 0, need
    noball = ~np.isfinite(ball[c]).all(1) & (content >= 0) & ~invalid
    ns, ne = runs(noball)
    placed = 0
    for r in np.argsort(ns - ne):                                                  # longest stoppage first
        x, y = int(ns[r]), int(ne[r])
        if need <= 0 or y - x < 2 * fps:
            break
        if invalid[max(0, x - 13):y + 13].any():                                   # keep the stretches separate
            continue
        y = min(y, x + need)
        invalid[x:y] = True
        need -= y - x
        placed += 1
    tries = 0
    while need > 0:                                                                # the rest: close-ups during play
        L_ = min(need, int(rng.uniform(3, 10) * fps))
        x = int(rng.integers(0, B - L_))
        tries += 1
        assert tries < 200000
        if invalid[max(0, x - 13):x + L_ + 13].any() or (content[x:x + L_] < 0).any():
            continue
        invalid[x:x + L_] = True
        need -= L_
        placed += 1
    valid = ~invalid
    # --- camera window, per-shot calibration error, visible players
    bf = ball.copy()
    fin = np.isfinite(bf).all(1)
    idx = np.maximum.accumulate(np.where(fin, np.arange(n), -1))
    bf = np.where((idx >= 0)[:, None], bf[np.maximum(idx, 0)], PITCH / 2)
    center = bf[c]
    shots = np.cumsum(rng.random(B) < 1.0 / (rng.uniform(3, 10) * fps))
    ns_ = shots.max() + 1
    bias = rng.normal(0, q['bias_sd'], (ns_, 2))[shots]
    P = players[c].astype(np.float32)
    vis = (np.abs(P[..., 0] - center[:, None, 0]) <= q['hx']) & (np.abs(P[..., 1] - center[:, None, 1]) <= q['hy'])
    vis &= np.isfinite(P).all(2) & valid[:, None]
    A = rng.normal(0, q['bias_sd'] / 20.0, (ns_, 2, 2))[shots]
    P = P + bias[:, None] + np.einsum('bij,bsj->bsi', A, P - center[:, None]) + rng.normal(0, q['p_sd'], P.shape)
    P = P.astype(np.float32)
    P[~vis] = np.nan
    bt = team.copy()
    used = np.flatnonzero(np.isfinite(P).all(2).any(0))
    j = int(rng.choice(used)); bt[j] = 1 - bt[j]                                    # one track with the wrong team
    avail = _markov(B, q['ball_frac'], int(2 * fps), rng) & valid
    bc0 = ball[c].astype(float)
    ball_only = rng.normal(0, 0.25 * q['bias_sd'], (ns_, 2))[shots]
    bb = bc0 + bias + np.einsum('bij,bj->bi', A, np.nan_to_num(bc0 - center)) + ball_only + rng.normal(0, q['b_sd'], (B, 2))
    out = rng.random(B) < q['outlier']
    bb[out] = center[out] + rng.uniform(-10, 10, (int(out.sum()), 2))
    bb[~avail | ~np.isfinite(ball[c]).all(1)] = np.nan
    have, want = int(np.isfinite(bb).all(1).sum()), int(round(PUB['bro_ball'] * B))
    if have < want:
        raise RuntimeError(f'broadcast ball share too low: {have / B:.3f}')
    keep = drop_runs(np.isfinite(bb).all(1), have - want, rng, 20)
    bb[~keep] = np.nan
    info = {'frames': int(B), 'studio_gap_frames': int(gap), 'replays': int(len(rs)), 'invalid_stretches': int(len(runs(invalid)[0])),
            'longest_invalid_s': round(float((runs(invalid)[1] - runs(invalid)[0]).max() / fps), 1),
            'valid_share': round(float(valid.mean()), 4), 'ball_share': round(float(np.isfinite(bb).all(1).mean()), 4),
            'ball_share_before_trim': round(have / B, 4), 'closeups_placed': placed,
            'published_invalid_stretches': PUB['bro_invalid_stretches']}
    return {'ball': bb.astype(np.float32), 'players': P, 'team': bt.astype(np.int8)}, valid, clock, info


def write_homography(path, valid, rng):
    err = rng.gamma(2.0, 0.4, len(valid))
    with open(path, 'w', encoding='ascii', newline='\n') as fh:
        fh.write('frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid\n')
        for i, v in enumerate(valid):
            if v:
                fh.write(f'{i},1822.663,-511.2005,44.48168,1.698323,169.2971,255.7303,-0.01907188,-0.5269586,1,{err[i]:.7g},1\n')
            else:
                fh.write(f'{i},NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,0\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seed', type=int, default=20261111); ap.add_argument('--profile', default='good')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    t0 = time.time()
    rng = np.random.default_rng(a.seed)
    params, bq = PROFILES[a.profile]
    clean, lab, src = assemble(rng)
    print('assembled', round(time.time() - t0), 's', flush=True)
    dm = degrade(clean, lab, rng, dict(params))
    print('degraded', round(time.time() - t0), 's', dm['players'].shape, flush=True)
    ball, players, team = dm['ball'].copy(), dm['players'].copy(), dm['team'].copy()
    bstat = trim_ball(ball, rng)
    dups = duplicates(players, team, rng, 0.0012)
    tstat = trim_tracked(players, dups, rng)
    # reference copy for the in-memory comparison (wide layout, before duplicated tracks and packing)
    id_team = np.r_[np.zeros(30, np.int8), np.ones(30, np.int8)]
    P_id, _ = pack(N, tracklets(players, team), id_team, 'sticky', gap=10 ** 9)      # a track always returns to its own slot
    np.savez_compressed(out / 'truth.npz', lab=lab, period_play=clean['period'], ball=ball, players=P_id, team=id_team)
    del P_id
    slot_team = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]
    rng.shuffle(slot_team)
    items = tracklets(players, team) + [(x, y, t, f'dup{i}', xy) for i, (x, y, t, xy) in enumerate(dups)]
    P46, peak = pack(N, items, slot_team, 'sticky')
    g = graded_mask()
    count = np.isfinite(P46).all(2).sum(1)
    tac = {'tracklets': len(items), 'duplicated_tracks': len(dups), 'peak_simultaneous_per_team': peak,
           'mean_tracked_on_graded': round(float(count[g].mean()), 4), 'share_of_graded_frames_above_22': round(float((count[g] > 22).mean()), 4),
           'ball': bstat, 'tracked_trim': tstat, 'slot_team': slot_team.tolist()}
    print('packed', round(time.time() - t0), 's', json.dumps(tac), flush=True)
    write_epts(out / 'bundle' / 'tactical', 'BAR-ATH_tactical', P46, ball, slot_team)
    print('tactical written', round(time.time() - t0), 's', flush=True)
    del P46, items
    # --- broadcast
    q = {'drift': 2e-5, 'pre_frames': LEAD[1] - LEAD[0], 'post_s': 30.0, 'hx': 26.0, 'hy': 17.0, 'ball_frac': 0.97, 'outlier': 0.01}
    q.update(bq)
    rb = np.random.default_rng(a.seed + 1)
    bro, valid, clock_t, binfo = simulate_broadcast(clean, lab, rb, q)
    print('broadcast simulated', round(time.time() - t0), 's', json.dumps(binfo), flush=True)
    bslot_team = np.r_[np.zeros(26, np.int8), np.ones(25, np.int8)]
    rb.shuffle(bslot_team)
    P51, bpeak = pack(len(valid), tracklets(bro['players'], bro['team']), bslot_team, 'sticky')
    write_epts(out / 'bundle' / 'broadcast', 'BAR-ATH_broadcast', P51, bro['ball'], bslot_team)
    write_homography(out / 'bundle' / 'broadcast' / 'BAR-ATH_broadcast_homography.csv', valid, rb)
    print('broadcast written', round(time.time() - t0), 's', flush=True)
    # --- clock readings of both recordings (kick-off based; second half from 45:00)
    blocks = [W1, W2]
    rc = np.random.default_rng(a.seed + 2)
    for cam, live_t, p_read in (('tactical', np.arange(N), 0.8), ('broadcast', clock_t, 0.7)):
        d = out / 'private' / 'possession-clock' / cam
        d.mkdir(parents=True)
        rows = sc.observations(live_t, blocks, FPS, rc, p_read, 0.02)
        (d / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (d / 'summary.json').write_text('{}')
    # --- synthetic ground truth in the organisers' file layout (X = not graded)
    gt = np.where(g, lab, 'X')
    (out / 'gt').mkdir()
    with open(out / 'gt' / 'PROVA_possession_gt.csv', 'w', newline='\n') as fh:
        fh.write('frame,label\n')
        fh.writelines(f'{i},{l}\n' for i, l in enumerate(gt.tolist()))
    info = {'seed': a.seed, 'profile': a.profile, 'degrade_params': params, 'broadcast_quality': q, 'sources': src,
            'tactical': tac, 'broadcast': dict(binfo, peak_simultaneous_per_team=bpeak),
            'labels_on_graded': {k: int((gt == k).sum()) for k in 'HADX'}, 'seconds': round(time.time() - t0)}
    (out / 'build.json').write_text(json.dumps(info, indent=1))
    print('DONE', json.dumps(info['labels_on_graded']), info['seconds'], 's', flush=True)


if __name__ == '__main__':
    main()
