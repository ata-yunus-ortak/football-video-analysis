"""TCN probabilities of other weights on the copies already stored by cache_old.py (development data). The strided input
features of a copy are stored on first use (the copy is rebuilt from its seed), so later weights only need the forward
pass. Usage: retcn.py TAG WEIGHTS MATCH_INDEX [conditions]   (TAG 'check' compares his weights with the stored values)"""
import sys, os, time, numpy as np
import lib214 as L
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
tag, weights, mi = sys.argv[1], sys.argv[2], int(sys.argv[3])
conds = sys.argv[4].split(',') if len(sys.argv) > 4 else ['tactical']
mem = L.tinfer.load_weights(weights) if weights.startswith('/') else L.members(weights)


def one(key, cond, per, feats):
    f = L.fname(key, cond)[:-4] + '.tcn_' + tag + '.npy'
    if os.path.exists(f):
        return
    t0 = time.time()
    tcn = L.tcn_from_features(mem, feats, per)
    if tag == 'check':
        old = np.load(L.fname(key, cond))['tcn']
        print(key, cond, 'max abs difference from the stored probabilities', float(np.abs(old - tcn).max()), flush=True)
        return
    np.save(f, tcn)
    print(key, cond, tag, round(time.time() - t0), 's', flush=True)


def run(name, seed, ci, cs, sim2_seed=None):
    todo = []
    for cond in cs:
        key = f'{name}|{sim2_seed}' if cond == 'tactical_sim2' else f'{name}|{seed}'
        ff = L.fname(key, cond)[:-4] + '.feat.npz'
        if os.path.exists(ff):
            one(key, cond, np.load(L.fname(key, cond))['per'], np.load(ff))
        else:
            todo.append(cond)
    if todo:
        for cond, key, path, base, lab, per, info in L.inputs(name, seed, ci, todo, sim2_seed):
            feats = L.strided_features(base, per)
            np.savez(L.fname(key, cond)[:-4] + '.feat.npz', **feats)
            one(key, cond, per, feats)


if mi == 4:
    run('MET3', 33103, 8, conds, 63108 if 'tactical_sim2' in conds else None)
else:
    name = NAMES[mi]
    for j in (0, 1, 2, 3):
        run(name, 13100 + 10 * mi + j, 2 * mi + j, [c for c in conds if c != 'tactical_sim2'])
    if 'tactical_sim2' in conds:
        run(name, 13100 + 10 * mi, 2 * mi, ['tactical_sim2'], 63100 + mi)
print('RETCNDONE', tag, mi, flush=True)
