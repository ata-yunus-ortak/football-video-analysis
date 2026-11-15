"""Reporting only (K007 diagnosis, part 3): is the ball visible in the corrupted input during the short possessions
the decoder misses? Same 8 used validation copies (regenerated with the same corruption seeds); no selection."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded
from possession.decode import emissions, decode_blocks
from possession.evaluate import _with_separators, SEP
from possession.features import play_blocks
from possession import official_metrics as pm
from err_spells import DEC, C, THR
acc = {k: [] for k in ('missed_short', 'found_short', 'missed_long', 'found_long', 'alive_all')}
for name in ('J03WN1', 'J03WR9', 'MET1', 'MET2'):
    for seed in (101, 102):
        m, lab = load(name); per = m['period']
        vis = np.isfinite(degraded(name, seed)['ball'][:, 0])
        z = np.load(f'{C}probs_sys_v21_{name}_{seed}_f2.npz')
        pred = decode_blocks(emissions(z['pd'], z['ph']), per, DEC)
        v = np.concatenate([np.r_[vis[a:b].astype(float), np.full(SEP, np.nan)] for a, b in play_blocks(per)])
        g, p = pm.label_codes(_with_separators(lab, per)), pm.label_codes(_with_separators(pred, per))
        runs = pm.valid_runs(g)
        gs, ps = pm.possession_spells(g, runs), pm.possession_spells(p, runs)
        nthr = sum(pm.matched_gt_flags(pm.spell_overlaps(gs, ps), len(gs), t).astype(int) for t in THR)
        for (a, b, k), n in zip(gs, nthr):
            key = ('missed' if n == 0 else 'found') + ('_short' if b - a < 50 else '_long')
            acc[key].append(float(np.nanmean(v[a:b])))
            acc['alive_all'].append(float(np.nanmean(v[a:b])))
out = {k: {'n': len(x), 'mean_ball_visible_share': round(float(np.mean(x)), 3),
           'share_of_spells_with_ball_visible_half_the_time_or_more': round(float(np.mean(np.array(x) >= 0.5)), 3)} for k, x in acc.items()}
print(json.dumps(out, indent=1)); json.dump(out, open('/home/claude/work/err_ballvis.json', 'w'), indent=1)
