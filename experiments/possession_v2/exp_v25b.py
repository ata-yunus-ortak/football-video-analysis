"""v2.5b validation (registered in possession-v25b-plan.json): v2.4 vs v2.5 (v4 alignment) vs v2.5b (clock
alignment) on 16 new tactical copies x 3 simulated broadcast accuracy regimes with simulated clock readings."""
import sys, json, time, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import broadcast as bc
from possession.fusion import fuse_gated, align_auto
from possession.clocksync import half_lags
from possession.noise import estimate_noise, choose_path
from possession.features import play_blocks
import synth_broadcast2 as sb2
import synth_clock as sc
from exp_v25 import run_path, quality, REGIMES, NAMES

PROF = {'orig': (RANGES, 3100), 'ext_players': (dict(RANGES, player_sigma_m=(0.3, 0.6)), 3500)}
OUT = '/home/claude/work/exp_v25b.json'

if __name__ == '__main__':
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['copy'], r['regime']) for r in res['rows']}
    ci = -1
    for kind, (ranges, base) in PROF.items():
        for i, name in enumerate(NAMES):
            m, lab = load(name)
            per, fps = m['period'], float(m['fps'])
            graded = per > 0
            blocks = play_blocks(per)
            halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
            for j in (0, 1):
                ci += 1
                seed = base + 10 * i + j
                key = f'{name}|{seed}|{kind}'
                if all((key, rg) in done for rg in REGIMES):
                    continue
                t0 = time.time()
                rng = np.random.default_rng(seed)
                dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
                path, _ = choose_path(estimate_noise(dm))
                ref = run_path(path, dm, lab, per)
                for ri, regime in enumerate(REGIMES):
                    if (key, regime) in done:
                        continue
                    rb = np.random.default_rng(19000 + 100 * ri + ci)
                    q = quality(rb, regime)
                    bro, valid, true_t, clock_t = sb2.simulate_with_clock(m, lab, rb, q)
                    rc = np.random.default_rng(29000 + 100 * ri + ci)
                    pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
                    pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
                    obs_t = sc.observations(np.arange(len(m['ball'])), blocks, fps, rc, pr_t, pm_t)
                    obs_b = sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b)
                    lags, crep = half_lags(obs_t, obs_b, fps, halves)
                    row = {'copy': key, 'kind': kind, 'regime': regime, 'path': path,
                           'broadcast_quality': {k: round(float(q[k]), 4) for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'invalid')},
                           'clock': {'p_read': [round(pr_t, 3), round(pr_b, 3)], 'report': crep,
                                     'true_lags': {}}, 'v2_4': [round(x, 4) for x in ref]}
                    live = true_t >= 0
                    for h, a, e in halves:
                        sel = np.flatnonzero(live & (true_t >= a) & (true_t <= e))
                        row['clock']['true_lags'][str(h)] = int(np.median(true_t[sel] - sel)) if len(sel) else None
                    for sysname, cl in (('v2_5', None), ('v2_5b', lags)):
                        bro2, t_of_b, arep = align_auto(dm, bro, valid, fps, m['pitch'], halves, clock_lags=cl)
                        acc = t_of_b >= 0
                        good = acc & live & (np.abs(t_of_b - true_t) <= 2)
                        fb, frep = fuse_gated(dm['ball'], bro2['ball'], t_of_b, fps, graded)
                        r = run_path(path, dict(dm, ball=fb), lab, per) if frep['used'] else ref
                        row[sysname] = [round(x, 4) for x in r]
                        row[sysname + '_info'] = {'mode': arep['mode'], 'accepted_fraction': arep['align'].get('accepted_fraction'),
                                                  'alignment_precision': round(float(good.sum() / max(acc.sum(), 1)), 4),
                                                  'gate': frep}
                    res['rows'].append(row)
                    json.dump(res, open(OUT, 'w'), indent=1)
                    print(key, regime, path, 'v2.4 %.4f v2.5 %.4f v2.5b %.4f' % (ref[0], row['v2_5'][0], row['v2_5b'][0]),
                          'mode', row['v2_5b_info']['mode'], 'acc %s/%s' % (row['v2_5_info']['accepted_fraction'], row['v2_5b_info']['accepted_fraction']),
                          'used %s/%s' % (row['v2_5_info']['gate']['used'], row['v2_5b_info']['gate']['used']),
                          'lags', lags, row['clock']['true_lags'], round(time.time() - t0), 's', flush=True)
    rows = res['rows']
    summ = {}
    for regime in REGIMES:
        sel = [r for r in rows if r['regime'] == regime]
        summ[regime] = {'n': len(sel), **{s: float(np.mean([r[s][0] for r in sel])) for s in ('v2_4', 'v2_5', 'v2_5b')},
                        'alignment_failures': {s: sum((r[s + '_info']['accepted_fraction'] or 0) < 0.05 for r in sel) for s in ('v2_5', 'v2_5b')},
                        'gate_open': {s: sum(r[s + '_info']['gate']['used'] for r in sel) for s in ('v2_5', 'v2_5b')},
                        'clock_mode': sum(r['v2_5b_info']['mode'] == 'clock' for r in sel)}
    g = summ['good']
    gates = {'good: v2.5b >= v2.4 + 0.010': g['v2_5b'] >= g['v2_4'] + 0.010,
             'medium: v2.5b >= v2.4 - 0.005': summ['medium']['v2_5b'] >= summ['medium']['v2_4'] - 0.005,
             'bad: v2.5b >= v2.4 - 0.002': summ['bad']['v2_5b'] >= summ['bad']['v2_4'] - 0.002,
             'good: v2.5b >= v2.5 - 0.002': g['v2_5b'] >= g['v2_5'] - 0.002,
             'good: alignment failures v2.5b <= v2.5': g['alignment_failures']['v2_5b'] <= g['alignment_failures']['v2_5']}
    res.update(summary=summ, gates=gates, selected=all(gates.values()))
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps(summ, indent=1)); print(json.dumps(gates, indent=1))
    print('VERDICT', 'SELECT_V25B' if all(gates.values()) else 'NOT_V25B', flush=True)
