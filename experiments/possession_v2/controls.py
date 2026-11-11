"""Negative controls for the rehearsal score: how the score of the delivered file changes when it is deliberately
mis-wired (teams exchanged, rows shifted). Reporting only."""
import sys, json
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
from possession.evaluate import score
from score_prova import read, N
z = np.load(sys.argv[1]); lab = z['lab']; pred = read(sys.argv[2])
graded = np.zeros(N, np.int8); graded[11185:90652] = 1; graded[110808:190198] = 2
def s(p):
    r = score(lab, p, graded); return {'spell_f1': round(float(r['spell_f1_mean']), 4), 'macro_f1': round(float(r['macro_f1']), 4)}
out = {'as delivered': s(pred)}
sw = pred.copy(); sw[pred == 'H'] = 'A'; sw[pred == 'A'] = 'H'
out['teams exchanged'] = s(sw)
for k in (1, 25, 125, -25, -125):
    out[f'rows shifted by {k:+d} frames'] = s(np.roll(pred, k))
print(json.dumps(out, indent=1))
