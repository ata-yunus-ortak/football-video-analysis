"""v2 features + simulated Smart Tagging columns. Usage: exp_tags.py out.pkl [sp_only]"""
import sys, os, time, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, DFL_TRAIN
from tagcols import tag_columns
from sklearn.ensemble import HistGradientBoostingClassifier
TAG = '_f2'
SP_ONLY = len(sys.argv) > 2 and sys.argv[2] == 'sp_only'
KEEP = [0, 1, 2, 3, 4, 5, 8, 11] if SP_ONLY else list(range(12))  # sp cols: common 0-4, h_sp 5, k_sp 8, diff_sp 11
HP = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0, early_stopping=False)

def rows(names, seeds, step=6):
    plan, total = [], 0
    for name in names:
        m, lab = load(name)
        for seed in seeds:
            idx = np.arange(seed % step, len(lab), step); idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            plan.append((name, seed, idx, lab[idx])); total += 2 * len(idx)
    k = feats(plan[0][0], plan[0][1], False, TAG).shape[1] + len(KEEP)
    X = np.empty((total, k)); yd = np.empty(total, np.int8); yh = np.empty(total, np.int8); r = 0
    for name, seed, idx, lab in plan:
        m, full = load(name)
        for swap in (False, True):
            F = feats(name, seed, swap, TAG); T = tag_columns(m, full, seed, swap)[:, KEEP]
            X[r:r + len(idx)] = np.hstack([F[idx], T[idx]]); del F
            yd[r:r + len(idx)] = lab == 'D'
            h = np.where(lab == 'H', 1, np.where(lab == 'A', 0, -1))
            yh[r:r + len(idx)] = np.where(h >= 0, 1 - h, -1) if swap else h
            r += len(idx)
    return X, yd, yh

if __name__ == '__main__':
    t = time.time()
    X, yd, yh = rows(DFL_TRAIN, [1, 2, 3])
    md = HistGradientBoostingClassifier(random_state=0, **HP).fit(X, yd)
    a = yh >= 0; Xa = X[a]; ya = yh[a]; del X
    mh = HistGradientBoostingClassifier(random_state=0, **HP).fit(Xa, ya)
    pickle.dump((md, mh, KEEP), open(sys.argv[1], 'wb'))
    print('trained', time.time() - t, flush=True)
