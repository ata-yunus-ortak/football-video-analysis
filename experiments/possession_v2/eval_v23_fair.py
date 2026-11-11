"""Reporting only (not part of the registered rule): how much of the v2.3 - v2.1 difference comes from
re-selecting the decoder on the 24 copies? v2.1 probabilities (cached by eval_v23.py) decoded with the best
of the same 54-point grid on the same 24 copies."""
import sys, json, itertools, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from eval_v23 import COPIES, C
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
cases = []
for name, seed, tag21, tag23, kind in COPIES:
    m, lab = load(name)
    z = np.load(f'{C}probs_sys_v21_{name}_{seed}{tag21}.npz')
    cases.append((kind, m['period'], lab, (z['pd'], z['ph'])))
grid = []
for sw, cost, bias in itertools.product([2, 3, 4, 5, 6, 8], [30, 60, 120], [-0.3, 0.0, 0.3]):
    dec = {'switch': sw, 'out_cost': cost, 'in_cost': cost, 'bias_dead': bias}
    v = [(k, score(lab, decode_blocks(emissions(*P), per, dec), per)['spell_f1_mean']) for k, per, lab, P in cases]
    grid.append((float(np.mean([x for _, x in v])), dec,
                 {kind: float(np.mean([x for k, x in v if k == kind])) for kind in ('orig', 'ext_ball', 'ext_players')}))
grid.sort(key=lambda g: -g[0])
out = {'v2_1_best_decoder_on_24': grid[0][1], 'all24': grid[0][0], **grid[0][2]}
print(json.dumps(out, indent=1))
json.dump(out, open('/home/claude/work/eval_v23_fair.json', 'w'), indent=1)
