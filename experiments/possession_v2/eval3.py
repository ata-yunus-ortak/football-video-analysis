"""Validation: DFL val + Metrica 1-2 (degraded seeds 101,102). Usage: eval2.py models.pkl [grid]"""
import sys, os, time, json, pickle, itertools, numpy as np
TAG = os.environ.get('FTAG', '')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, degraded, DFL_VAL, MET_VAL
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
from baselines import organizer_baseline, s001

def probs(models, name, seed, key=None):
    if key:
        path = f'/home/claude/work/cache/probs_{key}_{name}_{seed}.npz'
        if os.path.exists(path):
            z = np.load(path); return z['pd'], z['ph']
    pd_, ph = _probs(models, name, seed)
    if key:
        np.savez(path, pd=pd_, ph=ph)
    return pd_, ph

def _probs(models, name, seed):
    md, mh = models
    X = feats(name, seed, False, TAG); Xs = feats(name, seed, True, TAG)
    ok = np.isfinite(X).any(1)
    pd_ = np.full(len(X), 0.5); ph = np.full(len(X), 0.5)
    pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    return pd_, ph

def build_cases(models, sets, seeds=(101, 102), with_baselines=False, key=None):
    cases = []
    for name in sets:
        m, lab = load(name)
        for seed in seeds:
            pd_, ph = probs(models, name, seed, key)
            c = dict(name=name, seed=seed, lab=lab, period=m['period'], pd=pd_, ph=ph)
            if with_baselines:
                c['b50'] = np.load(f'/home/claude/work/cache/pred_baseline50_{name}_{seed}.npy')
                c['s001'] = np.load(f'/home/claude/work/cache/pred_S001_{name}_{seed}.npy')
            alive = np.isin(lab, ('H', 'A'))
            print(name, seed, 'D acc %.3f' % np.mean((pd_ > .5) == (lab == 'D'))[()],
                  'team acc %.3f' % np.mean(((ph > .5) == (lab == 'H'))[alive]), flush=True)
            cases.append(c)
    return cases

def mean_scores(cases, fn):
    rs = [score(c['lab'], fn(c), c['period']) for c in cases]
    keys = [k for k in rs[0] if rs[0][k] is not None]
    return {k: round(float(np.mean([r[k] for r in rs])), 4) for k in keys}, rs

def by_domain(cases, fn):
    out = {}
    for dom, pref in (('DFL', 'J03'), ('MET', 'MET')):
        cs = [c for c in cases if c['name'].startswith(pref)]
        if cs:
            out[dom] = mean_scores(cs, fn)[0]['spell_f1_mean']
    out['ALL'] = mean_scores(cases, fn)[0]['spell_f1_mean']
    return out

GRID = list(itertools.product([3, 8, 20, 50], [15, 60], [15, 60], [0.0]))

if __name__ == '__main__':
    models = pickle.load(open(sys.argv[1], 'rb'))
    key = os.path.basename(sys.argv[1]).replace('.pkl', '') + TAG
    cases = build_cases(models, DFL_VAL + MET_VAL, with_baselines=True, key=key)
    for nm, fn in (('baseline50', lambda c: c['b50']), ('S001', lambda c: c['s001']),
                   ('argmax', lambda c: np.where(c['pd'] > .5, 'D', np.where(c['ph'] > .5, 'H', 'A')))):
        s, _ = mean_scores(cases, fn)
        print(nm, by_domain(cases, fn), 'macro', s['macro_f1'], 'spells', s['n_pred_spells'], 'gt', s['n_gt_spells'], flush=True)
    res = []
    for sw, oc, ic, bd in GRID:
        prm = dict(switch=sw, out_cost=oc, in_cost=ic, bias_dead=bd)
        fn = lambda c: decode_blocks(emissions(c['pd'], c['ph']), c['period'], prm)
        s, _ = mean_scores(cases, fn)
        bd_ = by_domain(cases, fn)
        res.append((s['spell_f1_mean'], s['macro_f1'], bd_, prm, s['n_pred_spells']))
        print(round(s['spell_f1_mean'], 4), round(s['macro_f1'], 4), bd_, prm, s['n_pred_spells'], s['n_gt_spells'], flush=True)
    res.sort(key=lambda r: -r[0])
    print('BEST'); [print(r) for r in res[:8]]
