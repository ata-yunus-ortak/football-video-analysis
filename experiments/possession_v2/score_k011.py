"""K011 rehearsal: the delivered file of the v2.11k chain on the synthetic bundle Ak (bundle A of K003 + a synthetic Smart
Tagging file, prova_tagging.py) against the file-order proxy labels of the bundle (truth_stable.npz, K005), next to the
delivered files of the v2.11 and v2.11g chains of 11 November on bundle A. Also: where the v2.11k file differs from the
v2.11g file. Reporting only; wiring and size check, not accuracy on the provided match. Usage: score_k011.py OUT_JSON"""
import json, sys, hashlib
from pathlib import Path
import numpy as np
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, str(P))
from score_prova import report, read
files = {'possession-v2.11k chain, bundle Ak (13 Nov)': P / 'Ak' / 'private' / 'teslim' / 'Prova.csv',
         'possession-v2.11g chain, bundle A (11 Nov)': P / 'A' / 'private_v211g' / 'teslim' / 'Prova.csv',
         'possession-v2.11 chain, bundle A (11 Nov; second-half play from the published kick-off frame)': P / 'A' / 'private_v211' / 'teslim' / 'Prova.csv'}
out = {'labels': 'truth_stable.npz of bundle A (file-order Metrica proxy labels, K005); the invented stretch before the second-half kick-off is D',
       'environment': {'python': sys.version.split()[0], 'numpy': np.__version__}}
for name, f in files.items():
    r = report(P / 'A' / 'truth_stable.npz', f)
    out[name] = {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'graded windows': r['graded windows (as the organisers grade)'],
                 'labels on frames 110808-113741 (before the bundle kick-off)': r['lead-in labels'], 'outside graded windows': r['outside graded windows']}
k, g = read(files['possession-v2.11k chain, bundle Ak (13 Nov)']), read(files['possession-v2.11g chain, bundle A (11 Nov)'])
d = np.flatnonzero(k != g)
tag = 113682
out['v2.11k file against v2.11g file'] = {'frames_that_differ': int(len(d)), 'first': int(d.min()) if len(d) else None, 'last': int(d.max()) if len(d) else None,
                                          'all_inside_110808_to_tag_minus_1': bool(len(d) == 0 or (d.min() >= 110808 and d.max() < tag)),
                                          'all_changed_to_D': bool((k[d] == 'D').all()), 'synthetic_tag_start_frame': tag,
                                          'v2.11k_labels_before_tag': {x: int((k[110808:tag] == x).sum()) for x in 'HADX'},
                                          'v2.11k_labels_tag_to_kickoff': {x: int((k[tag:113742] == x).sum()) for x in 'HADX'}}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
