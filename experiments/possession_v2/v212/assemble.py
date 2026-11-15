"""v2.12 development, step 4: assemble /home/claude/work/v212/dev_results.json (development table + provenance).

Reads lomo_stage1.json, lomo_stack.json (if present), build_cache.json, check_cache.json, diag_events.json and
summarises: per held-out match (mean over its five copies) and overall (mean over the four matches) spellF1,
macroF1, transition F1 and the recall of ground-truth possessions shorter than 2 s matched at IoU 0.3 (pooled
counts), for base vs touch, at stage 1 only and with the second stage. It also re-checks on one development copy
(J03WOH seed 1) that (a) the cached touch arrays equal what the current possession/touch.py returns and (b) the two
cached team views obey the swap convention (h_/k_ exchanged, diff_ negated, common equal). Records environment
versions, every seed used, file hashes. Development numbers only: not a test, not a selection, not a competition
score. Usage: /usr/bin/python3 /home/claude/work/v212/assemble.py
"""
import sys, os, json, glob, platform, datetime
import numpy as np
sys.path.insert(0, '/home/claude/work/v212')
import common as C
import possession.touch as T

R1 = json.load(open(C.ROOT + 'lomo_stage1.json'))
R2 = json.load(open(C.ROOT + 'lomo_stack.json')) if os.path.exists(C.ROOT + 'lomo_stack.json') else None
R3 = json.load(open(C.ROOT + 'ablation_cap1.json')) if os.path.exists(C.ROOT + 'ablation_cap1.json') else None
if R3 and len(R3.get('rows', {})) < 20:
    R3 = None                                   # variant incomplete: not reported
BUILD = json.load(open(C.ROOT + 'build_cache.json'))
METRICS = ('spell_f1', 'macro_f1', 'trans_f1_12', 'trans_f1_25')


def table(rows, seeds_of=C.held_seeds, new='touch'):
    if new != 'touch':      # compare base with another set under the same output keys, then rename
        rows = {k.replace(f'|{new}|', '|touch|'): v for k, v in rows.items() if '|touch|' not in k}
        t = table(rows, seeds_of)
        return json.loads(json.dumps(t).replace('"touch', f'"{new}').replace('_touch_', f'_{new}_')) if t else None
    out = {'per_heldout_match': {}, 'mean_over_matches': {}, 'per_copy': {}}
    per = {}
    for held in C.MATCHES:
        per[held] = {}
        for fset in ('base', 'touch'):
            rs = [rows.get(f'{held}|{fset}|{s}') for s in seeds_of(held)]
            if any(r is None for r in rs):
                return None
            d = {k: round(float(np.mean([r[k] for r in rs])), 4) for k in METRICS}
            d['short_recall_iou03'] = round(sum(r['short_hit'] for r in rs) / max(1, sum(r['short_n'] for r in rs)), 4)
            d['short_n'] = int(sum(r['short_n'] for r in rs))
            d['n_pred_spells'] = round(float(np.mean([r['n_pred'] for r in rs])), 1)
            d['n_gt_spells'] = round(float(np.mean([r['n_gt'] for r in rs])), 1)
            d['pred_spells_under_2s'] = round(float(np.mean([r['pred_short_n'] for r in rs])), 1)
            for nm, _, _ in C.BINS:
                d[f'recall_iou03_{nm}'] = round(sum(r[f'hit_{nm}'] for r in rs) / max(1, sum(r[f'n_{nm}'] for r in rs)), 4)
            per[held][fset] = d
        per[held]['delta_touch_minus_base'] = {k: round(per[held]['touch'][k] - per[held]['base'][k], 4)
                                               for k in METRICS + ('short_recall_iou03',)}
        out['per_heldout_match'][held] = per[held]
    for fset in ('base', 'touch'):
        out['mean_over_matches'][fset] = {k: round(float(np.mean([per[h][fset][k] for h in C.MATCHES])), 4)
                                          for k in METRICS + ('short_recall_iou03',) + tuple(f'recall_iou03_{nm}' for nm, _, _ in C.BINS)}
    out['mean_over_matches']['delta_touch_minus_base'] = {
        k: round(out['mean_over_matches']['touch'][k] - out['mean_over_matches']['base'][k], 4)
        for k in METRICS + ('short_recall_iou03',)}
    deltas = []
    for held in C.MATCHES:
        for s in seeds_of(held):
            a, b = rows[f'{held}|base|{s}'], rows[f'{held}|touch|{s}']
            out['per_copy'][f'{held}_s{s}'] = {'base_spell_f1': round(a['spell_f1'], 4), 'touch_spell_f1': round(b['spell_f1'], 4),
                                                'base_macro_f1': round(a['macro_f1'], 4), 'touch_macro_f1': round(b['macro_f1'], 4),
                                                'base_short_hit': a['short_hit'], 'touch_short_hit': b['short_hit'], 'short_n': a['short_n']}
            deltas.append(b['spell_f1'] - a['spell_f1'])
    deltas = np.array(deltas)
    out['spell_f1_delta_per_copy'] = {'n_copies': int(len(deltas)), 'improved': int((deltas > 0).sum()),
                                      'worse': int((deltas < 0).sum()), 'mean': round(float(deltas.mean()), 4),
                                      'sd': round(float(deltas.std(ddof=1)), 4), 'min': round(float(deltas.min()), 4),
                                      'max': round(float(deltas.max()), 4)}
    return out


def subsets(rows):
    return {'training_seeds_1_2_3': table(rows, lambda h: C.TRAIN_SEEDS),
            'extra_seeds_9001_9008': table(rows, lambda h: C.EXTRA_SEEDS[h])}


# ---- re-checks on one development copy
name, seed = 'J03WOH', 1
dm = C.degraded(name, seed)
X0, names = T.touch_features(dm)
X1, _ = T.touch_features(dm, swap=True)
c0, c1 = np.load(C.touch_path(name, seed, 0)), np.load(C.touch_path(name, seed, 1))
i = {k: j for j, k in enumerate(names)}
sym = all(np.array_equal(c0[:, i[f'tc_{c}']], c1[:, i[f'tc_{c}']], equal_nan=True) for c in T.COMMON) and \
    all(np.array_equal(c0[:, i[f'h_tc_{c}']], c1[:, i[f'k_tc_{c}']], equal_nan=True) and
        np.array_equal(c0[:, i[f'diff_tc_{c}']], -c1[:, i[f'diff_tc_{c}']], equal_nan=True) for c in T.PERSP)
checks = {'cache_equals_current_touch_py_J03WOH_s1': bool(np.array_equal(X0, c0, equal_nan=True) and np.array_equal(X1, c1, equal_nan=True)),
          'swap_convention_on_cached_views_J03WOH_s1': bool(sym),
          'baseline_cache_equals_current_features_py': json.load(open(C.ROOT + 'check_cache.json'))}
del dm, X0, X1, c0, c1

tsec = BUILD['touch_seconds']
timing = {}
for h in C.MATCHES:
    v = [x for k, x in tsec.items() if k.startswith(h + '_')]
    timing[h] = {'calls': len(v), 'mean_s_per_call': round(float(np.mean(v)), 1), 'min_s': round(float(np.min(v)), 1),
                 'max_s': round(float(np.max(v)), 1)}
import pandas, sklearn, scipy
seeds_used = sorted(set(C.TRAIN_SEEDS) | {s for v in C.EXTRA_SEEDS.values() for s in v})
scripts = {os.path.basename(p): C.sha(p) for p in sorted(glob.glob(C.ROOT + '*.py'))}
res = {
    'record': 'possession v2.12 candidate, development stage: touch / control-change features (possession/touch.py) '
              'added to the stage-1 models; leave-one-match-out over the four DFL training matches',
    'written_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
    'status': 'development numbers only: not a test, not a selection, not a competition score; nothing released or frozen changed',
    'provided_fixture_used': False, 'not_a_competition_score': True,
    'data': {'matches': C.MATCHES, 'source': 'DFL/Sportec open data prepared-v1 (CC-BY 4.0), provider BallStatus/BallPossession labels',
             'training_seeds': C.TRAIN_SEEDS, 'extra_heldout_seeds': C.EXTRA_SEEDS, 'all_seeds_used': seeds_used,
             'seed_note': 'seeds 9001-9008 were checked against earlier plan/results files (no earlier use as corruption seeds found); '
                          'degrade draws its corruption parameters from the seed alone, so seeds 1-3 give the same three parameter '
                          'draws in every match (also those of the training rows) and 9001-9008 give eight new draws',
             'never_loaded': sorted(C.FORBIDDEN), 'heldout_copies_per_match': 5},
    'protocol': {'folds': 'leave one of the four matches out; stage-1 models trained on the other three (seeds 1-3, every 6th frame '
                          'from seed % 6, H/A/D frames, both team views) with possession-v2-config.json hyperparameters',
                 'hyperparameters_stage1': C.HP, 'hyperparameters_stage2': C.HP2, 'decoder': C.DEC,
                 'feature_sets': {'base': '227 frozen v2 columns (possession/features.py)', 'touch': 'base + 36 possession/touch.py columns'},
                 'stage1_only': 'symmetrised stage-1 probabilities decoded directly with the frozen decoder (no stacking)',
                 'stacked': 'second stage trained on nested out-of-fold stage-1 probabilities (pair models on the two other training '
                            'matches), as possession.train.stack_rows inside each outer fold; held-out copies use the stage-1 models '
                            'of the outer fold',
                 'scoring': 'possession.evaluate.score (organisers metric, unchanged); short-possession recall = ground-truth H/A spells '
                            'shorter than 50 frames matched one-to-one at IoU >= 0.3 (official_metrics.matched_gt_flags), pooled '
                            'over the copies of a match; overall = mean over the four matches',
                 'models': 'scikit-learn HistGradientBoostingClassifier predict_proba (not exported numpy trees)'},
    'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__,
                    'sklearn': sklearn.__version__, 'scipy': scipy.__version__,
                    'stage1_run': R1.get('environment'), 'stack_run': R2.get('environment') if R2 else None,
                    'cache_build': BUILD.get('environment')},
    'feature_set': {'module': 'possession/touch.py', 'sha256': C.sha('/home/claude/sc/possession/touch.py'),
                    'tests': 'tests/test_possession_touch.py', 'tests_sha256': C.sha('/home/claude/sc/tests/test_possession_touch.py'),
                    'names': names, 'constants': {k: getattr(T, k) for k in ('FIT_HALF_S', 'MIN_PTS', 'GAP_MAX_S', 'Z_TOUCH', 'DV_TOUCH',
                                                                                'JUMP_M', 'REACH_M', 'SIGMA_FLOOR', 'SIGMA_DEFAULT', 'STATE_CAP_S',
                                                                                'WIN_S', 'PRESS_M', 'MIN_SPAN', 'RES_K', 'VMAX_MS')}},
    'checks': checks,
    'touch_feature_seconds_per_call': {'note': 'one call = one corrupted copy (about 137k frames, 25 fps), one team view; '
                                               'both views = two calls; 2 CPUs, Python 3.13', 'per_match': timing},
    'stage1_only': {'all_copies': table(R1['rows']), **subsets(R1['rows']), 'fit_seconds': R1.get('fit_seconds')},
    'stacked': ({'all_copies': table(R2['rows']), **subsets(R2['rows']), 'fit_seconds': R2.get('fit_seconds')} if R2 else None),
    'variant_state_lookback_1s_stage1_only': (
        {'what': 'touch columns with possession.touch.STATE_CAP_S = 1.0 (event-state columns look back at most 1 s), '
                 'stage 1 only, same protocol (ablation_cap1.py); compared with the same base rows',
         'all_copies': table({**R1['rows'], **R3['rows']}, new='cap1'),
         'fit_seconds': R3.get('fit_seconds')} if R3 else None),
    'short_spell_probability_check_stage1': (json.load(open(C.ROOT + 'short_signal.json'))
                                             if os.path.exists(C.ROOT + 'short_signal.json') else None),
    'detector_sanity_check_J03WOH': json.load(open(C.ROOT + 'diag_events.json')) if os.path.exists(C.ROOT + 'diag_events.json') else None,
    'scripts_sha256': scripts,
}
json.dump(res, open(C.ROOT + 'dev_results.json', 'w'), indent=1)
for stage in ('stage1_only', 'stacked'):
    t = res[stage] and res[stage]['all_copies']
    if t:
        print(stage, json.dumps(t['mean_over_matches']), json.dumps(t['spell_f1_delta_per_copy']))
        for h in C.MATCHES:
            print(' ', h, {f: (t['per_heldout_match'][h][f]['spell_f1'], t['per_heldout_match'][h][f]['macro_f1'],
                              t['per_heldout_match'][h][f]['short_recall_iou03']) for f in ('base', 'touch')})
v = res['variant_state_lookback_1s_stage1_only']
if v and v['all_copies']:
    print('variant cap1', json.dumps(v['all_copies']['mean_over_matches']), json.dumps(v['all_copies']['spell_f1_delta_per_copy']))
print(json.dumps(checks))
