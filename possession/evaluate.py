"""Score predictions on external fixtures with the organisers' own metric code."""
import numpy as np
from . import official_metrics as pm

SEP = 50  # X frames inserted between play blocks so no spell/transition spans halftime


def _with_separators(labels, period):
    from .features import play_blocks
    parts = []
    for a, b in play_blocks(period):
        parts.append(np.asarray(labels[a:b]))
        parts.append(np.full(SEP, 'X'))
    return np.concatenate(parts)


def score(gt, pred, period):
    g = pm.label_codes(_with_separators(gt, period))
    p = pm.label_codes(_with_separators(pred, period))
    r = pm.evaluate(g, p)
    keep = ('spell_f1_mean', 'macro_f1', 'alive_dead_f1', 'team_acc_both_alive', 'n_gt_spells',
            'n_pred_spells', 'accuracy')
    out = {k: r[k] for k in keep}
    for k in ('H', 'A', 'D'):
        out[f'f1_{k}'] = r['per_class'][k]['f1']
    for tol, t in r['transitions'].items():
        out[f'trans_f1_{tol}'] = t['f1']
        out[f'trans_p_{tol}'] = t['precision']
        out[f'trans_r_{tol}'] = t['recall']
    return out
