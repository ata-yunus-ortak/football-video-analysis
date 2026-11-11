"""Robustness check (reporting only, no selection): tracker artefacts DATA.md describes but
degrade.py does not simulate -- slot identity swaps, duplicated players, longer false ball
detections. Frozen v2 models + selected decoder, v2 feature code, validation matches only."""
import sys, json, pickle, importlib.util, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.degrade import degrade
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
import os
spec = importlib.util.spec_from_file_location('fv2', os.environ.get('FEATV', '/home/claude/work/features_v2_backup.py'))
fv2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(fv2)
md, mh = pickle.load(open(sys.argv[1], 'rb')); prm = json.loads(sys.argv[2])
S2 = pickle.load(open(sys.argv[3], 'rb')) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
OUT = sys.argv[4] if len(sys.argv) > 4 else '/home/claude/work/stress2_v2.json'
from possession.stack import stack_features
def stage2(pd_, ph, period):
    if S2 is None: return pd_, ph
    sd, sh = S2
    S, _ = stack_features(pd_, ph, period); Sw, _ = stack_features(pd_, ph, period, swap=True)
    ok = np.isfinite(S).any(1); d2 = np.full(len(S), .5); h2 = np.full(len(S), .5)
    d2[ok] = .5 * (sd.predict_proba(S[ok])[:, 1] + sd.predict_proba(Sw[ok])[:, 1])
    h2[ok] = .5 * (sh.predict_proba(S[ok])[:, 1] + 1 - sh.predict_proba(Sw[ok])[:, 1])
    return d2, h2


def id_swaps(m, rng, rate=0.003, radius=2.0):
    P = m['players'].copy(); team = m['team']; n, s, _ = P.shape; k = 0
    for a in np.flatnonzero(rng.random(n) < rate):
        j = int(rng.integers(0, s))
        if not np.isfinite(P[a, j]).all():
            continue
        same = np.flatnonzero((team == team[j]) & (np.arange(s) != j))
        d = np.linalg.norm(P[a, same] - P[a, j], axis=1)
        d[~np.isfinite(d)] = np.inf
        if not len(d) or d.min() > radius:
            continue
        o = same[int(np.argmin(d))]
        P[a:, [j, o]] = P[a:, [o, j]]; k += 1
    out = dict(m); out['players'] = P; return out, k


def duplicates(m, rng, rate=0.001):
    P = m['players']; team = m['team']; n, s, _ = P.shape; cols, tt = [], []
    for a in np.flatnonzero(rng.random(n) < rate):
        j = int(rng.integers(0, s)); b = min(n, a + int(rng.integers(25, 250)))
        ang = rng.uniform(0, 2 * np.pi); r = rng.uniform(0.2, 1.0)
        c = np.full((n, 2), np.nan, np.float32)
        c[a:b] = P[a:b, j] + np.array([np.cos(ang), np.sin(ang)], np.float32) * r + rng.normal(0, .1, (b - a, 2))
        cols.append(c); tt.append(team[j])
    out = dict(m)
    if cols:
        out['players'] = np.concatenate([P, np.stack(cols, 1)], 1); out['team'] = np.r_[team, np.array(tt, np.int8)]
    return out, len(cols)


def long_fp(m, rng, rate=0.0005):
    B = m['ball'].copy(); n = len(B); L, W = m['pitch']; k = 0
    for a in np.flatnonzero(rng.random(n) < rate):
        b = min(n, a + int(rng.integers(25, 125)))
        B[a:b] = rng.uniform([0, 0], [L, W]) + rng.normal(0, .2, (b - a, 2)); k += 1
    out = dict(m); out['ball'] = B; return out, k


VARIANTS = {'base': [], 'id_swaps': [id_swaps], 'duplicates': [duplicates], 'long_fp': [long_fp],
            'all3': [id_swaps, duplicates, long_fp]}
res = {v: [] for v in VARIANTS}
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    dm0 = degrade(m, lab, np.random.default_rng(101))
    for v, fns in VARIANTS.items():
        dm = dm0; rng = np.random.default_rng(7); cnt = []
        for f in fns:
            dm, k = f(dm, rng); cnt.append(k)
        X, _ = fv2.features(dm); Xs, _ = fv2.features(dm, swap=True)
        ok = np.isfinite(X).any(1); pd_ = np.full(len(X), .5); ph = np.full(len(X), .5)
        pd_[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
        ph[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
        pd_, ph = stage2(pd_, ph, m['period'])
        r = score(lab, decode_blocks(emissions(pd_, ph), m['period'], prm), m['period'])
        res[v].append(r['spell_f1_mean'])
        print(v, name, cnt, 'spell %.4f macro %.4f' % (r['spell_f1_mean'], r['macro_f1']), flush=True)
summary = {v: float(np.mean(x)) for v, x in res.items()}
print('SUMMARY', json.dumps(summary), flush=True)
json.dump({'per_match': res, 'mean': summary, 'note': 'reporting only; degrade seed 101; artefact seed 7'},
          open(OUT, 'w'), indent=1)
