"""Diagnostics for the TCN side (reporting only, training matches, in-sample for every TCN weight file): how much does the
TCN-alone score depend on single components of our corruption simulator? No fusion parameter is chosen here.
Usage: diag1.py MATCH SEED VARIANT [VARIANT ...]"""
import sys, json, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v213')
import exp_v213 as E
from possession.degrade import degrade, sample_params, RANGES
from possession.features import play_blocks
from possession.noise import estimate_noise
from possession import keeper2

def boxcar(x, k):
    """NaN-aware centred moving average along time; NaN stays NaN where the centre sample is missing."""
    x = np.asarray(x, np.float64)
    ok = np.isfinite(x)
    c = np.cumsum(np.where(ok, x, 0.0), axis=0); n = np.cumsum(ok, axis=0)
    h = k // 2
    pad = lambda a: np.concatenate([np.zeros((1,) + a.shape[1:]), a], axis=0)
    c, n = pad(c), pad(n)
    T = len(x); i = np.arange(T)
    lo, hi = np.clip(i - h, 0, T), np.clip(i + h + 1, 0, T)
    s = c[hi] - c[lo]; m = n[hi] - n[lo]
    out = np.where(ok & (m > 0), s / np.maximum(m, 1), np.nan)
    return out.astype(np.float32)

VARIANTS = {
    'ours': {},
    'no_flips': {'team_flip_rate': 0.0},
    'no_dead_extra': {'ball_miss_dead_extra': 0.0},
    'low_noise': {'ball_sigma_m': 0.03, 'player_sigma_m': 0.03},
    'no_player_miss': {'player_miss': 0.0},
    'no_fp': {'ball_fp_rate': 0.0},
    'short_gaps': {'ball_miss_tau_s': 0.3},
    'clean_all': {'team_flip_rate': 0.0, 'ball_miss_dead_extra': 0.0, 'ball_sigma_m': 0.03, 'player_sigma_m': 0.03, 'ball_fp_rate': 0.0},
}

def tcn_alone(mem, m_in, per):
    out = np.full(len(per), 'D', dtype='<U1')
    for a, b in play_blocks(per):
        prob = E.tinfer.probabilities(mem, *E.tcn_arrays(m_in, a, b))
        out[a:b] = E.LETTERS[E.tdecode.decode(prob, E.tfuse.SWITCH_COST, E.tinfer.STRIDE, b - a)]
    return out

if __name__ == '__main__':
    name, seed = sys.argv[1], int(sys.argv[2])
    m, lab = E.load(name)
    per = m['period']
    mem = E.members('tcn_dfl6.npz')
    res = {}
    for v in sys.argv[3:]:
        t0 = time.time()
        smooth = None
        base = v
        if '+box' in v:
            base, k = v.split('+box'); smooth = int(k)
        if base == 'sim2':
            dm = E.sim2(m, seed); mm = dm
        elif base == 'clean':
            mm = m
        else:
            rng = np.random.default_rng(seed)
            p = sample_params(rng, ranges=RANGES)
            p.update(VARIANTS[base])
            dm = degrade(m, lab, rng, p)
            mm = E.packed(dm)
            mm, _ = keeper2.correct_goalkeepers(mm)
        nz = estimate_noise(mm)
        if smooth:
            mm = dict(mm, ball=np.concatenate([boxcar(mm['ball'][:, :2], smooth), mm['ball'][:, 2:]], 1) if mm['ball'].shape[1] > 2 else boxcar(mm['ball'], smooth),
                      players=boxcar(mm['players'], smooth))
        pred = tcn_alone(mem, mm, per)
        r = E.metrics(lab, pred, per)
        res[v] = {'spell_f1': round(r['spell_f1'], 4), 'macro_f1': round(r['macro_f1'], 4), 'pred_spells': r['n_pred_spells'], 'gt_spells': r['n_gt_spells'],
                  'ball_visible': round(float(np.isfinite(mm['ball'][:, 0])[per > 0].mean()), 3),
                  'noise': {k: round(float(x), 3) for k, x in nz.items() if isinstance(x, float)}, 's': round(time.time() - t0)}
        print(name, seed, v, json.dumps(res[v]), flush=True)
