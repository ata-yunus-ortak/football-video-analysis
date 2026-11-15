"""Error mining, step 2: what the prediction says where a GT possession is missed, what the truth says under a spurious
predicted possession, and how matched pairs lose credit (boundaries)."""
import numpy as np
gt, pr = np.load('mine1_gt.npy'), np.load('mine1_pr.npy')
N = len(gt) + len(pr); LOSS = 1 - 2 * gt['credit'].sum() / N
sh = lambda m, arr: (1 - arr['credit'][m]).sum() / N / LOSS
def cause(own, oth, dead):
    return np.select([own >= 0.5, oth >= 0.5, dead >= 0.5], [0, 1, 2], 3)
cg = cause(gt['p_own'], gt['p_oth'], gt['p_dead']); cn = ['own team (merged / misaligned)', 'other team', 'dead', 'mixed']
miss = ~gt['m03']
print(f'GT possessions unmatched at IoU 0.3: {miss.mean():.3f} of GT spells, {sh(miss, gt):.3f} of the loss')
for lo, hi, nm in ((0, 50, '< 2 s'), (50, 200, '2-8 s'), (200, 10 ** 9, '> 8 s')):
    d = (gt['dur'] >= lo) & (gt['dur'] < hi)
    print(f'  {nm}: {(miss & d).sum()} missed of {d.sum()}; loss share {sh(miss & d, gt):.3f}')
    for c in range(4):
        m = miss & d & (cg == c)
        if m.sum():
            print(f'      prediction says {cn[c]:32s} {m.sum():5d} ({m.sum() / max((miss & d).sum(), 1):.2f})  loss share {sh(m, gt):.3f}  ball seen {gt["seen"][m].mean():.2f}  mean P(own) {gt["prob"][m].mean():.2f}  max P(own) {gt["probmax"][m].mean():.2f}')
part = gt['m03'] & (gt['credit'] < 0.99)
full = gt['credit'] > 0.99
print(f'\nGT possessions matched with partial credit: {part.mean():.3f} of GT spells, loss share GT side {sh(part, gt):.3f} (the predicted partner loses the same again)')
print(f'GT possessions with full credit: {full.mean():.3f}')
cp = cause(pr['g_own'], pr['g_oth'], pr['g_dead'])
pm = ~pr['m03']
print(f'\npredicted possessions unmatched at 0.3: {pm.mean():.3f} of predicted, loss share {sh(pm, pr):.3f}')
for c in range(4):
    m = pm & (cp == c)
    print(f'      truth under it is {["own team (extra piece / merged)", "other team", "dead", "mixed"][c]:32s} {m.sum():5d} ({m.sum() / pm.sum():.2f}) loss share {sh(m, pr):.3f}  median length {np.median(pr["dur"][m]) / 25:.1f} s')
pp = pr['m03'] & (pr['credit'] < 0.99)
print(f'predicted possessions matched with partial credit: {pp.mean():.3f}, loss share {sh(pp, pr):.3f}')
# boundaries of matched pairs
m = gt['m03']
print('\nmatched pairs (IoU >= 0.3): boundary error in seconds (predicted minus true): median | mean | P10 | P90 | share within 0.5 s')
tn = {0: 'H', 1: 'A', 2: 'D', 3: 'edge'}
for side, col, ctx in (('start', 'se', 'prev'), ('end', 'ee', 'next')):
    for kind, sel in (('after/before dead ball', gt[ctx] == 2), ('turnover', (gt[ctx] == 0) | (gt[ctx] == 1))):
        s = m & sel
        e = gt[col][s] / 25.0
        print(f'  {side:5s} {kind:22s} n={s.sum():5d}  {np.median(e):+.2f} | {e.mean():+.2f} | {np.percentile(e, 10):+.2f} | {np.percentile(e, 90):+.2f} | {(np.abs(e) <= 0.5).mean():.2f}')
# which boundary limits partial matches
p = part
se, ee, dur, pdur = gt['se'][p], gt['ee'][p], gt['dur'][p], gt['pdur'][p]
longer = pdur > dur
print(f'\npartially matched GT spells: predicted partner longer in {longer.mean():.2f}; median GT length {np.median(dur) / 25:.1f} s, partner {np.median(pdur) / 25:.1f} s')
early_start = (-se).clip(0); late_start = se.clip(0); late_end = ee.clip(0); early_end = (-ee).clip(0)
tot = early_start + late_start + late_end + early_end
for nm, v in (('partner starts too early', early_start), ('partner starts too late', late_start), ('partner ends too late', late_end), ('partner ends too early', early_end)):
    print(f'  {nm:26s} share of the non-overlapping frames {v.sum() / tot.sum():.2f}; spells where it is the larger part {(v >= tot / 2).mean():.2f}')
