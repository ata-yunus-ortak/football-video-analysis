"""v2.8: Metrica-labelled matches added to training. Usage:
  v28.py train VARIANT NAME,NAME,...        (stage 1 on all, out-of-fold stage 2; resumable)
  v28.py eval  VARIANT SWITCH out.json NAME:SEED ...
Feature version 2 everywhere (first 227 columns of any cached matrix)."""
import sys, os, json, time, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, CACHE
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
K = 227
TAGS = os.environ.get('TAGS', '_f4,_m2,_n2,_f2').split(',')
HP = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200, l2_regularization=1.0, early_stopping=False)
HP2 = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=400, l2_regularization=1.0, early_stopping=False)
SEEDS = [1, 2, 3]


def getX(name, seed, swap):
    for tag in TAGS:
        p = f'{CACHE}{name}_s{seed}_w{int(swap)}{tag}.npy'
        if os.path.exists(p):
            return np.load(p)[:, :K]
    raise FileNotFoundError((name, seed, swap))


def rows(names, step=6):
    Xs, yd, yh = [], [], []
    for name in names:
        m, lab = load(name)
        for seed in SEEDS:
            idx = np.arange(seed % step, len(lab), step); idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            l = lab[idx]
            for swap in (False, True):
                Xs.append(getX(name, seed, swap)[idx].astype(np.float32)); yd.append((l == 'D').astype(np.int8))
                h = np.where(l == 'H', 1, np.where(l == 'A', 0, -1))
                yh.append((np.where(h >= 0, 1 - h, -1) if swap else h).astype(np.int8))
    return np.concatenate(Xs), np.concatenate(yd), np.concatenate(yh)


def fit1(names):
    X, yd, yh = rows(names)
    md = HGB(random_state=0, **HP).fit(X, yd)
    a = yh >= 0
    mh = HGB(random_state=0, **HP).fit(X[a], yh[a])
    return md, mh


def probs1(models, name, seed):
    md, mh = models
    X = getX(name, seed, False); Xs = getX(name, seed, True)
    ok = np.isfinite(X).any(1)
    p = np.full(len(X), .5); q = np.full(len(X), .5)
    p[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    return p, q


def probs2(stack, p1, q1, per):
    sd, sh = stack
    S = [stack_features(p1, q1, per, swap=w)[0] for w in (False, True)]
    ok = np.isfinite(S[0][:, 0])
    p = np.full(len(p1), .5); q = np.full(len(p1), .5)
    p[ok] = .5 * (sd.predict_proba(S[0][ok])[:, 1] + sd.predict_proba(S[1][ok])[:, 1])
    q[ok] = .5 * (sh.predict_proba(S[0][ok])[:, 1] + 1 - sh.predict_proba(S[1][ok])[:, 1])
    return p, q


def train(variant, names):
    t = time.time()
    f1 = f'{CACHE}v28_{variant}_s1.pkl'
    if not os.path.exists(f1):
        pickle.dump(fit1(names), open(f1, 'wb')); print('stage1', round(time.time() - t), flush=True)
    oof = {}
    for k in names:
        fo = f'{CACHE}v28_{variant}_oof_{k}.pkl'
        if not os.path.exists(fo):
            models = fit1([n for n in names if n != k])
            pickle.dump({(k, s): probs1(models, k, s) for s in SEEDS}, open(fo, 'wb')); del models
            print('fold', k, round(time.time() - t), flush=True)
        oof.update(pickle.load(open(fo, 'rb')))
    Xs, yd, yh = [], [], []
    for (k, seed), (p, q) in oof.items():
        m, lab = load(k)
        idx = np.arange(seed % 3, len(lab), 3); idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
        for swap in (False, True):
            S, _ = stack_features(p, q, m['period'], swap=swap)
            Xs.append(S[idx]); yd.append((lab[idx] == 'D').astype(np.int8))
            h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
            yh.append((np.where(h >= 0, 1 - h, -1) if swap else h).astype(np.int8))
    X2, yd2, yh2 = np.concatenate(Xs), np.concatenate(yd), np.concatenate(yh)
    sd = HGB(random_state=0, **HP2).fit(X2, yd2); a = yh2 >= 0
    sh = HGB(random_state=0, **HP2).fit(X2[a], yh2[a])
    pickle.dump((sd, sh), open(f'{CACHE}v28_{variant}_s2.pkl', 'wb'))
    print('TRAINED', variant, round(time.time() - t), flush=True)


def evaluate(variant, sw, out, items):
    if variant == 'base':
        s1 = pickle.load(open(CACHE + 'models_v2.pkl', 'rb')); s2 = pickle.load(open(CACHE + 'stack_v2.pkl', 'rb'))
    else:
        s1 = pickle.load(open(f'{CACHE}v28_{variant}_s1.pkl', 'rb')); s2 = pickle.load(open(f'{CACHE}v28_{variant}_s2.pkl', 'rb'))
    DEC = {'switch': float(sw), 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
    res = json.load(open(out)) if os.path.exists(out) else {}
    for item in items:
        if item in res:
            continue
        name, seed = item.split(':'); seed = int(seed)
        m, lab = load(name); per = m['period']
        p2, q2 = probs2(s2, *probs1(s1, name, seed), per)
        s = score(lab, decode_blocks(emissions(p2, q2), per, DEC), per)
        res[item] = {'spell': s['spell_f1_mean'], 'macro': s['macro_f1'], 'n_pred': s['n_pred_spells'], 'n_gt': s['n_gt_spells']}
        print(variant, item, round(s['spell_f1_mean'], 4), round(s['macro_f1'], 4), flush=True)
        json.dump(res, open(out, 'w'), indent=1)
    print('EVALDONE', variant, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'train':
        train(sys.argv[2], sys.argv[3].split(','))
    else:
        evaluate(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
