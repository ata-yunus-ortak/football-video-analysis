import sys, os, time, pickle, numpy as np
TAG = os.environ.get('FTAG', '')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, DFL_TRAIN
from sklearn.ensemble import HistGradientBoostingClassifier

def rows(names_list, seeds, step=6):
    plan = []
    total = 0
    for name in names_list:
        m, lab = load(name)
        for seed in seeds:
            idx = np.arange(seed % step, len(lab), step)
            idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            plan.append((name, seed, idx, lab[idx]))
            total += 2 * len(idx)
    k = len(feats(plan[0][0], plan[0][1], False, TAG)[0])
    X = np.empty((total, k), np.float64); yd = np.empty(total, np.int8); yh = np.empty(total, np.int8)
    r = 0
    for name, seed, idx, lab in plan:
        for swap in (False, True):
            F = feats(name, seed, swap, TAG)
            X[r:r + len(idx)] = F[idx]; del F
            yd[r:r + len(idx)] = lab == 'D'
            h = np.where(lab == 'H', 1, np.where(lab == 'A', 0, -1))
            if swap: h = np.where(h >= 0, 1 - h, -1)
            yh[r:r + len(idx)] = h
            r += len(idx)
    return X, yd, yh

if __name__ == '__main__':
    out = sys.argv[1]
    hp = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0, early_stopping=False)
    t = time.time()
    X, yd, yh = rows(DFL_TRAIN, [1, 2, 3])
    print('rows', X.shape, time.time() - t, flush=True)
    md = HistGradientBoostingClassifier(random_state=0, **hp).fit(X, yd)
    print('dead model', time.time() - t, flush=True)
    a = yh >= 0
    Xa = X[a]; ya = yh[a]; del X
    mh = HistGradientBoostingClassifier(random_state=0, **hp).fit(Xa, ya)
    print('home model', time.time() - t, flush=True)
    pickle.dump((md, mh), open(out, 'wb'))
    print('trained', time.time() - t, flush=True)
