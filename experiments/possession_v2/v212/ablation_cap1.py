"""v2.12 development, variant check (resumable): the touch features with event-state look-back capped at 1 s.

possession/touch.py lets its causal event-state columns (since, last, d_last, last_*, since_change) carry the latest
touch for up to STATE_CAP_S = 10 s, while every window statistic spans at most 1 s. Under the stricter reading
"nothing looks back more than about 1 s", this script sets possession.touch.STATE_CAP_S = 1.0 in memory (the file is
not changed), rebuilds the touch columns for the same copies (cache/touchcap1_*.npy, rows_cap1_*.npz) and repeats
the stage-1 leave-one-match-out run of lomo_stage1.py for this set only ('cap1' = base 227 + 36 touch columns with
the 1 s cap). Same matches, seeds, hyperparameters, decoder and scoring; results ablation_cap1.json.
Development data only; not a test or a selection. Usage: /usr/bin/python3 /home/claude/work/v212/ablation_cap1.py
"""
import sys, os, json, time, platform
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
import possession.touch as T

T.STATE_CAP_S = 1.0
OUT = C.ROOT + 'ablation_cap1.json'


def tpath(name, seed, w):
    return f'{C.VC}touchcap1_{name}_s{seed}_w{w}.npy'


def feats(name, seed, w, rows=None):
    b = C.base(name, seed, w, rows)
    a = np.load(tpath(name, seed, w), mmap_mode='r')
    return np.concatenate([b, np.asarray(a if rows is None else a[rows], np.float32)], 1)


def build(R):
    for name in C.MATCHES:
        m, lab = C.load(name)
        for seed in C.held_seeds(name):
            need = [w for w in (0, 1) if not os.path.exists(tpath(name, seed, w))]
            if not need:
                continue
            dm = C.degraded(name, seed)
            for w in need:
                t0 = time.time(); X, _ = T.touch_features(dm, swap=bool(w))
                tmp = tpath(name, seed, w)[:-4] + '.tmp.npy'; np.save(tmp, X); os.replace(tmp, tpath(name, seed, w))
                print(name, seed, w, 'cap1 touch', round(time.time() - t0, 1), flush=True)
            del dm
        rp = f'{C.VC}rows_cap1_{name}.npz'
        if not os.path.exists(rp):
            Xs, yds, yhs = [], [], []
            for seed in C.TRAIN_SEEDS:
                idx = C.row_index(lab, seed, C.STEP)
                for w in (0, 1):
                    Xs.append(feats(name, seed, w, idx)); yd, yh = C.targets(lab, idx, w); yds.append(yd); yhs.append(yh)
            tmp = rp[:-4] + '.tmp.npz'
            np.savez(tmp, X=np.concatenate(Xs), yd=np.concatenate(yds), yh=np.concatenate(yhs)); os.replace(tmp, rp)


def lomo(R):
    for held in C.MATCHES:
        m, lab = C.load(held)
        mp = f'{C.VC}s1_{held}_cap1.pkl'
        if os.path.exists(mp):
            md, mh = C.load_pickle(mp)
        else:
            parts = [np.load(f'{C.VC}rows_cap1_{x}.npz') for x in C.MATCHES if x != held]
            X = np.concatenate([z['X'] for z in parts]); yd = np.concatenate([z['yd'] for z in parts])
            yh = np.concatenate([z['yh'] for z in parts]); del parts
            t0 = time.time(); md, mh = C.fit(X, yd, yh, C.HP); dt = time.time() - t0
            del X
            C.save_pickle((md, mh), mp)
            R['fit_seconds'][held] = round(dt, 1); json.dump(R, open(OUT, 'w'), indent=1)
            print(held, 'cap1 fit', round(dt, 1), flush=True)
        for seed in C.held_seeds(held):
            key = f'{held}|cap1|{seed}'
            if key in R['rows']:
                continue
            X, Xs = feats(held, seed, 0), feats(held, seed, 1)
            pd_, ph = C.probs(md, mh, X, Xs, m['period'])
            del X, Xs
            np.savez(f'{C.VC}p1_{held}_cap1_s{seed}.npz', pd=pd_, ph=ph)
            r = C.evaluate(lab, m['period'], pd_, ph)
            R['rows'][key] = r; json.dump(R, open(OUT, 'w'), indent=1)
            print(key, round(r['spell_f1'], 4), round(r['macro_f1'], 4), r['short_hit'], '/', r['short_n'], flush=True)
        del md, mh


if __name__ == '__main__':
    R = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': {}, 'fit_seconds': {}}
    R['variant'] = 'possession.touch.STATE_CAP_S = 1.0 in memory; everything else as lomo_stage1.py touch set'
    build(R)
    lomo(R)
    import pandas, sklearn
    R['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__,
                        'sklearn': sklearn.__version__}
    json.dump(R, open(OUT, 'w'), indent=1)
