import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
g = json.load(open('/home/claude/work/grid3_v3t_default.json'))
best = max(g, key=lambda r: (r['all'], r['macro']))
prm = best['prm']
print('decoder', prm, 'default grid best', round(best['all'], 4))
keys = ['v3t_default', 'v3t_none', 'v3t_clean', 'v3t_noisy', 'v3t_bad_team', 'v3t_inverted_defending',
        'v3t_default_nogate', 'v3t_bad_team_nogate', 'v3t_inverted_defending_nogate']
cache = {name: load(name) for name in DFL_VAL + MET_VAL}
res = {}
for key in keys:
    sp, mac, dfl, met = [], [], [], []
    for name in DFL_VAL + MET_VAL:
        m, lab = cache[name]
        for seed in (101, 102):
            z = np.load(f'/home/claude/work/cache/probs_{key}_{name}_{seed}.npz')
            r = score(lab, decode_blocks(emissions(z['pd'], z['ph']), m['period'], prm), m['period'])
            sp.append(r['spell_f1_mean']); mac.append(r['macro_f1'])
            (dfl if name.startswith('J03') else met).append(r['spell_f1_mean'])
    res[key] = {'spell_f1_all': float(np.mean(sp)), 'dfl': float(np.mean(dfl)), 'metrica': float(np.mean(met)),
                'macro_f1': float(np.mean(mac)), 'per_copy': [round(x, 4) for x in sp]}
    print('%-34s %.4f  dfl %.4f  met %.4f  macro %.4f' % (key, res[key]['spell_f1_all'], res[key]['dfl'], res[key]['metrica'], res[key]['macro_f1']), flush=True)
V21 = 0.6312
gates = {'default >= v2.1+0.010': res['v3t_default']['spell_f1_all'] >= V21 + 0.010,
         'none >= v2.1-0.005': res['v3t_none']['spell_f1_all'] >= V21 - 0.005,
         'noisy >= v2.1-0.005': res['v3t_noisy']['spell_f1_all'] >= V21 - 0.005,
         'bad_team >= v2.1-0.010': res['v3t_bad_team']['spell_f1_all'] >= V21 - 0.010,
         'inverted_defending >= v2.1-0.010': res['v3t_inverted_defending']['spell_f1_all'] >= V21 - 0.010}
print(json.dumps(gates, indent=1))
print('SELECT_V3' if all(gates.values()) else 'KEEP_V21')
json.dump({'decoder': prm, 'regimes': res, 'gates': gates, 'v21_reference': V21, 'selected': all(gates.values())},
          open('/home/claude/work/sel_v3.json', 'w'), indent=1)
