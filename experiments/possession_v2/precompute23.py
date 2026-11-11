"""Cache v2 features under a corruption profile, optionally after input smoothing.
Usage: precompute23.py TAG PROFILE SMOOTH(0/1) SEEDS NAMES...
PROFILE: v2 | v2.3 | val-ext-ball | val-ext-players"""
import sys, os, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, CACHE
from possession.degrade import degrade, sample_params, RANGES, RANGES_V23
from possession.features import features
from possession.smooth import smooth_positions
PROF = {'v2': RANGES, 'v2.3': RANGES_V23,
        'val-ext-ball': dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0)),
        'val-ext-players': dict(RANGES, player_sigma_m=(0.3, 0.6))}
tag, profile, smooth = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
seeds, names = [int(x) for x in sys.argv[4].split(',')], sys.argv[5:]
for name in names:
    m, lab = load(name)
    for seed in seeds:
        paths = [f'{CACHE}{name}_s{seed}_w{int(sw)}{tag}.npy' for sw in (False, True)]
        if all(os.path.exists(p) for p in paths):
            continue
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=PROF[profile]))
        if smooth:
            dm = smooth_positions(dm)
        for sw, path in zip((False, True), paths):
            X, nm = features(dm, swap=sw)
            np.save(path, X)
            json.dump(nm, open(CACHE + f'names{tag}.json', 'w'))
        print('cached', name, seed, flush=True)
print('DONE', flush=True)
