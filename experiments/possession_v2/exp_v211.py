"""v2.11 validation (possession-v211-plan.json): the release logic without a goalkeeper correction (v2.9), with the
second version of the correction (possession/keeper2.py, v2.11) and, in the camera-window conditions with correct
ids, with the first version (possession/keeper.py, v2.10; reporting only), on 8 new corrupted copies of the four
validation matches. Conditions: correct ids and three simulated goalkeeper errors with the whole pitch in view
(as exp_v210.py), and a camera that follows play and does not show players further than 42 m / 35 m from the centre
of play (camera_view.py) with correct ids and, at 42 m, with both goalkeepers under the other id.
Tracks are packed into 46 anonymous slots as in the provided file. Models: the validation models (trained without
these matches), as in every earlier validation.
Usage: exp_v211.py PART      PART = 0 | 1 (matches 0 and 2 | matches 1 and 3)  |  reserved"""
import sys, json, time, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.noise import estimate_noise, choose_path
from possession import keeper, keeper2
from possession.epts_export import tracklets, pack
from exp_v25 import run_path
from exp_v210 import true_goalkeepers, with_error, wrong_share, SLOT46
from camera_view import apply_view

NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
# (name, error simulated by exp_v210.with_error, half-width of the camera window in metres or None)
CONDITIONS = (('none', 'none', None), ('gk_one', 'gk_one', None), ('gk_both', 'gk_both', None), ('gk_part', 'gk_part', None),
              ('view42_none', 'none', 42.0), ('view35_none', 'none', 35.0), ('view42_gk_both', 'gk_both', 42.0))
SEED, ERR_SEED = 11100, 21100


def false_moves(wide, team, true, isgk, fixed):
    """Positions of outfield players that had the right team id as given and carry the wrong one after the correction."""
    C, tc = np.asarray(fixed['players']), np.asarray(fixed['team'])
    bad = 0
    for c in np.flatnonzero(~isgk & (team == true)):
        rows = np.flatnonzero(np.isfinite(wide[:, c]).all(1))
        if len(rows):
            eq = (C[rows, :, 0] == wide[rows, c, 0][:, None]) & (C[rows, :, 1] == wide[rows, c, 1][:, None])
            bad += int((tc[np.argmax(eq, 1)] != true[c]).sum())
    return bad


def rows_for(name, seed, ci, res, OUT, done):
    m, lab = load(name)
    per = m['period']
    gk = true_goalkeepers(m)
    gk['clean_team'] = m['team'].copy()
    rng = np.random.default_rng(seed)
    dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
    n = len(dm['ball'])
    views = {}
    for k, (cond, error, hw) in enumerate(CONDITIONS):
        key = f'{name}|{seed}'
        if (key, cond) in done:
            continue
        t0 = time.time()
        if hw not in views:
            views[hw] = (dm, None) if hw is None else apply_view(dm, m, hw)
        dv, vis = views[hw]
        wide, team, true, isgk = with_error(error, dv, gk, np.random.default_rng(ERR_SEED + 100 * k + ci))
        P, _ = pack(n, tracklets(wide, team), SLOT46)
        mm = dict(dv, players=P, team=SLOT46)
        path, _ = choose_path(estimate_noise(mm))                     # on the tracking as given, as in the entry point
        a = run_path(path, mm, lab, per)
        row = {'copy': key, 'condition': cond, 'path': path, 'v2_9': [round(x, 4) for x in a],
               'goalkeeper_columns': {str(t): sorted(gk[t]) for t in (0, 1)},
               'mean_tracked_in_play': round(float(np.isfinite(P).all(2)[per > 0].sum(1).mean()), 2)}
        if vis is not None:
            g = sorted(gk[0] | gk[1])
            there = np.isfinite(np.asarray(m['players'])[:, g]).all(2) & (per > 0)[:, None]
            row['goalkeeper_in_view_share'] = round(float(vis[:, g][there].mean()), 3)
        systems = [('v2_11', keeper2)] + ([('v2_10', keeper)] if cond in ('view42_none', 'view35_none') else [])
        for tag, mod in systems:
            fixed, rep = mod.correct_goalkeepers(mm)
            b = a if fixed is mm else run_path(path, fixed, lab, per)
            row[tag] = [round(x, 4) for x in b]
            row[tag + '_moved'] = {'pieces': rep['moved_pieces'], 'frames': rep.get('moved_frames'),
                                   'goalkeeper_positions_with_wrong_id_before_after': [
                                       wrong_share(wide, true, isgk, P, SLOT46),
                                       wrong_share(wide, true, isgk, np.asarray(fixed['players']), np.asarray(fixed['team']))],
                                   'outfield_positions_moved_to_the_wrong_team': false_moves(wide, team, true, isgk, fixed)}
        row['seconds'] = round(time.time() - t0)
        res['rows'].append(row)
        json.dump(res, open(OUT, 'w'), indent=1)
        print(key, cond, path, 'v2.9 %.4f v2.11 %.4f' % (a[0], row['v2_11'][0]), ('v2.10 %.4f' % row['v2_10'][0]) if 'v2_10' in row else '',
              'moved', row['v2_11_moved']['pieces'], row['v2_11_moved']['goalkeeper_positions_with_wrong_id_before_after'],
              'false', row['v2_11_moved']['outfield_positions_moved_to_the_wrong_team'], row['seconds'], 's', flush=True)


if __name__ == '__main__':
    part = sys.argv[1]
    OUT = f'/home/claude/work/exp_v211_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if part == 'reserved':
        rows_for('MET3', 31103, 99, res, OUT, done)
    else:
        for i, name in enumerate(NAMES):
            if i % 2 != int(part):
                continue
            for j in (0, 1):
                rows_for(name, SEED + 10 * i + j, 2 * i + j, res, OUT, done)
    print('V211DONE', part, flush=True)
