"""Add the rebuilt v2.1 validation models' probabilities to the stored DFL development copies (v2.1 path only)."""
import sys, os, glob, pickle, numpy as np
import env
from env import E
import dev216 as D
C = '/Users/umut/BARCELONA/work/v216u/v2cache/'
E.MODELS['v2.1'] = [pickle.load(open(C + f, 'rb')) for f in ('models_v2.pkl', 'stack_v2.pkl')]
name = sys.argv[1]; i = D.NAMES.index(name)
for seed0, sim0 in D.SETS:
    for j in range(4):
        for cond, key, path, base, lab, per, info in D.L.inputs(name, seed0 + 10 * i + j, 2 * i + j, ('tactical', 'tactical_sim2'),
                                                                sim2_seed=(sim0 + i) if j == 0 else None):
            f = D.D + 'v2_' + key.replace('|', '_') + '_' + cond + '.npz'
            if os.path.exists(f) or path != 'v2.1':
                continue
            p11, pd_, ph = E.v2_validation(path, base, per)
            np.savez_compressed(f, v2_labels=p11, p_dead=pd_, p_home=ph)
            print(key, cond, round(E.metrics(lab, p11, per)['spell_f1'], 4), flush=True)
