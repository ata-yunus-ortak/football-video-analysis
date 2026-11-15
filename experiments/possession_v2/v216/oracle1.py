"""What-if analyses (development, with the labels as an oracle; upper bounds, never a method):
 snap       every predicted change that has a true change into the same state within W s is moved to the true moment
 snap_seen  the same, only where the ball is seen around the true moment
 nodead     dead-ball frames made perfect, team decisions as predicted
"""
import errlib as E, numpy as np, json
def changes(w):
    return np.flatnonzero(w[1:] != w[:-1]) + 1
def snap(lab, pred, per, seen=None, W=75, kinds=('HA', 'D')):
    out = pred.copy()
    for a, b in E.play_blocks(per):
        g, p = lab[a:b], pred[a:b].copy()
        gt_t, pr_t = changes(g), changes(p)
        pairs = []
        for u in pr_t:
            c = gt_t[np.abs(gt_t - u) <= W]
            c = c[g[c] == p[u]] if len(c) else c
            for t in c:
                pairs.append((abs(int(t) - int(u)), int(u), int(t)))
        pairs.sort()
        used_u, used_t, new = set(), set(), {}
        for dist, u, t in pairs:
            if u in used_u or t in used_t:
                continue
            if seen is not None and seen[a + max(t - 12, 0):a + t + 13].mean() < 0.8:
                continue
            if (p[u] in 'HA') != ('HA' in kinds) and (p[u] == 'D') != ('D' in kinds):
                continue
            used_u.add(u); used_t.add(t); new[u] = t
        bounds = [0] + [new.get(int(u), int(u)) for u in pr_t] + [len(p)]
        states = [p[0]] + [p[u] for u in pr_t]
        q = p.copy()
        ok = all(bounds[i] < bounds[i + 1] for i in range(len(bounds) - 1))
        if not ok:                                   # keep the order: drop moves that cross a neighbour
            bounds = [0] + [int(u) for u in pr_t] + [len(p)]
            for i, u in enumerate(pr_t):
                t = new.get(int(u), int(u))
                if bounds[i] < t < bounds[i + 2]:
                    bounds[i + 1] = t
        for i, s in enumerate(states):
            q[bounds[i]:bounds[i + 1]] = s
        out[a:b] = q
    return out
def nodead(lab, pred, per):
    out = pred.copy()
    for a, b in E.play_blocks(per):
        g, p = lab[a:b], pred[a:b].copy()
        team = np.where(p == 'D', '', p)
        idx = np.arange(len(p)); known = np.where(team != '', idx, -1)
        last = np.maximum.accumulate(known)
        nxt = np.where(team != '', idx, len(p) * 2); nxt = np.minimum.accumulate(nxt[::-1])[::-1]
        fill = np.where(last >= 0, p[np.clip(last, 0, None)], np.where(nxt < len(p), p[np.clip(nxt, 0, len(p) - 1)], 'H'))
        q = np.where(g == 'D', 'D', fill)
        out[a:b] = q
    return out
res = {}
for f in E.copies():
    d = E.load(f)
    lab, pred, per = d['lab'], d['pred'], d['per']
    r = {'base': E.f1_of(lab, pred, per)}
    r['snap_3s'] = E.f1_of(lab, snap(lab, pred, per), per)
    r['snap_1s'] = E.f1_of(lab, snap(lab, pred, per, W=25), per)
    r['snap_3s_seen'] = E.f1_of(lab, snap(lab, pred, per, seen=d['ball_seen']), per)
    r['snap_3s_turnovers'] = E.f1_of(lab, snap(lab, pred, per, kinds=('HA',)), per)
    r['snap_3s_dead'] = E.f1_of(lab, snap(lab, pred, per, kinds=('D',)), per)
    r['nodead'] = E.f1_of(lab, nodead(lab, pred, per), per)
    res[d['key']] = r
json.dump(res, open('oracle1.json', 'w'), indent=1)
for nm, sel in (('all 42', lambda k: True), ('DFL', lambda k: k.startswith('J03')), ('Metrica', lambda k: k.startswith('MET'))):
    ks = [k for k in res if sel(k)]
    print(nm, ' '.join(f"{c}={np.mean([res[k][c] for k in ks]):.4f}" for c in res[ks[0]]))
