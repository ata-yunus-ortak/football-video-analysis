"""v3 stage 2: stacking features + simulated Smart Tagging features, trained on OOF stage-1
probabilities of the 4 DFL training matches (seeds 1-3), two tag draws per copy.
Usage: exp_v3.py out.pkl"""
import sys, time, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_TRAIN
from possession.stack import stack_features
from possession import smarttags as st
from sklearn.ensemble import HistGradientBoostingClassifier
HP2 = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=400, l2_regularization=1.0,
           early_stopping=False)
STEP, DRAWS = 4, 2

if __name__ == '__main__':
    t0 = time.time()
    oof = pickle.load(open('/home/claude/work/cache/oof_f2.pkl', 'rb'))
    Xs, yd, yh = [], [], []
    for fi, name in enumerate(DFL_TRAIN):
        m, lab = load(name)
        for seed in (1, 2, 3):
            pd_, ph = oof[(name, seed)]
            S = [stack_features(pd_, ph, m['period'], m['fps'], swap=sw)[0] for sw in (False, True)]
            for draw in range(DRAWS):
                rng = np.random.default_rng([seed, fi, draw, 11])
                prm = st.sample_params(rng)
                tags = st.simulate(lab, m['ball'], m['players'], m['team'], m['period'], m['pitch'], m['fps'], rng, prm)
                off = (seed * 2 + draw) % STEP
                idx = np.arange(off, len(lab), STEP)
                idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
                for sw in (False, True):
                    T, tn = st.features(tags, len(lab), m['period'], m['fps'], swap=sw)
                    Xs.append(np.hstack([S[sw][idx], T[idx]]).astype(np.float32))
                    yd.append((lab[idx] == 'D').astype(np.int8))
                    h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
                    yh.append((np.where(h >= 0, 1 - h, -1) if sw else h).astype(np.int8))
        print('rows', name, sum(len(x) for x in Xs), round(time.time() - t0), flush=True)
    X = np.concatenate(Xs); del Xs
    yd = np.concatenate(yd); yh = np.concatenate(yh)
    sd = HistGradientBoostingClassifier(random_state=0, **HP2).fit(X, yd)
    a = yh >= 0
    sh = HistGradientBoostingClassifier(random_state=0, **HP2).fit(X[a], yh[a])
    pickle.dump((sd, sh), open(sys.argv[1], 'wb'))
    print('trained', X.shape, round(time.time() - t0), flush=True)
