"""Find corrupted Metrica copies that the noise gate sends to the v2.3 path and store what is needed to test pooling
there (v2.15 does not pool on that path). Seeds 31000 + 100 * match + k. Usage: scan23.py NAME N"""
import sys, os, importlib, numpy as np
import env
from env import E, play_blocks
import dev216 as V
L = V.L
sys.path.insert(0, '/Users/umut/BARCELONA/work/v216u'); F2 = importlib.import_module('features2')
O = '/Users/umut/BARCELONA/work/v216u/dev23/'
name, n = sys.argv[1], int(sys.argv[2]); i = V.NAMES.index(name)
m, lab = E.load(name); per = m['period']
if name.startswith('J03'):
    import pickle
    E.MODELS['v2.3'] = [pickle.load(open('/Users/umut/BARCELONA/work/v216u/v2cache/' + f, 'rb')) for f in ('models_v23.pkl', 'stack_v23.pkl')]
for k in range(n):
    seed = 32000 + 100 * i + k
    stem = f'{name}_{seed}_tactical.npz'
    rng = np.random.default_rng(seed)
    from possession.degrade import RANGES_V23
    mm = E.packed(E.degrade(m, lab, rng, E.sample_params(rng, ranges=RANGES_V23)))
    path, _ = E.choose_path(E.estimate_noise(mm))
    print(seed, path, flush=True)
    if path != 'v2.3' or os.path.exists(O + stem):
        continue
    base, _ = E.keeper2.correct_goalkeepers(mm)
    p11, pd_, ph = E.v2_validation(path, base, per) if name.startswith('J03') else E.v2_released(path, base)
    f2 = {}
    for b_, (a, b) in enumerate(play_blocks(per)):
        ball, t0, t1 = E.tcn_arrays(base, a, b)
        f2[f'x{b_}'] = F2.build(ball, t0, t1)[0][::2].astype(np.float32); f2[f'w{b_}'] = F2.build(ball, t1, t0)[0][::2].astype(np.float32)
    np.savez_compressed(O + 'f2_' + stem, **f2)
    np.savez_compressed(O + stem, lab=np.asarray(lab), per=per, path=path, v2_labels=p11, p_dead=pd_, p_home=ph, **L.strided_features(base, per))
