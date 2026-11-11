"""v2.7 evaluation helper. Usage: eval27.py STAGE1.pkl STACK.pkl FTAG SWITCH out.json NAME:SEED ...
Scores stage-1+stage-2 with the fixed decoder (SWITCH/60/60/-0.3) on cached feature copies."""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, feats, CACHE
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
s1p, s2p, tag, sw, out = sys.argv[1:6]
md, mh = pickle.load(open(s1p, 'rb')); sd, sh = pickle.load(open(s2p, 'rb'))
DEC = {'switch': float(sw), 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
rows = {}
for item in sys.argv[6:]:
    name, seed = item.split(':'); seed = int(seed)
    m, lab = load(name); per = m['period']
    X = feats(name, seed, False, tag); Xs = feats(name, seed, True, tag)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    del X, Xs
    S = [stack_features(p1, q1, per, swap=w)[0] for w in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(p1), .5); q2 = np.full(len(p1), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    np.savez(f'{CACHE}probs_e27_{out.split("/")[-1][:-5]}_{name}_{seed}.npz', pd=np.round(p2, 6), ph=np.round(q2, 6))
    s = score(lab, decode_blocks(emissions(p2, q2), per, DEC), per)
    rows[item] = {'spell': s['spell_f1_mean'], 'macro': s['macro_f1'], 'n_pred': s['n_pred_spells'], 'n_gt': s['n_gt_spells']}
    print(item, round(s['spell_f1_mean'], 4), round(s['macro_f1'], 4), s['n_pred_spells'], s['n_gt_spells'], flush=True)
    json.dump(rows, open(out, 'w'), indent=1)
print('MEAN', round(float(np.mean([r['spell'] for r in rows.values()])), 4), round(float(np.mean([r['macro'] for r in rows.values()])), 4), flush=True)
