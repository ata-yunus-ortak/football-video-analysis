"""Reserved test (Metrica game 3), once after freezing: v2.1 vs v2.3 frozen bundles on 6 copies:
v2.1 corruption (201/202), extended ball error (401/402), extended player error (601/602).
Registered in possession-v23-plan.json ("then")."""
import sys, json, numpy as np, warnings, subprocess
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.evaluate import score
EXT_BALL = dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0))
EXT_PLAYERS = dict(RANGES, player_sigma_m=(0.3, 0.6))
B = {'v2.1': load_bundle('/home/claude/sc/models/possession-v2.npz'),
     'v2.3': load_bundle('/home/claude/sc/models/possession-v23.npz')}
HALF = {'v2.1': 0, 'v2.3': int(B['v2.3']['card']['smooth_half'])}
m, lab = load('MET3')
out = {'fixture': 'Metrica Sample_Game_3 (reserved; first and only use for v2.3)',
       'run_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
       'bundles': {k: v['sha256'] for k, v in B.items()}, 'cases': {}}
for prof, seeds, ranges in (('v2', (201, 202), RANGES), ('ext_ball', (401, 402), EXT_BALL),
                            ('ext_players', (601, 602), EXT_PLAYERS)):
    for seed in seeds:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
        row = {}
        for k, b in B.items():
            x = smooth_positions(dm, HALF[k]) if HALF[k] else dm
            labels, _, _ = predict_labels(x, b)
            r = score(lab, labels, m['period'])
            row[k] = {'spell_f1_mean': r['spell_f1_mean'], 'macro_f1': r['macro_f1']}
        out['cases'][f'{prof}|{seed}'] = row
        print(prof, seed, {k: round(v['spell_f1_mean'], 4) for k, v in row.items()}, flush=True)
for k in B:
    for prof in ('v2', 'ext_ball', 'ext_players'):
        out.setdefault('mean', {}).setdefault(k, {})[prof] = float(np.mean(
            [c[k]['spell_f1_mean'] for key, c in out['cases'].items() if key.split('|')[0] == prof]))
    out['mean'][k]['all'] = float(np.mean([c[k]['spell_f1_mean'] for c in out['cases'].values()]))
print('SUMMARY', json.dumps(out['mean']), flush=True)
json.dump(out, open('/home/claude/work/reserved_test_v23.json', 'w'), indent=1)
