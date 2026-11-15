"""Error mining, step 4: transitions. For every GT change of state, the nearest predicted change into the same state within
3 s: found or not, timing error, split by kind and by whether the ball is seen around the true moment."""
import errlib as E, numpy as np
rows = []
for f in E.copies():
    d = E.load(f)
    lab, pred, per, seen = d['lab'], d['pred'], d['per'], d['ball_seen']
    for a, b in E.play_blocks(per):
        g, p = lab[a:b], pred[a:b]
        gt_t = np.flatnonzero(g[1:] != g[:-1]) + 1; pr_t = np.flatnonzero(p[1:] != p[:-1]) + 1
        for t in gt_t:
            to, fr = g[t], g[t - 1]
            c = pr_t[(np.abs(pr_t - t) <= 75)]
            c = c[p[c] == to] if len(c) else c
            err = (c[np.argmin(np.abs(c - t))] - t) if len(c) else 999
            kind = 0 if (fr in 'HA' and to in 'HA') else 1 if to == 'D' else 2          # turnover / ball goes dead / restart
            s = seen[a + max(t - 12, 0):a + t + 13].mean()
            rows.append((d['match'].startswith('J03'), kind, err, s))
r = np.array(rows, dtype=[('dfl', '?'), ('kind', 'i1'), ('err', 'i4'), ('seen', 'f4')])
np.save('mine4.npy', r)
for nm, sel in (('DFL', r['dfl']), ('Metrica', ~r['dfl'])):
    print(f'\n{nm}: GT transitions {sel.sum()}')
    for k, kn in enumerate(('turnover', 'ball goes dead', 'restart')):
        for sn, ss in (('ball seen around it', r['seen'] >= 0.8), ('ball mostly unseen', r['seen'] < 0.2), ('partly seen', (r['seen'] >= 0.2) & (r['seen'] < 0.8))):
            m = sel & (r['kind'] == k) & ss
            if m.sum() < 30:
                continue
            e = r['err'][m]; found = e != 999; ef = e[found] / 25.0
            print(f'  {kn:15s} {sn:20s} n={m.sum():5d} ({m.sum() / sel.sum():.2f})  found within 3 s {found.mean():.2f}  within 0.5 s {(np.abs(e) <= 12).mean():.2f}  within 1 s {(np.abs(e) <= 25).mean():.2f}'
                  f'  | of the found: median {np.median(ef):+.2f} s, mean {ef.mean():+.2f}, P10 {np.percentile(ef, 10):+.2f}, P90 {np.percentile(ef, 90):+.2f}')
