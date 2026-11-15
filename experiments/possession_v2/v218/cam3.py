"""K016 exploration, third part: is the gain of F (players the tactical tracking lost, added from the second camera) still
there when the simulated broadcast stream loses and invents players itself? The stream of cam1/cam2 (regime 'good', same
seeds) is degraded before the alignment:
  dropouts   every broadcast track is missing 10% of the time (correlated over 1-3 s), and 25% of the frames in which
             another player is within 0.8 m
  ghosts     four extra tracks (two per team); each shows, for 1-4 s at a time and about 15% of the time, a copy of a
             visible player displaced by 2-5 m, under its team (70%) or the other team (30%)
  teams      two more tracks carry the wrong team for the whole match (the simulator already has one)
Variants: A (the release) and F on this stream. Fixed before any row of this part was computed.
Reporting only; nothing here opens the provided match. Usage: cam3.py PART"""
import sys, json, os, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v218'); sys.path.insert(0, '/home/claude/sc')
import cam1 as C
import cam2 as C2
from scipy.ndimage import gaussian_filter1d
from scipy.stats import norm
X, E = C.X, C.E
from possession.features import play_blocks


def corr(rng, n, tau):
    z = gaussian_filter1d(rng.standard_normal(n), tau, mode='nearest')
    return z / max(z.std(), 1e-9)


def degrade_bro(bro, rng, fps):
    P = np.asarray(bro['players'], np.float64).copy(); team = np.asarray(bro['team']).copy()
    B, S = P.shape[:2]
    vis0 = np.isfinite(P).all(2)
    for j in range(S):                                           # dropouts
        P[corr(rng, B, rng.uniform(1, 3) * fps) < norm.ppf(0.10), j] = np.nan
    for a in range(0, B, 8000):                                  # occlusion
        q = P[a:a + 8000]
        d = np.linalg.norm(q[:, :, None] - q[:, None], axis=3)
        d[:, np.arange(S), np.arange(S)] = np.inf
        close = np.nanmin(np.where(np.isnan(d), np.inf, d), axis=2) < 0.8
        q[close & (rng.random(close.shape) < 0.25)] = np.nan
    for j in rng.choice(S, 2, replace=False):                    # wrong team
        team[j] = 1 - team[j]
    ghosts, gteam = [], []
    for g in range(4):                                           # ghosts
        col = np.full((B, 2), np.nan); t = 0
        while t < B:
            t += int(rng.exponential(rng.uniform(8, 20)) * fps)   # gap between appearances
            dur = int(rng.uniform(1, 4) * fps)
            if t + dur >= B:
                break
            cand = np.flatnonzero(vis0[t])
            if len(cand):
                j = int(cand[rng.integers(len(cand))])
                ang = rng.uniform(0, 2 * np.pi); r = rng.uniform(2, 5)
                col[t:t + dur] = np.asarray(bro['players'], np.float64)[t:t + dur, j] + r * np.array([np.cos(ang), np.sin(ang)])
            t += dur
        ghosts.append(col); gteam.append(g % 2 if rng.random() < 0.7 else 1 - g % 2)
    P = np.concatenate([P, np.stack(ghosts, 1)], 1)
    team = np.r_[team, np.array(gteam, team.dtype)]
    st = {'broadcast_player_positions_before': int(vis0.sum()), 'after_dropouts': int(np.isfinite(P[:, :S]).all(2).sum()),
          'ghost_positions': int(np.isfinite(P[:, S:]).all(2).sum())}
    return dict(bro, players=P.astype(np.asarray(bro['players']).dtype), team=team), st


if __name__ == '__main__':
    part = int(sys.argv[1])
    OUT = f'{C.V}cam3_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': [], 'stats': {}}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    j, regime = 0, 'good'
    for mi, name in enumerate(C.NAMES):
        if mi % 2 != part:
            continue
        key0 = f'{name}|{C.SEED + 10 * mi + j}'
        if all((key0, f'good_degraded|{v}') in done for v in ('A', 'F')):
            continue
        m, lab, seed, mm, path, fixed = C.tactical(name, mi, j)
        per, fps = m['period'], float(m['fps']); graded = per > 0
        blocks = play_blocks(per); halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
        T = len(m['ball']); ri = C.ORDER.index(regime)
        rb = np.random.default_rng(C.STREAM + 100 * ri + 2 * mi + j)
        q = C.quality(rb, regime)
        bro, valid, true_t, clock_t = C.sb3.simulate_warp(m, lab, rb, q)
        bro, dst = degrade_bro(bro, np.random.default_rng(73100 + mi), fps)
        rc = np.random.default_rng(C.CLOCK + 100 * ri + 2 * mi + j)
        pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
        pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
        lags, crep = E.half_lags(C.sc.observations(np.arange(T), blocks, fps, rc, pr_t, pm_t),
                                 C.sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b), fps, halves)
        bro2, t_of_b, arep = E.align_auto(mm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
        reg_ball, rrep = E.register_ball(bro2, mm, t_of_b, fps)
        fb, frep = E.fuse_gated(mm['ball'], reg_ball, t_of_b, fps, graded)
        dst.update(gate_used=bool(frep['used']), gate_median_distance_m=frep.get('median_distance_m'))
        inp = {'A': dict(fixed, ball=np.asarray(fb)) if frep['used'] else fixed}
        if frep['used']:
            pf, tf, n_add = C2.players_fill(mm['players'], mm['team'], bro2['players'], bro2['team'], bro2['ball'], t_of_b, fps)
            ex = pf[:, np.asarray(mm['players']).shape[1]:]
            rr, cc = np.nonzero(np.isfinite(ex).all(2)); sel = slice(None, None, 11)
            err = C.nearest_clean(ex[rr, cc][sel].astype(np.float64), np.asarray(m['players'], np.float64)[rr[sel]])
            dst.update(added_player_positions=int(n_add), share_of_added_within_1m_of_a_clean_player=round(float(np.mean(err <= 1.0)), 3),
                       share_of_frames_with_an_added_player=round(float(np.isfinite(ex).all(2).any(1)[graded].mean()), 4))
            fixed_f, _ = E.keeper2.correct_goalkeepers(dict(mm, players=pf, team=tf))
            inp['F'] = dict(fixed_f, ball=np.asarray(fb))
            del pf, ex
        res['stats'][f'{key0}|good_degraded'] = dst
        del bro, bro2
        for v in ('A', 'F'):
            if (key0, f'good_degraded|{v}') in done or v not in inp:
                continue
            row = X.row_for(name, key0, f'good_degraded|{v}', path, inp[v], lab, per)
            res['rows'].append(row); done.add((key0, f'good_degraded|{v}'))
            json.dump(res, open(OUT + '.tmp', 'w'), indent=0); os.replace(OUT + '.tmp', OUT)
            print(time.strftime('%H:%M:%S'), key0, v, path, 'v2.11', round(row['v2_11']['spell_f1'], 4), 'v2.15', round(row['fused']['spell_f1'], 4), dst, flush=True)
        del inp
    print('done', flush=True)
