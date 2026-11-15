"""Apply the gates of possession-v216-plan.json to the validation rows (exp_v216_0..3.json) and write
possession-v216-results.json. Written before any validation row existed; the gates are applied once, to all rows.
Usage: /usr/bin/python3 assemble_v216.py REPO_DIR"""
import json, sys, hashlib, numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
REPO = Path(sys.argv[1]); V = Path('/home/claude/work/v218')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan = json.loads((REPO / 'possession-v216-plan.json').read_text())
rows, stats, env, hashes = [], {}, None, None
for p in range(4):
    d = json.loads((V / f'exp_v216_{p}.json').read_text())
    rows += d['rows']; stats.update(d['stats'])
    assert env in (None, d['environment']) and hashes in (None, d['sha256']), 'parts ran with different environments or scripts'
    env, hashes = d['environment'], d['sha256']
assert hashes['possession/playerfill.py'] == plan['hashes']['possession/playerfill.py'] == sha(REPO / 'possession' / 'playerfill.py'), 'the candidate module changed'
assert hashes['exp_v216.py'] == plan['hashes']['exp_v216.py'], 'the validation script changed after the registration'
by = {(r['copy'], r['condition']): r for r in rows}
EXPECT = {'good': 16, 'medium': 8, 'good_degraded': 8, 'sim2_good': 4}
out_rows, diff = [], {}
for cond, n in EXPECT.items():
    copies = sorted({c for c, k in by if k == f'{cond}|v2_15'})
    assert len(copies) == n and all((c, f'{cond}|candidate') in by for c in copies), (cond, len(copies))
    for c in copies:
        a, f = by[(c, f'{cond}|v2_15')], by[(c, f'{cond}|candidate')]
        st = stats[f'{c}|{cond}']
        r = {'copy': c, 'condition': cond, 'path': a['path'], 'gate_open': bool(st['gate_used']),
             'v2_15': {k: round(a['fused'][k], 6) for k in ('spell_f1', 'macro_f1')}, 'candidate': {k: round(f['fused'][k], 6) for k in ('spell_f1', 'macro_f1')},
             'diff_spell_f1': f['fused']['spell_f1'] - a['fused']['spell_f1'], 'diff_macro_f1': f['fused']['macro_f1'] - a['fused']['macro_f1'],
             'without_second_model': {'v2_11': round(a['v2_11']['spell_f1'], 6), 'v2_11_with_added_players': round(f['v2_11']['spell_f1'], 6)},
             'added': {k: st.get(k) for k in ('player_positions_added', 'tactical_player_positions', 'share_of_added_within_1m_of_a_clean_player',
                                             'share_of_graded_frames_with_an_added_player', 'extra_slots_used', 'ghost_positions', 'gate_median_distance_m')}}
        out_rows.append(r); diff.setdefault(cond, []).append(r)
def mean(cond, key='diff_spell_f1', sel=lambda r: True):
    v = [r[key] for r in diff[cond] if sel(r)]
    return float(np.mean(v)), len(v)
dfl = lambda r: r['copy'].startswith('J03'); met = lambda r: r['copy'].startswith('MET')
g1, n1 = mean('good'); g2, n2 = mean('good', sel=dfl); g3, n3 = mean('good', sel=met)
worst = min(diff['good'], key=lambda r: r['diff_spell_f1'])
g5, _ = mean('good', 'diff_macro_f1'); g6a, _ = mean('medium'); g6b, _ = mean('good_degraded'); g7, _ = mean('sim2_good')
assert n1 == 16 and n2 == 8 and n3 == 8
gates = {
    'G1 gain': {'value': g1, 'threshold': 0.008, 'passed': bool(g1 >= 0.008)},
    'G2 gain on provider flags': {'value': g2, 'threshold': 0.008, 'passed': bool(g2 >= 0.008)},
    'G3 no harm on event proxies': {'value': g3, 'threshold': -0.002, 'passed': bool(g3 >= -0.002)},
    'G4 no bad copy': {'value': worst['diff_spell_f1'], 'copy': worst['copy'], 'threshold': -0.010, 'passed': bool(worst['diff_spell_f1'] >= -0.010)},
    'G5 macroF1': {'value': g5, 'threshold': -0.003, 'passed': bool(g5 >= -0.003)},
    'G6 other streams': {'medium': g6a, 'good_degraded': g6b, 'threshold': 0.0, 'passed': bool(g6a >= 0.0 and g6b >= 0.0)},
    'G7 other simulator': {'value': g7, 'threshold': 0.0, 'passed': bool(g7 >= 0.0)}}
selected = all(g['passed'] for g in gates.values())
summ = {}
for cond in EXPECT:
    v = np.array([r['diff_spell_f1'] for r in diff[cond]])
    summ[cond] = {'copies': len(v), 'v2_15_mean': round(float(np.mean([r['v2_15']['spell_f1'] for r in diff[cond]])), 4),
                  'candidate_mean': round(float(np.mean([r['candidate']['spell_f1'] for r in diff[cond]])), 4), 'mean_diff': round(float(v.mean()), 4),
                  'dfl': round(mean(cond, sel=dfl)[0], 4), 'metrica': round(mean(cond, sel=met)[0], 4), 'min': round(float(v.min()), 4), 'max': round(float(v.max()), 4),
                  'better': int((v > 1e-9).sum()), 'worse': int((v < -1e-9).sum()), 'equal': int((np.abs(v) <= 1e-9).sum()),
                  'gate_open': int(sum(r['gate_open'] for r in diff[cond])), 'mean_diff_macro_f1': round(mean(cond, 'diff_macro_f1')[0], 4),
                  'mean_diff_without_second_model': round(float(np.mean([r['without_second_model']['v2_11_with_added_players'] - r['without_second_model']['v2_11'] for r in diff[cond]])), 4)}
res = {'version': 'possession-v2.16 validation', 'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
       'plan_sha256': sha(REPO / 'possession-v216-plan.json'),
       'note': 'Agreement with other providers labels on corrupted external copies with a SIMULATED second camera; not a competition score. The provided match was not read.',
       'gates': {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in g.items()} for k, g in gates.items()},
       'selected': bool(selected), 'summary': summ,
       'rows': [dict(r, diff_spell_f1=round(r['diff_spell_f1'], 6), diff_macro_f1=round(r['diff_macro_f1'], 6)) for r in out_rows],
       'environment': env, 'sha256': hashes, 'provided_fixture_used': False}
(REPO / 'possession-v216-results.json').write_text(json.dumps(res, indent=1) + '\n', encoding='utf-8')
print(json.dumps({'gates': res['gates'], 'selected': selected, 'summary': summ}, indent=1))
