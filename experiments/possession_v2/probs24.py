"""Cache stage-2 probabilities of one path for the 24 fresh v2.4 copies. Usage: probs24.py SYS TAG"""
import sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from eval_v23 import probs
sysname, tag = sys.argv[1], sys.argv[2]
for base in (1100, 1300, 1500):
    for i, name in enumerate(['J03WN1', 'J03WR9', 'MET1', 'MET2']):
        m, lab = load(name)
        for j in (0, 1):
            probs(sysname, name, base + 10 * i + j, tag, m['period'])
            print('probs', sysname, name, base + 10 * i + j, flush=True)
print('DONE', flush=True)
