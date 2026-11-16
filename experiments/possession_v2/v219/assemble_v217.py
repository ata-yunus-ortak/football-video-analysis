"""Apply the gates of possession-v217-plan.json to the validation rows (exp_v217_0..3.json) and write
possession-v217-results.json. Written before any validation row existed; the gates are applied once, to all rows.
Usage: /usr/bin/python3 assemble_v217.py REPO_DIR"""
import json, sys, hashlib, numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
REPO = Path(sys.argv[1]); V = Path('/home/claude/work/v219')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan = json.loads((REPO / 'possession-v217-plan.json').read_text())
rows, stats, env, hashes = [], {}, None, None
for p in range(4):
    d = json.loads((V / f'exp_v217_{p}.json').read_text())
    rows += d['rows']; stats.update(d['stats'])
    assert env in (None, d['environment']) and hashes in (None, d['sha256']), 'parts ran with different environments or scripts'
    env, hashes = d['environment'], d['sha256']
for k in ('candidate_weights', 'release_weights', 'tcn2', 'exp_v217.py', 'exp_v216.py', 'exp_v215.py', 'exp_v213.py', 'pooling.py'):
    assert hashes[k] == plan['hashes'][k], f'{k} changed after the registration'
assert sha(V / 'assemble_v217.py') == plan['hashes']['assemble_v217.py'], 'this script changed after the registration'
by = {(r['copy'], r['condition']): r for r in rows}
assert len(by) == len(rows), 'a row appears twice'
EXPECT = {'tactical': 16, 'fill_good': 8, 'fill_medium': 8, 'tactical_sim2': 4}
out_rows, diff = [], {}
for cond, n in EXPECT.items():
    copies = sorted({c for c, k in by if k == f'{cond}|v2_16'})
    assert len(copies) == n and all((c, f'{cond}|candidate') in by for c in copies), (cond, len(copies))
    for c in copies:
        a, f = by[(c, f'{cond}|v2_16')], by[(c, f'{cond}|candidate')]
        assert a['v2_11'] == f['v2_11'] and a['path'] == f['path']
        st = stats.get(f'{c}|{cond}', {})
        r = {'copy': c, 'condition': cond, 'path': a['path'], 'pooled': bool(a['pooled_on_this_path']),
             'v2_11': {k: round(a['v2_11'][k], 6) for k in ('spell_f1', 'macro_f1')},
             'v2_16': {k: round(a['fused'][k], 6) for k in ('spell_f1', 'macro_f1')},
             'candidate': {k: round(f['fused'][k], 6) for k in ('spell_f1', 'macro_f1')},
             'diff_spell_f1': f['fused']['spell_f1'] - a['fused']['spell_f1'], 'diff_macro_f1': f['fused']['macro_f1'] - a['fused']['macro_f1'],
             'network_alone': {'v2_16': None if a['tcn_alone'] is None else round(a['tcn_alone']['spell_f1'], 6),
                               'candidate': None if f['tcn_alone'] is None else round(f['tcn_alone']['spell_f1'], 6)},
             'frames_changed_from_v2_16': f.get('frames_changed_from_v2_16')}
        if cond.startswith('fill_'):
            r['gate_open'] = bool(st.get('gate_used'))
            r['player_positions_added'] = st.get('player_positions_added')
        out_rows.append(r); diff.setdefault(cond, []).append(r)
def mean(cond, key='diff_spell_f1', sel=lambda r: True):
    v = [r[key] for r in diff[cond] if sel(r)]
    return float(np.mean(v)), len(v)
dfl = lambda r: r['copy'].startswith('J03'); met = lambda r: r['copy'].startswith('MET')
g1, n1 = mean('tactical'); g2, n2 = mean('tactical', sel=dfl); g3, n3 = mean('tactical', sel=met)
worst = min(diff['tactical'], key=lambda r: r['diff_spell_f1'])
g5, _ = mean('tactical', 'diff_macro_f1'); g6a, _ = mean('fill_good'); g6b, _ = mean('fill_medium'); g7, _ = mean('tactical_sim2')
assert n1 == 16 and n2 == 8 and n3 == 8
gates = {
    'G1 gain': {'value': g1, 'threshold': 0.008, 'passed': bool(g1 >= 0.008)},
    'G2 gain on provider flags': {'value': g2, 'threshold': 0.008, 'passed': bool(g2 >= 0.008)},
    'G3 no harm on event proxies': {'value': g3, 'threshold': -0.002, 'passed': bool(g3 >= -0.002)},
    'G4 no bad copy': {'value': worst['diff_spell_f1'], 'copy': worst['copy'], 'threshold': -0.010, 'passed': bool(worst['diff_spell_f1'] >= -0.010)},
    'G5 macroF1': {'value': g5, 'threshold': -0.003, 'passed': bool(g5 >= -0.003)},
    'G6 broadcast fill': {'fill_good': g6a, 'fill_medium': g6b, 'threshold': 0.0, 'passed': bool(g6a >= 0.0 and g6b >= 0.0)},
    'G7 other simulator': {'value': g7, 'threshold': 0.0, 'passed': bool(g7 >= 0.0)}}
selected = all(g['passed'] for g in gates.values())
summ = {}
for cond in EXPECT:
    rr = diff[cond]
    v = np.array([r['diff_spell_f1'] for r in rr])
    alone = [(r['network_alone']['v2_16'], r['network_alone']['candidate']) for r in rr if r['pooled']]
    summ[cond] = {'copies': len(v), 'on_the_v2_3_path_not_pooled': int(sum(not r['pooled'] for r in rr)),
                  'v2_11_mean': round(float(np.mean([r['v2_11']['spell_f1'] for r in rr])), 4),
                  'v2_16_mean': round(float(np.mean([r['v2_16']['spell_f1'] for r in rr])), 4),
                  'candidate_mean': round(float(np.mean([r['candidate']['spell_f1'] for r in rr])), 4), 'mean_diff': round(float(v.mean()), 4),
                  'dfl': round(mean(cond, sel=dfl)[0], 4), 'metrica': round(mean(cond, sel=met)[0], 4), 'min': round(float(v.min()), 4), 'max': round(float(v.max()), 4),
                  'better': int((v > 1e-9).sum()), 'worse': int((v < -1e-9).sum()), 'equal': int((np.abs(v) <= 1e-9).sum()),
                  'mean_diff_macro_f1': round(mean(cond, 'diff_macro_f1')[0], 4),
                  'candidate_minus_v2_11': round(float(np.mean([r['candidate']['spell_f1'] - r['v2_11']['spell_f1'] for r in rr])), 4),
                  'v2_16_minus_v2_11': round(float(np.mean([r['v2_16']['spell_f1'] - r['v2_11']['spell_f1'] for r in rr])), 4),
                  'network_alone_mean_on_pooled_copies': {'v2_16': round(float(np.mean([a for a, _ in alone])), 4) if alone else None,
                                                          'candidate': round(float(np.mean([c for _, c in alone])), 4) if alone else None}}
    if cond.startswith('fill_'):
        summ[cond]['gate_open'] = int(sum(r['gate_open'] for r in rr))
res = {'version': 'possession-v2.17 validation', 'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
       'plan_sha256': sha(REPO / 'possession-v217-plan.json'), 'plan_registered_at': plan['registered_at'],
       'note': 'Agreement with other providers\' labels on corrupted external copies (second camera SIMULATED); not a competition score. The provided match was not read.',
       'gates': {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in g.items()} for k, g in gates.items()},
       'selected': bool(selected), 'summary': summ,
       'rows': [dict(r, diff_spell_f1=round(r['diff_spell_f1'], 6), diff_macro_f1=round(r['diff_macro_f1'], 6)) for r in out_rows],
       'environment': env, 'sha256': hashes, 'provided_fixture_used': False}
(REPO / 'possession-v217-results.json').write_text(json.dumps(res, indent=1) + '\n', encoding='utf-8')
print(json.dumps({'gates': res['gates'], 'selected': selected, 'summary': summ}, indent=1))
