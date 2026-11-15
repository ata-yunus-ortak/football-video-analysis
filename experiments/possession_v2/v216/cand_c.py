"""Candidate C (development): contact evidence at decoding time. Where the ball is seen within R metres of a player of one
team and no player of the other team is nearly as close, lam is added to that team's log emission before the v2 decoder.
Grid on the 42 development copies; difference of spellF1 to v2.15."""
import errlib as E, numpy as np, json, os, sys
from possession.decode import emissions, decode_blocks
GRID = [(R, M, lam) for R in (1.0, 1.5) for M in (0.5, 1.0) for lam in (0.1, 0.2, 0.4)]
res = {}
for f in E.copies():
    d = E.load(f)
    tf = 'track/' + d['key'] + '.npz'
    if not os.path.exists(tf):
        continue
    z = np.load(tf); d0, d1 = z['d0'].astype(float), z['d1'].astype(float)
    em = emissions(d['pd2'], d['ph2'])
    base = E.f1_of(d['lab'], d['pred'], d['per'])
    r = {'base': base}
    big = np.where(np.isnan(d0), 1e3, d0), np.where(np.isnan(d1), 1e3, d1)
    for R, M, lam in GRID:
        c0 = (big[0] < R) & (big[1] > big[0] + M); c1 = (big[1] < R) & (big[0] > big[1] + M)
        e2 = em.copy(); e2[:, 0] += lam * c0; e2[:, 1] += lam * c1
        r[f'R{R}_M{M}_l{lam}'] = E.f1_of(d['lab'], decode_blocks(e2, d['per'], E.DEC), d['per']) - base
    res[d['key']] = r
    print(d['key'], ' '.join(f'{v:+.4f}' for k, v in r.items() if k != 'base'), flush=True)
json.dump(res, open('cand_c.json', 'w'), indent=1)
print(len(res), 'copies')
for k in list(res.values())[0]:
    if k == 'base':
        continue
    v = {x: res[x][k] for x in res}
    dfl = [v[x] for x in v if x.startswith('J03')]; met = [v[x] for x in v if x.startswith('MET')]
    print(f'{k:16s} all {np.mean(list(v.values())):+.4f} DFL {np.mean(dfl):+.4f} Metrica {np.mean(met):+.4f} worst {min(v.values()):+.4f} better {sum(x > 0 for x in v.values())}/{len(v)}')
