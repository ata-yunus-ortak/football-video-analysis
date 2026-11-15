"""Audit finding M1: were the cached touch arrays (and the training rows built from them) produced by the touch.py
that the records name? For every development copy (4 training matches x seeds 1, 2, 3 and the two extra seeds, both
team views) the corrupted copy is rebuilt and possession.touch.touch_features is recomputed with the current file;
the result must equal the cached array bit for bit (NaN positions included). The stage-1 rows (rows_{name}.npz) must
equal the cached base and touch arrays at their row indices. Writes verify_caches.json.
Usage: /usr/bin/python3 verify_caches.py"""
import sys, json, time, platform, os
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
from possession.touch import touch_features


def same(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return a.shape == b.shape and a.dtype == b.dtype and bool(np.array_equal(a, b, equal_nan=True)) and \
        bool(np.array_equal(np.isnan(a), np.isnan(b)))


def main():
    R = {'touch_py_sha256': C.sha('/home/claude/sc/possession/touch.py'), 'arrays': {}, 'rows': {}}
    t0 = time.time()
    for name in C.MATCHES:
        m, lab = C.load(name)
        for seed in C.held_seeds(name):
            dm = C.degraded(name, seed)
            for w in (0, 1):
                X, _ = touch_features(dm, swap=bool(w))
                R['arrays'][f'{name}_s{seed}_w{w}'] = same(X, np.load(C.touch_path(name, seed, w)))
                print(name, seed, w, R['arrays'][f'{name}_s{seed}_w{w}'], round(time.time() - t0), flush=True)
            del dm
        z = np.load(f'{C.VC}rows_{name}.npz')
        Xs = []
        for seed in C.TRAIN_SEEDS:
            idx = C.row_index(lab, seed, C.STEP)
            for w in (0, 1):
                Xs.append(C.feats(name, seed, w, 'touch', rows=idx))
        R['rows'][name] = same(z['X'], np.concatenate(Xs))
        print(name, 'rows', R['rows'][name], flush=True)
    R['all_equal'] = all(R['arrays'].values()) and all(R['rows'].values())
    R['environment'] = {'python': platform.python_version(), 'numpy': np.__version__}
    R['seconds'] = round(time.time() - t0)
    R['written_at'] = os.popen('date -Iseconds').read().strip()
    json.dump(R, open(C.ROOT + 'verify_caches.json', 'w'), indent=1)
    print('ALL_EQUAL', R['all_equal'], flush=True)


if __name__ == '__main__':
    main()
