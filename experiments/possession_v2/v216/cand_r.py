"""Candidate R (development): reception rule. After decoding, a change of team o -> n at frame u is re-timed with the tracking:
 later  : if at u the nearest player of n is farther than RFAR from the seen ball (the ball has not arrived), the change moves
          to the first later frame (within W, before the next change) where a player of n is within R of the ball;
 earlier: if n has been the only team within R of the ball without interruption up to u, the change moves back to the start of
          that contact (at most W).
Grid on the 42 development copies; difference of spellF1 to v2.15."""
import errlib as E, numpy as np, json, os
def retime(pred, per, d0, d1, R, RFAR, W, M=0.5, early=True, late=True):
    out = pred.copy()
    dn = (np.where(np.isnan(d0), 1e3, d0), np.where(np.isnan(d1), 1e3, d1))
    seen = ~np.isnan(d0) | ~np.isnan(d1)
    moved = 0
    for a, b in E.play_blocks(per):
        p = out[a:b]
        ch = np.flatnonzero(p[1:] != p[:-1]) + 1
        bounds = np.r_[0, ch, len(p)]
        for i in range(1, len(bounds) - 1):
            u = int(bounds[i]); prev, nxt = p[u - 1], p[u]
            if prev not in 'HA' or nxt not in 'HA':
                continue
            n = 0 if nxt == 'H' else 1; o = 1 - n
            g = a + u
            lo, hi = int(bounds[i - 1]) + 5, int(bounds[i + 1]) - 5         # stay inside the two possessions
            new_u = u
            if late and seen[g] and dn[n][g] > RFAR:
                v = g + 1; end = min(a + hi, g + W)
                while v < end and not (seen[v] and dn[n][v] < R):
                    v += 1
                if v < end:
                    new_u = v - a
            elif early and seen[g - 1] and dn[n][g - 1] < R and dn[o][g - 1] > dn[n][g - 1] + M:
                v = g - 1; start = max(a + lo, g - W)
                while v > start and seen[v - 1] and dn[n][v - 1] < R and dn[o][v - 1] > dn[n][v - 1] + M:
                    v -= 1
                new_u = v - a
            if new_u != u and lo < new_u < hi:
                if new_u > u:
                    p[u:new_u] = prev
                else:
                    p[new_u:u] = nxt
                moved += 1
        out[a:b] = p
    return out, moved
if __name__ == '__main__':
    GRID = [dict(R=R, RFAR=F, W=W, early=e, late=l) for R in (1.0, 1.5) for F in (2.0, 3.0) for W in (38, 75) for e, l in ((True, True), (False, True), (True, False))]
    res = {}
    for f in E.copies():
        d = E.load(f); z = np.load('track/' + d['key'] + '.npz')
        base = E.f1_of(d['lab'], d['pred'], d['per'])
        r = {}
        for g in GRID:
            q, mv = retime(d['pred'], d['per'], z['d0'].astype(float), z['d1'].astype(float), **g)
            r[json.dumps(g)] = (E.f1_of(d['lab'], q, d['per']) - base, mv)
        res[d['key']] = r
    json.dump(res, open('cand_r.json', 'w'))
    for k in list(res.values())[0]:
        v = {x: res[x][k][0] for x in res}
        dfl = [v[x] for x in v if x.startswith('J03')]; met = [v[x] for x in v if x.startswith('MET')]
        g = json.loads(k)
        print(f"R{g['R']} far{g['RFAR']} W{g['W']} early{int(g['early'])} late{int(g['late'])}: all {np.mean(list(v.values())):+.4f} DFL {np.mean(dfl):+.4f} MET {np.mean(met):+.4f} worst {min(v.values()):+.4f} better {sum(x > 0 for x in v.values())}/42 moved/copy {np.mean([res[x][k][1] for x in res]):.0f}")
