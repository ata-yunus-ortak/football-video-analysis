"""Version-independent storage and numpy evaluation of binary gradient-boosted trees.

Training uses scikit-learn's HistGradientBoostingClassifier on external data only; the fitted
trees are exported to plain arrays so that inference needs only numpy and gives identical
results regardless of the installed scikit-learn version.
"""
import numpy as np

FIELDS = ('feature', 'threshold', 'left', 'right', 'leaf', 'value', 'nan_left')


def export_hgb(clf):
    if clf.n_trees_per_iteration_ != 1:
        raise ValueError('binary classifier expected')
    offs, arrays = [0], {k: [] for k in FIELDS}
    for (tree,) in clf._predictors:
        nd = tree.nodes
        if np.any(nd['is_categorical']):
            raise ValueError('categorical splits are not supported')
        arrays['feature'].append(nd['feature_idx'].astype(np.int32))
        arrays['threshold'].append(nd['num_threshold'].astype(np.float64))
        arrays['left'].append(nd['left'].astype(np.int32))
        arrays['right'].append(nd['right'].astype(np.int32))
        arrays['leaf'].append(nd['is_leaf'].astype(bool))
        arrays['value'].append(nd['value'].astype(np.float64))
        arrays['nan_left'].append(nd['missing_go_to_left'].astype(bool))
        offs.append(offs[-1] + len(nd))
    out = {k: np.concatenate(v) for k, v in arrays.items()}
    out['offsets'] = np.array(offs, np.int64)
    out['baseline'] = np.array(float(np.ravel(clf._baseline_prediction)[0]))
    return out


def raw_score(model, X):
    X = np.asarray(X, np.float64)
    n = len(X)
    total = np.full(n, float(model['baseline']))
    f, thr, lft, rgt, leaf, val, nl = (model[k] for k in FIELDS)
    offs = model['offsets']
    rows = np.arange(n)
    for t in range(len(offs) - 1):
        o = int(offs[t])
        node = np.zeros(n, np.int64)
        active = ~leaf[o + node]
        while active.any():
            idx = rows[active]
            nd = node[idx] + o
            x = X[idx, f[nd]]
            go_left = np.where(np.isnan(x), nl[nd], x <= thr[nd])
            node[idx] = np.where(go_left, lft[nd], rgt[nd])
            active[idx] = ~leaf[o + node[idx]]
        total += val[o + node]
    return total


def predict_proba(model, X):
    return 1.0 / (1.0 + np.exp(-raw_score(model, X)))
