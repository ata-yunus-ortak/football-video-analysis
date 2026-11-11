import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.decode import emissions, decode_blocks
from diagnose import diagnose
key = sys.argv[1]; prm = json.loads(sys.argv[2])
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    for seed in (101,):
        z = np.load(f'/home/claude/work/cache/probs_{key}_{name}_{seed}.npz')
        pred = decode_blocks(emissions(z['pd'], z['ph']), m['period'], prm)
        r = diagnose(lab, pred, m['period'])
        print(name, seed, {k: v for k, v in r.items()})
