"""Out-of-fold stacking experiment. Usage: exp_stack.py FTAG out.pkl"""
import sys, os, time, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, DFL_TRAIN
from train1 import rows
from possession.stack import stack_features
from sklearn.ensemble import HistGradientBoostingClassifier
import train1
TAG = sys.argv[1]; train1.TAG = TAG
HP = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0, early_stopping=False)
HP2 = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=400, l2_regularization=1.0, early_stopping=False)
SEEDS = [1, 2, 3]

def fit1(names):
    X, yd, yh = rows(names, SEEDS)
    md = HistGradientBoostingClassifier(random_state=0, **HP).fit(X, yd)
    a = yh >= 0; Xa = X[a]; ya = yh[a]; del X
    mh = HistGradientBoostingClassifier(random_state=0, **HP).fit(Xa, ya)
    return md, mh

def probs(models, name, seed):
    md, mh = models
    X = feats(name, seed, False, TAG); Xs = feats(name, seed, True, TAG)
    ok = np.isfinite(X).any(1)
    pd_ = np.full(len(X), 0.5); ph = np.full(len(X), 0.5)
    pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    return pd_, ph

if __name__ == '__main__':
    t = time.time()
    oof = {}
    for k in DFL_TRAIN:
        others = [n for n in DFL_TRAIN if n != k]
        models = fit1(others)
        for seed in SEEDS:
            oof[(k, seed)] = probs(models, k, seed)
        print('fold', k, time.time() - t, flush=True)
        del models
    pickle.dump(oof, open(f'/home/claude/work/cache/oof{TAG}.pkl', 'wb'))
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
    pickle.dump((sd, sh), open(sys.argv[2], 'wb'))
    print('stacked', time.time() - t, flush=True)
