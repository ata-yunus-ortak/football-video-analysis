"""Error mining, step 5: turnovers by the length of the possessions on both sides (stable = both at least 2 s)."""
import errlib as E, numpy as np
rows = []
for f in E.copies():
    d = E.load(f)
    lab, pred, per, seen = d['lab'], d['pred'], d['per'], d['ball_seen']
    gs = E.spells(lab, per)
    for (a0, b0, k0), (a1, b1, k1) in zip(gs[:-1], gs[1:]):
        if b0 != a1 or per[a0] != per[a1]:
            continue                                              # only direct turnovers (no stoppage between)
        t = a1
        lo, hi = max(t - 75, 0), min(t + 76, len(lab))
        w = pred[lo:hi]
        c = np.flatnonzero((w[1:] != w[:-1]) & (w[1:] == lab[t])) + 1 + lo
        err = (c[np.argmin(np.abs(c - t))] - t) if len(c) else 999
        rows.append((d['match'].startswith('J03'), b0 - a0, b1 - a1, err, seen[max(t - 12, 0):t + 13].mean()))
r = np.array(rows, dtype=[('dfl', '?'), ('d0', 'i4'), ('d1', 'i4'), ('err', 'i4'), ('seen', 'f4')])
np.save('mine5.npy', r)
for nm, sel in (('DFL', r['dfl']), ('Metrica', ~r['dfl'])):
    print(f'\n{nm}: direct turnovers {sel.sum()}')
    for kn, ks in (('both sides >= 2 s', (r['d0'] >= 50) & (r['d1'] >= 50)), ('new possession < 2 s', r['d1'] < 50), ('old possession < 2 s, new >= 2 s', (r['d0'] < 50) & (r['d1'] >= 50))):
        for sn, ss in (('ball seen', r['seen'] >= 0.8), ('ball unseen', r['seen'] < 0.2)):
            m = sel & ks & ss
            e = r['err'][m]; found = e != 999; ef = e[found] / 25.0
            print(f'  {kn:32s} {sn:11s} n={m.sum():5d} ({m.sum() / sel.sum():.2f}) found 3 s {found.mean():.2f} | within 0.25 s {(np.abs(e) <= 6).mean():.2f} 0.5 s {(np.abs(e) <= 12).mean():.2f} 1 s {(np.abs(e) <= 25).mean():.2f}'
                  f' | found: median {np.median(ef):+.2f} P10 {np.percentile(ef, 10):+.2f} P25 {np.percentile(ef, 25):+.2f} P75 {np.percentile(ef, 75):+.2f} P90 {np.percentile(ef, 90):+.2f}')
