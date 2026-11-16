"""Strided features of an alternative feature builder for the stored development copies. Usage: devfeat.py FEAT NAME"""
import sys, os, importlib, numpy as np
import env
from env import E, play_blocks
import dev216 as V
sys.path.insert(0, '/Users/umut/BARCELONA/work/v216u')
F = importlib.import_module('features' + sys.argv[1]); name = sys.argv[2]; i = V.NAMES.index(name)
for seed0, sim0 in V.SETS:
    for j in range(4):
        for cond, key, path, base, lab, per, info in V.L.inputs(name, seed0 + 10 * i + j, 2 * i + j, ('tactical', 'tactical_sim2'),
                                                                sim2_seed=(sim0 + i) if j == 0 else None):
            f = V.D + 'f%s_' % sys.argv[1] + key.replace('|', '_') + '_' + cond + '.npz'
            if os.path.exists(f):
                continue
            out = {}
            for k, (a, b) in enumerate(play_blocks(per)):
                ball, t0, t1 = E.tcn_arrays(base, a, b)
                out[f'x{k}'] = F.build(ball, t0, t1)[0][::2].astype(np.float32)
                out[f'w{k}'] = F.build(ball, t1, t0)[0][::2].astype(np.float32)
            np.savez_compressed(f, **out)
print('done', name)
