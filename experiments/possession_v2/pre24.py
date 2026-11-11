"""Fresh v2.4 validation copies: per-copy seeds base + 10*i + j (i = match index, j = 0/1).
Usage: pre24.py TAG PROFILE SMOOTH(0/1) BASE.  With SMOOTH=0 also records the gate's noise estimate."""
import sys, os, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, CACHE
from possession.degrade import degrade, sample_params, RANGES
from possession.features import features
from possession.smooth import smooth_positions
from possession.noise import estimate_noise
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
PROF = {'v2': RANGES,
        'val-ext-ball': dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0)),
        'val-ext-players': dict(RANGES, player_sigma_m=(0.3, 0.6))}
tag, profile, smooth, base = sys.argv[1], sys.argv[2], sys.argv[3] == '1', int(sys.argv[4])
NJ = '/home/claude/work/noise24.json'
for i, name in enumerate(NAMES):
    m, lab = load(name)
    for j in (0, 1):
        seed = base + 10 * i + j
        paths = [f'{CACHE}{name}_s{seed}_w{int(sw)}{tag}.npy' for sw in (False, True)]
        if all(os.path.exists(p) for p in paths):
            continue
        rng = np.random.default_rng(seed)
        params = sample_params(rng, ranges=PROF[profile])
        dm = degrade(m, lab, rng, params)
        if not smooth:
            nz = json.load(open(NJ)) if os.path.exists(NJ) else {}
            nz[f'{name}|{seed}'] = dict(estimate_noise(dm), profile=profile,
                                        true_player_sigma_m=params['player_sigma_m'], true_ball_sigma_m=params['ball_sigma_m'],
                                        true_ball_bias_sd_m=params.get('ball_bias_sd_m', 0.0))
            json.dump(nz, open(NJ, 'w'), indent=1)
        else:
            dm = smooth_positions(dm)
        for sw, path in zip((False, True), paths):
            X, nm = features(dm, swap=sw)
            np.save(path, X)
            json.dump(nm, open(CACHE + f'names{tag}.json', 'w'))
        print('cached', name, seed, flush=True)
print('DONE', flush=True)
