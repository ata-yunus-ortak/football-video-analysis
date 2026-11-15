"""Development: inside the predicted possessions of v2.15, stretches where the pooled probability of the OTHER team rises above
0.15 without the decoder switching ("bumps"). How often is a bump a true possession of the other team, by peak height?"""
import errlib as E, numpy as np
rows = []
for f in E.copies():
    d = E.load(f)
    lab, pred, per, seen = d['lab'], d['pred'], d['per'], d['ball_seen']
    ph = d['ph2']; v2h = d['p_home']; tc = d['tcn'].astype(float); tch = tc[:, 0] / np.maximum(tc[:, 0] + tc[:, 1], 1e-9)
    gs = E.spells(lab, per)
    gstart = np.array([g[0] for g in gs]); 
    for a, b, k in E.spells(pred, per):
        q = (1 - ph[a:b]) if k == 0 else ph[a:b]
        qv = (1 - v2h[a:b]) if k == 0 else v2h[a:b]; qt = (1 - tch[a:b]) if k == 0 else tch[a:b]
        on = q > 0.15
        ed = np.diff(np.r_[0, on.astype(np.int8), 0])
        for s, e in zip(np.flatnonzero(ed == 1), np.flatnonzero(ed == -1)):
            if e - s < 5:
                continue
            A, B = a + s, a + e
            # true possessions of the other team that overlap the bump
            best = 0.0; glen = 0
            j = np.searchsorted(gstart, A) - 1
            for g in gs[max(j, 0):j + 6]:
                if g[2] == 1 - k and g[1] > A and g[0] < B:
                    iou = (min(B, g[1]) - max(A, g[0])) / (max(B, g[1]) - min(A, g[0]))
                    if iou > best:
                        best, glen = iou, g[1] - g[0]
            other = ((lab[A:B] == ('A' if k == 0 else 'H')).mean())
            rows.append((d['match'].startswith('J03'), d['match'], e - s, q[s:e].max(), q[s:e].mean(), qv[s:e].max(), qt[s:e].max(), seen[A:B].mean(), best, other, glen, min(s, b - a - e)))
r = np.array(rows, dtype=[('dfl', '?'), ('match', 'U8'), ('dur', 'i4'), ('peak', 'f4'), ('mean', 'f4'), ('peak_v2', 'f4'), ('peak_tcn', 'f4'), ('seen', 'f4'), ('iou', 'f4'), ('other', 'f4'), ('glen', 'i4'), ('edge', 'i4')])
np.save('bump1.npy', r)
print('bumps', len(r), 'per copy', len(r) / 42)
print('by peak of the pooled probability of the other team: n | true possession under it (other-team share >= 0.5) | IoU >= 0.3 with a true possession | median bump length s | median true length s')
for lo, hi in ((0.15, 0.2), (0.2, 0.25), (0.25, 0.3), (0.3, 0.35), (0.35, 0.4), (0.4, 0.45), (0.45, 0.5), (0.5, 1.01)):
    m = (r['peak'] >= lo) & (r['peak'] < hi)
    for nm, sel in (('DFL', r['dfl']), ('MET', ~r['dfl'])):
        mm = m & sel
        if mm.sum():
            print(f'  {lo:.2f}-{hi:.2f} {nm} n={mm.sum():5d} | {np.mean(r["other"][mm] >= 0.5):.2f} | {np.mean(r["iou"][mm] >= 0.3):.2f} | {np.median(r["dur"][mm]) / 25:.2f} | {np.median(r["glen"][mm][r["glen"][mm] > 0]) / 25 if (r["glen"][mm] > 0).any() else 0:.2f}')
