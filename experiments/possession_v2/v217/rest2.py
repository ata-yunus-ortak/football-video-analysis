"""Exploration 2 (development copies): for every true dead-ball stretch that ends in a restart, does the v2.15 decision
have any D on it, and what does it write instead?"""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/work/v216')
import errlib as E
R = json.load(open('restarts.json'))
rows = []
for f in E.copies():
    d = E.load(f)
    pred, lab, per = d['pred'], d['lab'], d['per']
    isd = pred == 'D'
    for s, t, typ, p, n, first in R[d['match']]['restarts']:
        cov = isd[s:t].mean()
        near = isd[max(0, s - 50):t + 50].any()
        w = pred[max(0, s - 1)], pred[min(len(pred) - 1, t)]
        rows.append((d['match'], d['key'], int(d['sim2']), s, t, typ, p, n, cov, near, d['pd2'][s:t].max(), d['pd2'][s:t].mean(), d['ball_seen'][s:t].mean(), d['path']))
a = np.array(rows, dtype=[('match', 'U8'), ('key', 'U40'), ('sim2', 'i1'), ('s', 'i4'), ('t', 'i4'), ('typ', 'U12'), ('p', 'U1'), ('n', 'U1'), ('cov', 'f4'),
                          ('near', '?'), ('pmax', 'f4'), ('pmean', 'f4'), ('seen', 'f4'), ('path', 'U4')])
np.save('rest2.npy', a)
dur = (a['t'] - a['s']) / 25.0
print('true dead-ball stretches ending in a restart:', len(a), 'in', len(set(a['key'])), 'copies')
print(f'  no D frame of ours on the stretch: {(a["cov"] == 0).mean():.3f}   no D within 2 s around it either: {(~a["near"]).mean():.3f}   mean coverage {a["cov"].mean():.3f}')
print('by type:   n/copy | missed entirely | missed (also nothing within 2 s) | mean coverage | median length s | max P(dead) on missed')
for typ in ('throw-in', 'corner kick', 'goal kick', 'free kick', 'kick off'):
    m = a['typ'] == typ
    mm = m & (a['cov'] == 0)
    print(f'  {typ:12s} {m.sum() / 42:5.1f} | {(a["cov"][m] == 0).mean():.3f} | {(~a["near"][m]).mean():.3f} | {a["cov"][m].mean():.3f} | {np.median(dur[m]):5.1f} | {np.median(a["pmax"][mm]) if mm.any() else float("nan"):.3f}')
print('by length of the stretch: share | missed entirely | mean coverage')
for lo, hi in ((0, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 1e9)):
    m = (dur >= lo) & (dur < hi)
    print(f'  {lo:>3}-{hi:<5} s {m.mean():.3f} | {(a["cov"][m] == 0).mean():.3f} | {a["cov"][m].mean():.3f}')
print('by match: missed entirely', {k: round(float((a['cov'][a['match'] == k] == 0).mean()), 3) for k in sorted(set(a['match']))})
print('by simulator: ', {int(k): round(float((a['cov'][a['sim2'] == k] == 0).mean()), 3) for k in (0, 1)}, ' by path', {k: round(float((a['cov'][a['path'] == k] == 0).mean()), 3) for k in sorted(set(a['path']))})
mm = a['cov'] == 0
print('missed stretches: same team before and after', round(float((a['p'][mm] == a['n'][mm]).mean()), 3), ' ball seen share on them', round(float(a['seen'][mm].mean()), 3),
      ' vs found', round(float(a['seen'][~mm].mean()), 3), ' median length', np.median(dur[mm]), 'vs', np.median(dur[~mm]))
print('max P(dead) on missed stretches, quantiles 10/25/50/75/90:', np.round(np.quantile(a['pmax'][mm], [.1, .25, .5, .75, .9]), 3))
