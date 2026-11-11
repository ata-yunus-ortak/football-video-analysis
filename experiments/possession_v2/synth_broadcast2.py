"""Synthetic broadcast stream (as synth_broadcast.simulate) that also returns the live timeline shown by the
on-screen clock (replays keep the live clock while showing old content)."""
import numpy as np
import sys
sys.path.insert(0, '/home/claude/sc')
from possession.features import play_blocks
from synth_broadcast import _markov, sample_quality


def simulate_with_clock(m, lab, rng, q):
    fps = float(m['fps'])
    n = len(m['ball'])
    ball, players, team = m['ball'], m['players'], m['team']
    S = players.shape[1]
    # content frame per broadcast frame (-1 = studio), live flag
    content, live, clock = [], [], []
    blocks = play_blocks(m['period'])
    for h, (a, e) in enumerate(blocks):
        t0 = max(0, a - int(q['pre_s'] * fps)); t1 = min(n, e + int(q['post_s'] * fps))
        if h:
            g = int(q['gap_s'] * fps); content += [-1] * g; live += [False] * g; clock += [-1] * g
        seg_c = list(range(t0, t1)); seg_l = [True] * (t1 - t0)
        # drift: occasionally duplicate/drop a frame so that live content slowly shifts
        steps = int(abs(q['drift']) * (t1 - t0))
        if steps:
            pos = np.sort(rng.choice(np.arange(1, t1 - t0 - 1), steps, replace=False))
            for k, p in enumerate(pos[::-1]):
                if q['drift'] > 0:
                    del seg_c[p]; del seg_l[p]
                else:
                    seg_c.insert(p, seg_c[p]); seg_l.insert(p, True)
        seg_clock = list(seg_c)   # live timeline (what the on-screen clock shows), kept through replays
        # replays at dead-ball runs (overwrite live content; timeline length unchanged)
        labs = lab[t0:t1]
        dead = np.r_[False, labs == 'D', False]
        dd = np.flatnonzero(np.diff(dead.astype(np.int8)))
        for s_, e_ in zip(dd[::2], dd[1::2]):
            if e_ - s_ < 4 * fps or rng.random() > 0.5:
                continue
            start = s_ + int(fps)
            dur = int(rng.uniform(4, 12) * fps)
            back = int(rng.uniform(6, 15) * fps)
            slow = rng.random() < 0.5
            for j in range(dur):
                k = start + j
                if k >= len(seg_c):
                    break
                src = start - back + (j // 2 if slow else j)
                seg_c[k] = t0 + max(0, src); seg_l[k] = False
        content += seg_c; live += seg_l; clock += seg_clock
    content = np.array(content); live = np.array(live)
    B = len(content)
    # validity: close-ups on live frames, replays valid with prob 0.3 (per replay run)
    valid = (content >= 0) & ~_markov(B, q['invalid'], int(3 * fps), rng)
    rr = np.r_[False, (~live) & (content >= 0), False]
    rd = np.flatnonzero(np.diff(rr.astype(np.int8)))
    for s_, e_ in zip(rd[::2], rd[1::2]):
        valid[s_:e_] = rng.random() < 0.3
    # camera window around the (ffilled) clean ball of the content frame
    bf = ball.copy()
    fin = np.isfinite(bf).all(1)
    idx = np.maximum.accumulate(np.where(fin, np.arange(n), -1))
    bf = np.where((idx >= 0)[:, None], bf[np.maximum(idx, 0)], np.array(m['pitch']) / 2)
    c = np.where(content >= 0, content, 0)
    center = bf[c]
    # per-shot calibration bias
    shots = np.cumsum(rng.random(B) < 1.0 / (rng.uniform(3, 10) * fps))
    bias = rng.normal(0, q['bias_sd'], (shots.max() + 1, 2))[shots] if q['bias_sd'] > 0 else np.zeros((B, 2))
    P = players[c].astype(float)
    vis = (np.abs(P[..., 0] - center[:, None, 0]) <= q['hx']) & (np.abs(P[..., 1] - center[:, None, 1]) <= q['hy'])
    vis &= np.isfinite(P).all(2) & valid[:, None]
    P = P + bias[:, None] + rng.normal(0, q['p_sd'], P.shape)
    P[~vis] = np.nan
    bt = team.copy()
    j = int(rng.integers(S)); bt[j] = 1 - bt[j]
    avail = _markov(B, q['ball_frac'], int(2 * fps), rng) & valid
    bb = ball[c].astype(float) + bias + rng.normal(0, q['b_sd'], (B, 2))
    out = rng.random(B) < q['outlier']
    bb[out] = center[out] + rng.uniform(-10, 10, (out.sum(), 2))
    bb[~avail | ~np.isfinite(ball[c]).all(1)] = np.nan
    true_t = np.where(live & valid, content, -1)
    bro = {'ball': bb, 'players': P, 'team': bt.astype(np.int8), 'fps': fps, 'pitch': m['pitch'],
           'period': np.ones(B, np.int8)}
    return bro, valid, true_t, np.array(clock)
