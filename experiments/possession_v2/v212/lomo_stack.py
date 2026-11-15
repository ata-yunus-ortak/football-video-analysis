"""v2.12 development, step 3: the same leave-one-match-out comparison WITH the second stage (resumable).

Mirrors possession.train.stack_rows inside each outer fold. For held-out match H with training matches T (the
other three): for each Ti in T, stage-1 models trained on the two matches T minus Ti (one "pair model" per pair of
development matches and feature set, shared between outer folds) give out-of-fold probabilities on Ti's training
copies (seeds 1, 2, 3, all frames); stage-2 rows = possession.stack.stack_features of those probabilities (every
third frame from seed % 3, H/A/D frames, both team views); stage-2 models are fitted with the config's "stack"
hyperparameters. The held-out copies of H then go stage-1 probabilities from lomo_stage1.py (models trained on
all of T) -> stage 2 -> frozen decoder -> organisers' metric + short-spell recall. Same for base and touch sets.
Artifacts: cache/s1pair_{A}_{B}_{set}.pkl, cache/oof_{Ti}_by_{A}_{B}_{set}_s{seed}.npz, cache/s2_{H}_{set}.pkl;
results lomo_stack.json. Run after lomo_stage1.py. Development data only; not a test.
Usage: /usr/bin/python3 /home/claude/work/v212/lomo_stack.py [pairs|stage2|all]
"""
import sys, os, json, time, platform, itertools
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
from possession.stack import stack_features

OUT = C.ROOT + 'lomo_stack.json'
FSETS = ('base', 'touch')


def jsave(R):
    json.dump(R, open(OUT, 'w'), indent=1)


def pairs_phase(R):
    for pair in itertools.combinations(C.MATCHES, 2):
        key = '_'.join(pair)
        for fset in FSETS:
            mp = f'{C.VC}s1pair_{key}_{fset}.pkl'
            others = [x for x in C.MATCHES if x not in pair]
            need = [(ti, s) for ti in others for s in C.TRAIN_SEEDS
                    if not os.path.exists(f'{C.VC}oof_{ti}_by_{key}_{fset}_s{s}.npz')]
            if os.path.exists(mp) and not need:
                continue
            if os.path.exists(mp):
                md, mh = C.load_pickle(mp)
            else:
                X, yd, yh = C.train_rows(list(pair), fset)
                t0 = time.time(); md, mh = C.fit(X, yd, yh, C.HP); dt = time.time() - t0
                del X, yd, yh
                C.save_pickle((md, mh), mp)
                R['fit_seconds'][f'pair|{key}|{fset}'] = round(dt, 1); jsave(R)
                print('pair', key, fset, 'fit', round(dt, 1), flush=True)
            for ti, s in need:
                m, lab = C.load(ti)
                X = C.feats(ti, s, 0, fset); Xs = C.feats(ti, s, 1, fset)
                pd_, ph = C.probs(md, mh, X, Xs, m['period'])
                del X, Xs
                np.savez(f'{C.VC}oof_{ti}_by_{key}_{fset}_s{s}.npz', pd=pd_, ph=ph)
                print('oof', ti, key, fset, s, flush=True)
            del md, mh


def stage2_phase(R):
    for held in C.MATCHES:
        T = [x for x in C.MATCHES if x != held]
        for fset in FSETS:
            mp = f'{C.VC}s2_{held}_{fset}.pkl'
            if os.path.exists(mp):
                sd, sh = C.load_pickle(mp)
            else:
                S_all, d_all, h_all = [], [], []
                for ti in T:
                    key = '_'.join(sorted([x for x in T if x != ti], key=C.MATCHES.index))
                    m, lab = C.load(ti)
                    for s in C.TRAIN_SEEDS:
                        z = np.load(f'{C.VC}oof_{ti}_by_{key}_{fset}_s{s}.npz')
                        idx = C.row_index(lab, s, C.STEP2)
                        for w in (0, 1):
                            S, cols = stack_features(z['pd'], z['ph'], m['period'], m['fps'], swap=bool(w))
                            S_all.append(S[idx]); yd, yh = C.targets(lab, idx, w); d_all.append(yd); h_all.append(yh)
                S, yd, yh = np.concatenate(S_all), np.concatenate(d_all), np.concatenate(h_all)
                del S_all
                t0 = time.time(); sd, sh = C.fit(S, yd, yh, C.HP2); dt = time.time() - t0
                del S
                C.save_pickle((sd, sh), mp)
                R['fit_seconds'][f'stage2|{held}|{fset}'] = round(dt, 1); jsave(R)
                print('stage2', held, fset, 'fit', round(dt, 1), flush=True)
            m, lab = C.load(held)
            for s in C.held_seeds(held):
                key = f'{held}|{fset}|{s}'
                if key in R['rows']:
                    continue
                z = np.load(f'{C.VC}p1_{held}_{fset}_s{s}.npz')
                d2, h2 = C.stack_probs(sd, sh, z['pd'], z['ph'], m['period'], m['fps'])
                np.savez(f'{C.VC}p2_{held}_{fset}_s{s}.npz', pd=d2, ph=h2)
                r = C.evaluate(lab, m['period'], d2, h2)
                R['rows'][key] = r; jsave(R)
                print(key, round(r['spell_f1'], 4), round(r['macro_f1'], 4), r['short_hit'], '/', r['short_n'], flush=True)
            del sd, sh


def main(what):
    R = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': {}, 'fit_seconds': {}}
    if what in ('pairs', 'all'):
        pairs_phase(R)
    if what in ('stage2', 'all'):
        stage2_phase(R)
    import pandas, sklearn
    R['environment'] = {'python': platform.python_version(), 'numpy': np.__version__,
                        'pandas': pandas.__version__, 'sklearn': sklearn.__version__}
    jsave(R)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
