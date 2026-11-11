"""Reporting only: sensitivity of frozen-recipe v2.1 (4-match validation models) to tactical ball
POSITION errors beyond the training range (degrade ball_sigma 0.05-0.3 m): extra i.i.d. noise,
slowly varying bias, and height-projection errors on fast (aerial-like) balls."""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, DFL_VAL, MET_VAL
from exp_v4 import pipeline  # noqa: E402  (module guarded below)


def smooth_noise(n, sd, tau, rng):
    a = np.exp(-1.0 / tau)
    e = rng.normal(0, sd * np.sqrt(1 - a * a), (n, 2))
    out = np.zeros((n, 2)); out[0] = rng.normal(0, sd, 2)
    for t in range(1, n):
        out[t] = a * out[t - 1] + e[t]
    return out


def aerial(ball, fps, rng, scale):
    """Fast balls (> 15 m/s over 0.2 s) are displaced away from a camera at the halfway line, as a
    ground projection of a ball in the air would be (height ~ U(1, 4) m per pass)."""
    n = len(ball)
    k = max(1, int(0.2 * fps))
    v = np.full(n, np.nan)
    v[k:] = np.linalg.norm(ball[k:] - ball[:-k], axis=1) * fps / k
    fast = np.nan_to_num(v) > 15
    out = ball.copy()
    cam = np.array([52.5, -40.0]); hc = 18.0
    edges = np.flatnonzero(np.diff(np.r_[0, fast.astype(np.int8), 0]))
    for s, e in zip(edges[::2], edges[1::2]):
        h = rng.uniform(1, 4) * scale * np.sin(np.linspace(0, np.pi, e - s))
        vec = ball[s:e] - cam
        out[s:e] = ball[s:e] + vec * (h / (hc - h))[:, None]
    return out


if __name__ == '__main__':
    VARIANTS = ['base', 'iid_0.5', 'iid_1.0', 'bias_1.0', 'aerial']
    res = {v: [] for v in VARIANTS}
    for name in DFL_VAL + MET_VAL:
        m, lab = load(name)
        for seed in (101,):
            dm = degraded(name, seed)
            for v in VARIANTS:
                rng = np.random.default_rng(99)
                b = dm['ball'].copy()
                if v.startswith('iid'):
                    b = b + rng.normal(0, float(v.split('_')[1]), b.shape)
                elif v == 'bias_1.0':
                    b = b + smooth_noise(len(b), 1.0, 5 * m['fps'], rng)
                elif v == 'aerial':
                    b = aerial(b, m['fps'], rng, 1.0)
                r = pipeline(dict(dm, ball=b), lab, m['period'])
                res[v].append(r['spell_f1_mean'])
                print(v, name, seed, 'spell %.4f' % r['spell_f1_mean'], flush=True)
    print('SUMMARY', json.dumps({v: round(float(np.mean(x)), 4) for v, x in res.items()}), flush=True)
    json.dump(res, open('/home/claude/work/ballnoise.json', 'w'))
