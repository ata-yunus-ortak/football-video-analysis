"""Reporting only: details of the pieces that the correction moved wrongly on validation copies with correct ids."""
import json, sys, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import keeper as K
from possession.features import play_blocks
from possession.epts_export import tracklets, pack
from exp_v210 import SLOT46, true_goalkeepers
for name, seed in (('J03WR9', 10110), ('J03WR9', 10111), ('MET1', 10120)):
    m, lab = load(name); gk = true_goalkeepers(m); S = m['players'].shape[1]; clean = np.asarray(m['players'])
    rng = np.random.default_rng(seed); dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
    wide = np.asarray(dm['players']); true = np.r_[m['team'], 1 - dm['team'][S:]]; n = len(wide)
    P, _ = pack(n, tracklets(wide, dm['team']), SLOT46); L, W = m['pitch']
    for h, (a, b) in enumerate(play_blocks(m['period'])):
        Q = P[a:b].astype(np.float64); fin = np.isfinite(Q).all(2); cx = np.nanmedian(Q[..., 0], 1)
        found, facts = K._block(Q, SLOT46, L, W)
        for slot, s, e, t in found:
            f = np.flatnonzero(fin[s:e, slot]); r = a + s + int(f[len(f) // 2])
            c = int(np.flatnonzero((wide[r, :, 0] == P[r, slot, 0]) & (wide[r, :, 1] == P[r, slot, 1]))[0])
            if true[c] == t:
                continue
            side = 'left' if facts['left_team'] == t else 'right'
            far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= K.FAR_M
            x = Q[s:e, slot, 0]; dgoal = np.hypot(x if side == 'left' else L - x, Q[s:e, slot, 1] - W / 2)
            dd = np.where(fin, np.hypot(Q[..., 0] if side == 'left' else L - Q[..., 0], Q[..., 1] - W / 2), np.inf)
            nearest = np.argmin(dd[s:e], 1) == slot
            nf = far[s:e] & fin[s:e, slot]
            # the true goalkeeper of that goal (team t): tracked in the corrupted copy during the piece?
            g = [j for j in gk[t]]
            gtrack = np.isfinite(wide[a + s:a + e][:, g]).all(2).any(1)
            # which wide columns does the piece consist of (identity changes inside the piece)?
            cols = []
            for rr in f[:: max(1, len(f) // 40)]:
                cc = np.flatnonzero((wide[a + s + rr, :, 0] == P[a + s + rr, slot, 0]) & (wide[a + s + rr, :, 1] == P[a + s + rr, slot, 1]))
                cols.append(int(cc[0]) if len(cc) else -1)
            runs = [cols[0]] + [y for x_, y in zip(cols, cols[1:]) if y != x_]
            print(json.dumps({'copy': f'{name}|{seed}', 'half': h + 1, 'frames': [a + s, a + e], 'len': e - s, 'slot': slot, 'slot_team': int(SLOT46[slot]), 'moved_to': t, 'side': side,
                              'far_frames': int(nf.sum()), 'nearest_in_far': int((nf & nearest).sum()), 'nearest_overall_share': round(float(nearest[fin[s:e, slot]].mean()), 3),
                              'median_dist_to_goal': round(float(np.nanmedian(dgoal)), 1), 'dist_quantiles': [round(float(q), 1) for q in np.nanquantile(dgoal, [0.1, 0.5, 0.9])],
                              'true_goalkeeper_of_that_goal_tracked_share': round(float(gtrack.mean()), 3), 'wide_columns_in_piece': runs[:12], 'S': S,
                              'true_team_of_columns': [int(true[c_]) if c_ >= 0 else None for c_ in runs[:12]], 'is_goalkeeper_column': [c_ in gk[0] | gk[1] for c_ in runs[:12]]}))
