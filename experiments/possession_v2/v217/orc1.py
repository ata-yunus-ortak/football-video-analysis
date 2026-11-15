"""Exploration 3 (development copies): ceilings. What would spellF1 gain if set-piece tags were used perfectly?
 O_miss : on tagged restarts whose dead-ball stretch has no D of ours, write the true stretch as D.
 O_time : on tagged restarts whose stretch we found, move the end of our D to the true restart.
 both   : the two together.   'all' = every restart tagged; 'pub' = tagged at the published per-type counts (DATA.md)."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/work/v216')
import errlib as E
from possession.evaluate import score
R = json.load(open('restarts.json'))
PUB = {'throw-in': 26, 'corner kick': 12, 'goal kick': 10, 'free kick': 5, 'kick off': 4}
MIN = 158857 / 25.0 / 60.0

def apply(pred, rs, miss=True, time=True):
    out = pred.copy(); n = len(out); k_m = k_t = 0
    for s, t in rs:
        isd = out[s:t] == 'D'
        if not isd.any():
            if miss:
                out[s:t] = 'D'; k_m += 1
            continue
        if not time:
            continue
        # our D run that covers the last D frame on the stretch
        j = s + int(np.flatnonzero(isd)[-1])
        e = j + 1
        while e < n and out[e] == 'D':
            e += 1
        if e > t:                       # our D ends late: frames [t, e) get the label that follows our D
            nxt = out[e] if e < n and out[e] in ('H', 'A') else None
            if nxt is not None:
                out[t:e] = nxt; k_t += 1
        elif e < t:                     # our D ends early: extend it to the restart
            out[e:t] = 'D'; k_t += 1
    return out, k_m, k_t

res = {}
for f in E.copies():
    d = E.load(f)
    pred, lab, per = d['pred'], d['lab'], d['per']
    rr = R[d['match']]['restarts']; minutes = R[d['match']]['minutes']
    cnt = {}
    for s, t, typ, p, n, first in rr:
        cnt[typ] = cnt.get(typ, 0) + 1
    rng = np.random.default_rng(900000 + len(res))
    tagged = [(s, t) for s, t, typ, p, n, first in rr if rng.random() < min(1.0, PUB[typ] / MIN * minutes / cnt[typ])]
    allr = [(s, t) for s, t, typ, p, n, first in rr]
    base = E.f1_of(lab, pred, per)
    row = {'base': base, 'n_all': len(allr), 'n_pub': len(tagged)}
    for nm, rs in (('all', allr), ('pub', tagged)):
        for key, kw in (('miss', dict(miss=True, time=False)), ('time', dict(miss=False, time=True)), ('both', dict(miss=True, time=True))):
            o, km, kt = apply(pred, rs, **kw)
            row[f'{nm}_{key}'] = E.f1_of(lab, o, per) - base
            row[f'{nm}_{key}_n'] = (km, kt)
    res[d['key']] = row
json.dump(res, open('orc1.json', 'w'), indent=0)
ks = list(res)
def mean(k, sel=lambda x: True):
    v = [res[c][k] for c in ks if sel(c)]
    return float(np.mean(v))
print('copies', len(ks), 'base', round(mean('base'), 4), 'restarts/copy', round(mean('n_all'), 1), 'tagged at published counts', round(mean('n_pub'), 1))
for k in ('all_miss', 'all_time', 'all_both', 'pub_miss', 'pub_time', 'pub_both'):
    v = np.array([res[c][k] for c in ks]); n = np.array([res[c][k + '_n'] for c in ks])
    print(f'  {k:9s} mean {v.mean():+.4f}  DFL {mean(k, lambda c: c.startswith("J03")):+.4f}  Metrica {mean(k, lambda c: c.startswith("MET")):+.4f}  min {v.min():+.4f} max {v.max():+.4f}  better {(v > 1e-9).sum()} worse {(v < -1e-9).sum()}  acted miss/time per copy {n[:, 0].mean():.1f}/{n[:, 1].mean():.1f}')
