"""v2.9 validation (possession-v29-plan.json): v2.4 vs v2.5b vs v2.9 (player-registered, smoothed broadcast ball)
on 16 new tactical copies x 3 regimes of the warp simulator (synth_broadcast3). Usage: exp_v29.py KIND"""
import sys, json, time, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.fusion import fuse_gated, align_auto, project
from possession.register import register_ball
from possession.clocksync import half_lags
from possession.noise import estimate_noise, choose_path
from possession.features import play_blocks
import synth_broadcast3 as sb3
import synth_clock as sc
from exp_v25 import run_path, quality, REGIMES, NAMES

PROF = {'orig': (RANGES, 4100, 0), 'ext_players': (dict(RANGES, player_sigma_m=(0.3, 0.6)), 4500, 8)}
if __name__ == '__main__':
    kind = sys.argv[1]
    ranges, base, c0 = PROF[kind]
    OUT = f'/home/claude/work/exp_v29_{kind}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['copy'], r['regime']) for r in res['rows']}
    for i, name in enumerate(NAMES):
        m, lab = load(name)
        per, fps = m['period'], float(m['fps']); graded = per > 0
        blocks = play_blocks(per); halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
        T = len(m['ball']); clean_ok = np.isfinite(m['ball']).all(1)
        for j in (0, 1):
            ci = c0 + 2 * i + j
            seed = base + 10 * i + j
            key = f'{name}|{seed}|{kind}'
            if all((key, rg) in done for rg in REGIMES):
                continue
            rng = np.random.default_rng(seed)
            dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
            path, _ = choose_path(estimate_noise(dm))
            ref = run_path(path, dm, lab, per)
            for ri, regime in enumerate(REGIMES):
                if (key, regime) in done:
                    continue
                t0 = time.time()
                rb = np.random.default_rng(39000 + 100 * ri + ci)
                q = quality(rb, regime)
                bro, valid, true_t, clock_t = sb3.simulate_warp(m, lab, rb, q)
                rc = np.random.default_rng(49000 + 100 * ri + ci)
                pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
                pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
                lags, crep = half_lags(sc.observations(np.arange(T), blocks, fps, rc, pr_t, pm_t),
                                       sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b), fps, halves)
                bro2, t_of_b, arep = align_auto(dm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
                reg_ball, rrep = register_ball(bro2, dm, t_of_b, fps)
                row = {'copy': key, 'kind': kind, 'regime': regime, 'path': path, 'mode': arep['mode'],
                       'accepted_fraction': arep['align'].get('accepted_fraction'),
                       'broadcast_quality': {k: round(float(q[k]), 4) for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'invalid')},
                       'v2_4': [round(x, 4) for x in ref], 'registration': rrep}
                for sysname, bl in (('v2_5b', bro2['ball']), ('v2_9', reg_ball)):
                    fb, frep = fuse_gated(dm['ball'], bl, t_of_b, fps, graded)
                    r = run_path(path, dict(dm, ball=fb), lab, per) if frep['used'] else ref
                    bb = project(bl, t_of_b, T); ok = np.isfinite(bb).all(1) & clean_ok
                    e = np.linalg.norm(bb[ok] - m['ball'][ok], axis=1)
                    row[sysname] = [round(x, 4) for x in r]
                    row[sysname + '_info'] = {'gate': frep, 'true_ball_error_median_m': round(float(np.median(e)), 4) if len(e) else None}
                res['rows'].append(row)
                json.dump(res, open(OUT, 'w'), indent=1)
                print(key, regime, path, 'v2.4 %.4f v2.5b %.4f v2.9 %.4f' % (ref[0], row['v2_5b'][0], row['v2_9'][0]),
                      'used %s/%s' % (row['v2_5b_info']['gate']['used'], row['v2_9_info']['gate']['used']), round(time.time() - t0), 's', flush=True)
    print('KINDDONE', kind, flush=True)
