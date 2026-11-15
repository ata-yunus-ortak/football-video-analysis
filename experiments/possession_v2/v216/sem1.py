"""Label semantics (development, reporting): score of the v2.15 decision against external labels in which possessions
shorter than tau that follow the other team's possession do not count (reading of CHALLENGE.md: a touch without control is
no change of possession), with the same rule applied to the prediction with threshold m. Mean spellF1 over the 42 copies."""
import errlib as E, numpy as np, json
TAU = [0, 13, 25, 38, 50, 75]; M = [0, 13, 25, 38, 50, 75]
res = {}
for f in E.copies():
    d = E.load(f)
    G = {t: E.spells(E.controlled(d['lab'], d['per'], t), d['per']) for t in TAU}
    Pm = {m: E.spells(E.controlled(d['pred'], d['per'], m), d['per']) for m in M}
    res[d['key']] = {'n_gt': {t: len(G[t]) for t in TAU}, 'n_pred': {m: len(Pm[m]) for m in M},
                     'f1': {f'{t}|{m}': E.match(G[t], Pm[m])[5] for t in TAU for m in M}}
json.dump(res, open('sem1.json', 'w'))
for nm, sel in (('all 42', lambda k: True), ('DFL 20', lambda k: k.startswith('J03')), ('Metrica 22', lambda k: k.startswith('MET'))):
    ks = [k for k in res if sel(k)]
    print(f'\n{nm}: GT possessions per copy by tau (s): ' + '  '.join(f'{t / 25:.1f}: {np.mean([res[k]["n_gt"][t] for k in ks]):.0f}' for t in TAU))
    print('   predicted per copy by m (s):   ' + '  '.join(f'{m / 25:.1f}: {np.mean([res[k]["n_pred"][m] for k in ks]):.0f}' for m in M))
    print('   rows: labels with tau; columns: prediction with m = ' + ' '.join(f'{m / 25:.1f}s' for m in M))
    for t in TAU:
        v = [np.mean([res[k]['f1'][f'{t}|{m}'] for k in ks]) for m in M]
        print(f'   tau {t / 25:.1f}s: ' + ' '.join(f'{x:.4f}' for x in v) + f'   best m {M[int(np.argmax(v))] / 25:.1f}s')
