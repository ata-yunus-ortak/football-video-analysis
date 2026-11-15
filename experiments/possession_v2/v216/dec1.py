"""Development: does the best decoder constant depend on how often the ball is seen in a copy? (pooled v2.15 probabilities)"""
import errlib as E, numpy as np, json
from possession.decode import emissions, decode_blocks
GRID = [('sw2', dict(switch=2)), ('sw3', {}), ('sw4', dict(switch=4)), ('sw5', dict(switch=5)), ('b-0.6', dict(bias_dead=-0.6)), ('b0', dict(bias_dead=0.0))]
res = {}
for f in E.copies():
    d = E.load(f)
    em = emissions(d['pd2'], d['ph2'])
    vis = json.loads(str(d['info']))['ball_visible_in_play']
    res[d['key']] = {'vis': vis, **{n: E.f1_of(d['lab'], decode_blocks(em, d['per'], dict(E.DEC, **p)), d['per']) for n, p in GRID}}
json.dump(res, open('dec1.json', 'w'), indent=1)
ks = sorted(res, key=lambda k: res[k]['vis'])
for lo, hi in ((0, 0.45), (0.45, 0.6), (0.6, 0.75), (0.75, 1.01)):
    g = [k for k in ks if lo <= res[k]['vis'] < hi]
    print(f'ball seen {lo:.2f}-{hi:.2f}: {len(g)} copies ' + ' '.join(f"{n}={np.mean([res[k][n] - res[k]['sw3'] for k in g]):+.4f}" for n, _ in GRID if n != 'sw3') + f"  base {np.mean([res[k]['sw3'] for k in g]):.4f}")
