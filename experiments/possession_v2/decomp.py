"""Reporting only: where does v2.1 lose spellF1? v2.1 4-match validation models + frozen decoder on the four
validation matches, corruption seed 101, with parts of the corruption switched off (same random draws)."""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.features import features
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
C = '/home/claude/work/cache/'
DEC = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
(md, mh), (sd, sh) = [pickle.load(open(C + f, 'rb')) for f in ('models_v2.pkl', 'stack_v2.pkl')]
COND = {
    'clean': None,
    'v2.1 corruption': {},
    'no ball missing': {'ball_miss_alive': 1e-6, 'ball_miss_dead_extra': 0.0, 'ball_out_miss': 0.0,
                        'ball_crowd_logit': 0.0, 'ball_fast_logit': 0.0},
    'no position noise': {'ball_sigma_m': 0.0, 'player_sigma_m': 0.0},
    'ball missing only': {'ball_sigma_m': 0.0, 'player_sigma_m': 0.0, 'ball_fp_rate': 0.0, 'player_miss': 0.0,
                          'team_flip_rate': 0.0},
}


def probs(m):
    X, _ = features(m); Xs, _ = features(m, swap=True)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    del X, Xs
    S = [stack_features(p1, q1, m['period'], swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(p1), .5); q2 = np.full(len(p1), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    return np.round(p2, 6), np.round(q2, 6)


out = {}
for name in ('J03WN1', 'J03WR9', 'MET1', 'MET2'):
    m, lab = load(name)
    for cond, fixed in COND.items():
        if fixed is None:
            dm = m
        else:
            rng = np.random.default_rng(101)
            dm = degrade(m, lab, rng, sample_params(rng, fixed=fixed))
        r = score(lab, decode_blocks(emissions(*probs(dm)), m['period'], DEC), m['period'])
        out.setdefault(cond, {})[name] = (r['spell_f1_mean'], r['macro_f1'])
        print(name, cond, round(r['spell_f1_mean'], 4), round(r['macro_f1'], 4), flush=True)
summary = {c: {'spell_f1': round(float(np.mean([v[0] for v in d.values()])), 4),
               'macro_f1': round(float(np.mean([v[1] for v in d.values()])), 4)} for c, d in out.items()}
print('SUMMARY', json.dumps(summary), flush=True)
json.dump({'summary': summary, 'per_match': out, 'note': 'reporting only; validation matches; not a competition score'},
          open('/home/claude/work/decomp.json', 'w'), indent=1)
