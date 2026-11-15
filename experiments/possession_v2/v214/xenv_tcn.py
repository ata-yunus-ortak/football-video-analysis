"""Do the two Python environments give the same rounded network probabilities? Runs tcn/infer.forward (NumPy float64) of
the given members on the stored strided features of one development copy and prints a SHA-256 of the 4-decimal
probabilities (mean over members and both team orders, as tcn/infer.probabilities). Usage: xenv_tcn.py FEAT.npz W.npz [W.npz ...]"""
import sys, hashlib, numpy as np
sys.path.insert(0, '/home/claude/work/v213')
from tcn import infer
import tcn.infer as ti
feats = np.load(sys.argv[1])
members = sum((infer.load_weights(f) for f in sys.argv[2:]), [])
old = ti.STRIDE
ti.STRIDE = 1                         # the stored features are already strided
h = hashlib.sha256(); unrounded = hashlib.sha256()
k = 0
while f'x{k}' in feats:
    total = 0.0
    for w in members:
        total = total + infer.forward(w, feats[f'x{k}']) + infer.forward(w, feats[f'w{k}'])[:, [1, 0, 2]]
    p = total / (2 * len(members))
    unrounded.update(np.ascontiguousarray(p).tobytes())
    h.update(np.ascontiguousarray(np.round(p, infer.PROB_DECIMALS)).tobytes())
    k += 1
ti.STRIDE = old
print(sys.version.split()[0], np.__version__, 'blocks', k, 'rounded', h.hexdigest()[:16], 'unrounded', unrounded.hexdigest()[:16])
