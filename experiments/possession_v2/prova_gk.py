"""Full-size rehearsal bundle with both goalkeepers under the other team's id (v2.10 wiring check).

Development only; nothing of the provided match is used. Same content, seed, profile and steps as prova_build.py
(bundle A of the K003 rehearsal) with one change: the tracks of the goalkeepers (one per team in the Metrica
game 3 part and one per team in the appended game 2 part) carry the other team's id for the whole match, as a
tracker that decides the team from the kit could do. The duplicated tracks copy that id as they copy any other.
The truth copy (truth.npz) keeps the true ids, so it equals the truth copy of bundle A.

  --feeds tactical   only the tactical tracking has the error (the broadcast tracking has the true ids)
  --feeds both       the broadcast tracking has the same error

Usage: prova_gk.py OUT_DIR [--seed N] [--profile good|hard] [--feeds tactical|both]
"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova_build as pb
from prova_build import N, FPS, LEAD, W1, W2, PROFILES
from possession.degrade import degrade
import synth_clock as sc


def goalkeepers(clean, src):
    """Columns of the goalkeepers in the assembled clean match: per source piece and team the column (active in
    more than half of the piece) with the most extreme mean x towards the goal its team defends."""
    P, team = clean['players'], clean['team']
    out, facts = set(), {}
    for name, s in src.items():
        a, b = s['to']
        act = np.isfinite(P[a:b]).all(2).mean(0)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)                  # columns of the other game are empty here
            mx = np.nanmean(P[a:b, :, 0], 0)
        cols = act > 0.5
        side = [np.nanmean(P[a:b][:, cols & (team == k), 0]) for k in (0, 1)]
        for k in (0, 1):
            idx = np.flatnonzero(cols & (team == k))
            j = int(idx[np.argmin(mx[idx])] if side[k] < side[1 - k] else idx[np.argmax(mx[idx])])
            out.add(j)
            facts[f'{name}, team {k}'] = {'column': j, 'mean_x_m': round(float(mx[j]), 1), 'team_mean_x_m': round(float(side[k]), 1)}
    return sorted(out), facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--seed', type=int, default=20261111); ap.add_argument('--profile', default='good')
    ap.add_argument('--feeds', choices=('tactical', 'both'), default='tactical')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    t0 = time.time()
    rng = np.random.default_rng(a.seed)
    params, bq = PROFILES[a.profile]
    clean, lab, src = pb.assemble(rng)
    gk, gk_facts = goalkeepers(clean, src)
    print('assembled', round(time.time() - t0), 's; goalkeeper columns', gk, json.dumps(gk_facts), flush=True)
    dm = degrade(clean, lab, rng, dict(params))
    ball, players, team_true = dm['ball'].copy(), dm['players'].copy(), dm['team'].copy()
    team = team_true.copy()
    team[gk] = 1 - team[gk]                                                # THE CHANGE: goalkeepers under the other id
    bstat = pb.trim_ball(ball, rng)
    dups = pb.duplicates(players, team, rng, 0.0012)
    tstat = pb.trim_tracked(players, dups, rng)
    id_team = np.r_[np.zeros(30, np.int8), np.ones(30, np.int8)]
    P_id, _ = pb.pack(N, pb.tracklets(players, team_true), id_team, 'sticky', gap=10 ** 9)
    np.savez_compressed(out / 'truth.npz', lab=lab, period_play=clean['period'], ball=ball, players=P_id, team=id_team)
    del P_id
    slot_team = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]
    rng.shuffle(slot_team)
    items = pb.tracklets(players, team) + [(x, y, t, f'dup{i}', xy) for i, (x, y, t, xy) in enumerate(dups)]
    P46, peak = pb.pack(N, items, slot_team, 'sticky')
    g = pb.graded_mask()
    count = np.isfinite(P46).all(2).sum(1)
    fin = np.isfinite(players[:, gk]).all(2)
    tac = {'tracklets': len(items), 'duplicated_tracks': len(dups), 'peak_simultaneous_per_team': peak,
           'mean_tracked_on_graded': round(float(count[g].mean()), 4), 'ball': bstat, 'tracked_trim': tstat,
           'goalkeeper_columns': gk, 'goalkeeper_positions_under_the_other_id': int(fin.sum()),
           'share_of_all_player_positions': round(float(fin.sum() / np.isfinite(players).all(2).sum()), 4)}
    print('packed', round(time.time() - t0), 's', json.dumps(tac), flush=True)
    pb.write_epts(out / 'bundle' / 'tactical', 'BAR-ATH_tactical', P46, ball, slot_team)
    del P46, items
    q = {'drift': 2e-5, 'pre_frames': LEAD[1] - LEAD[0], 'post_s': 30.0, 'hx': 26.0, 'hy': 17.0, 'ball_frac': 0.97, 'outlier': 0.01}
    q.update(bq)
    rb = np.random.default_rng(a.seed + 1)
    bclean = clean
    if a.feeds == 'both':
        bteam = clean['team'].copy()
        bteam[gk] = 1 - bteam[gk]
        bclean = dict(clean, team=bteam)
    bro, valid, clock_t, binfo = pb.simulate_broadcast(bclean, lab, rb, q)
    bslot_team = np.r_[np.zeros(26, np.int8), np.ones(25, np.int8)]
    rb.shuffle(bslot_team)
    P51, bpeak = pb.pack(len(valid), pb.tracklets(bro['players'], bro['team']), bslot_team, 'sticky')
    pb.write_epts(out / 'bundle' / 'broadcast', 'BAR-ATH_broadcast', P51, bro['ball'], bslot_team)
    pb.write_homography(out / 'bundle' / 'broadcast' / 'BAR-ATH_broadcast_homography.csv', valid, rb)
    print('broadcast written', round(time.time() - t0), 's', flush=True)
    blocks = [W1, W2]
    rc = np.random.default_rng(a.seed + 2)
    for cam, live_t, p_read in (('tactical', np.arange(N), 0.8), ('broadcast', clock_t, 0.7)):
        d = out / 'private' / 'possession-clock' / cam
        d.mkdir(parents=True)
        rows = sc.observations(live_t, blocks, FPS, rc, p_read, 0.02)
        (d / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (d / 'summary.json').write_text('{}')
    gt = np.where(g, lab, 'X')
    (out / 'gt').mkdir()
    with open(out / 'gt' / 'PROVA_possession_gt.csv', 'w', newline='\n') as fh:
        fh.write('frame,label\n')
        fh.writelines(f'{i},{l}\n' for i, l in enumerate(gt.tolist()))
    info = {'seed': a.seed, 'profile': a.profile, 'feeds_with_the_error': a.feeds, 'goalkeepers': gk_facts, 'tactical': tac,
            'broadcast': dict(binfo, peak_simultaneous_per_team=bpeak), 'seconds': round(time.time() - t0)}
    (out / 'build.json').write_text(json.dumps(info, indent=1))
    print('DONE', info['seconds'], 's', flush=True)


if __name__ == '__main__':
    main()
