"""v2.12 development, design look (reporting only, no selection): what do short possessions look like in ONE
development match (DFL J03WOH, clean tracking and training corruption seed 1)?

Prints: transition counts, ground-truth spell length bins, and around the first frame of every team spell
(H/A run) that starts from the other team: ball visibility (clean vs corrupted), the nearest player's team and
distance at the start, and a simple velocity change of the clean ball. Labels are DFL provider flags of a
development match (allowed); no validation/reserved match is touched.
Usage: /usr/bin/python3 /home/claude/work/v212/explore_short.py
"""
import sys, json
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded
from possession.features import play_blocks

m, lab = load('J03WOH')
dm = degraded('J03WOH', 1)
per = m['period']
blocks = play_blocks(per)
tr = {}
spells = []
for a, b in blocks:
    w = lab[a:b]
    br = np.flatnonzero(w[1:] != w[:-1]) + 1
    bounds = np.r_[0, br, len(w)]
    segs = [(a + int(bounds[i]), a + int(bounds[i + 1]), w[bounds[i]]) for i in range(len(bounds) - 1)]
    for (s0, e0, k0), (s1, e1, k1) in zip(segs[:-1], segs[1:]):
        tr[f'{k0}->{k1}'] = tr.get(f'{k0}->{k1}', 0) + 1
    for i, (s, e, k) in enumerate(segs):
        if k in 'HA':
            prev = segs[i - 1][2] if i else 'start'
            nxt = segs[i + 1][2] if i + 1 < len(segs) else 'end'
            spells.append((s, e, k, prev, nxt))
print('transitions', json.dumps(tr))
L = np.array([e - s for s, e, *_ in spells])
print('spells', len(L), 'lt1s', int((L < 25).sum()), '1-2s', int(((L >= 25) & (L < 50)).sum()), 'median', float(np.median(L)))
short = [(s, e, k, p, n) for s, e, k, p, n in spells if e - s < 50]
kinds = {}
for s, e, k, p, n in short:
    kinds[f'{p}->[{k}]->{n}'] = kinds.get(f'{p}->[{k}]->{n}', 0) + 1
print('short spell contexts', json.dumps(dict(sorted(kinds.items(), key=lambda x: -x[1])[:12])))
ball, P, team = m['ball'], m['players'], m['team']
vis_c = np.isfinite(ball).all(1); vis_d = np.isfinite(dm['ball']).all(1)


def near_at(t, bpos):
    d = np.linalg.norm(P[t] - bpos, axis=1)
    d = np.where(np.isfinite(d), d, np.inf)
    j = int(np.argmin(d))
    dk = [float(np.min(np.where(team == q, d, np.inf))) for q in (0, 1)]
    return int(team[j]), float(d[j]), dk


rows = []
for s, e, k, p, n in spells:
    if p not in 'HA':
        continue
    kk = 0 if k == 'H' else 1
    # best frame in [s-5, s+5] where a player of team kk is nearest the clean ball
    best = None
    for t in range(max(s - 5, 0), min(s + 6, len(lab))):
        if vis_c[t]:
            tm, dmn, dk = near_at(t, ball[t])
            if best is None or dk[kk] < best[0]:
                best = (dk[kk], dk[1 - kk], t - s)
    v1 = ball[s] - ball[s - 4] if s >= 4 else np.full(2, np.nan)
    v2 = ball[s + 4] - ball[s] if s + 4 < len(lab) else np.full(2, np.nan)
    dv = float(np.linalg.norm(v2 - v1) * 25 / 4)
    rows.append({'len': e - s, 'dk': None if best is None else best[0], 'do': None if best is None else best[1],
                 'dv': dv, 'vis_c_win': float(vis_c[max(s - 12, 0):s + 13].mean()),
                 'vis_d_win': float(vis_d[max(s - 12, 0):s + 13].mean())})
for nm, sel in (('short<2s', lambda r: r['len'] < 50), ('long>=2s', lambda r: r['len'] >= 50)):
    R = [r for r in rows if sel(r)]
    dk = np.array([r['dk'] if r['dk'] is not None else np.nan for r in R])
    do = np.array([r['do'] if r['do'] is not None else np.nan for r in R])
    dv = np.array([r['dv'] for r in R])
    print(nm, 'n', len(R), 'team-start: new team within 1.5m', round(float(np.nanmean(dk < 1.5)), 3),
          'within 3m', round(float(np.nanmean(dk < 3)), 3), 'new team nearer than other', round(float(np.nanmean(dk < do)), 3),
          'median dk', round(float(np.nanmedian(dk)), 2), 'median |dv| m/s', round(float(np.nanmedian(dv)), 2),
          'vis clean', round(float(np.mean([r['vis_c_win'] for r in R])), 3),
          'vis corrupted', round(float(np.mean([r['vis_d_win'] for r in R])), 3))
