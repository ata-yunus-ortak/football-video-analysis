"""Single post-freeze evaluation on reserved external test (Metrica sample game 3).
Uses the FROZEN bundle through the production inference code path (possession.pipeline)."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.evaluate import score
from baselines import organizer_baseline, s001
bundle = load_bundle(sys.argv[1])
out = {'bundle_sha256': bundle['sha256'], 'fixture': 'Metrica Sample_Game_3', 'seeds': [201, 202], 'cases': {}}
m, lab = load('MET3')
for seed in (201, 202):
    dm = degrade(m, lab, np.random.default_rng(seed))
    pred, _, _ = predict_labels(dm, bundle)
    r = {'v2': score(lab, pred, m['period']), 'baseline50': score(lab, organizer_baseline(dm, 50), m['period']),
         'S001': score(lab, s001(dm), m['period'])}
    out['cases'][seed] = r
    print(seed, {k: (round(v['spell_f1_mean'], 4), round(v['macro_f1'], 4)) for k, v in r.items()}, flush=True)
out['mean'] = {k: {f: float(np.mean([out['cases'][s][k][f] for s in (201, 202)])) for f in ('spell_f1_mean', 'macro_f1')}
               for k in ('v2', 'baseline50', 'S001')}
print(json.dumps(out['mean'], indent=1))
json.dump(out, open(sys.argv[2], 'w'), indent=1, default=float)
