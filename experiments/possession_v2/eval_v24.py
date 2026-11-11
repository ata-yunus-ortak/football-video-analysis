"""v2.4 (noise-gated v2.1 / v2.3) vs v2.1 on 24 fresh copies. Registered in possession-v24-plan.json."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from eval_v23 import probs
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
from possession.noise import choose_path
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
DEC = {'v2.1': {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3},
       'v2.3': {'switch': 5, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}}
SETS = (('orig', 1100), ('ext_ball', 1300), ('ext_players', 1500))
noise = json.load(open('/home/claude/work/noise24.json'))
rows = []
for kind, base in SETS:
    for i, name in enumerate(NAMES):
        m, lab = load(name)
        per = m['period']
        for j in (0, 1):
            seed = base + 10 * i + j
            r = {}
            for path, sysname, tag in (('v2.1', 'v21', '_g21'), ('v2.3', 'v23', '_g23')):
                P = probs(sysname, name, seed, tag, per)
                s = score(lab, decode_blocks(emissions(*P), per, DEC[path]), per)
                r[path] = (s['spell_f1_mean'], s['macro_f1'])
            nz = noise[f'{name}|{seed}']
            choice, why = choose_path(nz)
            rows.append({'copy': f'{name}|{seed}|{kind}', 'kind': kind, 'noise': nz, 'path': choice, 'trigger': why,
                         'v2_1': r['v2.1'][0], 'v2_3': r['v2.3'][0], 'v2_4': r[choice][0],
                         'v2_1_macro': r['v2.1'][1], 'v2_4_macro': r[choice][1]})
            print(rows[-1]['copy'], choice, round(nz['players_m'], 3), round(nz['ball_m'], 3),
                  round(r['v2.1'][0], 4), round(r['v2.3'][0], 4), flush=True)
mean = lambda k, kind=None: float(np.mean([x[k] for x in rows if kind is None or x['kind'] == kind]))
summ = {s: {'all24': mean(s), **{kind: mean(s, kind) for kind, _ in SETS}} for s in ('v2_1', 'v2_4', 'v2_3')}
summ['paths_chosen'] = {kind: {p: sum(1 for x in rows if x['kind'] == kind and x['path'] == p) for p in ('v2.1', 'v2.3')}
                        for kind, _ in SETS}
gates = {'all24 >= v2.1 + 0.010': summ['v2_4']['all24'] >= summ['v2_1']['all24'] + 0.010,
         'orig >= v2.1 orig - 0.005': summ['v2_4']['orig'] >= summ['v2_1']['orig'] - 0.005}
print(json.dumps(summ, indent=1)); print(json.dumps(gates, indent=1))
print('VERDICT', 'SELECT_V24' if all(gates.values()) else 'KEEP_V21', flush=True)
json.dump({'summary': summ, 'gates': gates, 'selected': all(gates.values()), 'rows': rows,
           'note': 'v2_3 = v2.3 path on every copy (reporting only)'},
          open('/home/claude/work/eval_v24.json', 'w'), indent=1)
