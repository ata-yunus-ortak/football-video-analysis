"""Upside check (reporting only): how much would v2.1 gain if a second, perfectly aligned camera
filled part of the tactical ball gaps? Oracle-aligned 'broadcast' ball = true ball + noise, available
in bursts covering a fraction of frames; fills only frames where the degraded tactical ball is missing."""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, DFL_VAL, MET_VAL
from possession.features import features
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
C = '/home/claude/work/cache/'
md, mh = pickle.load(open(C + 'models_v2.pkl', 'rb'))
sd, sh = pickle.load(open(C + 'stack_v2.pkl', 'rb'))
DEC = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}


def burst_mask(n, frac, mean_run, rng):
    """Two-state Markov availability with stationary fraction frac and mean 'on' run mean_run frames."""
    p_off = 1.0 / mean_run
    p_on = p_off * frac / (1 - frac)
    out = np.zeros(n, bool); s = rng.random() < frac
    flips = rng.random(n)
    for t in range(n):
        out[t] = s
        s = (flips[t] >= p_off) if s else (flips[t] < p_on)
    return out


def run(m_deg, lab, period):
    X, _ = features(m_deg); Xs, _ = features(m_deg, swap=True)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    S = [stack_features(p1, q1, period, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(X), .5); q2 = np.full(len(X), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    return score(lab, decode_blocks(emissions(p2, q2), period, DEC), period)['spell_f1_mean']


res = {}
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    for seed in (101, 102):
        dm = degraded(name, seed)
        miss = ~np.isfinite(dm['ball']).all(1) & np.isfinite(m['ball']).all(1) & np.isin(lab, ('H', 'A'))
        for frac in (0.0, 0.3, 0.5):
            rng = np.random.default_rng([seed, int(frac * 10)])
            avail = burst_mask(len(lab), frac, 50, rng) if frac > 0 else np.zeros(len(lab), bool)
            fill = miss & avail
            d2 = dict(dm); b = dm['ball'].copy()
            b[fill] = m['ball'][fill] + rng.normal(0, 1.0, (fill.sum(), 2))
            d2['ball'] = b
            vis_alive = np.isfinite(b[np.isin(lab, ('H', 'A'))]).all(1).mean()
            s = run(d2, lab, m['period'])
            res.setdefault(frac, []).append(s)
            print(name, seed, 'frac', frac, 'alive-ball visible %.3f' % vis_alive, 'spell %.4f' % s, flush=True)
print('SUMMARY', {k: round(float(np.mean(v)), 4) for k, v in res.items()}, flush=True)
json.dump({str(k): v for k, v in res.items()}, open('/home/claude/work/upside_fill.json', 'w'))
