"""Assemble possession-v2-results.json from experiment outputs (aggregate numbers only)."""
import json, sys, numpy as np
base = json.load(open('/home/claude/work/base_eval.json'))
def agg(tag):
    ks = [k for k in base if k.startswith(tag + '|')]
    dom = lambda p: [k for k in ks if k.split('|')[1].startswith(p)]
    f = lambda kk, m: float(np.mean([base[k][m] for k in kk]))
    return {'spell_f1_all': f(ks, 'spell_f1_mean'), 'spell_f1_dfl': f(dom('J03'), 'spell_f1_mean'),
            'spell_f1_metrica': f(dom('MET'), 'spell_f1_mean'), 'macro_f1_all': f(ks, 'macro_f1'),
            'n_pred_spells': f(ks, 'n_pred_spells'), 'n_gt_spells': f(ks, 'n_gt_spells')}
res = {'comparators_on_validation_copies': {t: agg(t) for t in ('baseline50', 'S001')}}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(res, indent=1))
