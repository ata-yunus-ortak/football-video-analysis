"""Development scoring on copies already used in the team's v2.14 / v2.15 validations (their seeds; development data now).
DFL (J03WN1, J03WR9): TCN alone (the four-match v2 validation models are not in the repository).
Metrica 1, 2: v2.11 side from the released bundles, pooled exactly as possession-v2.15, and TCN alone.
  dev216.py prep NAME            build and store the copies' TCN features (+ v2 probabilities on Metrica)
  dev216.py score TAG WEIGHT W1.npz [W2.npz ...]   TAG = d4 (DFL copies) | d6 (Metrica copies)
"""
import sys, os, json, glob, numpy as np
import env
from env import E, pooling, emissions, decode_blocks, play_blocks, tinfer, tdecode, tfuse
_mk = os.makedirs
os.makedirs = lambda p, *a, **k: None if str(p).startswith('/home/claude') else _mk(p, *a, **k)
import lib214 as L
os.makedirs = _mk
D = '/Users/umut/BARCELONA/work/v216u/dev/'
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
SETS = ((19100, 69100), (16100, 66100))          # (copy seed base, second-simulator seed base) of v2.15 and v2.14
LETTERS = np.array(['H', 'A', 'D'])

def prep(name):
    i = NAMES.index(name)
    for seed0, sim0 in SETS:
        for j in range(4):
            for cond, key, path, base, lab, per, info in L.inputs(name, seed0 + 10 * i + j, 2 * i + j, ('tactical', 'tactical_sim2'),
                                                                  sim2_seed=(sim0 + i) if j == 0 else None):
                f = D + key.replace('|', '_') + '_' + cond + '.npz'
                if os.path.exists(f):
                    continue
                out = dict(lab=np.asarray(lab), per=per, path=path, **L.strided_features(base, per))
                if name.startswith('MET'):
                    p11, pd_, ph = E.v2_released(path, base)
                    out.update(v2_labels=p11, p_dead=pd_, p_home=ph)
                np.savez_compressed(f, **out)
                print(key, cond, path, flush=True)

def score(tag, weight, names):
    """names: weight-file stems whose member probabilities fwd216.py stored (all members of all files are averaged)."""
    rows = []
    for f in sorted(glob.glob(D + ('J03*' if tag == 'd4' else 'MET*') + '.npz')):
        z = dict(np.load(f)); per, lab, path = z['per'], z['lab'], str(z['path'])
        mem = [np.load(g) for n in names for g in sorted(glob.glob(f'{D}probs/{n}.m*__{os.path.basename(f)}'))]
        assert mem, (names, f)
        tcn = np.full((len(per), 3), 1.0 / 3.0); alone = np.full(len(per), 'D', dtype='<U1')
        for k, (a, b) in enumerate(play_blocks(per)):
            prob = np.round(sum(m[f'p{k}'] for m in mem) / len(mem), tinfer.PROB_DECIMALS)
            tcn[a:b] = tdecode.upsample(prob, tinfer.STRIDE, b - a)
            alone[a:b] = LETTERS[tdecode.decode(prob, tfuse.SWITCH_COST, tinfer.STRIDE, b - a)]
        r = {'copy': os.path.basename(f)[:-4], 'path': path, 'tcn_alone': E.metrics(lab, alone, per)['spell_f1']}
        v2f = D + 'v2_' + os.path.basename(f)
        if 'p_dead' not in z and os.path.exists(v2f):
            z.update(np.load(v2f))
        if 'p_dead' in z:
            r['v2_11'] = E.metrics(lab, z['v2_labels'], per)['spell_f1']
            for wt in weight:
                if path == 'v2.1':
                    pd2, ph2 = pooling.pool(tcn, z['p_dead'], z['p_home'], weight=wt)
                    fus = decode_blocks(emissions(pd2, ph2), per, E.PATHS[path][2])
                else:
                    fus = z['v2_labels']
                r['pool%.1f' % wt] = E.metrics(lab, fus, per)['spell_f1']
        rows.append(r)
    keys = [k for k in rows[0] if k not in ('copy', 'path')]
    for r in rows:
        print(r['copy'].ljust(26), r['path'], ' '.join('%s %.4f' % (k, r[k]) for k in keys), flush=True)
    print('MEAN', {k: round(float(np.mean([r[k] for r in rows])), 4) for k in keys})
    if 'v2_11' in rows[0]:
        print('DIFF vs v2_11 (mean, worst)', {k: (round(float(np.mean([r[k] - r['v2_11'] for r in rows])), 4), round(float(min(r[k] - r['v2_11'] for r in rows)), 4)) for k in keys if k != 'v2_11'})
    return rows

if __name__ == '__main__':
    if sys.argv[1] == 'prep':
        prep(sys.argv[2])
    else:
        rows = score(sys.argv[2], [float(v) for v in sys.argv[3].split(',')], sys.argv[4:])
        json.dump(rows, open(D + 'score_' + '+'.join(sys.argv[4:]) + '_' + sys.argv[2] + '.json', 'w'))
