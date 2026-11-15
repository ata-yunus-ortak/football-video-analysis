"""Write possession-v212-plan.json: registration of the v2.12 validation, before any result of the touch columns on a
validation or reserved match. Run once, after the independent audit of possession/touch.py and before exp_v212.py
runs on a validation match. Usage: /usr/bin/python3 register_v212.py AUDIT_SUMMARY_JSON"""
import hashlib, json, subprocess, sys, platform
from pathlib import Path
import numpy as np

REPO, WORK, V = Path('/home/claude/sc'), Path('/home/claude/work'), Path('/home/claude/work/v212')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
dev = json.loads((V / 'dev_results.json').read_text())
k007 = json.loads((REPO / 'possession-k007-diagnosis.json').read_text())
tv = json.loads((V / 'train_val.json').read_text())
smoke = json.loads((V / 'exp_v212_smoke.json').read_text())
audit = json.loads(Path(sys.argv[1]).read_text())
vc = json.loads((V / 'verify_caches.json').read_text())
assert vc['all_equal'] and vc['touch_py_sha256'] == sha(REPO / 'possession/touch.py'), 'cache provenance not closed'


def seed_search(seeds):
    """Files of the repository copy and the workspace that contain any of the seeds as a whole number (data fixtures,
    feature caches and the v2.12 validation files themselves excluded)."""
    import os, re
    own = {'exp_v212.py', 'assemble_v212.py', 'register_v212.py', 'exp_v212_smoke.json', 'exp_v212_smoke.log'}
    hits = {}
    for root in (REPO, WORK):
        for dp, dn, fn in os.walk(root):
            if '/cache' in dp or '__pycache__' in dp or '/.git' in dp or 'repro25_fixture' in dp or '/audit' in dp:
                continue
            for f in fn:
                if f in own or f.endswith('_atd.txt') or not f.endswith(('.py', '.json', '.md', '.log', '.txt', '.sh', '.cmd', '.ps1', '.yml')):
                    continue
                try:
                    text = open(os.path.join(dp, f), errors='ignore').read()
                except OSError:
                    continue
                found = set(int(t) for t in re.findall(r'(?<![\d.])(\d{4,5})(?![\d.])', text)) & seeds
                if found:
                    hits[os.path.join(dp, f)] = sorted(found)
    return hits


SEEDS = set(range(12100, 12134)) | {b + 100 * r + c for b in (42100, 52100) for r in (0, 1) for c in range(9)} | {32103, 42199, 52199}
HITS = seed_search(SEEDS)
assert not HITS, HITS


plan = {
 'version': 'possession-v2.12-plan',
 'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
 'background': {
  'diagnosis_k007': 'possession-k007-diagnosis.json (reporting only, 8 used validation copies, seeds 101/102, v2.1 core): spellF1 0.6312; '
                    '74% of the ground-truth possessions shorter than 2 s are missed (686 of 926); inserting the missed ones would give '
                    '0.7879, exact boundaries of the detected ones 0.8957; no systematic lag; in missed short possessions the corrupted '
                    'ball is visible 56% of the time on average, in found ones 83%.',
  'development': 'dev_results.json (written ' + dev['written_at'] + '): touch / control-change columns (possession/touch.py) added to the '
                 'stage-1 input; leave-one-match-out over the four DFL training matches, 5 held-out copies per match (training seeds '
                 '1-3 and new seeds 9001-9008). With the second stage: spellF1 0.669 -> 0.690 (mean of the 4 held-out matches), '
                 'same sign on every match, 19 of 20 copies better, smallest copy difference -0.0011; on the 8 copies with new '
                 'corruption draws +0.016; recall of possessions under 2 s 0.322 -> 0.380; macroF1 0.926 -> 0.930. Development '
                 'numbers, not a test.',
  'design_choice_on_development_data': 'The design brief asked for windows of at most about 1 s. The event-age columns (time since '
                 'a team\'s last touch, team of the last touch) carry the latest touch for up to 10 s (causal); two columns are not '
                 'capped at all (see touch_columns_time_reach). possession/features.py caps its since/until columns at 30 s, and its '
                 'held / next-seen ball positions and attack directions have no time limit. Capping STATE_CAP_S at 1 s gave +0.0105 at '
                 'stage 1 (16 of 20 copies better) against +0.0195 for 10 s. The 10 s version is registered; this choice was made on '
                 'development data only, before any validation result.',
  'independent_audit': audit,
 },
 'candidate': 'possession-v2.12 = possession-v2.11 with the 36 touch columns of possession/touch.py (touch_features, sha256 below) '
              'appended to the 227 possession.features columns at the input of the two stage-1 models of the v2.1 path (the path '
              'taken when the measured input noise is at most 0.30 m), with new stage-1 and second-stage models trained exactly '
              'like the v2.1 models (possession/train.py procedure, possession-v2-config.json hyperparameters, seeds 1-3, every 6th '
              'frame, stacking every 3rd frame on leave-one-fixture-out probabilities; same decoder switch 3, out/in 60, bias_dead '
              '-0.3). The touch columns are computed on the goalkeeper-corrected tactical tracking (keeper2) before the broadcast '
              'fill; the base columns see the filled ball as in v2.9/v2.11. Noise gate, goalkeeper correction, alignment, '
              'registration, 0.50 m gate, play blocks and kick-off frame are unchanged. The v2.3 path (noisy inputs) is '
              'unchanged: the touch detector was developed only at the v2 noise profile.',
 'touch_columns_time_reach': 'as measured by the independent audit (finding m1/m2), more exactly than the touch.py docstring: '
              'event-state columns depend on ball and player data up to about t + 23 frames, and the suppression of nearby events '
              'can chain, so there is no fixed bound (on J03WOH seed 1 at most 27 frames for frame events; a constructed case needs '
              't + 29); tc_zmax_c1 reaches t + 34 and zt_c1 t + 35, plus the same suppression chains; the per-half ball-noise '
              'estimate that scales every '
              'threshold uses the whole half (as features.attack_dirs does); tc_since_change and tc_nchange_p1 compare with the '
              'previous attributed event however old it is (their look-back is not capped at 10 s, and the 1 s development variant '
              'did not cap them either). h_/k_tc_press is 0 when no opponent is tracked (opp_gap is NaN then). These are properties '
              'of the registered file, not changed: changing them would change the output and need a new development run.',
 'models': {
  'validation_models': 'v212/models_v212_val.pkl + v212/stack_v212_val.pkl (train_val.py): trained on the four DFL training matches '
                       'only, as the v2.1 validation models (cache/models_v2.pkl + stack_v2.pkl) that every earlier validation used',
  'train_val_record': {k: tv[k] for k in ('stage1_rows', 'stack_rows', 'outputs_sha256', 'environment', 'written_at')},
  'cache_provenance': 'audit finding M1: the cached touch arrays and training rows were built by a process that started before the '
                      'last edit of touch.py. Closed by v212/verify_caches.py: all 40 cached touch arrays (4 matches x 5 seeds x 2 '
                      'views) recomputed with the registered touch.py are bit-identical (NaN positions included), and the four row '
                      'files equal the cached arrays and labels at their row indices (verify_caches.json, all_equal = ' +
                      str(vc['all_equal']) + ', written ' + vc['written_at'] + '). The development results and the validation models '
                      'therefore belong to the registered touch.py.',
  'release_bundle_if_selected': 'trained by the same procedure on the six DFL fixtures of possession-v2.npz (J03WOH, J03WOY, J03WPY, '
                                'J03WQQ, J03WN1, J03WR9), exported to numpy trees; not trained before the decision',
 },
 'seen_before_registration': 'The development rows above; a detector sanity check on training match J03WOH; the smoke run of '
          'exp_v212.py on training match J03WOH, training seed 1 (in-sample for both model sets; it only checks the wiring, and that '
          'the v2.11 arm equals exp_v25.run_path); the K007 diagnosis of the v2.1 core on 8 earlier copies (seeds 101/102) of the '
          'four validation matches, which motivated the design. No result of the touch columns on a validation or reserved match. '
          'The validation matches are therefore not fresh for this design (they never were: used for every earlier selection).',
 'validation': {
  'script': 'v212/exp_v212.py (parts 0-3, one validation match each; helpers exp_v25.py, exp_v210.py, camera_view.py, '
            'synth_broadcast3.py, synth_clock.py); gates applied by v212/assemble_v212.py, written before any validation row',
  'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
  'copies': '16 new corrupted copies: possession.degrade, v2 profile (RANGES), parameters sampled from the seed, seed '
            '12100 + 10 * match_index + j, j = 0..3; tracks packed into 46 anonymous slots, 23 per team (possession/epts_export.pack)',
  'conditions': {
   'tactical': 'all 16 copies, tactical camera only',
   'fill_good': 'copies j = 0, 1 (8): simulated broadcast camera (synth_broadcast3 warp simulator, exp_v25 regime good), simulated '
                'clock readings, alignment, player registration and the 0.50 m gate as possession.run211; stream seed 42100 + '
                '2 * match_index + j, clock seed 52100 + 2 * match_index + j',
   'fill_medium': 'the same with regime medium; stream seed 42200 + 2 * match_index + j, clock seed 52200 + 2 * match_index + j',
   'reserved_after_decision': 'Metrica game 3, copy seed 32103, copy index 8 (streams 42108 / 42208, clock readings 52108 / 52208), '
                              'all four conditions, once, after the decision (reported, not a gate)',
   'view42': 'copies j = 0, 1 (8): camera window of +-42 m around the centre of play (camera_view.py), tactical only (reported)'},
  'systems': {'v2_11': 'noise gate on the tracking as given; keeper2; v2.1 path cache/models_v2.pkl + stack_v2.pkl, v2.3 path '
                       'models_v23.pkl + stack_v23.pkl (exp_v25.run_path)',
              'v2_12': 'the same, except the v2.1 path uses features + touch columns with the v2.12 validation models; on the '
                       'v2.3 path the output is the v2.11 output (difference 0)'},
  'metric': 'spellF1 and macroF1 of the organisers\' possession_metrics (possession.evaluate.score) on the DFL provider labels and '
            'the Metrica proxy labels (experiments/possession_v2/metrica_labels.py, stable sort, K005)',
  'environment': {'python': platform.python_version(), 'numpy': np.__version__},
  'seeds_checked_unused': None,          # filled below by the search this script runs
 },
 'gates': {
  'G1 gain': 'condition tactical, all 16 copies: mean(v2_12 - v2_11) spellF1 >= +0.008',
  'G2 gain on provider flags': 'condition tactical, the 8 DFL copies: mean(v2_12 - v2_11) spellF1 >= +0.008',
  'G3 no harm on event proxies': 'condition tactical, the 8 Metrica copies: mean(v2_12 - v2_11) spellF1 >= -0.002',
  'G4 no bad copy': 'condition tactical: every copy has v2_12 - v2_11 >= -0.010',
  'G5 macroF1': 'condition tactical, all 16 copies: mean(v2_12 - v2_11) macroF1 >= -0.003',
  'G6 broadcast fill': 'conditions fill_good and fill_medium, 8 copies each: mean(v2_12 - v2_11) spellF1 >= 0.000 in each',
 },
 'decision_rule': 'All six gates pass: possession-v2.12 is selected and integrated as the next release (new entry point and '
                  'manifest; possession-v2.11 becomes the next step of the technical ladder). It replaces v2.11 in the delivery only '
                  'if, before the freeze (14 Nov 2026 23:59 Istanbul), the release bundle is trained, its exported trees reproduce '
                  'the scikit-learn probabilities, the output on the synthetic provided-like bundle is byte-identical across Python '
                  '3.10/numpy 1.26 and Python 3.13/numpy 2.5, the full test suite passes and the delivery chain runs OK on the team\'s '
                  'computer; otherwise v2.11 stays. Any gate fails: possession-v2.11 stays the release and v2.12 is not used. The '
                  'gates are applied once, to all rows; nothing is re-run with other seeds or settings.',
 'reported_alongside': [
  'every row; means per source (DFL, Metrica); recall of possessions under 2 s and under 1 s; transition F1 at 12/25 frames; '
  'numbers of predicted spells; frames changed; noise path and goalkeeper moves per copy',
  'view42: not a gate (the camera window does not remove players near the ball)',
  'reserved Metrica game 3, one new copy (seed 32103), the four conditions, once, after the decision (not a gate)',
  'the final test on the untouched DFL match J03WMX stays after the freeze; its plan is re-registered for the released version '
  'while J03WMX is untouched'],
 'limits': [
  'The validation matches were used for every earlier selection and for the K007 diagnosis that motivated this design; only the '
  'copies are new. This is a validation, not a fresh test.',
  'Corruption, slot packing, camera window and broadcast camera are simulated by us; the provided tracking may differ.',
  'DFL labels are the provider\'s per-frame flags (the closest analogue we have of the organisers\' ground truth, which is derived '
  'from corrected tracking); Metrica labels are our event-derived proxies.',
  'If the measured noise of the provided tracking exceeds 0.30 m, v2.12 gives exactly the v2.11 output (v2.3 path unchanged).',
  'The touch detector reads the tactical ball track; the quality of the provided ball track was not looked at.',
  'In development the gain on new corruption parameter draws was about two thirds of the gain on the training draws.'],
 'hashes': {**{f'possession/{n}': sha(REPO / 'possession' / n) for n in
               ('touch.py', 'features.py', 'stack.py', 'decode.py', 'evaluate.py', 'official_metrics.py', 'degrade.py', 'epts_export.py',
                'keeper2.py', 'fusion.py', 'register.py', 'clocksync.py', 'noise.py', 'smooth.py', 'train.py', 'run211.py')},
            'tests/test_possession_touch.py': sha(REPO / 'tests/test_possession_touch.py'),
            'possession-v211-release.json': sha(REPO / 'possession-v211-release.json'),
            'possession-v211-plan.json': sha(REPO / 'possession-v211-plan.json'),
            'possession-k007-diagnosis.json': sha(REPO / 'possession-k007-diagnosis.json'),
            'experiments/possession_v2/metrica_labels.py': sha(REPO / 'experiments/possession_v2/metrica_labels.py'),
            **{f'work/{n}': sha(WORK / n) for n in ('harness.py', 'metrica_labels.py', 'exp_v25.py', 'exp_v210.py', 'camera_view.py',
                                                   'synth_broadcast.py', 'synth_broadcast3.py', 'synth_clock.py',
                                                   'cache/models_v2.pkl', 'cache/stack_v2.pkl', 'cache/models_v23.pkl', 'cache/stack_v23.pkl')},
            **{f'integration_at_registration/{n}': sha(REPO / n) for n in
               ('possession/run212.py', 'possession/pipeline212.py', 'possession/train212.py', 'possession/run212g.py',
                'tests/test_possession_v212.py')},
            **{f'work/v212/{n}': sha(V / n) for n in ('exp_v212.py', 'assemble_v212.py', 'verify_caches.py', 'verify_caches.json',
                                                     'register_v212.py', 'train_val.py', 'common.py', 'build_cache.py', 'lomo_stage1.py',
                                                     'lomo_stack.py', 'dev_results.json', 'train_val.json', 'models_v212_val.pkl',
                                                     'stack_v212_val.pkl', 'exp_v212_smoke.json')}},
 'integration_note': 'The integration files listed under hashes/integration_at_registration (entry point, pipeline, training '
                     'script, reserve entry point, tests) are not part of what is validated; they may change before the freeze only '
                     'by documented fixes, and the release manifest records their final hashes.',
 'provided_fixture_used': False,
}
plan['validation']['seeds_checked_unused'] = ('12100-12133, 42100-42108, 42200-42208, 52100-52108, 52200-52208, 32103 and the smoke '
                                              'streams 42199 / 52199 occur in no plan, results file, document, script or log of the '
                                              'repository copy or the workspace; searched by register_v212.py at registration (data '
                                              'fixtures, feature caches, the audit folder and the v2.12 validation files excluded)')
assert plan['hashes']['possession/touch.py'] == dev['feature_set']['sha256'] == tv['touch_py_sha256'], 'touch.py changed since development'
assert plan['hashes']['possession/keeper2.py'] == json.loads((REPO / 'possession-v211-release.json').read_text())['source_sha256']['keeper2.py']
assert all(r['copy'].startswith('J03WOH|') for r in smoke['rows']), 'smoke run must use the training match only'
out = REPO / 'possession-v212-plan.json'
assert not out.exists(), 'already registered'
out.write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8')
print(plan['registered_at'], plan['hashes']['possession/touch.py'][:16], plan['hashes']['work/v212/exp_v212.py'][:16])
