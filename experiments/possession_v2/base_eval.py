import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, DFL_VAL, MET_VAL
from possession.evaluate import score
from baselines import organizer_baseline, s001
out = {}
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    for seed in (101, 102):
        dm = degraded(name, seed)
        for tag, fn in (('baseline50', lambda d: organizer_baseline(d, 50)), ('S001', s001)):
            pred = fn(dm)
            np.save(f'/home/claude/work/cache/pred_{tag}_{name}_{seed}.npy', pred)
            out[f'{tag}|{name}|{seed}'] = score(lab, pred, m['period'])
            print(tag, name, seed, round(out[f'{tag}|{name}|{seed}']['spell_f1_mean'], 4), flush=True)
json.dump(out, open('/home/claude/work/base_eval.json', 'w'), indent=1)
