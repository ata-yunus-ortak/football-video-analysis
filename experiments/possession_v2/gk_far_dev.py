"""Development (training matches only, no model): what possession.keeper moves when the camera window hides far
players. Counts, per condition, goalkeeper positions under a wrong id before/after and pieces of outfield players
that are moved to the other team (false moves). Usage: far_dev.py MODULE MATCH [MATCH ...]   (MODULE = keeper module name)"""
import sys, json, time, warnings, importlib
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.epts_export import tracklets, pack
from possession.features import play_blocks
from exp_v210 import true_goalkeepers, with_error, SLOT46
from camera_view import apply_view

mod = importlib.import_module(sys.argv[1])


def audit(wide, true, isgk, fixed, given_team_of_wide):
    """Per wide column: positions whose team in `fixed` differs from the true team. Returns
    (gk wrong before, gk wrong after, gk positions, outfield positions moved to the wrong team, outfield false pieces)."""
    C, tc = np.asarray(fixed['players']), np.asarray(fixed['team'])
    gk_b = gk_a = gk_n = out_bad = 0
    for c in range(wide.shape[1]):
        rows = np.flatnonzero(np.isfinite(wide[:, c]).all(1))
        if not len(rows):
            continue
        eq = (C[rows, :, 0] == wide[rows, c, 0][:, None]) & (C[rows, :, 1] == wide[rows, c, 1][:, None])
        got = tc[np.argmax(eq, 1)]
        if isgk[c]:
            gk_b += int(len(rows) if given_team_of_wide[c] != true[c] else 0); gk_a += int((got != true[c]).sum()); gk_n += len(rows)
        elif given_team_of_wide[c] == true[c]:
            out_bad += int((got != true[c]).sum())
    return gk_b, gk_a, gk_n, out_bad


if __name__ == '__main__':
    for name in sys.argv[2:]:
        m, lab = load(name)
        gk = true_goalkeepers(m); gk['clean_team'] = m['team'].copy()
        seed = 6000 + sum(map(ord, name)) % 1000
        rng = np.random.default_rng(seed)
        dm0 = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
        n = len(dm0['ball'])
        for hw in (None, 50.0, 42.0, 35.0):
            dm, vis = (dm0, None) if hw is None else apply_view(dm0, m, hw)
            if vis is not None:
                gcols = sorted(gk[0] | gk[1])
                fin0 = np.isfinite(np.asarray(m['players'])[:, gcols]).all(2)
                per = m['period'] > 0
                seen = round(float(vis[:, gcols][fin0 & per[:, None]].mean()), 3)
                tracked = round(float(np.isfinite(dm['players']).all(2)[per].sum(1).mean()), 2)
            else:
                seen, tracked = 1.0, round(float(np.isfinite(dm['players']).all(2)[m['period'] > 0].sum(1).mean()), 2)
            for k, cond in enumerate(('none', 'gk_one', 'gk_both', 'gk_part')):
                wide, team, true, isgk = with_error(cond, dm, gk, np.random.default_rng(seed + 50 + k))
                P, _ = pack(n, tracklets(wide, team), SLOT46)
                mm = dict(dm, players=P, team=SLOT46)
                t0 = time.time()
                fixed, rep = mod.correct_goalkeepers(mm)
                gb, ga, gn, ob = audit(wide, true, isgk, fixed, team)
                print(json.dumps({'match': name, 'view_half_width': hw, 'goalkeeper_in_view': seen, 'mean_tracked': tracked, 'condition': cond,
                                  'gk_wrong_before': round(gb / max(gn, 1), 4), 'gk_wrong_after': round(ga / max(gn, 1), 4),
                                  'outfield_positions_moved_to_wrong_team': ob, 'moved_pieces': rep['moved_pieces'], 'moved_frames': rep.get('moved_frames'),
                                  'seconds': round(time.time() - t0, 1)}), flush=True)
