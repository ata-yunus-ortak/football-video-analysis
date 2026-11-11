"""v2.2 vs v2.1 on V_orig (seeds 101/102, v2.1 corruption) + V_ext (seeds 301/302, extended ball error).
Registered in possession-v22-plan.json."""
import sys, os, json, pickle, itertools, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, DFL_VAL, MET_VAL
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
C = '/home/claude/work/cache/'
DEC21 = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
SYS = {'v21': (C + 'models_v2.pkl', C + 'stack_v2.pkl'), 'v22': (C + 'models_v22.pkl', C + 'stack_v22.pkl')}
COPIES = [(n, s, '_f2', 'orig') for n in DFL_VAL + MET_VAL for s in (101, 102)] + \
         [(n, s, '_f2v', 'ext') for n in DFL_VAL + MET_VAL for s in (301, 302)]


def probs(sysname, name, seed, tag, period):
    path = f'{C}probs_sys_{sysname}_{name}_{seed}{tag}.npz'
    if os.path.exists(path):
        z = np.load(path); return z['pd'], z['ph']
    (md, mh), (sd, sh) = [pickle.load(open(p, 'rb')) for p in SYS[sysname]]
    X = feats(name, seed, False, tag); Xs = feats(name, seed, True, tag)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    S = [stack_features(p1, q1, period, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(X), .5); q2 = np.full(len(X), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    p2, q2 = np.round(p2, 6), np.round(q2, 6)
    np.savez(path, pd=p2, ph=q2)
    return p2, q2


if __name__ == '__main__':
    cases = []
    for name, seed, tag, kind in COPIES:
        m, lab = load(name)
        P = {s: probs(s, name, seed, tag, m['period']) for s in SYS}
        cases.append((name, seed, kind, m['period'], lab, P))
        print('probs', name, seed, kind, flush=True)

    def evaluate(sysname, dec):
        out = {}
        for name, seed, kind, per, lab, P in cases:
            r = score(lab, decode_blocks(emissions(*P[sysname]), per, dec), per)
            out[(name, seed, kind)] = (r['spell_f1_mean'], r['macro_f1'])
        return out

    r21 = evaluate('v21', DEC21)
    grid = []
    for sw, cost, bias in itertools.product([2, 3, 4, 5, 6, 8], [30, 60, 120], [-0.3, 0.0, 0.3]):
        dec = {'switch': sw, 'out_cost': cost, 'in_cost': cost, 'bias_dead': bias}
        r = evaluate('v22', dec)
        grid.append((float(np.mean([v[0] for v in r.values()])), float(np.mean([v[1] for v in r.values()])), dec, r))
    grid.sort(key=lambda g: (-g[0], -g[1]))
    best_all, best_mac, dec22, r22 = grid[0]
    def mean(r, kind=None):
        return float(np.mean([v[0] for k, v in r.items() if kind is None or k[2] == kind]))
    summ = {'v21': {'all16': mean(r21), 'orig': mean(r21, 'orig'), 'ext': mean(r21, 'ext')},
            'v22': {'all16': mean(r22), 'orig': mean(r22, 'orig'), 'ext': mean(r22, 'ext'), 'decoder': dec22}}
    gates = {'all16 >= v2.1 + 0.010': summ['v22']['all16'] >= summ['v21']['all16'] + 0.010,
             'orig >= 0.6312 - 0.010': summ['v22']['orig'] >= 0.6312 - 0.010}
    print(json.dumps(summ, indent=1)); print(json.dumps(gates, indent=1))
    print('VERDICT', 'SELECT_V22' if all(gates.values()) else 'KEEP_V21', flush=True)
    json.dump({'summary': summ, 'gates': gates, 'selected': all(gates.values()),
               'per_copy_v21': {f'{k[0]}|{k[1]}|{k[2]}': v for k, v in r21.items()},
               'per_copy_v22': {f'{k[0]}|{k[1]}|{k[2]}': v for k, v in r22.items()},
               'grid_top5': [(g[0], g[1], g[2]) for g in grid[:5]]},
              open('/home/claude/work/eval_v22.json', 'w'), indent=1)
