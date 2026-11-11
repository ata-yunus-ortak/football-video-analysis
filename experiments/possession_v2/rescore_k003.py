"""K005: the rehearsal bundles of K003 were built under Python 3.10 / pandas 2.1.4, where the unstable default sort in
metrica_labels.labels_from_events orders tied events differently from the file order and drops about half of the
dead-ball intervals of the Metrica proxy labels. This script writes the proxy labels in file order (stable sort; the
labels every validation used) as truth_stable.npz / gt_stable for bundles A and B and re-scores the stored outputs.
Usage: rescore_k003.py OUT_JSON"""
import hashlib, json, subprocess, sys, shutil
from pathlib import Path
import numpy as np
import pandas as pd
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, str(P))
import prova_build as pb
from score_prova import report, read, N
from possession.evaluate import score

orig = pd.DataFrame.sort_values
pd.DataFrame.sort_values = lambda self, by, **kw: orig(self, by, **dict(kw, kind='stable'))     # ties keep the file order
_, lab, src = pb.assemble(np.random.default_rng(0))
pd.DataFrame.sort_values = orig
g1 = np.load(P / 'G1' / 'truth.npz')['lab']
assert np.array_equal(lab, g1), 'the labels of bundle G1 (built under Python 3.13) are the file-order labels'
graded = pb.graded_mask()
out = {'labels': {'file_order_sha256': hashlib.sha256(''.join(lab.tolist()).encode()).hexdigest(),
                  'file_order_counts_on_graded_frames': {k: int((lab[graded] == k).sum()) for k in 'HADX'}}}
for b in ('A', 'B'):
    z = np.load(P / b / 'truth.npz')
    old = z['lab']
    np.savez_compressed(P / b / 'truth_stable.npz', **{k: (lab if k == 'lab' else z[k]) for k in z.files})
    (P / b / 'gt_stable').mkdir(exist_ok=True)
    with open(P / b / 'gt_stable' / 'PROVA_possession_gt.csv', 'w', newline='\n') as fh:
        fh.write('frame,label\n'); fh.writelines(f'{i},{l}\n' for i, l in enumerate(np.where(graded, lab, 'X').tolist()))
    rec = {'labels_used_in_K003': {'counts_on_graded_frames': {k: int((old[graded] == k).sum()) for k in 'HADX'},
                                   'frames_that_differ_from_file_order': int((old != lab).sum())}}
    files = {'delivered file of the K003 chain (possession-v2.9)': P / b / 'private' / 'teslim' / 'Prova.csv',
             'in-memory reference (r1)': P / b / 'r1.csv', 'tactical camera only (r3, possession.run25c)': P / b / 'r3' / 'submission.csv'}
    if b == 'A':
        files['reserve chain of K003 (possession-v2.9g)'] = P / 'A' / 'private_g' / 'teslim' / 'Prova.csv'
    for name, f in files.items():
        new = report(P / b / 'truth_stable.npz', f)['graded windows (as the organisers grade)']
        was = report(P / b / 'truth.npz', f)['graded windows (as the organisers grade)']
        rec[name] = {'as_recorded_in_K003': {k: was[k] for k in ('spell_f1_mean', 'macro_f1', 'f1_D', 'gt_spells', 'pred_spells')},
                     'against_file_order_labels': {k: new[k] for k in ('spell_f1_mean', 'macro_f1', 'f1_H', 'f1_A', 'f1_D', 'gt_spells', 'pred_spells')}}
    # organisers' scorer
    res, o = P / b / 'orgscore_stable' / 'results', P / b / 'orgscore_stable' / 'out'
    shutil.rmtree(P / b / 'orgscore_stable', ignore_errors=True); res.mkdir(parents=True)
    shutil.copy(P / b / 'private' / 'teslim' / 'Prova.csv', res / 'Prova.csv')
    r = subprocess.run([sys.executable, 'evaluation/run_evaluation.py', '--gt', str(P / b / 'gt_stable' / 'PROVA_possession_gt.csv'), '--results', str(res),
                        '--out', str(o), '--bootstrap', '0'], cwd='/home/claude/org/repo', capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-800:]
    rep = json.loads((o / 'reports' / 'Prova.json').read_text())
    rec['organisers_scorer_against_file_order_labels'] = {k: rep[k] for k in ('spell_f1_mean', 'macro_f1', 'n_graded', 'n_gt_spells', 'n_pred_spells')} if 'spell_f1_mean' in rep else {k: rep.get(k) for k in ('macro_f1', 'n_graded', 'n_gt_spells')}
    rec['organisers_scoreboard_line'] = (o / 'scoreboard.csv').read_text().splitlines()[1].split(',')[:6]
    out[f'bundle {b}'] = rec
# negative controls on bundle A
pred = read(P / 'A' / 'private' / 'teslim' / 'Prova.csv')
per = np.zeros(N, np.int8); per[11185:90652] = 1; per[110808:190198] = 2
s = lambda p: {k: round(float(v), 4) for k, v in zip(('spell_f1', 'macro_f1'), (lambda r: (r['spell_f1_mean'], r['macro_f1']))(score(lab, p, per)))}
sw = pred.copy(); sw[pred == 'H'] = 'A'; sw[pred == 'A'] = 'H'
out['negative_controls_bundle_A_against_file_order_labels'] = dict({'as delivered': s(pred), 'teams exchanged': s(sw)},
                                                                   **{f'rows shifted by {k:+d} frames': s(np.roll(pred, k)) for k in (1, 25, 125, -25, -125)})
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1)[:3500])
