"""Development: print what the tracking and the pooled probability look like around true turnovers that the decision times
badly although the ball is seen (both possessions >= 2 s). One line per 0.2 s: distance of the old team's and of the new
team's nearest player to the ball (m), ball speed (m/s), pooled P(new team | alive)."""
import errlib as E, numpy as np, sys
key = sys.argv[1]; want = sys.argv[2]; nmax = int(sys.argv[3])
d = E.load(E.L.PROBS + key + '.npz'); z = np.load('track/' + key + '.npz')
lab, pred, per, seen = d['lab'], d['pred'], d['per'], d['ball_seen']
dn = np.stack([z['d0'], z['d1']], 1); ball = z['ball']
sp = np.full(len(ball), np.nan); sp[2:-2] = np.hypot(*(ball[4:] - ball[:-4]).T) * 25 / 4
gs = E.spells(lab, per); shown = 0
for (a0, b0, k0), (a1, b1, k1) in zip(gs[:-1], gs[1:]):
    if b0 != a1 or per[a0] != per[a1] or b0 - a0 < 50 or b1 - a1 < 50:
        continue
    t = a1
    if seen[t - 12:t + 13].mean() < 0.8:
        continue
    w = pred[t - 75:t + 76]
    c = np.flatnonzero((w[1:] != w[:-1]) & (w[1:] == lab[t])) + 1 + t - 75
    if not len(c):
        continue
    u = c[np.argmin(np.abs(c - t))]; err = u - t
    if (want == 'early' and err > -13) or (want == 'late' and err < 13):
        continue
    pn = d['ph2'] if k1 == 0 else 1 - d['ph2']
    print(f'\ntrue turnover at frame {t} (old possession {(b0 - a0) / 25:.1f} s, new {(b1 - a1) / 25:.1f} s); predicted {err / 25:+.2f} s')
    for o in range(-40, 41, 5):
        i = t + o
        print(f'  {o / 25:+.1f}s  old {dn[i, k0]:5.1f}  new {dn[i, k1]:5.1f}  speed {sp[i]:5.1f}  P(new) {pn[i]:.2f}  truth {lab[i]} pred {pred[i]}' + ('  <- true' if o == 0 else '') + ('  <- predicted' if abs(i - u) < 3 else ''))
    shown += 1
    if shown >= nmax:
        break
