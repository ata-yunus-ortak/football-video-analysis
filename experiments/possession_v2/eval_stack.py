"""Evaluate stage1+stage2: eval_stack.py stage1.pkl stage2.pkl FTAG"""
import sys, os, pickle, itertools, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
os.environ['FTAG'] = sys.argv[3]
import eval2
from eval2 import probs, mean_scores, by_domain
from harness import load, DFL_VAL, MET_VAL
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks

s1 = pickle.load(open(sys.argv[1], 'rb')); sd, sh = pickle.load(open(sys.argv[2], 'rb'))
KEY = sys.argv[4] if len(sys.argv) > 4 else 'stack_v2_f2'
cases = []
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    for seed in (101, 102):
        pd1, ph1 = probs(s1, name, seed)
        S, _ = stack_features(pd1, ph1, m['period']); Sw, _ = stack_features(pd1, ph1, m['period'], swap=True)
        ok = np.isfinite(S).any(1)
        pd2 = np.full(len(S), .5); ph2 = np.full(len(S), .5)
        pd2[ok] = .5 * (sd.predict_proba(S[ok])[:, 1] + sd.predict_proba(Sw[ok])[:, 1])
        ph2[ok] = .5 * (sh.predict_proba(S[ok])[:, 1] + 1 - sh.predict_proba(Sw[ok])[:, 1])
        cases.append(dict(name=name, seed=seed, lab=lab, period=m['period'], pd=pd2, ph=ph2, pd1=pd1, ph1=ph1))
        np.savez(f'/home/claude/work/cache/probs_{KEY}_{name}_{seed}.npz', pd=pd2, ph=ph2)
res = []
for sw, oc, ic, bd in itertools.product([1, 3, 8, 20, 50], [5, 15, 60], [5, 15, 60], [0.0]):
    prm = dict(switch=sw, out_cost=oc, in_cost=ic, bias_dead=bd)
    fn = lambda c: decode_blocks(emissions(c['pd'], c['ph']), c['period'], prm)
    s, _ = mean_scores(cases, fn); b = by_domain(cases, fn)
    res.append((s['spell_f1_mean'], s['macro_f1'], b, prm, s['n_pred_spells']))
res.sort(key=lambda r: -r[0])
print('STACK BEST'); [print(r) for r in res[:6]]
