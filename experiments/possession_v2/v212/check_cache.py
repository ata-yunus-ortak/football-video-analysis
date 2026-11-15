"""v2.12 development, step 0: verify that a cached baseline feature array equals what the current
(frozen) possession.features.features() returns, before any cached array is reused.

Case checked: DFL training match J03WOH, training corruption seed 1, swap=False (and swap=True), cache file
/home/claude/work/cache/J03WOH_s1_w{0,1}_f4.npy (275 columns = 227 v2 columns + 48 v2.7 columns; only the first 227
are the v2 features). Also times load / degrade / features. Development data only (no validation or reserved match).
Usage: /usr/bin/python3 /home/claude/work/v212/check_cache.py  -> prints a JSON line, writes check_cache.json
"""
import sys, json, time
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, CACHE
from possession.features import features

out = {}
t0 = time.time(); m, lab = load('J03WOH'); out['load_s'] = round(time.time() - t0, 1)
t0 = time.time(); dm = degraded('J03WOH', 1); out['degrade_s'] = round(time.time() - t0, 1)
names2 = json.load(open(CACHE + 'names_f2.json'))
for swap in (0, 1):
    t0 = time.time(); X, names = features(dm, swap=bool(swap)); out[f'features_s_w{swap}'] = round(time.time() - t0, 1)
    C = np.load(f'{CACHE}J03WOH_s1_w{swap}_f4.npy', mmap_mode='r')[:, :len(names)]
    same_nan = bool(np.array_equal(np.isnan(X), np.isnan(C)))
    f = np.isfinite(X)
    out[f'w{swap}'] = {'names_equal_names_f2': names == names2, 'shape': list(X.shape), 'cache_cols': int(C.shape[1]),
                       'nan_pattern_equal': same_nan, 'finite_values_equal': bool(np.array_equal(X[f], np.asarray(C)[f])),
                       'max_abs_diff': float(np.max(np.abs(X[f] - np.asarray(C)[f]))) if f.any() else 0.0}
    del X, C
json.dump(out, open('/home/claude/work/v212/check_cache.json', 'w'), indent=1)
print(json.dumps(out))
