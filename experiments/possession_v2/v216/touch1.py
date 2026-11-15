"""Development: for true direct turnovers (both possessions >= 2 s, ball seen around the moment), where the tracking shows the
new team's first contact, relative to the true moment and to the predicted moment."""
import errlib as E, numpy as np, glob, os
R = 1.5
def q(x):
    x = np.asarray(x) / 25.0
    return f'median {np.median(x):+.2f} P10 {np.percentile(x, 10):+.2f} P25 {np.percentile(x, 25):+.2f} P75 {np.percentile(x, 75):+.2f} P90 {np.percentile(x, 90):+.2f} | within 0.25 s {(np.abs(x) <= 0.25).mean():.2f} 0.5 s {(np.abs(x) <= 0.5).mean():.2f}'
for f in sorted(glob.glob('track/*.npz')):
    key = os.path.basename(f)[:-4]
    d = E.load(E.L.PROBS + key + '.npz'); z = np.load(f)
    lab, pred, per, seen = d['lab'], d['pred'], d['per'], d['ball_seen']
    dn = np.stack([z['d0'], z['d1']], 1)                      # nearest distance per team (NaN when the ball is unseen)
    gs = E.spells(lab, per)
    rows = []
    for (a0, b0, k0), (a1, b1, k1) in zip(gs[:-1], gs[1:]):
        if b0 != a1 or per[a0] != per[a1] or b0 - a0 < 50 or b1 - a1 < 50:
            continue
        t = a1
        if seen[t - 12:t + 13].mean() < 0.8:
            continue
        lo, hi = t - 75, t + 76
        w = pred[lo:hi]
        c = np.flatnonzero((w[1:] != w[:-1]) & (w[1:] == lab[t])) + 1 + lo
        if not len(c):
            continue
        u = c[np.argmin(np.abs(c - t))]
        new, old = dn[:, k1], dn[:, k0]
        # contact of the new team near the true moment: first frame in [t-37, t+37] where new < R and new < old
        win = np.arange(t - 37, t + 38)
        ok = (new[win] < R) & ~(old[win] < new[win])
        tc = win[ok][0] - t if ok.any() else None
        # the same search around the PREDICTED moment (what a rule could do): window [u-37, u+37]
        winu = np.arange(max(u - 37, 1), min(u + 38, len(lab) - 1))
        oku = (new[winu] < R) & ~(old[winu] < new[winu])
        # candidates: starts of contact episodes of the new team (previous frame not in contact)
        st = winu[oku & ~np.r_[False, oku[:-1]]]
        tu = st[np.argmin(np.abs(st - u))] - t if len(st) else None
        rows.append((u - t, tc, tu, new[t] if np.isfinite(new[t]) else 99, old[t] if np.isfinite(old[t]) else 99))
    e = np.array([r[0] for r in rows])
    tc = [r[1] for r in rows if r[1] is not None]; tu = np.array([(r[2] if r[2] is not None else r[0]) for r in rows])
    print(f'\n{key}: stable turnovers with the ball seen and a predicted change within 3 s: {len(rows)}')
    print(f'  predicted - true:                         {q(e)}')
    print(f'  first new-team contact - true ({len(tc)}/{len(rows)}): {q(tc)}')
    print(f'  nearest contact start to prediction - true (fallback: prediction): {q(tu)}')
    print(f'  distance of the new team at the true moment: median {np.median([r[3] for r in rows]):.2f} m; under 1.5 m in {np.mean([r[3] < 1.5 for r in rows]):.2f}; old team under 1.5 m in {np.mean([r[4] < 1.5 for r in rows]):.2f}')
