"""Development exploration (NOT a candidate, NOT a validation): how much could a learned combination of the two model
families give beyond the fixed pool? Leave-one-match-out over the five development matches: a gradient-boosted classifier
on the probabilities of both families and their temporal context, trained on the copies of four matches, applied to the
copies of the fifth, decoded by the unchanged decoder. Compared with v2.15 on the same copies."""
import errlib as E, numpy as np, json, time, sys
from sklearn.ensemble import HistGradientBoostingClassifier
from possession.decode import emissions, decode_blocks
OFF = (-50, -25, -12, -5, 5, 12, 25, 50)
def feats(d):
    v = np.stack([(1 - d['p_dead']) * d['p_home'], (1 - d['p_dead']) * (1 - d['p_home']), d['p_dead']], 1)
    t = d['tcn'].astype(float)
    per = d['per']; n = len(per)
    cols = [v, t]
    idx = np.arange(n)
    for o in OFF:
        j = np.clip(idx + o, 0, n - 1)
        ok = (per[j] == per)[:, None]
        cols.append(np.where(ok, v[j], v)); cols.append(np.where(ok, t[j], t))
    seen = d['ball_seen'].astype(float)
    cs = np.cumsum(np.r_[0, seen])
    for w in (12, 50):
        cols.append(((cs[np.clip(idx + w + 1, 0, n)] - cs[np.clip(idx - w, 0, n)]) / (2 * w + 1))[:, None])
    cols.append(seen[:, None])
    return np.concatenate(cols, 1)
def swap(X):
    X = X.copy()
    k = 6 * (1 + len(OFF))
    for c in range(0, k, 3):
        X[:, [c, c + 1]] = X[:, [c + 1, c]]
    return X
D = [E.load(f) for f in E.copies()]
for d in D:
    d['X'] = feats(d).astype(np.float32)
    d['y'] = np.select([d['lab'] == 'H', d['lab'] == 'A'], [0, 1], 2)
    d['play'] = np.zeros(len(d['per']), bool)
    for a, b in E.play_blocks(d['per']):
        d['play'][a:b] = True
matches = sorted(set(d['match'] for d in D))
res = {}
mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
for m in matches:
    t0 = time.time()
    tr = [d for d in D if d['match'] != m and (mode == 'all' or d['match'].startswith('J03') or m.startswith('J03') and False)]
    if mode == 'dfl':
        tr = [d for d in D if d['match'] != m and d['match'].startswith('J03')]
    if not tr:
        continue
    Xs, ys = [], []
    for d in tr:
        sel = np.flatnonzero(d['play'])[::7]
        Xs.append(d['X'][sel]); ys.append(d['y'][sel])
    X = np.concatenate(Xs); y = np.concatenate(ys)
    X = np.concatenate([X, swap(X)]); y = np.concatenate([y, np.where(y == 2, 2, 1 - y)])
    clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0, random_state=0)
    clf.fit(X, y)
    for d in D:
        if d['match'] != m:
            continue
        p = 0.5 * (clf.predict_proba(d['X']) + clf.predict_proba(swap(d['X']))[:, [1, 0, 2]])
        pd_ = np.round(p[:, 2], 6); ph = np.round(p[:, 0] / np.maximum(p[:, 0] + p[:, 1], 1e-12), 6)
        lab2 = decode_blocks(emissions(pd_, ph), d['per'], E.DEC)
        res[d['key']] = (E.f1_of(d['lab'], lab2, d['per']), E.f1_of(d['lab'], d['pred'], d['per']))
    ks = [k for k in res if k.startswith(m)]
    print(m, f'train rows {len(y)}', 'stacker', round(np.mean([res[k][0] for k in ks]), 4), 'v2.15', round(np.mean([res[k][1] for k in ks]), 4),
          'diff', f'{np.mean([res[k][0] - res[k][1] for k in ks]):+.4f}', 'worst', f'{min(res[k][0] - res[k][1] for k in ks):+.4f}', round(time.time() - t0), 's', flush=True)
json.dump(res, open(f'stack1_{mode}.json', 'w'), indent=1)
dv = [res[k][0] - res[k][1] for k in res]
print('all', f'{np.mean(dv):+.4f}', 'DFL', f"{np.mean([res[k][0] - res[k][1] for k in res if k.startswith('J03')]):+.4f}", 'MET', f"{np.mean([res[k][0] - res[k][1] for k in res if k.startswith('MET')]):+.4f}", 'worst', f'{min(dv):+.4f}', 'better', sum(x > 0 for x in dv), '/', len(dv))
