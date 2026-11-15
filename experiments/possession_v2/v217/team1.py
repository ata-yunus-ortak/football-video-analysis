"""Exploration 4 (development copies): is the team right after a restart wrong often enough for the taker's team of a
set-piece tag (corner, goal kick, free kick, kick-off; throw-ins carry N/A) to matter?"""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/work/v217')
import taglib as T
E = T.E
R = T.R
tot = wrong = 0; gain = []
for f in E.copies():
    d = E.load(f)
    pred, lab, per = d['pred'], d['lab'], d['per']
    rr = R[d['match']]['restarts']; minutes = R[d['match']]['minutes']
    cnt = {}
    for s, t, typ, p, n, first in rr:
        cnt[typ] = cnt.get(typ, 0) + 1
    rng = np.random.default_rng(930000 + len(gain))
    out = pred.copy(); N = len(pred)
    for s, t, typ, p, n, first in rr:
        if typ == 'throw-in' or rng.random() >= min(1.0, T.PUB[typ] / T.MIN * minutes / cnt[typ]):
            continue
        # first possession of ours that starts within 3 s around the true restart, after a D of ours
        j = None
        for u in range(max(1, t - 75), min(N - 1, t + 75)):
            if out[u] in ('H', 'A') and out[u - 1] == 'D':
                j = u; break
        if j is None:
            continue
        tot += 1
        if out[j] != n:
            wrong += 1
            e = j
            while e < N and out[e] == out[j]:
                e += 1
            out[j:e] = n
    gain.append(E.f1_of(lab, out, per) - E.f1_of(lab, pred, per))
print('tagged restarts with a team and a possession of ours starting after a D within 3 s:', tot, ' wrong team:', wrong, f'({wrong / tot:.3f})',
      ' per copy', round(wrong / 42, 2))
g = np.array(gain)
json.dump({'tagged_restarts_with_team_and_found_possession': tot, 'wrong_team': wrong, 'gain': [float(x) for x in g]}, open('team1.json', 'w'))
print(f'oracle (first possession relabelled with the true team): mean {g.mean():+.4f} min {g.min():+.4f} max {g.max():+.4f} better {(g > 1e-9).sum()} worse {(g < -1e-9).sum()}')
