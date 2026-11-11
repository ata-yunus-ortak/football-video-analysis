import sys, numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
import pandas as pd
from harness import load
from possession.evaluate import score
out = {}
for name in ('MET1', 'MET2', 'MET3', 'J03WN1', 'J03WR9'):
    m, lab = load(name)
    out[name] = int(score(lab, np.asarray(lab), m['period'])['n_gt_spells'])
print(sys.version.split()[0], 'pandas', pd.__version__, out, 'mean of the four validation matches', np.mean([out[k] for k in ('MET1', 'MET2', 'J03WN1', 'J03WR9')]))
