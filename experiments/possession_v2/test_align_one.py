import sys, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded
from possession import broadcast as bc
from possession.features import play_blocks
import synth_broadcast as sb
name, seed = sys.argv[1], int(sys.argv[2])
m, lab = load(name); dm = degraded(name, seed)
rng = np.random.default_rng(8001)
q = sb.sample_quality(rng, sys.argv[3] if len(sys.argv) > 3 else 'default')
t = time.time()
bro, valid, true_t = sb.simulate(m, lab, rng, q)
print('broadcast frames', len(valid), 'valid %.3f' % valid.mean(), 'live-valid %.3f' % (true_t >= 0).mean(), 'ball %.3f' % np.isfinite(bro['ball']).all(1).mean(), round(time.time() - t, 1), 's')
halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(play_blocks(m['period']))]
t = time.time()
bro2, orep = bc.orient(dm, bro, valid, m['fps'], m['pitch'])
print('orient', orep, round(time.time() - t, 1), 's')
t = time.time()
t_of_b, rep = bc.align(dm, bro2, valid, m['fps'], halves)
print('align', rep, round(time.time() - t, 1), 's')
acc = t_of_b >= 0
good = acc & (true_t >= 0) & (np.abs(t_of_b - true_t) <= 2)
print('precision %.4f recall %.4f median|err| %.1f' % (good.sum() / max(acc.sum(), 1), good.sum() / max((true_t >= 0).sum(), 1),
      np.median(np.abs(t_of_b[acc & (true_t >= 0)] - true_t[acc & (true_t >= 0)])) if (acc & (true_t >= 0)).any() else -1))
graded = np.isin(m['period'], (1, 2))
fb, frep = bc.fuse(dm['ball'], bro2['ball'], t_of_b, m['fps'], graded)
print('fuse', frep)
