"""Error mining, step 1 (development): where does the v2.15 decision lose spellF1 on the 42 development copies?
Per GT possession and per predicted possession: credit (share of the five IoU thresholds at which it is matched) and context.
Writes mine1_gt.npy / mine1_pr.npy (structured arrays) and prints tables."""
import errlib as E, numpy as np, json, sys
G, P = [], []
tot = {}
for f in E.copies():
    d = E.load(f)
    lab, pred, per = d['lab'], d['pred'], d['per']
    gs, ps = E.spells(lab, per), E.spells(pred, per)
    cg, cp, pg, pp, ig, f1 = E.match(gs, ps)
    tot[d['key']] = (len(gs), len(ps), f1)
    seen = d['ball_seen']
    pown = np.where(True, 0, 0)
    ph_team = np.stack([(1 - d['pd2']) * d['ph2'], (1 - d['pd2']) * (1 - d['ph2']), d['pd2']], 1)   # pooled H, A, D
    lab_i = np.select([lab == 'H', lab == 'A'], [0, 1], 2); pr_i = np.select([pred == 'H', pred == 'A'], [0, 1], 2)
    n = len(lab)
    for i, (a, b, k) in enumerate(gs):
        w = pr_i[a:b]
        j = pg[i]
        se = ee = 0
        if j >= 0:
            se, ee = ps[j][0] - a, ps[j][1] - b
        G.append((d['match'], d['key'], int(d['sim2']), a, b, b - a, k, cg[i], ig[i], lab_i[a - 1] if a > 0 and per[a - 1] == per[a] else 3,
                  lab_i[b] if b < n and per[b] == per[b - 1] else 3, seen[a:b].mean(), (w == k).mean(), (w == 1 - k).mean(), (w == 2).mean(),
                  ph_team[a:b, k].mean(), ph_team[a:b, k].max(), j >= 0, se, ee, (ps[j][1] - ps[j][0]) if j >= 0 else 0))
    for j, (a, b, k) in enumerate(ps):
        w = lab_i[a:b]
        P.append((d['match'], d['key'], int(d['sim2']), a, b, b - a, k, cp[j], pr_i[a - 1] if a > 0 and per[a - 1] == per[a] else 3,
                  pr_i[b] if b < n and per[b] == per[b - 1] else 3, seen[a:b].mean(), (w == k).mean(), (w == 1 - k).mean(), (w == 2).mean(),
                  ph_team[a:b, k].mean(), pp[j] >= 0))
gt = np.array(G, dtype=[('match', 'U8'), ('key', 'U40'), ('sim2', 'i1'), ('a', 'i4'), ('b', 'i4'), ('dur', 'i4'), ('team', 'i1'), ('credit', 'f4'), ('iou', 'f4'),
                        ('prev', 'i1'), ('next', 'i1'), ('seen', 'f4'), ('p_own', 'f4'), ('p_oth', 'f4'), ('p_dead', 'f4'), ('prob', 'f4'), ('probmax', 'f4'),
                        ('m03', '?'), ('se', 'i4'), ('ee', 'i4'), ('pdur', 'i4')])
pr = np.array(P, dtype=[('match', 'U8'), ('key', 'U40'), ('sim2', 'i1'), ('a', 'i4'), ('b', 'i4'), ('dur', 'i4'), ('team', 'i1'), ('credit', 'f4'),
                        ('prev', 'i1'), ('next', 'i1'), ('seen', 'f4'), ('g_own', 'f4'), ('g_oth', 'f4'), ('g_dead', 'f4'), ('prob', 'f4'), ('m03', '?')])
np.save('mine1_gt.npy', gt); np.save('mine1_pr.npy', pr)
json.dump(tot, open('mine1_tot.json', 'w'))
N = len(gt) + len(pr)
print(f'copies {len(tot)}  GT spells {len(gt)}  predicted {len(pr)}  spellF1 over all spells {2 * gt["credit"].sum() / N:.4f}  mean of copies {np.mean([v[2] for v in tot.values()]):.4f}')
print(f'loss {1 - 2 * gt["credit"].sum() / N:.4f} = GT side {(1 - gt["credit"]).sum() / N:.4f} + predicted side {(1 - pr["credit"]).sum() / N:.4f}')
bins = [0, 13, 25, 50, 100, 200, 400, 10 ** 9]; names = ['<0.5s', '0.5-1s', '1-2s', '2-4s', '4-8s', '8-16s', '>16s']
print('\nGT possessions by length: share of GT | mean credit | unmatched at 0.3 | share of the whole loss')
for k in range(len(names)):
    m = (gt['dur'] >= bins[k]) & (gt['dur'] < bins[k + 1])
    print(f'  {names[k]:7s} {m.mean():6.3f} | {gt["credit"][m].mean():5.3f} | {(~gt["m03"][m]).mean():5.3f} | {(1 - gt["credit"][m]).sum() / N / (1 - 2 * gt["credit"].sum() / N):5.3f}')
print('\npredicted possessions by length: share | mean credit | unmatched at 0.3 | share of the whole loss')
for k in range(len(names)):
    m = (pr['dur'] >= bins[k]) & (pr['dur'] < bins[k + 1])
    print(f'  {names[k]:7s} {m.mean():6.3f} | {pr["credit"][m].mean():5.3f} | {(~pr["m03"][m]).mean():5.3f} | {(1 - pr["credit"][m]).sum() / N / (1 - 2 * gt["credit"].sum() / N):5.3f}')
