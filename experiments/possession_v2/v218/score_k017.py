"""K017 rehearsal: the delivered file of the v2.16 chain on the synthetic bundle Ak (bundle A of K003 + the invented Smart
Tagging file of K011) against the file-order proxy labels of the bundle (truth_stable.npz, K005), next to the delivered
file of the v2.15 chain of 15 November on the same bundle, and where the two files differ.
Reporting only: a wiring and size check on synthetic files, not accuracy on the provided match and not a selection input.
Usage: score_k017.py OUT_JSON"""
import json, sys, hashlib
from pathlib import Path
import numpy as np
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, str(P))
from score_prova import report, read
files = {'possession-v2.16 chain, bundle Ak (15 Nov)': P / 'Ak' / 'private_v216' / 'teslim' / 'Prova.csv',
         'possession-v2.15 chain, bundle Ak (15 Nov)': P / 'Ak' / 'private_v215' / 'teslim' / 'Prova.csv'}
out = {'labels': 'truth_stable.npz of bundle A (file-order Metrica proxy labels, K005); the invented stretch before the second-half kick-off is D',
       'environment': {'python': sys.version.split()[0], 'numpy': np.__version__}}
pieces = ('game 3 first half', 'game 2 piece 1', 'game 3 second half', 'game 2 piece 2')
for name, f in files.items():
    r = report(P / 'A' / 'truth_stable.npz', f)
    out[name] = {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'graded windows': r['graded windows (as the organisers grade)'],
                 'labels on frames 110808-113741 (before the bundle kick-off)': r['lead-in labels'], 'outside graded windows': r['outside graded windows'],
                 'pieces of the bundle (spellF1, macroF1)': {k: [r[k]['spell_f1_mean'], r[k]['macro_f1']] for k in pieces}}
n, k = (read(f) for f in files.values())
d = np.flatnonzero(n != k)
graded = np.zeros(len(n), bool); graded[11185:90652] = True; graded[110808:190198] = True
play = np.zeros(len(n), bool); play[11185:90652] = True; play[113742:190198] = True
tag = 113682
out['v2.16 file against v2.15 file'] = {
    'frames_that_differ': int(len(d)), 'share_of_graded_frames': round(float(len(d) / graded.sum()), 4),
    'all_inside_graded_windows': bool(graded[d].all()), 'all_from_the_kick_offs_on': bool(play[d].all()),
    'none_before_the_synthetic_tag_of_the_second_half': bool(not ((d >= 110808) & (d < tag)).any()),
    'changes': {f'{a}->{b}': int(((k[d] == a) & (n[d] == b)).sum()) for a in 'HAD' for b in 'HAD' if a != b},
    'v2.16_labels_before_tag': {x: int((n[110808:tag] == x).sum()) for x in 'HADX'}}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
