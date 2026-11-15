"""AFTER the decision of possession-v214-plan.json: store the v2 probabilities and the network's input features of the
tactical and his-simulator copies of the v2.14 validation (seeds 16100 + 10 * match + j, 66100 + match). From that
moment they are development data. The copies are rebuilt from their seeds exactly as exp_v213.copy_rows builds them.
Usage: cache_new.py MATCH_INDEX"""
import sys, os, json, time, numpy as np
import lib214 as L
assert os.path.exists('/home/claude/sc/possession-v214-results.json'), 'only after the decision'
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
mi = int(sys.argv[1]); name = NAMES[mi]


def store(seed, ci, conds, sim2_seed=None):
    for cond, key, path, base, lab, per, info in L.inputs(name, seed, ci, conds, sim2_seed):
        f = L.fname(key, cond)
        if os.path.exists(f):
            continue
        t0 = time.time()
        if L.V2_SIDE[name] == 'validation models':
            p11, pd_, ph = L.v2_validation(path, base, per)
        else:
            p11, pd_, ph = L.v2_released(path, base)
        np.savez_compressed(f, lab=np.asarray(lab), per=per, v2_labels=p11, p_dead=np.asarray(pd_, np.float64), p_home=np.asarray(ph, np.float64),
                            tcn=np.zeros((len(per), 3), np.float32), path=path, info=json.dumps(info), ball_seen=np.isfinite(base['ball'][:, 0]))
        np.savez(f[:-4] + '.feat.npz', **L.strided_features(base, per))
        print(key, cond, path, round(time.time() - t0), 's', flush=True)


for j in (0, 1, 2, 3):
    store(16100 + 10 * mi + j, 2 * mi + j, ['tactical'])
store(16100 + 10 * mi, 2 * mi, ['tactical_sim2'], 66100 + mi)
print('CACHENEWDONE', mi, flush=True)
