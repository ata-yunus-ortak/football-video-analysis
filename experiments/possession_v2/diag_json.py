import sys, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.decode import emissions, decode_blocks
from diagnose import diagnose
out = {}
for key, prm in (('models_v2_f2', {"switch": 5, "out_cost": 120, "in_cost": 120, "bias_dead": -0.3}),
                 ('stack_v2_f2', {"switch": 3, "out_cost": 60, "in_cost": 60, "bias_dead": -0.3})):
    agg = {'gt_switch': 0, 'gt_switch_found_1s': 0, 'pred_switch': 0, 'pred_switch_false_1s': 0,
           'gt_D': 0, 'gt_D_found': 0, 'pred_D': 0, 'pred_D_false': 0}
    s1 = []; e1 = []
    for name in DFL_VAL + MET_VAL:
        m, lab = load(name)
        for seed in (101, 102):
            z = np.load(f'/home/claude/work/cache/probs_{key}_{name}_{seed}.npz')
            r = diagnose(lab, decode_blocks(emissions(z['pd'], z['ph']), m['period'], prm), m['period'])
            for k in agg: agg[k] += r[k]
            s1.append(r['D_start_err']['within1s']); e1.append(r['D_end_err']['within1s'])
    agg['switch_recall_1s'] = agg['gt_switch_found_1s'] / agg['gt_switch']
    agg['switch_precision_1s'] = 1 - agg['pred_switch_false_1s'] / agg['pred_switch']
    agg['D_segments_found'] = agg['gt_D_found'] / agg['gt_D']
    agg['D_start_within_1s'] = float(np.mean(s1)); agg['D_end_within_1s'] = float(np.mean(e1))
    out[key] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in agg.items()}
    print(key, out[key], flush=True)
json.dump({'note': 'boundary diagnostics on the 8 validation copies (reporting only)', **out},
          open('/home/claude/work/diagnostics_final.json', 'w'), indent=1)
