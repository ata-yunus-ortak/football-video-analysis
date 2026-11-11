import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.decode import emissions, decode_blocks
from possession.noise import choose_path
from possession.plausibility import stats
DEC = {'v2.1': {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}, 'v2.3': {'switch': 5, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}}
noise = json.load(open('noise24.json')); rows = []; gt = []
for base in (1100, 1300, 1500):
    for i, name in enumerate(['J03WN1', 'J03WR9', 'MET1', 'MET2']):
        m, lab = load(name)
        if base == 1100: gt.append(stats(np.where(lab == 'X', 'D', lab)))
        for j in (0, 1):
            seed = base + 10 * i + j; path, _ = choose_path(noise[f'{name}|{seed}'])
            z = np.load(f'cache/probs_sys_{"v21" if path == "v2.1" else "v23"}_{name}_{seed}_{"g21" if path == "v2.1" else "g23"}.npz')
            rows.append(stats(decode_blocks(emissions(z['pd'], z['ph']), m['period'], DEC[path])))
for k in rows[0]:
    v = [r[k] for r in rows]; g = [r[k] for r in gt]
    print(k, 'pred min %.3f max %.3f | provider min %.3f max %.3f' % (min(v), max(v), min(g), max(g)))
