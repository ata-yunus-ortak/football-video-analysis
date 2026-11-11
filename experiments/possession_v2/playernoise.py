"""Reporting only: sensitivity of a system to extra i.i.d. PLAYER position noise (0.5 m).
Usage: playernoise.py models.pkl stack.pkl decoder_json out.json"""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, DFL_VAL, MET_VAL
from possession.features import features
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
md, mh = pickle.load(open(sys.argv[1], 'rb')); sd, sh = pickle.load(open(sys.argv[2], 'rb')); DEC = json.loads(sys.argv[3])

def pipe(dm, lab, per):
    X, _ = features(dm); Xs, _ = features(dm, swap=True)
    ok = np.isfinite(X).any(1); p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    S = [stack_features(p1, q1, per, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0]); p2 = np.full(len(X), .5); q2 = np.full(len(X), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    return score(lab, decode_blocks(emissions(np.round(p2, 6), np.round(q2, 6)), per, DEC), per)['spell_f1_mean']

res = {'base': [], 'players_iid_0.5': []}
for name in DFL_VAL + MET_VAL:
    m, lab = load(name); dm = degraded(name, 101)
    rng = np.random.default_rng(77)
    res['base'].append(pipe(dm, lab, m['period']))
    res['players_iid_0.5'].append(pipe(dict(dm, players=dm['players'] + rng.normal(0, 0.5, dm['players'].shape).astype(np.float32)), lab, m['period']))
    print(name, {k: round(v[-1], 4) for k, v in res.items()}, flush=True)
print('SUMMARY', json.dumps({k: round(float(np.mean(v)), 4) for k, v in res.items()}), flush=True)
json.dump(res, open(sys.argv[4], 'w'))
