"""Reporting-only diagnostic: team membership errors that an automatic tracker can make and the validation never simulated.

DATA.md says about the provided ATD "You get positions and team membership, nothing more". Team membership of a
track is decided by the tracker (kit colour). Two errors are plausible for such a system and are not part of
possession.degrade, which only moves a player to the other team for 1-6 s:
  * a goalkeeper (different kit) carried under the other team's id for long periods;
  * a match official who is tracked and carried under a team id.
Whether the provided tracking has either is unknown and will not be looked at. This script measures how much the
frozen release would lose IF it had them.

Design, fixed before the first result (no selection, no gate, nothing is changed by this script alone): Metrica
sample games 1-3, the corrupted copies of the slot diagnostic (stress_slots.py: v2 profile, seeds 8101-8103), the
frozen release logic in memory, organisers' metric on the external labels. Variants of the same copy:
  base       as corrupted
  gk_one     the home goalkeeper's track carries the away team's id for the whole match
  gk_both    both goalkeepers carry the other team's id for the whole match
  gk_part    each goalkeeper carries the other team's id during random stretches of 30-300 s covering 30% of the match
  ref_home   one extra track that follows play at 8-18 m from the ball (a referee), present 90% of the time, home id
  ref_mixed  the same track with a team id that changes at random every 20-120 s
The goalkeeper of a team in a half is the track of that team with the most extreme mean x on its own side.
Usage: stress_roles.py OUT_JSON
"""
import json
import os
import sys
import time
import warnings
import numpy as np
from scipy.ndimage import gaussian_filter1d
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.features import play_blocks
from possession.evaluate import score
from stress_slots import release_labels

CASES = (('MET1', 8101), ('MET2', 8102), ('MET3', 8103))
VARIANTS = ('base', 'gk_one', 'gk_both', 'gk_part', 'ref_home', 'ref_mixed')


def goalkeepers(m):
    """{team: column} from the clean match: most extreme mean x on the own side, per half (must agree in both halves)."""
    P, team, L = m['players'], m['team'], m['pitch'][0]
    out = {}
    for a, b in play_blocks(m['period']):
        act = np.isfinite(P[a:b]).all(2).mean(0)
        mx = np.nanmean(P[a:b, :, 0], 0)
        for k in (0, 1):
            idx = np.flatnonzero((team == k) & (act > 0.5))
            j = int(idx[np.argmin(mx[idx])] if np.nanmean(mx[idx]) < L / 2 else idx[np.argmax(mx[idx])])
            out.setdefault(k, set()).add(j)
    return {k: v for k, v in out.items()}


def stretches(n, rng, share=0.3, fps=25.0):
    mask = np.zeros(n, bool)
    while mask.mean() < share:
        a = int(rng.integers(0, n))
        mask[a:a + int(rng.uniform(30, 300) * fps)] = True
    return mask


def referee(m, rng, fps=25.0):
    """A track that follows the (last seen, low-passed) clean ball at 8-18 m, direction drifting slowly."""
    ball = m['ball'].astype(float)
    n = len(ball)
    fin = np.isfinite(ball).all(1)
    idx = np.maximum.accumulate(np.where(fin, np.arange(n), -1))
    held = np.where((idx >= 0)[:, None], ball[np.maximum(idx, 0)], np.asarray(m['pitch']) / 2)
    centre = gaussian_filter1d(held, 3 * fps, axis=0, mode='nearest')
    ang = np.cumsum(rng.normal(0, 0.01, n)) + rng.uniform(0, 2 * np.pi)
    dist = 13 + 5 * np.sin(np.cumsum(rng.normal(0, 0.004, n)))
    pos = centre + np.stack([np.cos(ang), np.sin(ang)], 1) * dist[:, None]
    pos = np.clip(pos, 1, np.asarray(m['pitch']) - 1).astype(np.float32)
    z = gaussian_filter1d(rng.standard_normal(n), 2 * fps)
    seen = z > np.quantile(z, 0.1)
    pos[~seen] = np.nan
    pos[m['period'] == 0] = np.nan
    return pos


def variant(v, dm, clean, gk, rng):
    P, team = dm['players'], dm['team'].copy()
    n = len(P)
    if v == 'base':
        return dm
    if v in ('gk_one', 'gk_both'):
        for k in ((0,) if v == 'gk_one' else (0, 1)):
            for j in gk[k]:
                team[j] = 1 - team[j]
        return dict(dm, team=team)
    if v == 'gk_part':
        P = P.copy()
        cols, teams = [], []
        for k in (0, 1):
            for j in gk[k]:
                wrong = stretches(n, rng)
                col = np.full((n, 2), np.nan, np.float32)
                col[wrong] = P[wrong, j]
                P[wrong, j] = np.nan
                cols.append(col); teams.append(1 - k)
        return dict(dm, players=np.concatenate([P, np.stack(cols, 1)], 1), team=np.r_[team, np.array(teams, np.int8)])
    ref = referee(clean, rng)
    if v == 'ref_home':
        return dict(dm, players=np.concatenate([P, ref[:, None]], 1), team=np.r_[team, np.int8(0)])
    side = np.zeros(n, bool)
    t = 0
    while t < n:
        k = int(rng.uniform(20, 120) * 25)
        side[t:t + k] = rng.random() < 0.5
        t += k
    a, b = ref.copy(), ref.copy()
    a[side] = np.nan; b[~side] = np.nan
    return dict(dm, players=np.concatenate([P, a[:, None], b[:, None]], 1), team=np.r_[team, np.int8(0), np.int8(1)])


if __name__ == '__main__':
    OUT = sys.argv[1]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['match'], r['variant']) for r in res['rows']}
    b21 = load_bundle('/home/claude/sc/models/possession-v2.npz')
    b23 = load_bundle('/home/claude/sc/models/possession-v23.npz')
    half = int(b23['card']['smooth_half'])
    for name, seed in CASES:
        if all((name, v) in done for v in VARIANTS):
            continue
        m, lab = load(name)
        gk = goalkeepers(m)
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
        for i, v in enumerate(VARIANTS):
            if (name, v) in done:
                continue
            t0 = time.time()
            mv = variant(v, dm, m, gk, np.random.default_rng(seed + 700 + i))
            labels, path = release_labels(mv, b21, b23, half)
            r = score(lab, labels, m['period'])
            row = {'match': name, 'seed': seed, 'variant': v, 'path': path, 'spell_f1': round(r['spell_f1_mean'], 4),
                   'macro_f1': round(r['macro_f1'], 4), 'f1_H': round(r['f1_H'], 4), 'f1_A': round(r['f1_A'], 4), 'f1_D': round(r['f1_D'], 4),
                   'team_acc_both_alive': round(r['team_acc_both_alive'], 4), 'pred_spells': int(r['n_pred_spells']),
                   'goalkeeper_columns': {str(k): sorted(x) for k, x in gk.items()}, 'seconds': round(time.time() - t0)}
            res['rows'].append(row)
            json.dump(res, open(OUT, 'w'), indent=1)
            print(json.dumps(row), flush=True)
            del mv, labels
    print('ROLESDONE', flush=True)
