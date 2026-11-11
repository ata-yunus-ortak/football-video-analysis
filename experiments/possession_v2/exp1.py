import sys, time, json, numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from possession.data import read_dfl_prepared, read_metrica_csv
from possession.features import features
from possession.degrade import degrade
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
from sklearn.ensemble import HistGradientBoostingClassifier

BASE = '/mnt/user-data/uploads/sportec-development-20261107/prepared-v1/'
TRAIN = ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ']
VAL = ['J03WN1', 'J03WR9']

def load(name):
    m, lab = read_dfl_prepared(BASE + name)
    return m, lab

def feats_cached(name, seed, swap, m=None, lab=None):
    path = f'/home/claude/work/cache/{name}_s{seed}_w{int(swap)}.npy'
    try:
        return np.load(path)
    except FileNotFoundError:
        pass
    if m is None:
        m, lab = load(name)
    dm = degrade(m, lab, np.random.default_rng(seed)) if seed >= 0 else m
    X, names = features(dm, swap=swap)
    np.save(path, X)
    json.dump(names, open('/home/claude/work/cache/names.json', 'w'))
    return X

def rows(names_list, seeds, step=4):
    Xs, yd, yh = [], [], []
    for name in names_list:
        m, lab = load(name)
        for seed in seeds:
            for swap in (False, True):
                X = feats_cached(name, seed, swap, m, lab)
                idx = np.arange(0, len(lab), step) + (seed % step)
                idx = idx[idx < len(lab)]
                idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
                Xs.append(X[idx]); yd.append((lab[idx] == 'D').astype(np.int8))
                h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
                if swap: h = np.where(h >= 0, 1 - h, -1)
                yh.append(h.astype(np.int8))
    return np.concatenate(Xs), np.concatenate(yd), np.concatenate(yh)

if __name__ == '__main__':
    t = time.time()
    X, yd, yh = rows(TRAIN, seeds=[1, 2, 3])
    print('train rows', X.shape, 'dead frac', yd.mean(), time.time() - t, flush=True)
    t = time.time()
    md = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                        min_samples_leaf=200, l2_regularization=1.0, random_state=0)
    md.fit(X, yd)
    alive = yh >= 0
    mh = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                        min_samples_leaf=200, l2_regularization=1.0, random_state=0)
    mh.fit(X[alive], yh[alive])
    print('trained', time.time() - t, flush=True)
    import pickle
    pickle.dump((md, mh), open('/home/claude/work/cache/models_exp1.pkl', 'wb'))
