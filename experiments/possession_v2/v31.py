"""v3.1 = gate + fallback to v2.1 + agreement-weighted blend of v3 and v2.1 stage-2 probabilities.
1) decoder for the blend path on the ORIGINAL default copies (101/102);
2) confirmation on FRESH copies (degrade 103/104, tag seeds 7101-7108), all regimes, vs v2.1 on the same copies."""
import sys, json, pickle, itertools, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
import os
os.environ['FTAG'] = '_f2'
from harness import load, DFL_VAL, MET_VAL
import eval2
from possession.stack import stack_features
from possession import smarttags as st
from possession.decode import emissions, decode_blocks
from possession.evaluate import score

C = '/home/claude/work/cache/'
S1 = pickle.load(open(C + 'models_v2.pkl', 'rb'))
V21 = pickle.load(open(C + 'stack_v2.pkl', 'rb'))
V3 = pickle.load(open(C + 'stack_v3tags.pkl', 'rb'))
DEC21 = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
REGIMES = ['default', 'none', 'clean', 'noisy', 'bad_team', 'inverted_defending']
VAL = DFL_VAL + MET_VAL


def stage1(name, seed):
    path = f'{C}probs_models_v2_f2_{name}_{seed}.npz'
    if os.path.exists(path):
        z = np.load(path); return z['pd'], z['ph']
    pd_, ph = eval2.probs(S1, name, seed)
    np.savez(path, pd=pd_, ph=ph)
    return pd_, ph


def predict2(models, X0, X1):
    sd, sh = models
    ok = np.isfinite(X0[:, 0])
    d, h = np.full(len(X0), .5), np.full(len(X0), .5)
    d[ok] = .5 * (sd.predict_proba(X0[ok])[:, 1] + sd.predict_proba(X1[ok])[:, 1])
    h[ok] = .5 * (sh.predict_proba(X0[ok])[:, 1] + 1 - sh.predict_proba(X1[ok])[:, 1])
    return np.round(d, 6), np.round(h, 6)


def copy_outputs(name, seed, tag_seed, regimes):
    m, lab = load(name)
    pd1, ph1 = stage1(name, seed)
    S = [stack_features(pd1, ph1, m['period'], m['fps'], swap=sw)[0] for sw in (False, True)]
    p21 = predict2(V21, S[0], S[1])
    out = {}
    for regime in regimes:
        rng = np.random.default_rng(tag_seed)
        prm = st.sample_params(rng, regime)
        tags = st.simulate(lab, m['ball'], m['players'], m['team'], m['period'], m['pitch'], m['fps'], rng, prm)
        use, rep = st.gate(tags, pd1, ph1, m['period'])
        if not use:
            out[regime] = ('fallback', p21, 0.0)
            continue
        fr = sum(rep[g]['frames'] for g in use)
        A = sum(rep[g]['frames'] * rep[g]['agreement'] for g in use) / fr
        w = float(np.clip((A - 0.60) / 0.40, 0, 1))
        X = [np.hstack([S[sw], st.features(tags, len(lab), m['period'], m['fps'], swap=sw, use=use)[0]]) for sw in (False, True)]
        p3 = predict2(V3, X[0], X[1])
        out[regime] = ('blend', (w * p3[0] + (1 - w) * p21[0], w * p3[1] + (1 - w) * p21[1]), w)
    return m, lab, p21, out


def decode_score(lab, period, kind, probs, dec_blend):
    prm = DEC21 if kind == 'fallback' else dec_blend
    return score(lab, decode_blocks(emissions(*probs), period, prm), period)


if __name__ == '__main__':
    # 1) decoder for the blend path on the original default copies
    sel = []
    i = 0
    for name in VAL:
        for seed in (101, 102):
            i += 1
            m, lab, p21, out = copy_outputs(name, seed, 7000 + i, ['default'])
            sel.append((m['period'], lab, out['default']))
    grid = []
    for sw, cost, bias in itertools.product([2, 3, 4, 5, 6, 8], [30, 60, 120], [-0.3, 0.0, 0.3]):
        dec = {'switch': sw, 'out_cost': cost, 'in_cost': cost, 'bias_dead': bias}
        sp = [decode_score(lab, per, k, pr, dec)['spell_f1_mean'] for per, lab, (k, pr, w) in sel]
        grid.append((float(np.mean(sp)), dec))
    grid.sort(key=lambda r: -r[0])
    dec = grid[0][1]
    print('BLEND DECODER', dec, 'selection-copies mean %.4f' % grid[0][0], flush=True)
    # 2) confirmation on fresh copies
    res = {r: [] for r in REGIMES}; ref = []; ws = {r: [] for r in REGIMES}; dom = {r: [] for r in REGIMES}
    i = 0
    for name in VAL:
        for seed in (103, 104):
            i += 1
            m, lab, p21, out = copy_outputs(name, seed, 7100 + i, REGIMES)
            r21 = decode_score(lab, m['period'], 'fallback', p21, dec)['spell_f1_mean']
            ref.append(r21)
            for regime in REGIMES:
                k, pr, w = out[regime]
                res[regime].append(decode_score(lab, m['period'], k, pr, dec)['spell_f1_mean'])
                ws[regime].append(round(w, 3)); dom[regime].append(name[:3])
            print('copy', name, seed, 'v2.1 %.4f' % r21, {r: round(res[r][-1], 4) for r in REGIMES}, flush=True)
    R = float(np.mean(ref))
    summary = {r: float(np.mean(v)) for r, v in res.items()}
    gates = {'default >= ref+0.010': summary['default'] >= R + 0.010, 'none >= ref-0.005': summary['none'] >= R - 0.005,
             'noisy >= ref-0.005': summary['noisy'] >= R - 0.005, 'bad_team >= ref-0.010': summary['bad_team'] >= R - 0.010,
             'inverted_defending >= ref-0.010': summary['inverted_defending'] >= R - 0.010}
    print('REF v2.1 fresh copies %.4f' % R)
    for r in REGIMES:
        print('  %-20s %.4f  (%+.4f)  weights %s' % (r, summary[r], summary[r] - R, ws[r]))
    print(json.dumps(gates, indent=1))
    print('VERDICT', 'SELECT_V3_1' if all(gates.values()) else 'KEEP_V21', flush=True)
    json.dump({'blend_decoder': dec, 'decoder_grid_top5': grid[:5], 'reference_v21_fresh': R, 'reference_per_copy': ref,
               'regimes': summary, 'per_copy': res, 'weights': ws, 'gates': gates, 'selected': all(gates.values())},
              open('/home/claude/work/v31_result.json', 'w'), indent=1, default=str)
