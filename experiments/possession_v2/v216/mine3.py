"""Error mining, step 3: the same decomposition per label source (DFL provider flags / Metrica proxies from events)."""
import numpy as np, json
gt, pr = np.load('mine1_gt.npy'), np.load('mine1_pr.npy')
tot = json.load(open('mine1_tot.json'))
def cause(own, oth, dead):
    return np.select([own >= 0.5, oth >= 0.5, dead >= 0.5], [0, 1, 2], 3)
for nm, sel in (('DFL (J03WN1, J03WR9)', lambda x: np.char.startswith(x['match'], 'J03')), ('Metrica 1-3', lambda x: np.char.startswith(x['match'], 'MET'))):
    g, p = gt[sel(gt)], pr[sel(pr)]
    N = len(g) + len(p); F = 2 * g['credit'].sum() / N; LOSS = 1 - F
    nc = len(set(g['key']))
    print(f'\n== {nm}: {nc} copies, GT spells per copy {len(g) / nc:.0f}, predicted {len(p) / nc:.0f}, spellF1 {F:.4f}')
    sh = lambda m, arr: (1 - arr['credit'][m]).sum() / N / LOSS
    bins = [0, 25, 50, 100, 200, 10 ** 9]; names = ['<1s', '1-2s', '2-4s', '4-8s', '>8s']
    print('   GT by length: share | credit | loss share      predicted by length: share | credit | loss share')
    for k in range(len(names)):
        m = (g['dur'] >= bins[k]) & (g['dur'] < bins[k + 1]); q = (p['dur'] >= bins[k]) & (p['dur'] < bins[k + 1])
        print(f'   {names[k]:5s} {m.mean():5.3f} | {g["credit"][m].mean():5.3f} | {sh(m, g):5.3f}                         {q.mean():5.3f} | {p["credit"][q].mean():5.3f} | {sh(q, p):5.3f}')
    miss = ~g['m03']; cg = cause(g['p_own'], g['p_oth'], g['p_dead'])
    print(f'   missed GT (no match at 0.3): {miss.mean():.3f} of GT, loss share {sh(miss, g):.3f}: says other team {sh(miss & (cg == 1), g):.3f}, own team merged {sh(miss & (cg == 0), g):.3f}, dead {sh(miss & (cg == 2), g):.3f}')
    part = g['m03'] & (g['credit'] < 0.99)
    print(f'   partially matched pairs: {part.mean():.3f} of GT, loss share both sides {2 * sh(part, g):.3f}')
    pm = ~p['m03']; cp = cause(p['g_own'], p['g_oth'], p['g_dead'])
    print(f'   spurious predicted (no match at 0.3): {pm.mean():.3f} of predicted, loss share {sh(pm, p):.3f}: truth other team {sh(pm & (cp == 1), p):.3f}, own team extra piece {sh(pm & (cp == 0), p):.3f}, dead {sh(pm & (cp == 2), p):.3f}')
    for side, col, ctx in (('start', 'se', 'prev'), ('end', 'ee', 'next')):
        for kind, s2 in (('dead ball', g[ctx] == 2), ('turnover', (g[ctx] == 0) | (g[ctx] == 1))):
            s = g['m03'] & s2; e = g[col][s] / 25.0
            print(f'   boundary {side:5s} {kind:9s} n={s.sum():5d} median {np.median(e):+.2f} mean {e.mean():+.2f} P10 {np.percentile(e, 10):+.2f} P90 {np.percentile(e, 90):+.2f} within 0.5 s {(np.abs(e) <= 0.5).mean():.2f}')
