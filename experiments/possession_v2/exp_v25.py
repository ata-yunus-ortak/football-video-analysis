"""v2.5 validation (registered in possession-v25-plan.json): v2.4 with / without the gated broadcast ball fill
on 16 fresh tactical copies x 3 simulated broadcast accuracy regimes."""
import sys, json, pickle, time, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import broadcast as bc
from possession.fusion import fuse_gated
from possession.noise import estimate_noise, choose_path
from possession.smooth import smooth_positions
from possession.features import features, play_blocks
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
import synth_broadcast as sb
C = '/home/claude/work/cache/'
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
PROF = {'orig': (RANGES, 2100), 'ext_players': (dict(RANGES, player_sigma_m=(0.3, 0.6)), 2500)}
REGIMES = {'good': ((0.0, 0.2), (0.05, 0.25), (0.05, 0.25)), 'medium': ((0.2, 0.6), (0.25, 0.5), (0.25, 0.5)),
           'bad': ((0.6, 1.5), (0.5, 1.0), (0.5, 1.0))}
PATHS = {'v2.1': (C + 'models_v2.pkl', C + 'stack_v2.pkl', {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}),
         'v2.3': (C + 'models_v23.pkl', C + 'stack_v23.pkl', {'switch': 5, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3})}
MODELS = {k: [pickle.load(open(p, 'rb')) for p in v[:2]] for k, v in PATHS.items()}


def run_path(path, m_in, lab, period):
    (md, mh), (sd, sh) = MODELS[path]
    m_ = smooth_positions(m_in, 2) if path == 'v2.3' else m_in
    X, _ = features(m_); Xs, _ = features(m_, swap=True)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    del X, Xs
    S = [stack_features(p1, q1, period, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(p1), .5); q2 = np.full(len(p1), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    r = score(lab, decode_blocks(emissions(np.round(p2, 6), np.round(q2, 6)), period, PATHS[path][2]), period)
    return r['spell_f1_mean'], r['macro_f1']


def quality(rng, regime):
    q = sb.sample_quality(rng, 'default')
    (b0, b1), (s0, s1), (p0, p1) = REGIMES[regime]
    q.update(bias_sd=float(rng.uniform(b0, b1)), b_sd=float(rng.uniform(s0, s1)), p_sd=float(rng.uniform(p0, p1)))
    return q


if __name__ == '__main__':
    OUT = '/home/claude/work/exp_v25.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['copy'], r['regime']) for r in res['rows']}
    ci = -1
    for kind, (ranges, base) in PROF.items():
        for i, name in enumerate(NAMES):
            m, lab = load(name)
            per = m['period']
            graded = per > 0
            halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(play_blocks(per))]
            for j in (0, 1):
                ci += 1
                seed = base + 10 * i + j
                key = f'{name}|{seed}|{kind}'
                if all((key, rg) in done for rg in REGIMES):
                    continue
                t0 = time.time()
                rng = np.random.default_rng(seed)
                dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
                nz = estimate_noise(dm)
                path, _ = choose_path(nz)
                ref = run_path(path, dm, lab, per)
                for ri, regime in enumerate(REGIMES):
                    if (key, regime) in done:
                        continue
                    rb = np.random.default_rng(9000 + 100 * ri + ci)
                    q = quality(rb, regime)
                    bro, valid, true_t = sb.simulate(m, lab, rb, q)
                    bro2, orep = bc.orient(dm, bro, valid, m['fps'], m['pitch'])
                    t_of_b, arep = bc.align(dm, bro2, valid, m['fps'], halves)
                    acc, live = t_of_b >= 0, true_t >= 0
                    good = acc & live & (np.abs(t_of_b - true_t) <= 2)
                    prec = float(good.sum() / max(acc.sum(), 1))
                    fb, frep = fuse_gated(dm['ball'], bro2['ball'], t_of_b, m['fps'], graded)
                    r25 = run_path(path, dict(dm, ball=fb), lab, per) if frep['used'] else ref
                    row = {'copy': key, 'kind': kind, 'regime': regime, 'path': path,
                           'tactical_noise': {k: round(v, 4) for k, v in nz.items() if isinstance(v, float)},
                           'broadcast_quality': {k: round(float(q[k]), 4) for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'invalid')},
                           'alignment_precision': round(prec, 4), 'accepted_fraction': arep.get('accepted_fraction'),
                           'gate': frep, 'v2_4': [round(x, 4) for x in ref], 'v2_5': [round(x, 4) for x in r25]}
                    res['rows'].append(row)
                    json.dump(res, open(OUT, 'w'), indent=1)
                    print(key, regime, path, 'v2.4 %.4f v2.5 %.4f' % (ref[0], r25[0]), 'used', frep['used'],
                          'med', frep.get('median_distance_m'), 'vis', frep.get('ball_visible_graded_before'), '->',
                          frep.get('ball_visible_graded_after'), 'prec %.3f' % prec, round(time.time() - t0), 's', flush=True)
    rows = res['rows']
    summ = {}
    for regime in REGIMES:
        sel = [r for r in rows if r['regime'] == regime]
        summ[regime] = {'n': len(sel), 'v2_4': float(np.mean([r['v2_4'][0] for r in sel])),
                        'v2_5': float(np.mean([r['v2_5'][0] for r in sel])),
                        'gate_open': sum(r['gate']['used'] for r in sel),
                        'v2_4_macro': float(np.mean([r['v2_4'][1] for r in sel])),
                        'v2_5_macro': float(np.mean([r['v2_5'][1] for r in sel]))}
    gates = {'good >= v2.4 + 0.010': summ['good']['v2_5'] >= summ['good']['v2_4'] + 0.010,
             'medium >= v2.4 - 0.005': summ['medium']['v2_5'] >= summ['medium']['v2_4'] - 0.005,
             'bad >= v2.4 - 0.002': summ['bad']['v2_5'] >= summ['bad']['v2_4'] - 0.002}
    res.update(summary=summ, gates=gates, selected=all(gates.values()))
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps(summ, indent=1)); print(json.dumps(gates, indent=1))
    print('VERDICT', 'SELECT_V25' if all(gates.values()) else 'KEEP_V24', flush=True)
