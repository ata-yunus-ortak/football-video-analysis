"""Development on the copies already scored in the v2.13 validation (NOT a validation): fusion rules computed from the
stored probabilities of both model families. Usage: explore.py [pattern]"""
import sys, glob, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v213'); sys.path.insert(0, '/home/claude/sc')
from possession.decode import emissions, viterbi as our_viterbi, LETTERS
from possession.features import play_blocks
from possession.evaluate import score
from tcn.decode import viterbi as his_viterbi
import lib214 as L

OUR = {'v2.1': {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}}
import exp_v25
for k, v in exp_v25.PATHS.items():
    OUR[k] = v[2]


def three(p_dead, p_home):
    return np.stack([(1 - p_dead) * p_home, (1 - p_dead) * (1 - p_home), p_dead], axis=1)


def dec_his(mixed, per, cost=6.0):
    out = np.full(len(per), 'D', dtype='<U1')
    for a, b in play_blocks(per):
        out[a:b] = LETTERS[his_viterbi(np.log(np.clip(mixed[a:b], 1e-6, 1.0)), cost)]
    return out


def dec_our(p_dead, p_home, per, params):
    e = emissions(p_dead, p_home)
    out = np.full(len(per), 'D', dtype='<U1')
    for a, b in play_blocks(per):
        out[a:b] = LETTERS[our_viterbi(e[a:b], params['switch'], params['out_cost'], params['in_cost'], params.get('bias_dead', 0.0))]
    return out


def split(mixed):
    alive = np.maximum(mixed[:, 0] + mixed[:, 1], 1e-9)
    return mixed[:, 2], mixed[:, 0] / alive


def variants(d):
    per = d['per']; path = str(d['path'])
    v3 = three(d['p_dead'], d['p_home']); t = d['tcn'].astype(np.float64)
    par = OUR[path]
    out = {}
    out['v2_11'] = d['v2_labels']
    out['his_w50_c6'] = dec_his(0.5 * t + 0.5 * v3, per, 6.0)                    # the v2.13 rule
    out['tcn_alone'] = dec_his(t, per, 6.0)
    for w in (0.2, 0.3, 0.4, 0.5, 0.7):
        m = w * t + (1 - w) * v3
        pd_, ph = split(m)
        out[f'our_w{int(w * 100)}'] = dec_our(pd_, ph, per, par)                 # mean of probabilities, OUR decoder
    for w in (0.3, 0.5):                                                         # geometric pooling, OUR decoder
        g = np.exp(w * np.log(np.clip(t, 1e-4, 1)) + (1 - w) * np.log(np.clip(v3, 1e-4, 1)))
        g /= g.sum(1, keepdims=True)
        pd_, ph = split(g)
        out[f'our_geo{int(w * 100)}'] = dec_our(pd_, ph, per, par)
    for w in (0.3,):                                                             # the v2.13 decoder with another weight
        out[f'his_w{int(w * 100)}_c6'] = dec_his(w * t + (1 - w) * v3, per, 6.0)
    td, th = split(t)
    out['our_tcn_only'] = dec_our(td, th, per, par)                              # TCN probabilities through OUR decoder
    # dead from v2 only, team from the mean; and the reverse
    m = 0.5 * t + 0.5 * v3
    pd_m, ph_m = split(m)
    out['our_deadv2_teammix'] = dec_our(d['p_dead'], ph_m, per, par)
    out['our_deadmix_teamv2'] = dec_our(pd_m, d['p_home'], per, par)
    # team probability mixed on the conditional scale (given alive), dead from the mean
    out['our_deadmix_teamcond'] = dec_our(pd_m, 0.5 * th + 0.5 * d['p_home'], per, par)
    out['our_deadv2_teamcond'] = dec_our(d['p_dead'], 0.5 * th + 0.5 * d['p_home'], per, par)
    return out


if __name__ == '__main__':
    pat = sys.argv[1] if len(sys.argv) > 1 else '*'
    tag = sys.argv[2] if len(sys.argv) > 2 else ''      # other TCN weights: probabilities stored by retcn.py
    rows = {}
    for f in sorted(glob.glob(L.PROBS + pat + '.npz')):
        if f.endswith('.feat.npz'):
            continue
        d = dict(np.load(f, allow_pickle=False))
        if tag:
            import os
            if not os.path.exists(f[:-4] + '.tcn_' + tag + '.npy'):
                continue
            d['tcn'] = np.load(f[:-4] + '.tcn_' + tag + '.npy')
        lab, per = d['lab'], d['per']
        key = f.split('/')[-1][:-4]
        V = variants(d)
        rows[key] = {k: (lambda s: (float(s['spell_f1_mean']), float(s['macro_f1'])))(score(lab, v, per)) for k, v in V.items()}
        base = rows[key]['v2_11'][0]
        print(key, str(d['path']), ' '.join(f"{k}={v[0]:.4f}({v[0] - base:+.4f})" for k, v in rows[key].items()), flush=True)
    json.dump(rows, open('/home/claude/work/v214/explore_' + pat.replace('*', 'all') + ('_' + tag if tag else '') + '.json', 'w'), indent=1)
    names = list(next(iter(rows.values())).keys())
    def grp(k):
        return 'DFL' if k.startswith('J03') else 'MET'
    for g in ('all', 'DFL', 'MET'):
        ks = [k for k in rows if g == 'all' or grp(k) == g]
        if not ks: continue
        print('\n== mean spellF1 diff vs v2_11,', g, 'n =', len(ks))
        for nm in names:
            dsp = np.array([rows[k][nm][0] - rows[k]['v2_11'][0] for k in ks]); dm = np.array([rows[k][nm][1] - rows[k]['v2_11'][1] for k in ks])
            print(f"  {nm:24s} {dsp.mean():+.4f}  min {dsp.min():+.4f}  better {int((dsp > 0).sum())}/{len(ks)}  macro {dm.mean():+.4f}")
