"""The team member's experiments/v216u/xenv.py with the staging paths: hash of the candidate's rounded probabilities
on a synthetic input (no match data), to compare Python / NumPy builds and operating systems."""
import glob, hashlib, sys, platform, time
import numpy as np
sys.path.insert(0, '/home/claude/work/v219')
from tcn2 import infer
rng = np.random.default_rng(216)
n = 3000
ball = np.cumsum(rng.normal(size=(n, 2)), 0).astype(np.float32) % 60 - 30
ball[400:520] = np.nan; ball[1500:1505] = np.nan
t0 = (rng.normal(size=(n, 23, 2)) * 14 - [8, 0]).astype(np.float32); t1 = (rng.normal(size=(n, 23, 2)) * 14 + [8, 0]).astype(np.float32)
t0[:, 11:] = np.nan; t1[:, 11:] = np.nan; t0[900:960, 3] = np.nan
files = sorted(glob.glob('/home/claude/work/v219/weights/d6_[af]_s[0-3].npz'))
members = sum((infer.load_weights(f) for f in files), [])
t = time.time()
p = infer.probabilities(members, ball, t0, t1)
print(platform.python_version(), np.__version__, platform.system(), platform.machine(), len(members), 'members',
      hashlib.sha256(np.ascontiguousarray(p).tobytes()).hexdigest(), 'seconds', round(time.time() - t, 1), 'for', n, 'frames')
