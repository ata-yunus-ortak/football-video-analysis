import numpy as np, sys
sys.path.insert(0, '/home/claude/sc')
from possession.features import play_blocks

def segs(lab, a, b):
    out = []; s = a
    for t in range(a + 1, b + 1):
        if t == b or lab[t] != lab[s]:
            out.append((s, t, lab[s])); s = t
    return out

def diagnose(gt, pred, period, fps=25):
    r = {'gt_D': 0, 'gt_D_found': 0, 'pred_D': 0, 'pred_D_false': 0, 'gt_switch': 0, 'gt_switch_found_1s': 0,
         'pred_switch': 0, 'pred_switch_false_1s': 0, 'D_start_err': [], 'D_end_err': []}
    for a, b in play_blocks(period):
        G = segs(gt, a, b); P = segs(pred, a, b)
        pd_ = pred == 'D'; gd = gt == 'D'
        for s, e, k in G:
            if k == 'D' and e - s >= fps:
                r['gt_D'] += 1
                if pd_[s:e].mean() > 0.5:
                    r['gt_D_found'] += 1
                    # boundary errors: nearest predicted D segment
                    best = min((p for p in P if p[2] == 'D'), key=lambda p: -min(e, p[1]) + max(s, p[0]))
                    r['D_start_err'].append((best[0] - s) / fps); r['D_end_err'].append((best[1] - e) / fps)
        for s, e, k in P:
            if k == 'D' and e - s >= fps:
                r['pred_D'] += 1
                if gd[s:e].mean() < 0.5: r['pred_D_false'] += 1
        gsw = [s for s, e, k in G[1:] if k in 'HA' and gt[s - 1] in 'HA' and gt[s - 1] != k]
        psw = [s for s, e, k in P[1:] if k in 'HA' and pred[s - 1] in 'HA' and pred[s - 1] != k]
        r['gt_switch'] += len(gsw); r['pred_switch'] += len(psw)
        psw_a = np.array(psw); gsw_a = np.array(gsw)
        r['gt_switch_found_1s'] += sum(1 for s in gsw if len(psw_a) and np.min(np.abs(psw_a - s)) <= fps)
        r['pred_switch_false_1s'] += sum(1 for s in psw if not len(gsw_a) or np.min(np.abs(gsw_a - s)) > fps)
    for k in ('D_start_err', 'D_end_err'):
        v = np.array(r[k]); r[k] = {'median': float(np.median(v)) if len(v) else None, 'mae': float(np.mean(np.abs(v))) if len(v) else None,
                                   'within1s': float(np.mean(np.abs(v) <= 1)) if len(v) else None}
    return r
