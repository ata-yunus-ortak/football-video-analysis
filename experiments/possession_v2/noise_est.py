"""Estimator check (no labels, no possession scores): high-frequency position noise from the robust scale
of second differences, sigma_hat = 1.4826 * MAD(d2) / sqrt(6), per player slot (median over slots) and for
the ball, inside play blocks. Compared with the known i.i.d. noise added by degrade()."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.features import play_blocks


def sd_d2(xy, min_n=500):
    d2 = xy[2:] - 2 * xy[1:-1] + xy[:-2]
    v = d2[np.isfinite(d2).all(1)].ravel()
    if len(v) < min_n:
        return np.nan
    return float(1.4826 * np.median(np.abs(v - np.median(v))) / np.sqrt(6))


def estimate(match):
    blocks = list(play_blocks(match['period']))
    ball = np.concatenate([np.r_[match['ball'][a:b], np.full((1, 2), np.nan)] for a, b in blocks])
    pl = [np.concatenate([np.r_[match['players'][a:b, j], np.full((1, 2), np.nan)] for a, b in blocks])
          for j in range(match['players'].shape[1])]
    sp = [sd_d2(p) for p in pl]
    sp = [s for s in sp if np.isfinite(s)]
    return {'ball': sd_d2(ball), 'players': float(np.median(sp)) if sp else np.nan, 'slots': len(sp)}


if __name__ == '__main__':
    out = {}
    for name in ('J03WN1', 'J03WR9', 'J03WOH', 'MET1', 'MET2'):
        m, lab = load(name)
        out[name] = {'clean': estimate(m)}
        for sp_, sb in ((0.1, 0.1), (0.3, 0.3), (0.5, 0.5)):
            rng = np.random.default_rng(99)
            p = sample_params(rng, fixed={'player_sigma_m': sp_, 'ball_sigma_m': sb})
            out[name][f'p{sp_}_b{sb}'] = estimate(degrade(m, lab, rng, p))
        print(name, json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                                for k, v in out[name].items()}), flush=True)
    json.dump(out, open('/home/claude/work/noise_est.json', 'w'), indent=1)
