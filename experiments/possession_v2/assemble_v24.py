"""Write possession-v24-results.json (aggregate external results only)."""
import json, hashlib, subprocess
from pathlib import Path
W = Path('/home/claude/work'); S = Path('/home/claude/sc')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
r = lambda x: round(x, 4)
ev = json.loads((W / 'eval_v24.json').read_text())
s = ev['summary']
out = {
    'version': 'possession-v2.4 (noise-gated choice between the frozen v2.1 system and the v2.3 recipe)',
    'provided_fixture_used': False,
    'note': ('Agreement with other providers\' labels on corrupted copies of external matches; not a competition '
             'score. Validation models of both paths trained on DFL J03WOH/J03WOY/J03WPY/J03WQQ.'),
    'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
    'plan_sha256': sha(S / 'possession-v24-plan.json'),
    'code_sha256': {f: sha(S / 'possession' / f) for f in ('noise.py', 'smooth.py', 'run24.py')},
    'validation_fresh_copies': {
        'copies': '24 fresh copies of DFL J03WN1, J03WR9 and Metrica sample games 1-2, one degrade seed per copy '
                  '(bases 1100 v2.1 corruption, 1300 + extended ball error, 1500 + extended player error)',
        'v2_1': {k: r(v) for k, v in s['v2_1'].items()},
        'v2_4': {k: r(v) for k, v in s['v2_4'].items()},
        'v2_3_on_every_copy_reporting_only': {k: r(v) for k, v in s['v2_3'].items()},
        'paths_chosen_by_the_gate': s['paths_chosen'],
        'gates': ev['gates'],
        'per_copy': [{'copy': x['copy'], 'path': x['path'], 'measured_players_m': r(x['noise']['players_m']),
                      'measured_ball_m': r(x['noise']['ball_m']), 'true_player_sigma_m': r(x['noise']['true_player_sigma_m']),
                      'true_ball_sigma_m': r(x['noise']['true_ball_sigma_m']),
                      'true_ball_bias_sd_m': r(x['noise']['true_ball_bias_sd_m']),
                      'spell_f1_v2_1': r(x['v2_1']), 'spell_f1_v2_3_path': r(x['v2_3']), 'spell_f1_v2_4': r(x['v2_4'])}
                     for x in ev['rows']]},
    'limits': [
        'The three copy sets have disjoint noise ranges (<= 0.29 m vs >= 0.34 m), so the gate routed every copy as '
        'intended; its behaviour for noise close to 0.30 m was not tested.',
        'The fresh copies come from the same four validation matches; only the corruption is new.',
        'v2.4 was designed after the v2.3 results (disclosed in the plan).'],
    'selected': bool(ev['selected']),
}
res = W / 'reserved_test_v24.json'
if res.exists():
    t = json.loads(res.read_text())
    out['reserved_test'] = {
        'fixture': t['fixture'], 'run_at': t['run_at'], 'bundles_sha256': t['bundles'],
        'mean_spell_f1': {k: {kk: r(vv) for kk, vv in v.items()} for k, v in t['mean'].items()},
        'cases': {k: {'path': v['path'], 'measured_players_m': r(v['noise']['players_m']),
                      'measured_ball_m': r(v['noise']['ball_m']),
                      'v2_1': {'spell_f1': r(v['v2.1']['spell_f1_mean']), 'macro_f1': r(v['v2.1']['macro_f1'])},
                      'v2_4': {'spell_f1': r(v['v2.4']['spell_f1_mean']), 'macro_f1': r(v['v2.4']['macro_f1'])}}
                  for k, v in t['cases'].items()},
        'v2_1_reproduces_registered_reserved_values': t['v2_1_reproduces_registered_reserved_values']}
for name in ('possession-v23-config.json',):
    if (S / name).exists():
        out.setdefault('release', {})['v2_3_config_sha256'] = sha(S / name)
for key, path in (('v2_1_bundle_sha256', S / 'models' / 'possession-v2.npz'), ('v2_3_bundle_sha256', S / 'models' / 'possession-v23.npz')):
    if path.exists():
        out.setdefault('release', {})[key] = sha(path)
rep = W / 'repro_v24.json'
if rep.exists():
    out['reproducibility_checks'] = json.loads(rep.read_text())
out['decision'] = ('v2.4 selected under the registered rule; the submission is generated with python -m possession.run24'
                   if ev['selected'] else 'v2.4 NOT selected; v2.1 remains the submission system')
(S / 'possession-v24-results.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('selected', 'decision')}), json.dumps(out['validation_fresh_copies']['gates']))
