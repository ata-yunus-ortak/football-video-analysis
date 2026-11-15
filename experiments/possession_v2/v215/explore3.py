"""Development for a third candidate (NOT a validation): arithmetic pool with a smaller weight, on the 22 earlier
development copies and on the 20 tactical / his-simulator copies of the v2.14 validation (development data after its
decision; stored by v214/cache_new.py and retcn2.py). Usage: explore3.py"""
import sys, glob, json, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v214')
import explore2 as X
import lib214 as L
from possession.evaluate import score
X.GRID = [('arithmetic', w) for w in (0.1, 0.2, 0.3, 0.4, 0.5)]
rows = {}
for f in sorted(glob.glob(L.PROBS + '*.npz')):
    if f.endswith('.feat.npz') or '.m_' in f:
        continue
    key = os.path.basename(f)[:-4]
    tags = ['d4s0', 'd4s1', 'd4s2'] if key.startswith('J03') else ['d6s0', 'd6s1', 'd6s2']
    files = [f[:-4] + '.m_' + t + '.npz' for t in tags]
    assert all(os.path.exists(x) for x in files), key
    d = dict(np.load(f, allow_pickle=False))
    V = X.variants(d, L.ensemble_tcn(files, d['per']))
    rows[key] = {k: (lambda s: (float(s['spell_f1_mean']), float(s['macro_f1'])))(score(d['lab'], v, d['per'])) for k, v in V.items()}
    print(key, ' '.join(f"{k}={v[0] - rows[key]['v2_11'][0]:+.4f}" for k, v in rows[key].items() if k != 'v2_11'), flush=True)
json.dump(rows, open('/home/claude/work/v215/explore3.json', 'w'), indent=1)
