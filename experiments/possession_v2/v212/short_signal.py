"""v2.12 development, mechanism check (reporting only): do the stage-1 probabilities show short possessions more?

For every held-out development copy of lomo_stage1.py (four DFL training matches x seeds 1, 2, 3 and the extra
seeds 9001-9008), and for both feature sets, takes the cached stage-1 probabilities (cache/p1_*.npz) and the DFL
labels and reports, for ground-truth possession spells shorter than 2 s and for spells of at least 2 s:
the mean over spells of the spell-averaged P(spell's team | alive) and the share of spells whose average is above
0.5 / 0.8 (same quantity as possession-k007-diagnosis.json "mean_p_team", here on development copies), plus the
mean P(dead) inside the spells. Development data only; no model is trained or selected here.
Usage: /usr/bin/python3 /home/claude/work/v212/short_signal.py  -> short_signal.json
"""
import sys, json
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
from possession.features import play_blocks

out = {}
acc = {f: {'short': [], 'long': [], 'short_dead': [], 'long_dead': []} for f in ('base', 'touch')}
for held in C.MATCHES:
    m, lab = C.load(held)
    spells = []
    for a, b in play_blocks(m['period']):
        w = lab[a:b]
        br = np.flatnonzero(w[1:] != w[:-1]) + 1
        bd = np.r_[0, br, len(w)]
        spells += [(a + int(bd[i]), a + int(bd[i + 1]), w[bd[i]]) for i in range(len(bd) - 1) if w[bd[i]] in 'HA']
    for fset in ('base', 'touch'):
        for s in C.held_seeds(held):
            z = np.load(f'{C.VC}p1_{held}_{fset}_s{s}.npz')
            ph, pd_ = z['ph'], z['pd']
            for a, b, k in spells:
                pt = float(np.mean(ph[a:b] if k == 'H' else 1.0 - ph[a:b]))
                key = 'short' if b - a < 50 else 'long'
                acc[fset][key].append(pt); acc[fset][key + '_dead'].append(float(np.mean(pd_[a:b])))
for fset, d in acc.items():
    out[fset] = {}
    for key in ('short', 'long'):
        v = np.array(d[key])
        out[fset][key] = {'n_spells': int(len(v)), 'mean_p_team': round(float(v.mean()), 4),
                          'share_above_0.5': round(float((v > 0.5).mean()), 4), 'share_above_0.8': round(float((v > 0.8).mean()), 4),
                          'mean_p_dead': round(float(np.mean(d[key + '_dead'])), 4)}
out['note'] = 'stage-1 probabilities of the leave-one-match-out models on held-out development copies; reporting only'
out['provided_fixture_used'] = False
json.dump(out, open(C.ROOT + 'short_signal.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
