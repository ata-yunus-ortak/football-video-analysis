"""Broadcast-fill conditions (fill_good, fill_medium) for the new-seed check: copies j = 0, 1 of each match.
New stream / clock seeds 83100 / 93100. Usage: holdfill.py NAME"""
import sys, os, pickle, importlib, numpy as np
import env
from env import E, play_blocks
import dev216 as V
L = V.L
L.STREAM, L.CLOCK = 83100, 93100
L.quality = env._quality
sys.path.insert(0, '/Users/umut/BARCELONA/work/v216u'); F2 = importlib.import_module('features2')
C = '/Users/umut/BARCELONA/work/v216u/v2cache/'
E.MODELS['v2.1'] = [pickle.load(open(C + f, 'rb')) for f in ('models_v2.pkl', 'stack_v2.pkl')]
O = '/Users/umut/BARCELONA/work/v216u/holdfill/'
name = sys.argv[1]; i = V.NAMES.index(name)
for j in (0, 1):
    for cond, key, path, base, lab, per, info in L.inputs(name, 23100 + 10 * i + j, 2 * i + j, ('fill_good', 'fill_medium')):
        stem = key.replace('|', '_') + '_' + cond + '.npz'
        if os.path.exists(O + stem):
            continue
        if path != 'v2.1':
            print(key, cond, 'v2.3 path: not pooled, skipped', flush=True); continue
        p11, pd_, ph = E.v2_validation(path, base, per) if name.startswith('J03') else E.v2_released(path, base)
        f2 = {}
        for k, (a, b) in enumerate(play_blocks(per)):
            ball, t0, t1 = E.tcn_arrays(base, a, b)
            f2[f'x{k}'] = F2.build(ball, t0, t1)[0][::2].astype(np.float32); f2[f'w{k}'] = F2.build(ball, t1, t0)[0][::2].astype(np.float32)
        np.savez_compressed(O + 'f2_' + stem, **f2)
        np.savez_compressed(O + stem, lab=np.asarray(lab), per=per, path=path, v2_labels=p11, p_dead=pd_, p_home=ph, **L.strided_features(base, per))
        print(key, cond, path, info.get('gate_used'), flush=True)
print('done', name)
