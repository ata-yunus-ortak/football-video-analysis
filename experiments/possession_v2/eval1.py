import sys, time, json, pickle, itertools, numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from exp1 import load, feats_cached, VAL
from possession.degrade import degrade
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
from baselines import organizer_baseline, s001

md, mh = pickle.load(open(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/cache/models_exp1.pkl', 'rb'))
SEEDS = [101, 102]
cases = []
for name in VAL:
    m, lab = load(name)
    for seed in SEEDS:
        X = feats_cached(name, seed, False, m, lab); Xs = feats_cached(name, seed, True, m, lab)
        ok = np.isfinite(X).any(1)
        pd_ = np.full(len(lab), 0.5); ph = np.full(len(lab), 0.5)
        pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
        ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
        dm = degrade(m, lab, np.random.default_rng(seed))
        cases.append(dict(name=name, seed=seed, lab=lab, period=m['period'], pd=pd_, ph=ph, dm=dm))
        print(name, seed, 'frame acc D', np.mean((pd_ > .5) == (lab == 'D')),
              'team acc alive', np.mean(((ph > .5) == (lab == 'H'))[lab != 'D']), flush=True)

def mean_scores(fn):
    rs = [score(c['lab'], fn(c), c['period']) for c in cases]
    return {k: float(np.mean([r[k] for r in rs])) for k in rs[0] if rs[0][k] is not None}, rs

print('baseline50', mean_scores(lambda c: organizer_baseline(c['dm'], 50))[0])
print('S001', mean_scores(lambda c: s001(c['dm']))[0])
print('framewise argmax', mean_scores(lambda c: np.where(c['pd'] > .5, 'D', np.where(c['ph'] > .5, 'H', 'A')))[0])
results = []
for sw, oc, ic, bd in itertools.product([2, 5, 10, 20, 40], [5, 20, 60], [5, 20, 60], [0.0]):
    params = dict(switch=sw, out_cost=oc, in_cost=ic, bias_dead=bd)
    s, _ = mean_scores(lambda c: decode_blocks(emissions(c['pd'], c['ph']), c['period'], params))
    results.append((s['spell_f1_mean'], s['macro_f1'], params))
    print(round(s['spell_f1_mean'], 4), round(s['macro_f1'], 4), params, s['n_pred_spells'], s['n_gt_spells'], flush=True)
results.sort(key=lambda r: -r[0])
print('BEST', results[:5])
