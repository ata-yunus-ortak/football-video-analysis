"""Merge single-member weight files (tcn_jax.py exports) into one file with members m0, m1, ... in the key layout of
tcn/infer.load_weights. Usage: merge_weights.py OUT.npz MEMBER.npz [MEMBER.npz ...]"""
import sys, numpy as np
out, files = sys.argv[1], sys.argv[2:]
arrays = {}
for i, f in enumerate(files):
    blob = np.load(f)
    assert sorted({k.split('/')[0] for k in blob.files}) == ['m0'], f
    for k in blob.files:
        arrays['m%d/%s' % (i, k.split('/', 1)[1])] = blob[k]
np.savez_compressed(out, **arrays)
print('wrote', out, len(files), 'members', len(arrays), 'arrays')
