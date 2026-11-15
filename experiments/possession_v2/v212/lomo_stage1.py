"""v2.12 development, step 2: leave-one-match-out stage-1 comparison (resumable).

For each held-out development match H in (J03WOH, J03WOY, J03WPY, J03WQQ) and each feature set
  base  = the 227 frozen v2 features (possession.features, feature_version 2)
  touch = base + the 36 possession.touch columns,
the two stage-1 models (P dead, P home | alive) are trained with the possession-v2-config.json hyperparameters on
the other three matches (training seeds 1, 2, 3, every sixth frame, both team views; rows from build_cache.py),
then the held-out copies of H (seeds 1, 2, 3 and its two extra seeds 9001-9008) get symmetrised stage-1
probabilities, the frozen decoder (switch 3, out/in 60, bias_dead -0.3) and the organisers' metric
(possession.evaluate.score) plus short-spell recall (IoU 0.3). NO stacking here (see lomo_stack.py), so the two
sets are compared like with like at stage 1 only. Models: cache/s1_{H}_{set}.pkl; probabilities:
cache/p1_{H}_{set}_s{seed}.npz; results: lomo_stage1.json. Development data only; not a test.
Usage: /usr/bin/python3 /home/claude/work/v212/lomo_stage1.py [HELD ...]
"""
import sys, os, json, time, platform
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C

OUT = C.ROOT + 'lomo_stage1.json'
FSETS = ('base', 'touch')


def main(helds):
    R = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': {}, 'fit_seconds': {}}
    for held in helds:
        C.guard(held)
        m, lab = C.load(held)
        per = m['period']
        for fset in FSETS:
            mp = f'{C.VC}s1_{held}_{fset}.pkl'
            if os.path.exists(mp):
                md, mh = C.load_pickle(mp)
            else:
                tr = [x for x in C.MATCHES if x != held]
                X, yd, yh = C.train_rows(tr, fset)
                t0 = time.time(); md, mh = C.fit(X, yd, yh, C.HP); dt = time.time() - t0
                R['fit_seconds'][f'{held}|{fset}'] = round(dt, 1)
                R.setdefault('train_rows', {})[f'{held}|{fset}'] = [int(len(X)), int(X.shape[1])]
                del X, yd, yh
                C.save_pickle((md, mh), mp)
                json.dump(R, open(OUT, 'w'), indent=1)
                print(held, fset, 'fit', round(dt, 1), flush=True)
            for seed in C.held_seeds(held):
                key = f'{held}|{fset}|{seed}'
                if key in R['rows']:
                    continue
                pp = f'{C.VC}p1_{held}_{fset}_s{seed}.npz'
                if os.path.exists(pp):
                    z = np.load(pp); pd_, ph = z['pd'], z['ph']
                else:
                    X = C.feats(held, seed, 0, fset); Xs = C.feats(held, seed, 1, fset)
                    pd_, ph = C.probs(md, mh, X, Xs, per)
                    del X, Xs
                    np.savez(pp, pd=pd_, ph=ph)
                r = C.evaluate(lab, per, pd_, ph)
                R['rows'][key] = r
                json.dump(R, open(OUT, 'w'), indent=1)
                print(key, round(r['spell_f1'], 4), round(r['macro_f1'], 4), r['short_hit'], '/', r['short_n'], flush=True)
            del md, mh
    import pandas, sklearn
    R['environment'] = {'python': platform.python_version(), 'numpy': np.__version__,
                        'pandas': pandas.__version__, 'sklearn': sklearn.__version__}
    json.dump(R, open(OUT, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:] or C.MATCHES)
