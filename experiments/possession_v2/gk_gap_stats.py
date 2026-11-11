"""Development (training matches only, no model): in far frames, how much nearer to the goal is the nearest tracked
player than the second nearest? For true goalkeepers (full view) and for the outfield pieces that possession.keeper
moves falsely when a camera window hides the far goalkeeper. Usage: gap_stats.py MATCH [...]"""
import sys, json, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import keeper as K
from possession.epts_export import tracklets, pack
from possession.features import play_blocks
from exp_v210 import true_goalkeepers, SLOT46
from camera_view import apply_view

for name in sys.argv[1:]:
    m, lab = load(name); gk = true_goalkeepers(m); S = m['players'].shape[1]
    seed = 6000 + sum(map(ord, name)) % 1000
    rng = np.random.default_rng(seed); dm0 = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
    n = len(dm0['ball']); L, W = m['pitch']
    true = np.r_[m['team'], 1 - dm0['team'][S:]]
    for hw in (None, 42.0, 35.0):
        dm = dm0 if hw is None else apply_view(dm0, m, hw)[0]
        wide = np.asarray(dm['players'])
        P, _ = pack(n, tracklets(wide, dm['team']), SLOT46)
        for h, (a, b) in enumerate(play_blocks(m['period'])):
            Q = P[a:b].astype(np.float64); fin = np.isfinite(Q).all(2); cx = np.nanmedian(Q[..., 0], 1)
            found, facts = K._block(Q, SLOT46, L, W)
            for side, defending in (('left', facts['left_team']), ('right', 1 - facts['left_team'])):
                far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= K.FAR_M
                d = np.where(fin, np.hypot(Q[..., 0] if side == 'left' else L - Q[..., 0], Q[..., 1] - W / 2), np.inf)
                order = np.sort(d, 1)
                gap = order[:, 1] - order[:, 0]
                arg = np.argmin(d, 1)
                if hw is None:
                    # true goalkeeper of this goal: frames in which the nearest player is the goalkeeper
                    g = sorted(gk[defending])
                    isg = np.zeros(len(Q), bool)
                    for j in g:
                        gx = wide[a:b, j]
                        isg |= (Q[np.arange(len(Q)), arg, 0] == gx[:, 0]) & (Q[np.arange(len(Q)), arg, 1] == gx[:, 1])
                    sel = far & isg & np.isfinite(gap)
                    print(json.dumps({'match': name, 'half': h + 1, 'side': side, 'kind': 'true goalkeeper nearest, far frames', 'frames': int(sel.sum()),
                                      'gap_quantiles_1_5_10_25_50': [round(float(q), 1) for q in np.quantile(gap[sel], [0.01, 0.05, 0.1, 0.25, 0.5])],
                                      'share_gap_ge_6_8_10_12': [round(float((gap[sel] >= g_).mean()), 3) for g_ in (6, 8, 10, 12)],
                                      'dist_quantiles_50_90_99': [round(float(q), 1) for q in np.quantile(order[sel, 0], [0.5, 0.9, 0.99])]}), flush=True)
            for slot, s, e, t in found:
                f = np.flatnonzero(fin[s:e, slot]); r = a + s + int(f[len(f) // 2])
                c = int(np.flatnonzero((wide[r, :, 0] == P[r, slot, 0]) & (wide[r, :, 1] == P[r, slot, 1]))[0])
                if true[c] == t:
                    continue
                side = 'left' if facts['left_team'] == t else 'right'
                far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= K.FAR_M
                d = np.where(fin, np.hypot(Q[..., 0] if side == 'left' else L - Q[..., 0], Q[..., 1] - W / 2), np.inf)
                order = np.sort(d, 1); gap = order[:, 1] - order[:, 0]
                near = np.argmin(d[s:e], 1) == slot
                sel = far[s:e] & fin[s:e, slot] & near
                gg = gap[s:e][sel]
                print(json.dumps({'match': name, 'view': hw, 'half': h + 1, 'kind': 'FALSE move', 'len': e - s, 'far_frames': int((far[s:e] & fin[s:e, slot]).sum()), 'nearest_far': int(sel.sum()),
                                  'gap_quantiles_10_50_90': [round(float(q), 1) for q in np.quantile(gg, [0.1, 0.5, 0.9])] if len(gg) else None,
                                  'share_gap_ge_6_8_10_12': [round(float((gg >= g_).mean()), 3) for g_ in (6, 8, 10, 12)] if len(gg) else None,
                                  'dist_quantiles_10_50_90': [round(float(q), 1) for q in np.quantile(d[s:e, slot][fin[s:e, slot]], [0.1, 0.5, 0.9])]}), flush=True)
