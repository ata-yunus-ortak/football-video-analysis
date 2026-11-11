"""Development (training matches only): where goalkeepers and outfield players are when play is far from a goal."""
import sys, json, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.features import play_blocks

def stats(name):
    m, lab = load(name)
    P, team = m['players'].astype(np.float64), m['team']
    L, W = m['pitch']
    out = []
    for a, b in play_blocks(m['period']):
        Q = P[a:b]; fin = np.isfinite(Q).all(2)
        act = fin.mean(0)
        cx = np.nanmedian(Q[:, :, 0], 1)
        mx = np.nanmean(Q[:, :, 0], 0)
        for side in ('left', 'right'):
            far = (cx >= 50) if side == 'left' else (L - cx >= 50)
            d = np.hypot(Q[:, :, 0] if side == 'left' else L - Q[:, :, 0], Q[:, :, 1] - W / 2)        # (T, S) distance to goal centre
            nearest = np.nanargmin(np.where(fin, d, np.inf), 1)
            ok = far & fin.any(1)
            # the keeper of this goal: most extreme mean x on this side among regular players
            idx = np.flatnonzero(act > 0.5)
            gk = idx[np.argmin(mx[idx])] if side == 'left' else idx[np.argmax(mx[idx])]
            row = {'match': name, 'block': [int(a), int(b)], 'side': side, 'far_share': round(float(far.mean()), 3), 'gk': int(gk), 'gk_team': int(team[gk])}
            g = fin[:, gk] & far
            row['gk_d_quantiles_far'] = [round(float(q), 1) for q in np.quantile(d[g, gk], [0.5, 0.8, 0.9, 0.95, 0.99])]
            row['gk_is_nearest_far'] = round(float((nearest[g] == gk).mean()), 4)
            for R in (22, 26, 30, 35):
                row[f'gk_within_{R}'] = round(float((d[g, gk] <= R).mean()), 4)
            # the most keeper-like outfield player: share of far frames in which he is the nearest to this goal / within R
            others = [j for j in idx if j != gk]
            best_near = max(((nearest[far & fin[:, j]] == j).mean() if (far & fin[:, j]).sum() > 250 else 0.0) for j in others)
            row['best_outfield_nearest_share'] = round(float(best_near), 4)
            for R in (22, 30, 35):
                row[f'best_outfield_within_{R}'] = round(float(max(((d[far & fin[:, j], j] <= R).mean() if (far & fin[:, j]).sum() > 250 else 0.0) for j in others)), 4)
            # worst 10-second window of an outfield player: longest run of far frames spent within R of this goal
            for R in (22, 30):
                longest = 0
                for j in others:
                    z = far & fin[:, j] & (d[:, j] <= R)
                    e = np.diff(np.r_[0, z.astype(np.int8), 0]); s_, e_ = np.flatnonzero(e == 1), np.flatnonzero(e == -1)
                    if len(s_): longest = max(longest, int((e_ - s_).max()))
                row[f'longest_outfield_run_within_{R}_frames'] = longest
            out.append(row)
    return out

if __name__ == '__main__':
    for name in sys.argv[1:]:
        for r in stats(name):
            print(json.dumps(r), flush=True)
