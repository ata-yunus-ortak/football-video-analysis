"""Apply the rule written on 14 Nov 23:39 (v214/NOTES.md) for a third candidate and collect what was seen.
Reads v215/explore3.json (42 development copies) and possession-v214-results.json. Writes v215/development_summary.json."""
import json
import numpy as np
V = '/home/claude/work/v215/'
rows = json.load(open(V + 'explore3.json'))
res = json.load(open('/home/claude/sc/possession-v214-results.json'))
assert len(rows) == 42, len(rows)
new = [k for k in rows if k.split('_')[1][:2] in ('16', '66')]
assert len(new) == 20, len(new)
G = ['ari10', 'ari20', 'ari30', 'ari40', 'ari50']


def stats(name, keys):
    d = np.array([rows[k][name][0] - rows[k]['v2_11'][0] for k in keys])
    return {'n': len(keys), 'mean': float(d.mean()), 'min': float(d.min()), 'better': int((d > 0).sum()), 'below_-0.007': int((d < -0.007).sum()),
            'below_-0.010': int((d < -0.010).sum())}


groups = {'all 42': list(rows), 'DFL 20': [k for k in rows if k.startswith('J03')], 'Metrica 22': [k for k in rows if k.startswith('MET')],
          'DFL tactical 16': [k for k in rows if k.startswith('J03') and k.endswith('_tactical')],
          'earlier 22': [k for k in rows if k not in new], 'copies of the v2.14 validation 20': new,
          'our simulator 33': [k for k in rows if k.endswith('_tactical')], 'his simulator 9': [k for k in rows if k.endswith('sim2')]}
table = {g: {n: stats(n, ks) for n in ['tcn_alone'] + G} for g, ks in groups.items()}
gates214 = res['gates']
means_ok = all(gates214[k] for k in ('G1 gain', 'G2 gain on provider flags', 'G3 no harm on event proxies', 'G5 macroF1'))
cand = [n for n in ('ari10', 'ari20', 'ari30') if table['all 42'][n]['below_-0.007'] == 0]
chosen = max(cand, key=lambda n: table['all 42'][n]['mean']) if (cand and means_ok) else None
dfl_ok = bool(chosen) and table['DFL 20'][chosen]['mean'] >= 0.010 and table['DFL tactical 16'][chosen]['mean'] >= 0.010
out = {'rule_written': '14 Nov 2026 23:39 (v214/NOTES.md), when three rows of the v2.14 validation were known',
       'mean_gates_of_v214_passed': means_ok, 'weights_without_a_copy_below_-0.007': cand, 'largest_mean_among_them': chosen,
       'its_mean_on_the_DFL_copies_is_at_least_0.010': dfl_ok,
       'note_on_the_count': 'the rule text of 23:39 said 18 DFL development copies; there are 20 (16 tactical, 4 of his simulator). The '
                            'condition is required here both on all 20 and on the 16 tactical ones', 'third_attempt': bool(chosen and dfl_ok),
       'weight': (int(chosen[3:]) / 100.0) if (chosen and dfl_ok) else None, 'table': table}
json.dump(out, open(V + 'development_summary.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'table'}, indent=1))
for g in groups:
    print(g)
    for n in ['tcn_alone'] + G:
        t = table[g][n]
        print(f"   {n:10s} mean {t['mean']:+.4f}  min {t['min']:+.4f}  better {t['better']}/{t['n']}  below -0.007: {t['below_-0.007']}  below -0.010: {t['below_-0.010']}")
