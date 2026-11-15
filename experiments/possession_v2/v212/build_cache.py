"""v2.12 development, step 1: build the feature caches (resumable; skips files that already exist).

For each development match (J03WOH, J03WOY, J03WPY, J03WQQ) and each corruption seed (training seeds 1, 2, 3 and
the extra held-out seeds 9001-9008, two per match, see common.EXTRA_SEEDS), the corrupted copy is rebuilt with
possession.degrade (harness.degraded, seeded) and:
  - touch features (possession.touch.touch_features, both team views) -> cache/touch_{name}_s{seed}_w{0,1}.npy
  - for the extra seeds only, the frozen baseline features (possession.features.features, both views, 227 columns)
    -> cache/base_{name}_s{seed}_w{0,1}.npy (seeds 1-3 reuse the verified /home/claude/work/cache *_f4.npy arrays)
Then the stage-1 training rows of the match (seeds 1-3, every sixth frame from seed % 6, H/A/D frames, both
views; baseline columns followed by touch columns) -> cache/rows_{name}.npz.
Timings of touch_features per call are written to build_cache.json. Run alone (one heavy process at a time).
Usage: /usr/bin/python3 /home/claude/work/v212/build_cache.py [MATCH ...]
"""
import sys, os, json, time, platform
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
from possession.touch import touch_features
from possession.features import features

LOG = C.ROOT + 'build_cache.json'


def save_npy(path, arr):
    tmp = path[:-4] + '.tmp.npy'
    np.save(tmp, arr)
    os.replace(tmp, path)


def main(names):
    log = json.load(open(LOG)) if os.path.exists(LOG) else {'touch_seconds': {}, 'base_seconds': {}}
    for name in names:
        m, lab = C.load(name)
        for seed in C.held_seeds(name):
            need_t = [w for w in (0, 1) if not os.path.exists(C.touch_path(name, seed, w))]
            need_b = [w for w in (0, 1) if not os.path.exists(C.base_path(name, seed, w))]
            if not need_t and not need_b:
                continue
            dm = C.degraded(name, seed)
            for w in need_t:
                t0 = time.time(); X, tn = touch_features(dm, swap=bool(w)); dt = time.time() - t0
                save_npy(C.touch_path(name, seed, w), X)
                log['touch_seconds'][f'{name}_s{seed}_w{w}'] = round(dt, 2)
                json.dump(tn, open(C.VC + 'touch_names.json', 'w'))
                print(name, seed, w, 'touch', round(dt, 1), X.shape, flush=True)
            for w in need_b:
                if seed in C.TRAIN_SEEDS:
                    raise RuntimeError('baseline cache of a training seed is missing')
                t0 = time.time(); X, bn = features(dm, swap=bool(w)); dt = time.time() - t0
                assert len(bn) == C.NB
                save_npy(C.base_path(name, seed, w), X)
                log['base_seconds'][f'{name}_s{seed}_w{w}'] = round(dt, 2)
                print(name, seed, w, 'base', round(dt, 1), X.shape, flush=True)
            del dm
            json.dump(log, open(LOG, 'w'), indent=1)
        rp = f'{C.VC}rows_{name}.npz'
        if not os.path.exists(rp):
            Xs, yds, yhs, srcs = [], [], [], []
            for seed in C.TRAIN_SEEDS:
                idx = C.row_index(lab, seed, C.STEP)
                for w in (0, 1):
                    Xs.append(C.feats(name, seed, w, 'touch', rows=idx))
                    yd, yh = C.targets(lab, idx, w)
                    yds.append(yd); yhs.append(yh); srcs.append(np.full(len(idx), seed * 2 + w, np.int16))
            tmp = rp[:-4] + '.tmp.npz'
            np.savez(tmp, X=np.concatenate(Xs), yd=np.concatenate(yds), yh=np.concatenate(yhs), src=np.concatenate(srcs))
            os.replace(tmp, rp)
            print(name, 'rows', sum(len(x) for x in Xs), flush=True)
    log['environment'] = {'python': platform.python_version(), 'numpy': np.__version__}
    json.dump(log, open(LOG, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:] or C.MATCHES)
