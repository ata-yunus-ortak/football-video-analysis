"""Development: which pieces are moved although their true team is not the defending team (base condition)."""
import sys, json, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import keeper as K
from possession.features import play_blocks
import prova_build as pb
from stress_roles import goalkeepers
name, layout = sys.argv[1], sys.argv[2]
m, lab = load(name); gk = goalkeepers(m); S = m['players'].shape[1]
seed = 5000 + sum(map(ord, name)) % 1000
rng = np.random.default_rng(seed); dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
n = len(dm['ball']); SLOT46 = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]
wide = np.asarray(dm['players']); true_team = np.r_[m['team'], 1 - dm['team'][S:]]
P, _ = pb.pack(n, pb.tracklets(wide, dm['team']), SLOT46, layout)
L, W = m['pitch']
gcols = {j for k in (0, 1) for j in gk[k]}
for a, b in play_blocks(m['period']):
    Q = P[a:b].astype(np.float64)
    found, facts = K._block(Q, SLOT46, L, W)
    fin = np.isfinite(Q).all(2); cx = np.nanmedian(Q[..., 0], 1)
    for j, s, e, t in found:
        r = s + int(np.flatnonzero(fin[s:e, j])[0])
        c = np.flatnonzero((wide[a + r, :, 0] == Q[r, j, 0]) & (wide[a + r, :, 1] == Q[r, j, 1]))
        c = int(c[0])
        side = 'left' if facts['left_team'] == t else 'right'
        far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= K.FAR_M
        nf = int((far[s:e] & fin[s:e, j]).sum())
        d = np.hypot(Q[s:e, j, 0] if side == 'left' else L - Q[s:e, j, 0], Q[s:e, j, 1] - W / 2)
        kind = 'GK' if c in gcols else ('flip' if c >= S else 'outfield')
        print(name, (a + s, a + e), 'len', e - s, 'slot', j, 'to team', t, 'true', int(true_team[c]), kind, 'col', c, 'far', nf, 'median dist %.1f' % np.nanmedian(d),
              'OK' if true_team[c] == t else 'FALSE')
