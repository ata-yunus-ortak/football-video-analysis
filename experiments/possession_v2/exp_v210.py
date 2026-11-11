"""v2.10 validation (possession-v210-plan.json): the release logic with and without the goalkeeper team correction
(possession/keeper.py) on 8 new corrupted copies of the four validation matches, with correct team ids and with
three simulated goalkeeper errors. Tracks are packed into 46 anonymous slots as in the provided file. Models: the
validation models (trained without these matches), as in every earlier validation. Usage: exp_v210.py [reserved]"""
import sys, json, time, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.noise import estimate_noise, choose_path
from possession.features import play_blocks
from possession.keeper import correct_goalkeepers
from possession.epts_export import tracklets, pack
from exp_v25 import run_path

NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
CONDITIONS = ('none', 'gk_one', 'gk_both', 'gk_part')
SEED, ERR_SEED = 10100, 20100
SLOT46 = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]


def true_goalkeepers(m):
    """{team: set of columns}: per half the regular player of a team with the most extreme mean x towards the goal
    his team defends (the team with the smaller mean x defends the left goal)."""
    P, team = m['players'], m['team']
    out = {0: set(), 1: set()}
    for a, b in play_blocks(m['period']):
        act = np.isfinite(P[a:b]).all(2).mean(0)
        mx = np.nanmean(P[a:b, :, 0], 0)
        side = [np.nanmean(P[a:b][:, team == k, 0]) for k in (0, 1)]
        for k in (0, 1):
            idx = np.flatnonzero((team == k) & (act > 0.5))
            out[k].add(int(idx[np.argmin(mx[idx])] if side[k] < side[1 - k] else idx[np.argmax(mx[idx])]))
    return out


def stretches(n, rng, share=0.3, fps=25.0):
    mask = np.zeros(n, bool)
    while mask.mean() < share:
        a = int(rng.integers(0, n))
        mask[a:a + int(rng.uniform(30, 300) * fps)] = True
    return mask


def with_error(cond, dm, gk, rng):
    """(players, team, true team per column, is-goalkeeper per column) of the wide copy with the simulated error."""
    P, team = dm['players'], dm['team'].copy()
    S = len(gk['clean_team'])
    true = np.r_[gk['clean_team'], 1 - dm['team'][S:]]            # degrade's extra columns carry the wrong id by design
    isgk = np.zeros(P.shape[1], bool)
    for k in (0, 1):
        for j in gk[k]:
            isgk[j] = True
    if cond == 'none':
        return P, team, true, isgk
    if cond in ('gk_one', 'gk_both'):
        for k in ((0,) if cond == 'gk_one' else (0, 1)):
            for j in gk[k]:
                team[j] = 1 - team[j]
        return P, team, true, isgk
    P = P.copy()
    n = len(P)
    cols, teams, tt = [], [], []
    for k in (0, 1):
        for j in sorted(gk[k]):
            wrong = stretches(n, rng)
            col = np.full((n, 2), np.nan, np.float32)
            col[wrong] = P[wrong, j]
            P[wrong, j] = np.nan
            cols.append(col); teams.append(1 - k); tt.append(k)
    return (np.concatenate([P, np.stack(cols, 1)], 1), np.r_[team, np.array(teams, np.int8)], np.r_[true, tt],
            np.r_[isgk, np.ones(len(cols), bool)])


def wrong_share(wide, true, isgk, players, team):
    """Share of goalkeeper positions that carry a wrong team id in (players, team)."""
    bad = tot = 0
    for c in np.flatnonzero(isgk):
        rows = np.flatnonzero(np.isfinite(wide[:, c]).all(1))
        if not len(rows):
            continue
        eq = (players[rows, :, 0] == wide[rows, c, 0][:, None]) & (players[rows, :, 1] == wide[rows, c, 1][:, None])
        bad += int((team[np.argmax(eq, 1)] != true[c]).sum()); tot += len(rows)
    return round(bad / max(tot, 1), 4)


def rows_for(name, seed, ci, res, OUT, done, layout='sticky'):
    m, lab = load(name)
    per = m['period']
    gk = true_goalkeepers(m)
    gk['clean_team'] = m['team'].copy()
    rng = np.random.default_rng(seed)
    dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
    n = len(dm['ball'])
    for k, cond in enumerate(CONDITIONS):
        key = f'{name}|{seed}'
        if (key, cond) in done:
            continue
        t0 = time.time()
        wide, team, true, isgk = with_error(cond, dm, gk, np.random.default_rng(ERR_SEED + 100 * k + ci))
        P, _ = pack(n, tracklets(wide, team), SLOT46)
        mm = dict(dm, players=P, team=SLOT46)
        path, _ = choose_path(estimate_noise(mm))                     # on the tracking as given, as in the entry point
        a = run_path(path, mm, lab, per)
        fixed, rep = correct_goalkeepers(mm)
        b = a if fixed is mm else run_path(path, fixed, lab, per)
        row = {'copy': key, 'condition': cond, 'layout': layout, 'path': path,
               'v2_9': [round(x, 4) for x in a], 'v2_10': [round(x, 4) for x in b],
               'moved_pieces': rep['moved_pieces'], 'moved_frames': rep.get('moved_frames'),
               'goalkeeper_positions_with_wrong_id': [wrong_share(wide, true, isgk, P, SLOT46),
                                                      wrong_share(wide, true, isgk, np.asarray(fixed['players']), np.asarray(fixed['team']))],
               'goalkeeper_columns': {str(t): sorted(gk[t]) for t in (0, 1)}, 'seconds': round(time.time() - t0)}
        res['rows'].append(row)
        json.dump(res, open(OUT, 'w'), indent=1)
        print(key, cond, path, 'v2.9 %.4f v2.10 %.4f' % (a[0], b[0]), 'moved', rep['moved_pieces'], row['goalkeeper_positions_with_wrong_id'],
              row['seconds'], 's', flush=True)


if __name__ == '__main__':
    reserved = len(sys.argv) > 1 and sys.argv[1] == 'reserved'
    OUT = '/home/claude/work/exp_v210_reserved.json' if reserved else '/home/claude/work/exp_v210.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if reserved:
        rows_for('MET3', 30103, 99, res, OUT, done)
    else:
        for i, name in enumerate(NAMES):
            for j in (0, 1):
                rows_for(name, SEED + 10 * i + j, 2 * i + j, res, OUT, done)
    print('V210DONE', flush=True)
