"""Development: which goalkeeper pieces stay uncorrected and why (training match, gk_both, sticky layout)."""
import sys, json, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import keeper as K
from possession.features import play_blocks
from possession.epts_export import tracklets, pack
from stress_roles import goalkeepers, variant
name = sys.argv[1]
m, lab = load(name); gk = goalkeepers(m); S = m['players'].shape[1]
seed = 5000 + sum(map(ord, name)) % 1000
rng = np.random.default_rng(seed); dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
mv = variant('gk_both', dm, m, gk, np.random.default_rng(seed + 12))
n = len(dm['ball']); SLOT46 = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]
P, _ = pack(n, tracklets(np.asarray(mv['players']), mv['team']), SLOT46)
L, W = m['pitch']
# true goalkeeper positions per frame (two columns of the wide copy)
gcols = [j for k in (0, 1) for j in gk[k]]
G = np.asarray(mv['players'])[:, gcols]                                   # (n, 2, 2)
ball = np.asarray(dm['ball'])
for a, b in play_blocks(m['period']):
    Q = P[a:b].astype(np.float64); fin = np.isfinite(Q).all(2); x, y = Q[..., 0], Q[..., 1]
    cx = np.nanmedian(x, 1)
    pieces = [(j, s, e) for j in range(Q.shape[1]) for s, e in K._pieces(Q[:, j])]
    for gi in range(2):
        g = G[a:b, gi]
        gf = np.isfinite(g).all(1)
        side = 'left' if np.nanmean(g[:, 0]) < L / 2 else 'right'
        far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= K.FAR_M
        d = np.where(fin, np.hypot(x if side == 'left' else L - x, y - W / 2), np.inf)
        nearest = np.zeros_like(fin); has = fin.any(1); nearest[np.flatnonzero(has), np.argmin(d[has], 1)] = True
        cat = {'strong keeper': 0, 'strong not nearest': 0, 'weak': 0, 'neither': 0}
        near_ball = {k: 0 for k in cat}
        lens = {k: [] for k in cat}
        for j, s, e in pieces:
            own = (Q[s:e, j, 0] == g[s:e, 0]) & (Q[s:e, j, 1] == g[s:e, 1])
            if own.sum() < 0.5 * fin[s:e, j].sum():
                continue
            f = far[s:e] & fin[s:e, j]; nf = int(f.sum())
            if nf >= K.MIN_FAR:
                c = 'strong keeper' if (f & nearest[s:e, j]).sum() >= K.SHARE * nf else 'strong not nearest'
            else:
                c = 'weak' if nearest[s:e, j].sum() >= K.LINK_SHARE * fin[s:e, j].sum() else 'neither'
            cat[c] += int(own.sum()); lens[c].append(e - s)
            db = np.linalg.norm(Q[s:e, j] - ball[a + s:a + e], axis=1)
            near_ball[c] += int((own & (np.nan_to_num(db, nan=99) < 15)).sum())
        tot = sum(cat.values())
        print(name, (a, b), side, 'goalkeeper frames', tot, {k: round(v / tot, 4) for k, v in cat.items()},
              'pieces', {k: (len(v), int(np.median(v)) if v else 0) for k, v in lens.items()},
              'near-ball frames', {k: v for k, v in near_ball.items()}, 'far share %.2f' % far.mean())

print('--- pieces that are not strong keeper pieces')
wideP = np.asarray(mv['players']); wide_team = np.asarray(mv['team'])
for a, b in play_blocks(m['period']):
    Q = P[a:b].astype(np.float64); fin = np.isfinite(Q).all(2); x, y = Q[..., 0], Q[..., 1]
    cx = np.nanmedian(x, 1)
    pieces = [(j, s, e) for j in range(Q.shape[1]) for s, e in K._pieces(Q[:, j])]
    for gi in range(2):
        g = G[a:b, gi]
        side = 'left' if np.nanmean(g[:, 0]) < L / 2 else 'right'
        far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= K.FAR_M
        dd = np.hypot(x if side == 'left' else L - x, y - W / 2)
        d = np.where(fin, dd, np.inf)
        amin = np.argmin(d, 1)
        nearest = np.zeros_like(fin); has = fin.any(1); nearest[np.flatnonzero(has), amin[has]] = True
        for j, s, e in pieces:
            own = (Q[s:e, j, 0] == g[s:e, 0]) & (Q[s:e, j, 1] == g[s:e, 1])
            if own.sum() < 0.5 * fin[s:e, j].sum():
                continue
            f = far[s:e] & fin[s:e, j]; nf = int(f.sum())
            share_far = (f & nearest[s:e, j]).sum() / max(nf, 1)
            share_all = nearest[s:e, j].sum() / fin[s:e, j].sum()
            if nf >= K.MIN_FAR and share_far >= K.SHARE:
                continue
            # who is nearest instead: distance of the goalkeeper and of the nearest other
            rows = np.flatnonzero(fin[s:e, j] & ~nearest[s:e, j]) + s
            other = amin[rows]
            # identify the true wide column of the nearest other
            ident = []
            for r, o in zip(rows[::max(1, len(rows) // 5)], other[::max(1, len(rows) // 5)]):
                c = np.flatnonzero((wideP[a + r, :, 0] == Q[r, o, 0]) & (wideP[a + r, :, 1] == Q[r, o, 1]))
                ident.append((int(c[0]) if len(c) else -1, int(wide_team[c[0]]) if len(c) else -1, round(float(dd[r, o]), 1), round(float(dd[r, j]), 1)))
            print(side, 'slot', j, 'frames', (a + s, a + e), 'len', e - s, 'far', nf, 'share far %.2f all %.2f' % (share_far, share_all),
                  'gk dist median %.1f' % np.nanmedian(dd[s:e, j]), 'nearest other (wide col, team, its dist, gk dist):', ident[:5])
