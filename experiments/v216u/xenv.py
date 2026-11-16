"""Hash of the candidate's rounded probabilities on a synthetic input (no match data), to compare Python / NumPy builds.
Usage (from the branch root): python experiments/v216u/xenv.py"""
import glob, hashlib, sys, platform
import numpy as np
sys.path.insert(0, '.')
from possession import infer
rng = np.random.default_rng(216)
n = 3000
ball = np.cumsum(rng.normal(size=(n, 2)), 0).astype(np.float32) % 60 - 30
ball[400:520] = np.nan; ball[1500:1505] = np.nan
t0 = (rng.normal(size=(n, 23, 2)) * 14 - [8, 0]).astype(np.float32); t1 = (rng.normal(size=(n, 23, 2)) * 14 + [8, 0]).astype(np.float32)
t0[:, 11:] = np.nan; t1[:, 11:] = np.nan; t0[900:960, 3] = np.nan
members = sum((infer.load_weights(f) for f in sorted(glob.glob('possession/weights/v216u/d6_[af]_s[0-3].npz'))), [])
p = infer.probabilities(members, ball, t0, t1)
print(platform.python_version(), np.__version__, len(members), 'members', hashlib.sha256(np.ascontiguousarray(p).tobytes()).hexdigest())
