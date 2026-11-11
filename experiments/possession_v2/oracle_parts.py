"""Reporting only: which part of the decision limits v2.1? Cached v2.1 probabilities (8 original validation copies),
decoded with the frozen decoder after replacing either P(dead) or P(home|alive) by the provider labels."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
DEC = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
C = '/home/claude/work/cache/'
res = {}
for name in ('J03WN1', 'J03WR9', 'MET1', 'MET2'):
    m, lab = load(name)
    per = m['period']
    for seed in (101, 102):
        z = np.load(f'{C}probs_sys_v21_{name}_{seed}_f2.npz')
        pd_, ph = z['pd'], z['ph']
        dead = (lab == 'D').astype(float)
        home = np.where(lab == 'H', 1.0, np.where(lab == 'A', 0.0, 0.5))
        eps = 0.02
        cases = {'model': (pd_, ph),
                 'oracle_dead': (np.clip(dead, eps, 1 - eps), ph),
                 'oracle_team': (pd_, np.clip(home, eps, 1 - eps)),
                 'oracle_both': (np.clip(dead, eps, 1 - eps), np.clip(home, eps, 1 - eps))}
        for k, (a, b) in cases.items():
            r = score(lab, decode_blocks(emissions(a, b), per, DEC), per)
            res.setdefault(k, []).append((r['spell_f1_mean'], r['macro_f1']))
summ = {k: {'spell_f1': round(float(np.mean([x[0] for x in v])), 4), 'macro_f1': round(float(np.mean([x[1] for x in v])), 4)} for k, v in res.items()}
print(json.dumps(summ, indent=1))
json.dump({'summary': summ, 'note': 'reporting only; cached v2.1 validation probabilities; provider labels as oracle'}, open('/home/claude/work/oracle_parts.json', 'w'), indent=1)
