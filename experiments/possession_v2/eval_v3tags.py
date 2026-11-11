"""Validation of v3 stage 2 under the registered tag regimes (8 copies, fixed seeds).
Writes cache/probs_v3t_{regime}_{name}_{seed}.npz and gate reports.
Usage: eval_v3tags.py stage2.pkl"""
import sys, json, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, DFL_VAL, MET_VAL
from possession.stack import stack_features
from possession import smarttags as st

REGIMES = ['default', 'none', 'clean', 'noisy', 'bad_team', 'inverted_defending']
sd, sh = pickle.load(open(sys.argv[1], 'rb'))
report = {}
i = 0
for name in DFL_VAL + MET_VAL:
    m, lab = load(name)
    for seed in (101, 102):
        i += 1
        z = np.load(f'/home/claude/work/cache/probs_models_v2_f2_{name}_{seed}.npz')
        pd1, ph1 = z['pd'], z['ph']
        S = [stack_features(pd1, ph1, m['period'], m['fps'], swap=sw)[0] for sw in (False, True)]
        for ri, regime in enumerate(REGIMES):
            rng = np.random.default_rng(7000 + i)
            prm = st.sample_params(rng, regime)
            tags = st.simulate(lab, m['ball'], m['players'], m['team'], m['period'], m['pitch'], m['fps'], rng, prm)
            use, rep = st.gate(tags, pd1, ph1, m['period'])
            variants = [(regime, use)]
            if regime in ('bad_team', 'inverted_defending', 'default'):
                variants.append((regime + '_nogate', st.GROUPS))
            for key, u in variants:
                X = [np.hstack([S[sw], st.features(tags, len(lab), m['period'], m['fps'], swap=sw, use=u)[0]])
                     for sw in (False, True)]
                ok = np.isfinite(X[0][:, 0])
                d2, h2 = np.full(len(lab), .5), np.full(len(lab), .5)
                d2[ok] = .5 * (sd.predict_proba(X[0][ok])[:, 1] + sd.predict_proba(X[1][ok])[:, 1])
                h2[ok] = .5 * (sh.predict_proba(X[0][ok])[:, 1] + 1 - sh.predict_proba(X[1][ok])[:, 1])
                np.savez(f'/home/claude/work/cache/probs_v3t_{key}_{name}_{seed}.npz', pd=np.round(d2, 6), ph=np.round(h2, 6))
            report[f'{regime}|{name}|{seed}'] = {'n_tags': len(tags), 'gate': rep, 'used': list(use)}
            print(regime, name, seed, len(tags), 'used', use, {g: r['agreement'] for g, r in rep.items()}, flush=True)
json.dump(report, open('/home/claude/work/eval_v3tags_gate.json', 'w'), indent=1)
print('DONE', flush=True)
