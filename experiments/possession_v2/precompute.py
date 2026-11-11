import sys
sys.path.insert(0, '/home/claude/work')
from harness import feats
names = sys.argv[1].split(','); seeds = [int(s) for s in sys.argv[2].split(',')]
for n in names:
    for s in seeds:
        for w in (False, True):
            feats(n, s, w)
            print('done', n, s, w, flush=True)
