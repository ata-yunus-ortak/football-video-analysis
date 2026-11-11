"""Cache v2 features of corrupted copies under a given corruption profile.
Usage: precompute_ext.py TAG PROFILE SEEDS NAMES...   (PROFILE: v2.2 | val-ext)"""
import sys, os, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, CACHE
from possession.degrade import degrade, sample_params, RANGES, RANGES_V22
from possession.features import features
VAL_EXT = dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0))
tag, profile, seeds, names = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')], sys.argv[4:]
ranges = {'v2.2': RANGES_V22, 'val-ext': VAL_EXT}[profile]
for name in names:
    m, lab = load(name)
    for seed in seeds:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
        for sw in (False, True):
            path = f'{CACHE}{name}_s{seed}_w{int(sw)}{tag}.npy'
            if os.path.exists(path):
                continue
            X, nm = features(dm, swap=sw)
            np.save(path, X)
            json.dump(nm, open(CACHE + f'names{tag}.json', 'w'))
        print('cached', name, seed, flush=True)
print('DONE', flush=True)
