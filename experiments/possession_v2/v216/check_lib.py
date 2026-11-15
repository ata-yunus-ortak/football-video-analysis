import errlib as E, numpy as np, time
t = time.time()
for f in E.copies():
    d = E.load(f)
    s = E.score(d['lab'], d['pred'], d['per'])
    mine = E.f1_of(d['lab'], d['pred'], d['per'])
    s0 = E.score(d['lab'], d['v2_labels'], d['per'])['spell_f1_mean']
    print(d['key'], d['path'], f"official {s['spell_f1_mean']:.4f} mine {mine:.4f} v2.11 {s0:.4f} diff {s['spell_f1_mean'] - s0:+.4f}", '' if abs(mine - s['spell_f1_mean']) < 1e-9 else 'MISMATCH', flush=True)
print(round(time.time() - t), 's')
