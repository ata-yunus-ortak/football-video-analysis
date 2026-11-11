"""v4 validation: synthetic broadcast -> orient/align/fuse -> unchanged v2.1 pipeline. Registered in possession-v4-plan.json."""
import sys, json, pickle, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load, degraded, DFL_VAL, MET_VAL
from possession import broadcast as bc
from possession.features import features, play_blocks
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
import synth_broadcast as sb
C = '/home/claude/work/cache/'
md, mh = pickle.load(open(C + 'models_v2.pkl', 'rb'))
sd, sh = pickle.load(open(C + 'stack_v2.pkl', 'rb'))
DEC = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}


def pipeline(m_deg, lab, period):
    X, _ = features(m_deg); Xs, _ = features(m_deg, swap=True)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    S = [stack_features(p1, q1, period, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(X), .5); q2 = np.full(len(X), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    return score(lab, decode_blocks(emissions(np.round(p2, 6), np.round(q2, 6)), period, DEC), period)


if __name__ == '__main__':
    regime = sys.argv[1]
    out = {'regime': regime, 'copies': []}
    i = 0
    for name in DFL_VAL + MET_VAL:
        m, lab = load(name)
        for seed in (101, 102):
            i += 1
            t0 = time.time()
            dm = degraded(name, seed)
            z = np.load(f'{C}probs_stack_v2_f2_{name}_{seed}.npz')
            base = score(lab, decode_blocks(emissions(z['pd'], z['ph']), m['period'], DEC), m['period'])['spell_f1_mean']
            rng = np.random.default_rng(8000 + i)
            q = sb.sample_quality(rng, regime)
            bro, valid, true_t = sb.simulate(m, lab, rng, q)
            halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(play_blocks(m['period']))]
            bro2, orep = bc.orient(dm, bro, valid, m['fps'], m['pitch'])
            t_of_b, arep = bc.align(dm, bro2, valid, m['fps'], halves)
            acc = t_of_b >= 0
            live = true_t >= 0
            good = acc & live & (np.abs(t_of_b - true_t) <= 2)
            both = acc & live
            prec = float(good.sum() / max(acc.sum(), 1)); rec = float(good.sum() / max(live.sum(), 1))
            mederr = float(np.median(np.abs(t_of_b[both] - true_t[both]))) if both.any() else None
            graded = np.isin(m['period'], (1, 2))
            fb, frep = bc.fuse(dm['ball'], bro2['ball'], t_of_b, m['fps'], graded)
            r = pipeline(dict(dm, ball=fb), lab, m['period']) if frep['used'] else {'spell_f1_mean': base, 'macro_f1': None}
            row = {'name': name, 'seed': seed, 'v21': round(base, 4), 'v4': round(r['spell_f1_mean'], 4),
                   'precision': round(prec, 4), 'recall': round(rec, 4), 'median_abs_lag_err': mederr,
                   'orient': orep, 'align': arep, 'fuse': frep}
            out['copies'].append(row)
            print(regime, name, seed, 'v2.1 %.4f v4 %.4f' % (base, r['spell_f1_mean']), 'prec %.4f rec %.3f err %s' % (prec, rec, mederr),
                  'used', frep['used'], 'agree', frep['agreement'], 'vis %s->%s' % (frep.get('ball_visible_graded_before'), frep.get('ball_visible_graded_after')),
                  round(time.time() - t0), 's', flush=True)
    cs = out['copies']
    out['mean_v21'] = float(np.mean([c['v21'] for c in cs])); out['mean_v4'] = float(np.mean([c['v4'] for c in cs]))
    out['mean_precision'] = float(np.mean([c['precision'] for c in cs]))
    errs = [c['median_abs_lag_err'] for c in cs if c['median_abs_lag_err'] is not None]
    out['median_abs_lag_err'] = float(np.median(errs)) if errs else None
    print('SUMMARY', regime, 'v2.1 %.4f v4 %.4f (%+.4f) precision %.4f lagerr %s' % (out['mean_v21'], out['mean_v4'], out['mean_v4'] - out['mean_v21'], out['mean_precision'], out['median_abs_lag_err']), flush=True)
    json.dump(out, open(f'/home/claude/work/exp_v4_{regime}.json', 'w'), indent=1, default=str)
