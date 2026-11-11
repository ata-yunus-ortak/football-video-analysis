"""Score a rehearsal CSV against the external labels of the rehearsal bundle (reporting only)."""
import sys, json, csv
import numpy as np
sys.path.insert(0, '/home/claude/sc')
from possession.evaluate import score
N = 199319
def read(path):
    with open(path, newline='') as fh:
        r = csv.reader(fh); next(r)
        return np.array([row[1] for row in r])
def report(truth_npz, pred_csv):
    z = np.load(truth_npz)
    lab = z['lab']
    graded = np.zeros(N, np.int8); graded[11185:90652] = 1; graded[110808:190198] = 2
    pred = read(pred_csv)
    out = {}
    r = score(lab, pred, graded)
    out['graded windows (as the organisers grade)'] = {k: round(float(r[k]), 4) for k in ('spell_f1_mean', 'macro_f1', 'f1_H', 'f1_A', 'f1_D', 'team_acc_both_alive')} | {'gt_spells': int(r['n_gt_spells']), 'pred_spells': int(r['n_pred_spells'])}
    play = z['period_play']
    r = score(lab, pred, play)
    out['play only (kick-off to end of each half)'] = {k: round(float(r[k]), 4) for k in ('spell_f1_mean', 'macro_f1')}
    lead = pred[110808:113742]
    out['lead-in labels'] = {k: int((lead == k).sum()) for k in 'HADX'}
    out['outside graded windows'] = {k: int((pred[graded == 0] == k).sum()) for k in 'HADX'}
    for name, (a, b) in {'game 3 first half': (11185, 11185 + 69661), 'game 2 piece 1': (11185 + 69661, 90652),
                         'game 3 second half': (113742, 113742 + 74100), 'game 2 piece 2': (113742 + 74100, 190198)}.items():
        per = np.zeros(N, np.int8); per[a:b] = 1
        r = score(lab, pred, per)
        out[name] = {k: round(float(r[k]), 4) for k in ('spell_f1_mean', 'macro_f1')}
    return out
if __name__ == '__main__':
    print(json.dumps(report(sys.argv[1], sys.argv[2]), indent=1))
