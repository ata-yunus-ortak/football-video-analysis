"""Rebuild of the team's four-match v2.1 validation models (cache/models_v2.pkl, stack_v2.pkl; not in the repository)
with their scripts' logic: train1.py (FTAG=_f2) and exp_stack.py _f2. External DFL matches only. Development use.
  v2val.py feats NAME      features of the three training copies of one match
  v2val.py fit             stage 1 + out-of-fold stacking -> v2cache/models_v2.pkl, stack_v2.pkl"""
import sys, os, time, pickle, numpy as np
import env, harness
harness.CACHE = '/Users/umut/BARCELONA/work/v216u/v2cache/'
from harness import load, feats, DFL_TRAIN
TAG, SEEDS, C = '_f2', [1, 2, 3], harness.CACHE
if sys.argv[1] == 'feats':
    for s in SEEDS:
        for w in (False, True):
            feats(sys.argv[2], s, w, TAG)
    print('done', sys.argv[2]); sys.exit()
from sklearn.ensemble import HistGradientBoostingClassifier
from possession.stack import stack_features
HP = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0, early_stopping=False)
HP2 = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=400, l2_regularization=1.0, early_stopping=False)

def rows(names_list, seeds, step=6):          # train1.rows
    plan, total = [], 0
    for name in names_list:
        m, lab = load(name)
        for seed in seeds:
            idx = np.arange(seed % step, len(lab), step); idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            plan.append((name, seed, idx, lab[idx])); total += 2 * len(idx)
    k = feats(plan[0][0], plan[0][1], False, TAG).shape[1]
    X = np.empty((total, k), np.float64); yd = np.empty(total, np.int8); yh = np.empty(total, np.int8); r = 0
    for name, seed, idx, lab in plan:
        for swap in (False, True):
            F = feats(name, seed, swap, TAG); X[r:r + len(idx)] = F[idx]; del F
            yd[r:r + len(idx)] = lab == 'D'
            h = np.where(lab == 'H', 1, np.where(lab == 'A', 0, -1))
            if swap: h = np.where(h >= 0, 1 - h, -1)
            yh[r:r + len(idx)] = h; r += len(idx)
    return X, yd, yh

def fit1(names):
    X, yd, yh = rows(names, SEEDS)
    md = HistGradientBoostingClassifier(random_state=0, **HP).fit(X, yd)
    a = yh >= 0; Xa = X[a]; ya = yh[a]; del X
    return md, HistGradientBoostingClassifier(random_state=0, **HP).fit(Xa, ya)

def probs(models, name, seed):
    md, mh = models
    X = feats(name, seed, False, TAG); Xs = feats(name, seed, True, TAG)
    ok = np.isfinite(X).any(1); pd_ = np.full(len(X), 0.5); ph = np.full(len(X), 0.5)
    pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    return pd_, ph

t = time.time()
pickle.dump(fit1(DFL_TRAIN), open(C + 'models_v2.pkl', 'wb')); print('stage 1', round(time.time() - t), flush=True)
oof = {}
for k in DFL_TRAIN:
    models = fit1([n for n in DFL_TRAIN if n != k])
    for seed in SEEDS:
        oof[(k, seed)] = probs(models, k, seed)
    print('fold', k, round(time.time() - t), flush=True)
Xs, yd, yh = [], [], []
for (k, seed), (pd_, ph) in oof.items():
    m, lab = load(k)
    idx = np.arange(seed % 3, len(lab), 3); idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
    for swap in (False, True):
        S, cols = stack_features(pd_, ph, m['period'], swap=swap)
        Xs.append(S[idx]); yd.append((lab[idx] == 'D').astype(np.int8))
        h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
        yh.append((np.where(h >= 0, 1 - h, -1) if swap else h).astype(np.int8))
X2 = np.concatenate(Xs); yd2 = np.concatenate(yd); yh2 = np.concatenate(yh)
sd = HistGradientBoostingClassifier(random_state=0, **HP2).fit(X2, yd2)
a = yh2 >= 0
sh = HistGradientBoostingClassifier(random_state=0, **HP2).fit(X2[a], yh2[a])
pickle.dump((sd, sh), open(C + 'stack_v2.pkl', 'wb')); print('stacked', round(time.time() - t), flush=True)
