"""Reserved test (Metrica game 3), once after freezing: v2.1 vs v2.2 frozen bundles on 2 copies with the
v2.1 corruption (seeds 201/202) and 2 copies with the extended ball error (seeds 401/402)."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.evaluate import score
VAL_EXT = dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0))
B = {'v2.1': load_bundle('/home/claude/sc/models/possession-v2.npz'), 'v2.2': load_bundle('/home/claude/sc/models/possession-v22.npz')}
m, lab = load('MET3')
out = {'fixture': 'Metrica Sample_Game_3', 'bundles': {k: v['sha256'] for k, v in B.items()}, 'cases': {}}
for prof, seeds, ranges in (('v2', (201, 202), RANGES), ('ext', (401, 402), VAL_EXT)):
    for seed in seeds:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
        row = {}
        for k, b in B.items():
            labels, _, _ = predict_labels(dm, b)
            r = score(lab, labels, m['period'])
            row[k] = {'spell_f1_mean': r['spell_f1_mean'], 'macro_f1': r['macro_f1']}
        out['cases'][f'{prof}|{seed}'] = row
        print(prof, seed, {k: round(v['spell_f1_mean'], 4) for k, v in row.items()}, flush=True)
for k in B:
    for prof in ('v2', 'ext'):
        out.setdefault('mean', {}).setdefault(k, {})[prof] = float(np.mean([c[k]['spell_f1_mean'] for key, c in out['cases'].items() if key.startswith(prof)]))
    out['mean'][k]['all'] = float(np.mean([c[k]['spell_f1_mean'] for c in out['cases'].values()]))
print('SUMMARY', json.dumps(out['mean']), flush=True)
json.dump(out, open('/home/claude/work/reserved_test_v22.json', 'w'), indent=1)
