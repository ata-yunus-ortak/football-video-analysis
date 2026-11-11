"""Decoder grid on cached probabilities: grid2.py KEY [stage]"""
import sys, itertools, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
key = sys.argv[1]
cases = []
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    for seed in (101, 102):
        z = np.load(f'/home/claude/work/cache/probs_{key}_{name}_{seed}.npz')
        cases.append(dict(name=name, lab=lab, period=m['period'], pd=z['pd'], ph=z['ph']))
def run(prm):
    rs = [score(c['lab'], decode_blocks(emissions(c['pd'], c['ph']), c['period'], prm), c['period']) for c in cases]
    dfl = np.mean([r['spell_f1_mean'] for r, c in zip(rs, cases) if c['name'].startswith('J03')])
    met = np.mean([r['spell_f1_mean'] for r, c in zip(rs, cases) if c['name'].startswith('MET')])
    allm = np.mean([r['spell_f1_mean'] for r in rs]); mac = np.mean([r['macro_f1'] for r in rs])
    return dict(all=round(allm, 4), dfl=round(dfl, 4), met=round(met, 4), macro=round(mac, 4),
                spells=float(np.mean([r['n_pred_spells'] for r in rs])), prm=prm)
grid = [dict(switch=s, out_cost=c, in_cost=c, bias_dead=b) for s, c, b in
        itertools.product([5, 8, 12], [30, 60, 120], [-0.3, 0.0, 0.3])]
res = []
for prm in grid:
    r = run(prm); res.append(r); print(r, flush=True)
res.sort(key=lambda r: (-r['all'], -r['macro']))
print('BEST'); [print(r) for r in res[:5]]
json.dump(res, open(f'/home/claude/work/grid_{key}.json', 'w'), indent=1)
