"""Reserved test (Metrica game 3), once after freezing: v2.1 vs v2.4 (noise-gated) with the frozen bundles on
6 copies: v2.1 corruption (201/202), extended ball error (401/402), extended player error (601/602).
Registered in possession-v24-plan.json ("then"); reported, not a gate."""
import sys, json, numpy as np, warnings, subprocess
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.noise import estimate_noise, choose_path
from possession.evaluate import score
EXT_BALL = dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0))
EXT_PLAYERS = dict(RANGES, player_sigma_m=(0.3, 0.6))
b21 = load_bundle('/home/claude/sc/models/possession-v2.npz')
b23 = load_bundle('/home/claude/sc/models/possession-v23.npz')
half = int(b23['card']['smooth_half'])
m, lab = load('MET3')
out = {'fixture': 'Metrica Sample_Game_3 (reserved; first use since v2.1)',
       'run_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
       'bundles': {'v2.1': b21['sha256'], 'v2.3': b23['sha256']}, 'cases': {}}
for prof, seeds, ranges in (('v2', (201, 202), RANGES), ('ext_ball', (401, 402), EXT_BALL),
                            ('ext_players', (601, 602), EXT_PLAYERS)):
    for seed in seeds:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
        nz = estimate_noise(dm)
        path, why = choose_path(nz)
        l21, _, _ = predict_labels(dm, b21)
        r21 = score(lab, l21, m['period'])
        if path == 'v2.3':
            l24, _, _ = predict_labels(smooth_positions(dm, half), b23)
            r24 = score(lab, l24, m['period'])
        else:
            r24 = r21
        out['cases'][f'{prof}|{seed}'] = {'noise': nz, 'path': path,
                                           'v2.1': {'spell_f1_mean': r21['spell_f1_mean'], 'macro_f1': r21['macro_f1']},
                                           'v2.4': {'spell_f1_mean': r24['spell_f1_mean'], 'macro_f1': r24['macro_f1']}}
        print(prof, seed, path, round(nz['players_m'], 3), round(nz['ball_m'], 3),
              round(r21['spell_f1_mean'], 4), round(r24['spell_f1_mean'], 4), flush=True)
for k in ('v2.1', 'v2.4'):
    for prof in ('v2', 'ext_ball', 'ext_players'):
        out.setdefault('mean', {}).setdefault(k, {})[prof] = float(np.mean(
            [c[k]['spell_f1_mean'] for key, c in out['cases'].items() if key.split('|')[0] == prof]))
    out['mean'][k]['all'] = float(np.mean([c[k]['spell_f1_mean'] for c in out['cases'].values()]))
v21_repro = [round(out['cases'][f'v2|{s}']['v2.1']['spell_f1_mean'], 4) for s in (201, 202)]
out['v2_1_reproduces_registered_reserved_values'] = v21_repro == [0.6253, 0.7021]
print('SUMMARY', json.dumps(out['mean']), 'v2.1 reproduced:', v21_repro, flush=True)
json.dump(out, open('/home/claude/work/reserved_test_v24.json', 'w'), indent=1)
