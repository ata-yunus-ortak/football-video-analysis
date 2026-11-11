"""Write possession-v23-results.json (aggregate external results only) from eval_v23.json and, if v2.3 was
selected and frozen, reserved_test_v23.json."""
import json, hashlib, subprocess
from pathlib import Path
W = Path('/home/claude/work'); S = Path('/home/claude/sc')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ev = json.loads((W / 'eval_v23.json').read_text())
s = ev['summary']
r = lambda x: round(x, 4)
out = {
    'version': 'possession-v2.3 experiment (position-noise robustness: input smoothing + wider training noise)',
    'provided_fixture_used': False,
    'note': ('Agreement with other providers\' labels on corrupted copies of external matches; not a competition '
             'score. Validation models trained on DFL J03WOH/J03WOY/J03WPY/J03WQQ.'),
    'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
    'plan_sha256': sha(S / 'possession-v23-plan.json'),
    'code_sha256': {f: sha(S / 'possession' / f) for f in ('smooth.py', 'degrade.py', 'train.py')},
    'validation': {
        'copies': {'orig': 'seeds 101/102, v2.1 corruption', 'ext_ball': 'seeds 301/302, + ball noise 0.3-0.6 m and bias 0.2-0.6 m',
                   'ext_players': 'seeds 501/502, + player noise 0.3-0.6 m'},
        'matches': 'DFL J03WN1, J03WR9; Metrica sample games 1-2 (event-derived proxy labels)',
        'v2_1': {'decoder': {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3},
                 **{k: r(s['v21'][k]) for k in ('all24', 'orig', 'ext_ball', 'ext_players')}},
        'v2_3': {'decoder': s['v23']['decoder'], **{k: r(s['v23'][k]) for k in ('all24', 'orig', 'ext_ball', 'ext_players')}},
        'gates': ev['gates'],
        'decoder_grid_top5': [{'spell_f1': r(g[0]), 'macro_f1': r(g[1]), 'decoder': g[2]} for g in ev['grid_top5']],
        'per_copy_spell_f1': {k: {'v2_1': r(ev['per_copy_v21'][k][0]), 'v2_3': r(ev['per_copy_v23'][k][0])}
                              for k in ev['per_copy_v21']}},
    'selected': bool(ev['selected']),
}
res = W / 'reserved_test_v23.json'
if ev['selected'] and res.exists():
    t = json.loads(res.read_text())
    out['reserved_test'] = {'fixture': t['fixture'], 'run_at': t['run_at'], 'bundles_sha256': t['bundles'],
                            'mean_spell_f1': {k: {kk: r(vv) for kk, vv in v.items()} for k, v in t['mean'].items()},
                            'cases': {k: {kk: {'spell_f1': r(vv['spell_f1_mean']), 'macro_f1': r(vv['macro_f1'])}
                                          for kk, vv in v.items()} for k, v in t['cases'].items()}}
    cfg = S / 'possession-v23-config.json'
    if cfg.exists():
        out['config_sha256'] = sha(cfg)
    b = S / 'models' / 'possession-v23.npz'
    if b.exists():
        out['bundle_sha256'] = sha(b)
fair = json.loads((W / 'eval_v23_fair.json').read_text())
out['reporting_only'] = {
    'v2_1_with_its_best_decoder_on_the_24_copies': {'decoder': fair['v2_1_best_decoder_on_24'],
        **{k: r(fair[k]) for k in ('all24', 'orig', 'ext_ball', 'ext_players')}},
    'note': ('v2.3 had its decoder re-selected on the 24 copies, v2.1 kept its registered decoder; re-decoding '
             'v2.1 the same way shows that about 0.004 of the 0.014 difference on all 24 copies comes from the decoder.'),
    'noise_configuration_per_seed': 'degrade parameters depend only on the seed, so the 4 matches of one seed share them',
    'per_seed_noise': {}}
import numpy as np, sys
sys.path.insert(0, str(S))
from possession.degrade import sample_params, RANGES
PROF = {'orig': RANGES, 'ext_ball': dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0)),
        'ext_players': dict(RANGES, player_sigma_m=(0.3, 0.6))}
for kind, seeds in (('orig', (101, 102)), ('ext_ball', (301, 302)), ('ext_players', (501, 502))):
    for sd in seeds:
        q = sample_params(np.random.default_rng(sd), ranges=PROF[kind])
        diffs = [ev['per_copy_v23'][k][0] - ev['per_copy_v21'][k][0] for k in ev['per_copy_v21'] if k.split('|')[1:] == [str(sd), kind]]
        out['reporting_only']['per_seed_noise'][f'{kind}|{sd}'] = {
            'ball_sigma_m': r(q['ball_sigma_m']), 'ball_bias_sd_m': r(q.get('ball_bias_sd_m', 0.0)),
            'player_sigma_m': r(q['player_sigma_m']), 'mean_v2_3_minus_v2_1': r(float(np.mean(diffs)))}
out['decision'] = ('v2.3 selected under the registered rule' if ev['selected'] else
                   'v2.3 NOT selected: at least one registered gate failed; v2.1 remains the submission system')
(S / 'possession-v23-results.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('selected', 'decision')}), json.dumps(out['validation']['gates']))
