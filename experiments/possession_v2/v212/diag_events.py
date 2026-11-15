"""v2.12 development, detector sanity check (reporting only, no selection, no model training).

On ONE development match (DFL J03WOH; clean tracking and training corruption seeds 1, 2, 3) this script times
possession.touch.touch_features and compares the detected touch events with the DFL provider labels:
  - start recall: share of ground-truth team spells that start from the other team's spell and have an event
    attributed to the new team within +-7 frames of the first frame;
  - event agreement: share of attributed events whose team equals the label 3 frames after the event, and the
    share that fall in dead-ball (D) frames;
  - last-touch agreement: on alive frames (H/A), share where the team of the latest attributed event (h_/k_tc_last)
    equals the label, and the share of alive frames that have such a state (coverage);
  - the same last-touch agreement for the baseline's own kick state (features.py: team with the smaller
    t_since_kick, from the verified cache /home/claude/work/cache/J03WOH_s{seed}_w0_f4.npy) for comparison.
Labels are development labels. The design was NOT tuned on these numbers; they are a sanity check.
Usage: /usr/bin/python3 /home/claude/work/v212/diag_events.py  -> diag_events.json
"""
import sys, json, time, platform
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, CACHE
from possession.touch import touch_features, touch_events

NAME = 'J03WOH'
names2 = json.load(open(CACHE + 'names_f2.json'))
out = {'match': NAME, 'environment': {'python': platform.python_version(), 'numpy': np.__version__}, 'rows': {}}
m, lab = load(NAME)
for seed in (-1, 1, 2, 3):
    dm = m if seed < 0 else degraded(NAME, seed)
    t0 = time.time(); X, names = touch_features(dm); t1 = time.time() - t0
    t0 = time.time(); Xs, _ = touch_features(dm, swap=True); t2 = time.time() - t0
    e = touch_events(dm)
    i = {k: j for j, k in enumerate(names)}
    n = len(lab)
    alive = np.isin(lab, ('H', 'A'))
    gt = np.where(lab == 'H', 0, np.where(lab == 'A', 1, -1))
    # spells that start from the other team's spell
    starts = []
    br = np.flatnonzero(lab[1:] != lab[:-1]) + 1
    for t in br:
        if lab[t] in 'HA' and lab[t - 1] in 'HA' and m['period'][t] == m['period'][t - 1]:
            starts.append((t, 0 if lab[t] == 'H' else 1))
    ef, et = e['frame'], e['team']
    hit = [np.any((np.abs(ef - t) <= 7) & (et == k)) for t, k in starts]
    att = et >= 0
    after = np.clip(ef[att] + 3, 0, n - 1)
    agree = float(np.mean(gt[after] == et[att])) if att.any() else float('nan')
    in_dead = float(np.mean(lab[after] == 'D')) if att.any() else float('nan')
    st = np.where(X[:, i['h_tc_last']] == 1, 0, np.where(X[:, i['k_tc_last']] == 1, 1, -1))
    cov = float(np.mean(st[alive] >= 0)); acc = float(np.mean(st[alive & (st >= 0)] == gt[alive & (st >= 0)]))
    row = {'touch_features_s_per_call': round((t1 + t2) / 2, 1), 'sigma_blocks_m': [round(float(s), 3) for s in e['sigma']],
           'ball_visible_frac': round(float(np.isfinite(dm['ball']).all(1).mean()), 3),
           'events': int(len(ef)), 'attributed': int(att.sum()), 'inferred_across_gap': int((e['kind'] == 1).sum()),
           'team_starts': len(starts), 'start_recall_pm7': round(float(np.mean(hit)), 3),
           'event_team_agrees_label': round(agree, 3), 'event_in_dead_ball': round(in_dead, 3),
           'last_touch_alive_coverage': round(cov, 3), 'last_touch_alive_agreement': round(acc, 3)}
    if seed > 0:
        C = np.load(f'{CACHE}{NAME}_s{seed}_w0_f4.npy', mmap_mode='r')
        hs, ks = np.asarray(C[:, names2.index('h_t_since_kick')]), np.asarray(C[:, names2.index('k_t_since_kick')])
        bst = np.where(hs < ks, 0, np.where(ks < hs, 1, -1))
        bok = alive & (bst >= 0) & (np.minimum(hs, ks) < 10)
        row['baseline_kick_state_alive_coverage'] = round(float(bok.sum() / alive.sum()), 3)
        row['baseline_kick_state_alive_agreement'] = round(float(np.mean(bst[bok] == gt[bok])), 3)
    out['rows']['clean' if seed < 0 else f'seed{seed}'] = row
    print(seed, json.dumps(row), flush=True)
out['provided_fixture_used'] = False
out['note'] = 'development match only; sanity check of the detector, not a selection or accuracy claim'
json.dump(out, open('/home/claude/work/v212/diag_events.json', 'w'), indent=1)
