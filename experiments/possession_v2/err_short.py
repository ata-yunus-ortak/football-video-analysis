"""Reporting only (K007 diagnosis, part 2): do the cached v2.1 probabilities see the short possessions the decoder misses?
For missed ground-truth spells under 2 s: mean P(team of the spell | alive) and mean P(dead) inside them, compared with
equally long windows inside long spells of the other team (negatives). Same 8 used validation copies; no selection."""
import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.decode import emissions, decode_blocks
from possession.evaluate import _with_separators, SEP
from possession.features import play_blocks
from possession import official_metrics as pm
from err_spells import DEC, C, THR, greedy_pairs
rng = np.random.default_rng(0)
H, A = [int(c) for c in pm.label_codes(np.array(['H', 'A']))]
pos, neg = [], []
for name in ('J03WN1', 'J03WR9', 'MET1', 'MET2'):
    for seed in (101, 102):
        m, lab = load(name); per = m['period']
        z = np.load(f'{C}probs_sys_v21_{name}_{seed}_f2.npz')
        pred = decode_blocks(emissions(z['pd'], z['ph']), per, DEC)
        # probabilities laid out like the separated label arrays
        parts_h, parts_d = [], []
        for a, b in play_blocks(per):
            parts_h += [z['ph'][a:b], np.full(SEP, np.nan)]; parts_d += [z['pd'][a:b], np.full(SEP, np.nan)]
        ph, pdd = np.concatenate(parts_h), np.concatenate(parts_d)
        g, p = pm.label_codes(_with_separators(lab, per)), pm.label_codes(_with_separators(pred, per))
        runs = pm.valid_runs(g)
        gs, ps = pm.possession_spells(g, runs), pm.possession_spells(p, runs)
        ov = pm.spell_overlaps(gs, ps)
        nthr = sum(pm.matched_gt_flags(ov, len(gs), t).astype(int) for t in THR)
        for (a, b, k), n in zip(gs, nthr):
            pt = ph[a:b] if k == H else 1 - ph[a:b]
            if b - a < 50 and n == 0:
                pos.append((float(np.nanmean(pt)), float(np.nanmean(pdd[a:b])), b - a, float(np.nanmax(pt))))
            if b - a >= 250:                     # long spell: windows inside it, seen from the other team
                for _ in range(2):
                    L = int(rng.integers(10, 50)); s = int(rng.integers(a + 25, b - 25 - L))
                    po = 1 - (ph[s:s + L] if k == H else 1 - ph[s:s + L])
                    neg.append((float(np.nanmean(po)), float(np.nanmean(pdd[s:s + L])), L, float(np.nanmax(po))))
pos, neg = np.array(pos), np.array(neg)
out = {'n_missed_short': len(pos), 'n_negative_windows': len(neg)}
for col, nm in ((0, 'mean_p_team'), (3, 'max_p_team')):
    out[nm] = {f'>{t}': {'missed_short_spells': round(float(np.mean(pos[:, col] > t)), 3), 'windows_in_other_team_spells': round(float(np.mean(neg[:, col] > t)), 3)}
               for t in (0.5, 0.6, 0.7, 0.8, 0.9)}
out['mean_p_dead_inside'] = {'missed_short_spells': round(float(np.mean(pos[:, 1])), 3), 'negative_windows': round(float(np.mean(neg[:, 1])), 3)}
print(json.dumps(out, indent=1))
json.dump(out, open('/home/claude/work/err_short.json', 'w'), indent=1)
