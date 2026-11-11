"""Evaluate tag model under tag-quality regimes vs no-tag v2: eval_tags.py tagmodel.pkl v2key"""
import sys, pickle, json, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, DFL_VAL, MET_VAL
from tagcols import tag_columns
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
md, mh, KEEP = pickle.load(open(sys.argv[1], 'rb')); v2key = sys.argv[2]
PRM = json.loads(sys.argv[3]) if len(sys.argv) > 3 else dict(switch=8, out_cost=60, in_cost=60, bias_dead=0.0)
SP = ('throw-in', 'corner kick', 'goal kick', 'free kick', 'kick off')
REG = {'random': None,
       'poor': dict(recall={k: 0.3 for k in SP}, fp_per_restart=0.3, phase_coverage=0.3, phase_team_error=0.3),
       'good': dict(recall={k: 0.9 for k in SP}, fp_per_restart=0.05, phase_coverage=0.8, phase_team_error=0.05)}
out = {}
for reg, p in REG.items():
    sc = []; base = []
    for name in DFL_VAL + MET_VAL:
        m, lab = load(name)
        for seed in (101, 102):
            X = np.hstack([feats(name, seed, False, '_f2'), tag_columns(m, lab, seed, False, p)[:, KEEP]])
            Xs = np.hstack([feats(name, seed, True, '_f2'), tag_columns(m, lab, seed, True, p)[:, KEEP]])
            ok = np.isfinite(X[:, :50]).any(1)
            pd_ = np.full(len(X), .5); ph = np.full(len(X), .5)
            pd_[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
            ph[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
            r = score(lab, decode_blocks(emissions(pd_, ph), m['period'], PRM), m['period'])
            z = np.load(f'/home/claude/work/cache/probs_{v2key}_{name}_{seed}.npz')
            r0 = score(lab, decode_blocks(emissions(z['pd'], z['ph']), m['period'], PRM), m['period'])
            sc.append(r['spell_f1_mean']); base.append(r0['spell_f1_mean'])
            print(reg, name, seed, round(r['spell_f1_mean'], 4), 'no-tag', round(r0['spell_f1_mean'], 4), flush=True)
    out[reg] = dict(tags=float(np.mean(sc)), notag=float(np.mean(base)))
    print('REGIME', reg, out[reg], flush=True)
json.dump(out, open(sys.argv[1].replace('.pkl', '_eval.json'), 'w'), indent=1)
