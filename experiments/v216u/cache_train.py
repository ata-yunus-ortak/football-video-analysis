"""Training features for the TCN, made the way the release sees tracking: the team's corruption simulator or the second
one, then 46 packed anonymous slots and the goalkeeper correction. Six DFL matches, external only.
Usage: cache_train.py MATCH N_OURS N_SIM2"""
import sys, os, numpy as np
import env
from env import E, play_blocks, tfeat
OUT = '/Users/umut/BARCELONA/work/v216u/cache/'
MATCHES = ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ', 'J03WN1', 'J03WR9']
CODE = {'H': 0, 'A': 1, 'D': 2}
os.makedirs(OUT, exist_ok=True)
name, n_ours, n_sim2 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
mi = MATCHES.index(name)
m, lab = E.load(name)
y_all = np.array([CODE[c] for c in np.asarray(lab)], np.int8)
blocks = play_blocks(m['period'])

def write(dm, tag, r):
    fixed, _ = E.keeper2.correct_goalkeepers(E.packed(dm))
    for h, (a, b) in enumerate(blocks):
        ball, t0, t1 = E.tcn_arrays(fixed, a, b)
        y = y_all[a:b]
        if r % 2 == 1:
            t0, t1 = t1, t0; y = tfeat.swap_labels(y)
        x, _ = tfeat.build(ball, t0, t1)
        np.savez(f'{OUT}{name}_h{h + 1}_{tag}{r}.npz', x=x[::2].astype(np.float16), y=y[::2])

for r in range(n_ours):
    if not os.path.exists(f'{OUT}{name}_h{len(blocks)}_ours{r}.npz'):
        rng = np.random.default_rng(7100000 + 1000 * mi + r)
        write(E.degrade(m, lab, rng, E.sample_params(rng, ranges=E.RANGES)), 'ours', r)
for r in range(n_sim2):
    if not os.path.exists(f'{OUT}{name}_h{len(blocks)}_sim{r}.npz'):
        write(E.sim2(m, 7200000 + 1000 * mi + r), 'sim', r)
print(name, 'done', flush=True)
