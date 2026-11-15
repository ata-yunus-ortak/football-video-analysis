"""Stores, for every development copy (already scored in the v2.13 validation), the unrounded probabilities of ONE set
of TCN weights (one member) from the stored input features. Usage: retcn2.py TAG WEIGHTS.npz [pattern]"""
import sys, os, glob, time, numpy as np
import lib214 as L
tag, weights = sys.argv[1], sys.argv[2]
pat = sys.argv[3] if len(sys.argv) > 3 else '*'
mem = L.tinfer.load_weights(weights)
assert len(mem) == 1, 'one member per file'
for ff in sorted(glob.glob(L.PROBS + pat + '.feat.npz')):
    out = ff[:-9] + '.m_' + tag + '.npz'
    if os.path.exists(out):
        continue
    t0 = time.time()
    per = np.load(ff[:-9] + '.npz')['per']
    np.savez(out, **L.member_probs(mem[0], np.load(ff), per))
    print(os.path.basename(out), round(time.time() - t0), 's', flush=True)
print('RETCN2DONE', tag, flush=True)
