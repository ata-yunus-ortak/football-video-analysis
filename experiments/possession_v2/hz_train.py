"""v2.6: train the switch-hazard model on the 4 training matches (seeds 1-3, v2.1 corruption), with stack
features from the cached out-of-fold stage-1 probabilities (cache/oof_f2.pkl)."""
import sys, time, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, DFL_TRAIN
from hz_common import switch_target, hazard_matrix
from sklearn.ensemble import HistGradientBoostingClassifier
HP = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0,
          early_stopping=False)
t0 = time.time()
oof = pickle.load(open('/home/claude/work/cache/oof_f2.pkl', 'rb'))
Xs, ys = [], []
for name in DFL_TRAIN:
    m, lab = load(name)
    y_all = switch_target(lab)
    for seed in (1, 2, 3):
        dm = degraded(name, seed)
        p1, q1 = oof[(name, seed)]
        idx = np.arange(seed % 3, len(lab), 3)
        idx = idx[np.isin(lab[idx], ('H', 'A'))]
        for sw in (False, True):
            Xs.append(hazard_matrix(dm, m['period'], p1, q1, sw, idx).astype(np.float32))
            ys.append(y_all[idx])
        print('rows', name, seed, len(idx), round(time.time() - t0), flush=True)
X = np.concatenate(Xs); y = np.concatenate(ys); del Xs
print('train', X.shape, 'positive rate', round(float(y.mean()), 4), flush=True)
model = HistGradientBoostingClassifier(random_state=0, **HP).fit(X, y)
pickle.dump(model, open('/home/claude/work/cache/hazard_v2.pkl', 'wb'))
print('done', round(time.time() - t0), flush=True)
