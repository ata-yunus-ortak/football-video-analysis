"""Stress test of a frozen model on harsher/milder corruption (reporting only, no selection)."""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.degrade import degrade, sample_params
import importlib.util, os
_fp = os.environ.get('FEATV', '/home/claude/work/features_v2_backup.py')
_sp = importlib.util.spec_from_file_location('fsel', _fp); _fm = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_fm)
features = _fm.features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
from baselines import organizer_baseline
md, mh = pickle.load(open(sys.argv[1], 'rb')); prm = json.loads(sys.argv[2])
S2 = pickle.load(open(sys.argv[3], 'rb')) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
OUT = sys.argv[4] if len(sys.argv) > 4 else '/home/claude/work/stress_v2.json'
from possession.stack import stack_features
def stage2(pd_, ph, period):
    if S2 is None: return pd_, ph
    sd, sh = S2
    S, _ = stack_features(pd_, ph, period); Sw, _ = stack_features(pd_, ph, period, swap=True)
    ok = np.isfinite(S).any(1); d2 = np.full(len(S), .5); h2 = np.full(len(S), .5)
    d2[ok] = .5 * (sd.predict_proba(S[ok])[:, 1] + sd.predict_proba(Sw[ok])[:, 1])
    h2[ok] = .5 * (sh.predict_proba(S[ok])[:, 1] + 1 - sh.predict_proba(Sw[ok])[:, 1])
    return d2, h2
LEVELS = {'mild': dict(ball_miss_alive=0.12, ball_miss_dead_extra=0.0, ball_sigma_m=0.05, player_miss=0.02, ball_fp_rate=0.0),
          'harsh': dict(ball_miss_alive=0.40, ball_miss_dead_extra=0.0, ball_sigma_m=0.3, player_miss=0.12, ball_fp_rate=0.004),
          'harsh_dead_coupled': dict(ball_miss_alive=0.30, ball_miss_dead_extra=0.55, ball_sigma_m=0.3, player_miss=0.12, ball_fp_rate=0.004)}
out = {}
for lev, fixed in LEVELS.items():
    rs, bs = [], []
    for name in DFL_VAL + MET_VAL:
        m, lab = load(name)
        rng = np.random.default_rng(303)
        dm = degrade(m, lab, rng, sample_params(rng, fixed))
        X, _ = features(dm); Xs, _ = features(dm, swap=True)
        ok = np.isfinite(X).any(1); pd_ = np.full(len(X), .5); ph = np.full(len(X), .5)
        pd_[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
        ph[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
        pd_, ph = stage2(pd_, ph, m['period'])
        r = score(lab, decode_blocks(emissions(pd_, ph), m['period'], prm), m['period'])
        b = score(lab, organizer_baseline(dm, 50), m['period'])
        rs.append(r['spell_f1_mean']); bs.append(b['spell_f1_mean'])
        vis = np.isfinite(dm['ball']).all(1)
        print(lev, name, 'ball vis %.2f' % vis[np.isin(lab, ('H', 'A', 'D'))].mean(), 'v2 %.4f' % r['spell_f1_mean'], 'base50 %.4f' % b['spell_f1_mean'], flush=True)
    out[lev] = {'v2': float(np.mean(rs)), 'baseline50': float(np.mean(bs))}
    print('LEVEL', lev, out[lev], flush=True)
json.dump(out, open(OUT, 'w'), indent=1)
