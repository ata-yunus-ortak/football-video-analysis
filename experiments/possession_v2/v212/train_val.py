"""v2.12 validation models (before registration): the v2.1-path models with the touch columns, trained on the four
DFL training matches only, by the procedure of possession/train.py.

Stage 1: the two HistGradientBoosting models (P dead, P home | alive) with the possession-v2-config.json
hyperparameters on the rows of J03WOH, J03WOY, J03WPY, J03WQQ (training corruption seeds 1, 2, 3, every sixth frame
from seed % 6, H/A/D frames, both team views; base columns = possession.features, then possession.touch columns), in
the row order of possession.train.training_rows (rows built by build_cache.py, cache/rows_{name}.npz).
Stage 2: possession.train.stack_rows: for each training match, the stage-1 models trained on the other three
(cache/s1_{name}_touch.pkl, the outer-fold models of lomo_stage1.py, same rows and order as stack_rows' fit(X[tr]))
give symmetrised, 6-decimal probabilities on its copies of seeds 1, 2, 3 (cache/p1_{name}_touch_s{seed}.npz, as
possession.train.frame_probs); stage-2 rows = possession.stack.stack_features (every third frame from seed % 3,
H/A/D frames, both views); fitted with the config's stack hyperparameters.
Outputs: models_v212_val.pkl (md, mh), stack_v212_val.pkl (sd, sh), train_val.json (hashes, rows, timings).
The validation and reserved matches are not loaded. Usage: /usr/bin/python3 /home/claude/work/v212/train_val.py
"""
import sys, os, json, time, platform, hashlib
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
from possession.stack import stack_features

OUT = C.ROOT + 'train_val.json'
M_OUT, S_OUT = C.ROOT + 'models_v212_val.pkl', C.ROOT + 'stack_v212_val.pkl'


def main():
    R = {'record': 'v2.12 validation models (touch columns, v2.1 path), trained on the four DFL training matches only',
         'fixtures': C.MATCHES, 'seeds': C.TRAIN_SEEDS, 'step': C.STEP, 'stack_step': C.STEP2,
         'hyperparameters': C.HP, 'stack_hyperparameters': C.HP2, 'provided_fixture_used': False}
    t0 = time.time()
    # stage 2 rows from the outer-fold probabilities
    S_all, d_all, h_all, cols = [], [], [], None
    used = {}
    for name in C.MATCHES:
        m, lab = C.load(name)
        for s in C.TRAIN_SEEDS:
            p = f'{C.VC}p1_{name}_touch_s{s}.npz'
            used[os.path.basename(p)] = C.sha(p)
            z = np.load(p)
            idx = C.row_index(lab, s, C.STEP2)
            for w in (0, 1):
                S, cols = stack_features(z['pd'], z['ph'], m['period'], m['fps'], swap=bool(w))
                S_all.append(S[idx]); yd, yh = C.targets(lab, idx, w); d_all.append(yd); h_all.append(yh)
        used[f's1_{name}_touch.pkl'] = C.sha(f'{C.VC}s1_{name}_touch.pkl')
    S, yd, yh = np.concatenate(S_all), np.concatenate(d_all), np.concatenate(h_all)
    del S_all
    R['stack_rows'] = [int(len(S)), int(S.shape[1])]
    R['stack_feature_names'] = cols
    t1 = time.time(); sd, sh = C.fit(S, yd, yh, C.HP2); R['stack_fit_seconds'] = round(time.time() - t1, 1)
    del S
    C.save_pickle((sd, sh), S_OUT)
    print('stage 2 fitted', R['stack_rows'], R['stack_fit_seconds'], flush=True)
    # stage 1 on all four matches
    for name in C.MATCHES:
        used[f'rows_{name}.npz'] = C.sha(f'{C.VC}rows_{name}.npz')
    X, yd, yh = C.train_rows(C.MATCHES, 'touch')
    R['stage1_rows'] = [int(len(X)), int(X.shape[1])]
    t1 = time.time(); md, mh = C.fit(X, yd, yh, C.HP); R['stage1_fit_seconds'] = round(time.time() - t1, 1)
    del X
    C.save_pickle((md, mh), M_OUT)
    print('stage 1 fitted', R['stage1_rows'], R['stage1_fit_seconds'], flush=True)
    import pandas, sklearn
    R['inputs_sha256'] = used
    R['outputs_sha256'] = {'models_v212_val.pkl': C.sha(M_OUT), 'stack_v212_val.pkl': C.sha(S_OUT)}
    R['touch_py_sha256'] = C.sha('/home/claude/sc/possession/touch.py')
    R['script_sha256'] = C.sha(__file__)
    R['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__,
                        'sklearn': sklearn.__version__}
    R['seconds'] = round(time.time() - t0, 1)
    R['written_at'] = os.popen('date -Iseconds').read().strip()
    json.dump(R, open(OUT, 'w'), indent=1)
    print(json.dumps({k: R[k] for k in ('stage1_rows', 'stack_rows', 'seconds', 'outputs_sha256')}), flush=True)


if __name__ == '__main__':
    main()
