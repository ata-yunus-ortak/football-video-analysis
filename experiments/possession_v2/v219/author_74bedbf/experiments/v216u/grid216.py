"""Development grid: member sets x pooling weights on the 40 development copies, in parallel.
Usage: grid216.py OUT.json W1,W2,... NAME=stem,stem,... [NAME=...]   (stems without the d4_/d6_ prefix; 'HIS' = v2.15 members,
which exist for the six-match side only, so a set containing HIS is scored on Metrica alone)"""
import sys, os, json, glob, numpy as np
from multiprocessing import Pool
import dev216 as V
from dev216 import E, pooling, emissions, decode_blocks, play_blocks, tinfer, tdecode, tfuse, D, LETTERS

def one(args):
    f, sets, weights = args
    base = os.path.basename(f); dfl = base.startswith('J03')
    z = dict(np.load(f)); v2f = D + 'v2_' + base
    if 'p_dead' not in z:
        z.update(np.load(v2f))
    per, lab, path = z['per'], z['lab'], str(z['path'])
    m11 = E.metrics(lab, z['v2_labels'], per)
    out = {'copy': base[:-4], 'path': path, 'v2_11': m11['spell_f1'], 'v2_11_macro': m11['macro_f1'], 'sets': {}}
    for name, stems in sets.items():
        if dfl and 'HIS' in stems:
            continue
        files = []
        for s in stems:
            n = 'possession-tcn-v215' if s == 'HIS' else ('d4_' if dfl else 'd6_') + s
            files += sorted(glob.glob(f'{D}probs/{n}.m*__{base}'))
        mem = [np.load(g) for g in files]
        tcn = np.full((len(per), 3), 1.0 / 3.0); alone = np.full(len(per), 'D', dtype='<U1')
        for k, (a, b) in enumerate(play_blocks(per)):
            prob = np.round(sum(m[f'p{k}'] for m in mem) / len(mem), tinfer.PROB_DECIMALS)
            tcn[a:b] = tdecode.upsample(prob, tinfer.STRIDE, b - a)
            alone[a:b] = LETTERS[tdecode.decode(prob, tfuse.SWITCH_COST, tinfer.STRIDE, b - a)]
        r = {'alone': E.metrics(lab, alone, per)['spell_f1']}
        for w in weights:
            if path == 'v2.1':
                pd2, ph2 = pooling.pool(tcn, z['p_dead'], z['p_home'], weight=w)
                mm = E.metrics(lab, decode_blocks(emissions(pd2, ph2), per, E.PATHS[path][2]), per)
                r['w%.2f' % w] = mm['spell_f1']; r['macro_w%.2f' % w] = mm['macro_f1']
            else:
                r['w%.2f' % w] = out['v2_11']
        out['sets'][name] = r
    return out

if __name__ == '__main__':
    weights = [float(v) for v in sys.argv[2].split(',')]
    sets = {a.split('=')[0]: a.split('=')[1].split(',') for a in sys.argv[3:]}
    files = sorted(glob.glob(D + 'J03*.npz') + glob.glob(D + 'MET*.npz'))
    with Pool(8) as p:
        rows = p.map(one, [(f, sets, weights) for f in files])
    json.dump(rows, open(sys.argv[1], 'w'))
    for name in sets:
        print('==', name, ','.join(sets[name]))
        for grp, pre in (('DFL', 'J03'), ('MET', 'MET')):
            rr = [r for r in rows if r['copy'].startswith(pre) and name in r['sets']]
            if not rr:
                continue
            line = []
            for k in ['alone'] + ['w%.2f' % w for w in weights]:
                d = [r['sets'][name][k] - r['v2_11'] for r in rr]
                line.append('%s %+.4f/%+.4f' % (k, np.mean(d), min(d)))
            mac = ['macro w%.2f %+.4f' % (w, np.mean([r['sets'][name].get('macro_w%.2f' % w, r['v2_11_macro']) - r['v2_11_macro'] for r in rr])) for w in weights]
            print('  ', grp, len(rr), ' '.join(line), '|', ' '.join(mac), flush=True)
