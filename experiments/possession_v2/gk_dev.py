"""Development of the goalkeeper team correction (training matches only): how many goalkeeper positions carry the
wrong team id before and after possession.keeper.correct_goalkeepers, and how many other positions are touched.
No model is run. Usage: gk_dev.py MATCH [MATCH ...]"""
import sys, json, time, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.keeper import correct_goalkeepers
from possession.epts_export import tracklets, pack
from stress_roles import goalkeepers, variant
import prova_build as pb

SLOT46 = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]


def wrong_counts(wide, true_team, is_gk_col, fixed):
    """(goalkeeper positions with a wrong id, other positions with a wrong id, goalkeeper positions, other positions)."""
    C, tc = np.asarray(fixed['players']), np.asarray(fixed['team'])
    out = [0, 0, 0, 0]
    for c in range(wide.shape[1]):
        col = wide[:, c]
        fin = np.isfinite(col).all(1)
        if not fin.any():
            continue
        rows = np.flatnonzero(fin)
        eq = (C[rows, :, 0] == col[rows, 0][:, None]) & (C[rows, :, 1] == col[rows, 1][:, None])
        assert eq.any(1).all(), 'a position disappeared'
        got = tc[np.argmax(eq, 1)]
        k = 0 if is_gk_col[c] else 1
        out[k] += int((got != true_team[c]).sum())
        out[2 + k] += len(rows)
    return out


if __name__ == '__main__':
    for name in sys.argv[1:]:
        m, lab = load(name)
        gk = goalkeepers(m)
        S = m['players'].shape[1]
        seed = 5000 + sum(map(ord, name)) % 1000
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
        n = len(dm['ball'])
        base_true = np.r_[m['team'], 1 - dm['team'][S:]]                    # degrade's extra columns carry the wrong id by design
        for ci, cond in enumerate(('base', 'gk_one', 'gk_both', 'gk_part')):
            mv = variant(cond, dm, m, gk, np.random.default_rng(seed + 10 + ci))
            wide = np.asarray(mv['players'])
            true_team = base_true if wide.shape[1] == len(base_true) else np.r_[base_true, [k for k in (0, 1) for _ in gk[k]]]
            is_gk = np.zeros(wide.shape[1], bool)
            for k in (0, 1):
                for j in gk[k]:
                    is_gk[j] = True
            is_gk[len(base_true):] = True
            before = wrong_counts(wide, true_team, is_gk, mv)
            for layout in ('wide', 'sticky', 'lru', 'swap'):
                t0 = time.time()
                if layout == 'wide':
                    mm = mv
                elif layout == 'sticky':
                    P, _ = pack(n, tracklets(wide, mv['team']), SLOT46)
                    mm = dict(mv, players=P, team=SLOT46)
                else:
                    P, _ = pb.pack(n, pb.tracklets(wide, mv['team']), SLOT46, layout)
                    mm = dict(mv, players=P, team=SLOT46)
                fixed, rep = correct_goalkeepers(mm)
                after = wrong_counts(wide, true_team, is_gk, fixed)
                row = {'match': name, 'condition': cond, 'layout': layout,
                       'gk_wrong_before': round(before[0] / before[2], 4), 'gk_wrong_after': round(after[0] / after[2], 4),
                       'other_wrong_before': before[1], 'other_wrong_after': after[1], 'gk_positions': before[2],
                       'moved_pieces': rep['moved_pieces'], 'moved_frames': rep.get('moved_frames'), 'new_columns': rep.get('new_columns'),
                       'seconds': round(time.time() - t0, 1)}
                print(json.dumps(row), flush=True)
