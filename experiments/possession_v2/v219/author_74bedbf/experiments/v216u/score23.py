"""Pooling on the v2.3 path (development): the v2.3 bundle's second-stage probabilities pooled with the TCN, decoded
with the v2.3 decoder constants. Usage: DEVD=.../dev23/ score23.py W1,W2 NAME=stems ..."""
import sys, os, glob, json, numpy as np
from multiprocessing import Pool
from dev216 import E, pooling, emissions, decode_blocks, play_blocks, tinfer, tdecode, tfuse, D, LETTERS

def one(args):
    f, sets, weights = args
    base = os.path.basename(f); z = np.load(f); per, lab = z['per'], z['lab']
    out = {'copy': base[:-4], 'v2_11': E.metrics(lab, z['v2_labels'], per)['spell_f1'], 'sets': {}}
    for name, stems in sets.items():
        files = []
        for s in stems:
            files += sorted(glob.glob(f"{D}probs/{'possession-tcn-v215' if s == 'HIS' else ('d4_' if base.startswith('J03') else 'd6_') + s}.m*__{base}"))
        mem = [np.load(g) for g in files]
        tcn = np.full((len(per), 3), 1.0 / 3.0); alone = np.full(len(per), 'D', dtype='<U1')
        for k, (a, b) in enumerate(play_blocks(per)):
            prob = np.round(sum(m[f'p{k}'] for m in mem) / len(mem), tinfer.PROB_DECIMALS)
            tcn[a:b] = tdecode.upsample(prob, tinfer.STRIDE, b - a)
            alone[a:b] = LETTERS[tdecode.decode(prob, tfuse.SWITCH_COST, tinfer.STRIDE, b - a)]
        r = {'alone': E.metrics(lab, alone, per)['spell_f1']}
        for w in weights:
            pd2, ph2 = pooling.pool(tcn, z['p_dead'], z['p_home'], weight=w)
            r['w%.2f' % w] = E.metrics(lab, decode_blocks(emissions(pd2, ph2), per, E.PATHS['v2.3'][2]), per)['spell_f1']
        out['sets'][name] = r
    return out

if __name__ == '__main__':
    weights = [float(v) for v in sys.argv[1].split(',')]
    sets = {a.split('=')[0]: a.split('=')[1].split(',') for a in sys.argv[2:]}
    files = [f for f in sorted(glob.glob(D + os.environ.get('PAT', 'MET*') + '.npz')) if str(np.load(f)['path']) == 'v2.3']
    with Pool(8) as p:
        rows = p.map(one, [(f, sets, weights) for f in files])
    json.dump(rows, open(D + 'score23_%s.json' % os.environ.get('PAT', 'MET*')[:3], 'w'))
    for name in sets:
        line = []
        for k in ['alone'] + ['w%.2f' % w for w in weights]:
            d = [r['sets'][name][k] - r['v2_11'] for r in rows]
            line.append('%s %+.4f/%+.4f' % (k, np.mean(d), min(d)))
        print('==', name, len(rows), 'copies:', ' '.join(line), flush=True)
    for r in rows:
        print(r['copy'], '%.4f' % r['v2_11'], ' '.join('%s:%+.4f' % (n, r['sets'][n]['w%.2f' % weights[0]] - r['v2_11']) for n in sets))
