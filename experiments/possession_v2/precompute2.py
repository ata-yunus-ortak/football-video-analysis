import sys, os
sys.path.insert(0, '/home/claude/work')
import warnings; warnings.filterwarnings('ignore')
from harness import feats
names = sys.argv[1].split(','); seeds = [int(s) for s in sys.argv[2].split(',')]
tag = sys.argv[3] if len(sys.argv) > 3 else None
for n in names:
    for s in seeds:
        for w in (False, True):
            feats(n, s, w, tag)
            print('done', n, s, w, flush=True)
