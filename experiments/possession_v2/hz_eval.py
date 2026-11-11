"""v2.6 evaluation (registered in possession-v26-plan.json): decoder grid (s0, beta) on the 8 original v2.1
validation copies, then the selected decoder vs v2.4 (v2.1 path) on 8 fresh copies (seeds 4100 + 10*i + j)."""
import sys, os, json, pickle, itertools, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded
from possession.degrade import degrade, sample_params, RANGES
from possession.features import features
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.decode2 import decode_blocks_tv
from possession.evaluate import score
from hz_common import hazard_prob
C = '/home/claude/work/cache/'
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
DEC21 = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
hz = pickle.load(open(C + 'hazard_v2.pkl', 'rb'))
(md, mh), (sd, sh) = [pickle.load(open(C + f, 'rb')) for f in ('models_v2.pkl', 'stack_v2.pkl')]


def stage_probs(dm, period):
    X, _ = features(dm); Xs, _ = features(dm, swap=True)
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
    return p1, q1, np.round(p2, 6), np.round(q2, 6)


def case(name, seed, dm, m, lab, cached):
    path = f'{C}hz_case_{name}_{seed}.npz'
    if os.path.exists(path):
        z = np.load(path); return z['lp'], z['hz']
    if cached:
        z1 = np.load(f'{C}probs_models_v2_f2_{name}_{seed}.npz'); p1, q1 = z1['pd'], z1['ph']
        z2 = np.load(f'{C}probs_sys_v21_{name}_{seed}_f2.npz'); p2, q2 = z2['pd'], z2['ph']
    else:
        p1, q1, p2, q2 = stage_probs(dm, m['period'])
    h = hazard_prob(hz, dm, m['period'], p1, q1)
    lp = emissions(p2, q2)
    np.savez(path, lp=lp, hz=h)
    return lp, h


def sc(lab, labels, per):
    r = score(lab, labels, per)
    return r['spell_f1_mean'], r['macro_f1']


if __name__ == '__main__':
    sel_cases = []
    for name in NAMES:
        m, lab = load(name)
        for seed in (101, 102):
            lp, h = case(name, seed, degraded(name, seed), m, lab, cached=True)
            sel_cases.append((name, seed, m['period'], lab, lp, h))
            print('selection case', name, seed, flush=True)
    grid = []
    for s0, beta in itertools.product([2, 3, 4, 5, 6, 8], [0, 0.5, 1.0, 1.5, 2.0]):
        p = dict(switch_s0=s0, switch_beta=beta, out_cost=60, in_cost=60, bias_dead=-0.3)
        r = [sc(lab, decode_blocks_tv(lp, h, per, p), per) for _, _, per, lab, lp, h in sel_cases]
        grid.append((float(np.mean([x[0] for x in r])), float(np.mean([x[1] for x in r])), s0, beta))
        print('grid', s0, beta, round(grid[-1][0], 4), flush=True)
    grid.sort(key=lambda g: (-g[0], -g[1]))
    best = grid[0]
    P = dict(switch_s0=best[2], switch_beta=best[3], out_cost=60, in_cost=60, bias_dead=-0.3)
    ref_sel = float(np.mean([sc(lab, decode_blocks(lp, per, DEC21), per)[0] for _, _, per, lab, lp, h in sel_cases]))
    fresh = []
    for i, name in enumerate(NAMES):
        m, lab = load(name)
        for j in (0, 1):
            seed = 4100 + 10 * i + j
            rng = np.random.default_rng(seed)
            dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
            lp, h = case(name, seed, dm, m, lab, cached=False)
            a = sc(lab, decode_blocks(lp, m['period'], DEC21), m['period'])
            b = sc(lab, decode_blocks_tv(lp, h, m['period'], P), m['period'])
            fresh.append({'copy': f'{name}|{seed}', 'v2_4': [round(x, 4) for x in a], 'v2_6': [round(x, 4) for x in b]})
            print('fresh', name, seed, 'v2.4 %.4f v2.6 %.4f' % (a[0], b[0]), flush=True)
    mean = lambda k, q=0: float(np.mean([f[k][q] for f in fresh]))
    wins = sum(f['v2_6'][0] >= f['v2_4'][0] for f in fresh)
    summ = {'selected_decoder': P, 'selection_copies': {'v2_4': round(ref_sel, 4), 'v2_6': round(best[0], 4)},
            'fresh': {'v2_4': mean('v2_4'), 'v2_6': mean('v2_6'), 'v2_4_macro': mean('v2_4', 1), 'v2_6_macro': mean('v2_6', 1),
                      'copies_not_worse': wins}}
    gates = {'fresh mean >= v2.4 + 0.010': summ['fresh']['v2_6'] >= summ['fresh']['v2_4'] + 0.010,
             'not worse on >= 5 of 8 fresh copies': wins >= 5}
    print(json.dumps(summ, indent=1)); print(json.dumps(gates, indent=1))
    print('VERDICT', 'SELECT_V26' if all(gates.values()) else 'KEEP', flush=True)
    json.dump({'summary': summ, 'gates': gates, 'selected': all(gates.values()), 'fresh': fresh,
               'grid': [{'spell_f1': round(g[0], 4), 'macro_f1': round(g[1], 4), 's0': g[2], 'beta': g[3]} for g in grid]},
              open('/home/claude/work/hz_eval.json', 'w'), indent=1)
