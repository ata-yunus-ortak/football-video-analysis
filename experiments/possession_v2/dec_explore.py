import sys, json, itertools, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.decode import decode_blocks
from possession.evaluate import score
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
cases = []
for i, name in enumerate(NAMES):
    m, lab = load(name)
    for seed, tag in ((101, '_f2'), (102, '_f2'), (1100 + 10 * i, '_g21'), (1101 + 10 * i, '_g21')):
        z = np.load(f'cache/probs_sys_v21_{name}_{seed}{tag}.npz')
        cases.append((name, seed, lab, m['period'], z['pd'], z['ph']))
def em(pd_, ph, tt, td, eps=1e-4):
    pd_ = np.clip(pd_, eps, 1 - eps); ph = np.clip(ph, eps, 1 - eps)
    lh = np.log(ph / (1 - ph)) * tt; ph2 = 1 / (1 + np.exp(-lh))
    ld = np.log(pd_ / (1 - pd_)) * td; pd2 = 1 / (1 + np.exp(-ld))
    return np.stack([np.log1p(-pd2) + np.log(ph2), np.log1p(-pd2) + np.log1p(-ph2), np.log(pd2)], 1)
res = []
for sw, tt in itertools.product([1.5, 2, 3, 4, 6], [0.7, 1.0, 1.4, 2.0]):
    sc = [score(lab, decode_blocks(em(pd_, ph, tt, 1.0), per, {'switch': sw, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}), per) for _, _, lab, per, pd_, ph in cases]
    s = [x['spell_f1_mean'] for x in sc]
    res.append((np.mean(s), np.mean(s[0::4] + s[1::4]), np.mean(s[2::4] + s[3::4]), sw, tt, np.mean([x['n_pred_spells'] for x in sc])))
    print([round(float(v), 4) for v in res[-1]], flush=True)
