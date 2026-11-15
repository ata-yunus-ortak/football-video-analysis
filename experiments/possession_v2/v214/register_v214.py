"""Write the registration of the v2.14 validation (possession-v2.11 pooled with a re-trained temporal convolution
network, decoded by the v2 decoder), before any score of the candidate on a NEW copy of a validation match.
Usage: /usr/bin/python3 register_v214.py draft   -> v214/possession-v214-plan-DRAFT.json
       /usr/bin/python3 register_v214.py final   -> /home/claude/sc/possession-v214-plan.json"""
import hashlib, json, os, re, subprocess, sys, platform
from pathlib import Path
import numpy as np

REPO, WORK, V, V213 = Path('/home/claude/sc'), Path('/home/claude/work'), Path('/home/claude/work/v214'), Path('/home/claude/work/v213')
TCN_REPO = Path('/home/claude/ata-yunus-ortak/football-video-analysis')
COMMIT = '167dc7b198c094c2eb1db5cd7ed8a852f603f867'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mode = sys.argv[1]
assert mode in ('draft', 'final')
sys.path.insert(0, str(V))
import fuse2
assert fuse2.POOL in ('arithmetic', 'geometric') and isinstance(fuse2.WEIGHT, float), 'fix the pooling first'
for f in ('exp_v214_0.json', 'exp_v214_1.json', 'exp_v214_2.json', 'exp_v214_3.json', 'exp_v214_reserved.json', 'pff_v214.json'):
    assert not (V / f).exists(), f'{f} exists: registration must come before any validation row'
smoke = json.loads((V / 'exp_v214_smoke.json').read_text())
assert all('fused' not in r and 'v2_11' not in r for r in smoke['rows']), 'the smoke run must not hold scores'
assert smoke['fusion'] == {'pool': fuse2.POOL, 'weight': fuse2.WEIGHT, 'decoder': 'possession.decode with the constants of the path',
                           'fused_paths': ['v2.1'], 'stride': 2, 'prob_decimals': 4}, 'the smoke run used another pooling'
head = subprocess.check_output(['git', '-C', str(TCN_REPO), 'rev-parse', 'HEAD']).decode().strip()
assert head == COMMIT, head
MODULES = ('__init__.py', 'infer.py', 'features.py', 'decode.py', 'fuse.py', 'degrade.py')
for f in MODULES:      # the harness runs byte copies of the committed modules
    assert sha(V213 / 'tcn' / f) == sha(TCN_REPO / 'possession' / f), f
DFL4 = ['dfl4_both_s0.npz', 'dfl4_both_s1.npz', 'dfl4_both_s2.npz']
DFL6 = ['dfl6_both_s0.npz', 'dfl6_both_s1.npz', 'dfl6_both_s2.npz']
TRAIN = {f: json.loads((V / 'tcn_weights' / f.replace('.npz', '.json')).read_text()) for f in DFL4 + DFL6}
for f in DFL4:
    assert TRAIN[f]['matches'] == ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'] and TRAIN[f]['simulators'] == 'both' and TRAIN[f]['epochs'] == 6
for f in DFL6:
    assert sorted(TRAIN[f]['matches']) == ['J03WN1', 'J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ', 'J03WR9'] and TRAIN[f]['simulators'] == 'both' and TRAIN[f]['epochs'] == 6
assert smoke['sha256']['weights'] == {f: sha(V / 'tcn_weights' / f) for f in DFL4 + DFL6}, 'weights changed after the smoke run'
assert smoke['sha256']['fuse2.py'] == sha(V / 'fuse2.py') and smoke['sha256']['exp_v214.py'] == sha(V / 'exp_v214.py'), 'scripts changed after the smoke run'


def seed_search(seeds):
    """Files of the repository copy and the workspace that contain any of the seeds as a whole number (data fixtures,
    feature caches and the v2.14 validation files themselves excluded)."""
    own = {'exp_v214.py', 'assemble_v214.py', 'register_v214.py', 'pff_v214.py', 'exp_v214_smoke.json', 'exp_v214_smoke.log',
           'possession-v214-plan-DRAFT.json', 'possession-v214-plan.json', 'NOTES.md'}
    hits = {}
    for root in (REPO, WORK, TCN_REPO):
        for dp, dn, fn in os.walk(root):
            if '/cache' in dp or '__pycache__' in dp or '/.git' in dp or 'repro25_fixture' in dp or '/audit' in dp or '/probs' in dp \
                    or '/tcn_cache' in dp or '/tcn_weights' in dp:
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


SEEDS = (set(range(16100, 16134)) | {b + 100 * r + c for b in (46100, 56100) for r in (0, 1) for c in range(9)}
         | {36103} | {66100 + i for i in (0, 1, 2, 3, 8)})
HITS = seed_search(SEEDS)
assert not HITS, HITS

DEV = json.loads((V / 'development_summary.json').read_text())        # written by dev_summary.py from the explore2 outputs
W = fuse2.WEIGHT
plan = {
 'version': 'possession-v2.14-plan',
 'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip() if mode == 'final' else 'DRAFT; not registered',
 'candidate': 'possession-v2.14 = possession-v2.11k in which, on the v2.1 path (measured noise at most 0.30 m), the second-stage '
              'probabilities of the v2 models are pooled with the probabilities of a temporal convolution network (TCN) that was '
              're-trained for this candidate, and the pooled probabilities are decoded by the unchanged v2 decoder (possession/decode.py, '
              'constants of the bundle). On the v2.3 path nothing is pooled and the output is that of v2.11k. Everything before the '
              'decoder (reader, play blocks, noise gate, goalkeeper team check, broadcast alignment, registration, 0.50 m gate, both '
              'model paths and their second stage) is unchanged. The Smart Tagging kick-off rule of v2.11k stays and is not part of '
              'this validation (it cannot be measured on external data).',
 'why_a_second_attempt': 'possession-v2.13 (the same v2 probabilities averaged 50/50 with the team member\'s committed TCN weights and '
              'decoded by his single-cost decoder) failed three of six gates on 13 Nov and stays not selected; its gates are not '
              'changed. On 14 Nov 18:23 the team lead asked for one more attempt before the deadline. Development on the copies '
              'already scored for v2.13 (see seen_on_external_data_before_registration) pointed at three causes: the committed '
              'weights were trained on one corruption simulator only and are sensitive to the false ball detections of the other; '
              'the DFL rows used single-seed weights; and the single-cost decoder dropped the dead-ball entry / exit costs of the v2 '
              'decoder. This candidate changes those three things, does not pool on the v2.3 path, and is validated on new copies.',
 'tcn': {
  'architecture_features_inference': 'by Huseyin Umut Isik (team member): github.com/ata-yunus-ortak/football-video-analysis, branch '
              'mtah-possession, commit ' + COMMIT + ' (possession/train.py, features.py, infer.py, decode.py): 37 team-symmetric '
              'features per frame, dilated temporal convolution network at 12.5 Hz (stem conv 5, 14 residual blocks of dilated conv 3 + '
              'GroupNorm 8 + GELU + dropout 0.15 + conv 1, hidden 128, 1x1 head; three outputs team 0 / team 1 / dead), NumPy float64 '
              'inference with probabilities averaged over members and both team orders and rounded to 4 decimals. Byte copies of his '
              'inference modules are used unchanged.',
  'weights': 'trained by us on 14 Nov 2026 with v214/tcn_jax.py, a JAX re-implementation of his training (PyTorch could not be '
             'installed in this environment): AdamW (weight decay 1e-2), one-cycle learning rate up to 2e-3 (30% warm-up, cosine), '
             'gradient clipping 1.0, crops of 2048 steps, batch 16, cross-entropy. Differences from his script: constant Adam '
             'momentum 0.9 (PyTorch\'s OneCycleLR also cycles it between 0.85 and 0.95); JAX / NumPy initialisation and random streams; '
             'twelve replicas per half (six of his simulator, six of ours; odd replicas with the teams exchanged) and six epochs '
             'instead of six replicas and twelve epochs (the same number of optimisation steps per training match); our prepared data '
             'has no ball height, so the height term of his simulator is inactive. The JAX network was compared with his NumPy '
             'inference on random input and random weights (largest absolute difference of the probabilities 7.9e-7; float32 against float64).',
  'training_data': 'open DFL data only (Bassek et al. 2025, CC BY 4.0), as prepared for the v2 models; labels = the provider\'s flags. '
             'Replicas: his simulator (tcn/degrade.py, every half on its own, seed 1000 * match + 10 * half + replica) and ours '
             '(possession/degrade.py, v2 profile, seed 500000 + 1000 * match + replica). dfl4_both_s{0,1,2}: J03WOH, J03WOY, J03WPY, '
             'J03WQQ (the four matches of the v2 validation models). dfl6_both_s{0,1,2}: those four plus J03WN1 and J03WR9 (the six '
             'matches of the released v2 bundles). No Metrica game, no PFF game, not J03WMX, nothing of the provided match.',
  'training_runs': TRAIN,
  'weights_if_selected': 'dfl6_both_s0, s1, s2 merged into one file (three members), with the released v2 bundles; nothing is '
                         'trained after the decision',
 },
 'fusion_rule_fixed_before_any_score': {
  'source': 'v214/fuse2.py (the file that would be released as possession/fuse2.py)', 'pool': fuse2.POOL, 'weight': W,
  'steps': ['v2 side: second-stage P(dead) and P(home | alive), rounded to 6 decimals, exactly what the v2.11 decoder is given',
            'three classes: home = (1 - P(dead)) * P(home | alive), away = (1 - P(dead)) * (1 - P(home | alive)), dead = P(dead)',
            'TCN probabilities (12.5 Hz, 4 decimals) linearly interpolated to the 25 fps frame grid (tcn/decode.upsample), per play block',
            ('geometric pool: exp(%.1f * log(clip(TCN, 1e-4, 1)) + %.1f * log(clip(v2, 1e-4, 1)))' % (W, 1 - W)) if fuse2.POOL == 'geometric'
            else ('arithmetic pool: %.1f * TCN + %.1f * v2' % (W, 1 - W)),
            'pooled P(dead) = dead / sum, pooled P(home | alive) = home / (home + away), both rounded to 6 decimals',
            'possession.decode: emissions + Viterbi per play block with the constants of the path (v2.1: switch 3, entry / exit 60, '
            'dead bias -0.3); D outside the blocks',
            'v2.3 path (measured noise above 0.30 m): not pooled; the labels are the v2.11 labels'],
  'tcn_input': 'the tracking the v2 models see: packed slots, after the goalkeeper team check, with the filled ball when the 0.50 m '
               'gate opened; never smoothed; metres from the pitch centre, float32, NaN where missing; team 0 = home slots',
  'how_pool_and_weight_were_chosen': DEV['choice'],
 },
 'models_per_match': {
  'J03WN1, J03WR9 (DFL)': 'v2 side: validation models trained on J03WOH, J03WOY, J03WPY, J03WQQ (cache/models_v2.pkl, stack_v2.pkl, '
                          'models_v23.pkl, stack_v23.pkl), as in every earlier validation. TCN side: dfl4_both_s0, s1, s2 (the same four '
                          'matches; three members).',
  'Metrica games 1, 2 (and 3, reported)': 'the pair as it would be released: v2 bundles models/possession-v2.npz and possession-v23.npz '
                          'and dfl6_both_s0, s1, s2 (six DFL matches each). Neither saw a Metrica game.',
 },
 'known_asymmetries': [
  'DFL rows validate the recipe with members trained on four matches; the members that would be released are trained on six, the two '
  'DFL validation matches included, and are therefore measured on the Metrica rows only. The same holds for the v2 side (four-match '
  'validation models on DFL, the released six-match bundles on Metrica), as in the v2.13 validation.',
  'In training, the replicas of our simulator were not packed into 46 slots and not passed through the goalkeeper team check; in the '
  'validation and in a release the network reads packed, checked tracking.',
 ],
 'seen_on_external_data_before_registration': DEV['seen'],
 'validation': {
  'script': 'v214/exp_v214.py (parts 0-3, one validation match each). It imports v213/exp_v213.py unchanged for the copies, the '
            'conditions and the v2_11 arm (helpers harness.py, exp_v25.py, exp_v210.py, camera_view.py, synth_broadcast3.py, '
            'synth_clock.py; byte copies of the commit\'s modules under v213/tcn/) and replaces the fused arm by fuse2.pool + '
            'possession.decode. Gates applied by v214/assemble_v214.py, written before any validation row.',
  'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
  'copies': '16 new corrupted copies: possession.degrade, v2 profile (RANGES), parameters sampled from the seed, seed '
            '16100 + 10 * match_index + j, j = 0..3; tracks packed into 46 anonymous slots, 23 per team (possession/epts_export.pack); '
            'noise gate on the tracking as given; goalkeeper team check (keeper2)',
  'conditions': {
   'tactical': 'all 16 copies, tactical camera only',
   'fill_good': 'copies j = 0, 1 (8): simulated broadcast camera (synth_broadcast3 warp simulator, exp_v25 regime good), simulated '
                'clock readings, alignment, player registration and the 0.50 m gate as possession.run211; stream seed 46100 + '
                '2 * match_index + j, clock seed 56100 + 2 * match_index + j',
   'fill_medium': 'the same with regime medium; stream seed 46200 + 2 * match_index + j, clock seed 56200 + 2 * match_index + j',
   'view42': 'copies j = 0, 1 (8): camera window of +-42 m around the centre of play (camera_view.py), tactical only (reported)',
   'tactical_sim2': 'one copy per match made with the team member\'s simulator (tcn/degrade.py of the commit, each half on its own, '
                    'random severity, seed 66100 + match_index), packed and checked like the others (gate G7)',
   'pff_game_3839_after_decision': 'PFF FC World Cup 2022 game 3839 as converted for K009: v2_11 with the released bundles, the pooled '
                                   'system and the TCN alone with dfl6_both (v214/pff_v214.py), once, after the decision. Reported, '
                                   'not a gate: the data has no published licence and is not used for selection',
   'metrica_game3_after_decision': 'Metrica game 3, copy seed 36103, copy index 8 (streams 46108 / 46208, clock readings 56108 / '
                                   '56208), the four conditions, and one copy of the team member\'s simulator (seed 66108); once, '
                                   'after the decision (reported, not a gate; game 3 was used in the development of this candidate)'},
  'systems': {'v2_11': 'the release logic after the noise gate, with the models named under models_per_match',
              'fused': 'fusion_rule_fixed_before_any_score (on a copy that takes the v2.3 path it equals v2_11 and its difference is 0)',
              'tcn_alone': 'the new TCN probabilities through tcn/decode.py with switch cost 6; reported, not a gate'},
  'metric': 'spellF1 and macroF1 of the organisers\' possession_metrics (possession.evaluate.score) on the DFL provider labels and '
            'the Metrica proxy labels (experiments/possession_v2/metrica_labels.py, stable sort, K005)',
  'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                  'pandas': __import__('pandas').__version__, 'scikit_learn': __import__('sklearn').__version__,
                  'training_only': {'jax': __import__('jax').__version__, 'optax': __import__('optax').__version__}},
  'seeds_checked_unused': 'copy seeds 16100-16133, stream / clock seeds 46100-46108, 46200-46208, 56100-56108, 56200-56208, '
                          'simulator seeds 66100-66103 and 66108, 36103: no source, record or log file of the repository copy, the '
                          'workspace or the TCN branch contains any of these numbers (search run by this script)',
 },
 'gates': {
  'G1 gain': 'condition tactical, all 16 copies: mean(fused - v2_11) spellF1 >= +0.008',
  'G2 gain on provider flags': 'condition tactical, the 8 DFL copies: mean(fused - v2_11) spellF1 >= +0.008',
  'G3 no harm on event proxies': 'condition tactical, the 8 Metrica copies: mean(fused - v2_11) spellF1 >= -0.002',
  'G4 no bad copy': 'condition tactical: every copy has fused - v2_11 >= -0.010',
  'G5 macroF1': 'condition tactical, all 16 copies: mean(fused - v2_11) macroF1 >= -0.003',
  'G6 broadcast fill': 'conditions fill_good and fill_medium, 8 copies each: mean(fused - v2_11) spellF1 >= 0.000 in each',
  'G7 other simulator': 'condition tactical_sim2, 4 copies: mean(fused - v2_11) spellF1 >= 0.000',
  'note': 'G1-G6 are the six gates and thresholds of possession-v212-plan.json and possession-v213-plan.json, unchanged; G7 is '
          'added (in v2.13 these copies were reported only); evaluated on unrounded values',
 },
 'decision_rule': 'All seven gates pass: the pooled system is selected and integrated as possession-v2.14 (new entry point and '
                  'manifest; byte copies of the commit\'s inference modules; the three dfl6_both members with the registered SHA-256; '
                  'v2.11k becomes the next step of the technical ladder). It replaces v2.11k in the delivery only if, by 16 Nov 2026 '
                  '23:59 Istanbul, the ported inference runs under Python 3.10 / numpy 1.26.4, the output on synthetic provided-like '
                  'bundles is byte-identical across Python 3.10 / numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the full test suite '
                  'passes, a full-size chain rehearsal ends OK, and the documents describe the second model, its training data and '
                  'this history; and only if the delivery chain then runs OK on the team\'s computer. Otherwise v2.11k stays. Any '
                  'gate fails: v2.11k stays the release and the candidate is recorded as tried and not used. The gates are applied '
                  'once, to all rows; nothing is re-run with other seeds, weights, pools or decoder constants.',
 'reported_alongside': [
  'every row; means per source (DFL, Metrica) in every condition; the TCN alone; recall of possessions under 2 s and under 1 s; '
  'transition F1 at 12 / 25 frames; numbers of predicted spells; frames changed; noise path and goalkeeper moves per copy',
  'view42: not a gate',
  'Metrica game 3 and PFF game 3839 after the decision (not gates)'],
 'not_part_of_this_validation': [
  'The Smart Tagging kick-off rule: it cannot be measured on external data; it stays as in v2.11k.',
  'The pooling on the v2.3 path: not measured, therefore not used there.',
  'The provided match: not read, not run and not scored by this validation.'],
 'limits': [
  'The validation matches were used for every earlier selection of v2.x, for the development of the TCN recipe by its author and, '
  'through the copies of the v2.13 validation, for the development of this candidate (choice of pool and weight, decision to '
  're-train). Only the copies are new. This is a validation, not a fresh test.',
  'There is no untouched test for the pooled system: J03WMX was used in the TCN recipe\'s development by its author, and Metrica '
  'game 3 in the development of this candidate. The registered final test of v2.11k on J03WMX would not describe a released v2.14; '
  'its plan would have to be re-registered, and such a run could only be reported as not fresh for the TCN family.',
  'The plans of v2.12 and v2.13 named 14 Nov 2026 23:59 Istanbul as the last moment for a change of release. This plan sets a '
  'later one (16 Nov 23:59) at the team lead\'s request; the cost is less time for the checks on the team\'s computer.',
  'The weights were trained by the process that validates them; nobody else has checked the training script. PyTorch and JAX '
  'runs of the same recipe are not bit-identical, and a JAX run is not bit-reproducible across machines; the released weights are '
  'the files with the registered SHA-256, not a re-run.',
  'Corruption, slot packing, camera window and broadcast camera are simulated by us; the provided tracking may differ. The second '
  'model was shown the two simulators of the team and nothing else.',
  'DFL labels are the provider\'s per-frame flags; Metrica labels are our event-derived proxies.',
  'The reserve configuration without the kick-off rule (possession-release-graded-windows.json) stays the v2.11g ladder. If the rule '
  'written down in K011 sends the team to that reserve (a failed Smart Tagging check on the team\'s computer), the second model is '
  'not used either.',
  'NumPy matrix products are not guaranteed bit-identical across BLAS builds; the 4-decimal and 6-decimal rounding makes a '
  'different output unlikely, not impossible. Checked only by the integration tests named in the decision rule.',
 ],
 'hashes': {
  'tcn_modules_sha256': {f: sha(V213 / 'tcn' / f) for f in MODULES},
  'tcn_weights_sha256': {f: sha(V / 'tcn_weights' / f) for f in DFL4 + DFL6},
  'validation_scripts': {**{f: sha(V / f) for f in ('exp_v214.py', 'fuse2.py', 'assemble_v214.py', 'register_v214.py', 'pff_v214.py',
                                                    'tcn_jax.py')}, 'exp_v213.py': sha(V213 / 'exp_v213.py')},
  'development_scripts': {f: sha(V / f) for f in ('diag1.py', 'lib214.py', 'cache_old.py', 'retcn.py', 'retcn2.py', 'explore.py',
                                                  'explore2.py', 'dev_summary.py', 'test_tcn_jax.py', 'check_exp_v214.py', 'xenv_tcn.py')},
  'development_summary': sha(V / 'development_summary.json'),
  'pff_game_3839': {'converted_match_npz': sha('/home/claude/pff/3839_match.npz'),
                    'run_pff.py': sha(REPO / 'experiments/possession_v2/pff_viewer/run_pff.py')},
  'helpers': {f: sha(WORK / f) for f in ('harness.py', 'exp_v25.py', 'exp_v210.py', 'camera_view.py', 'synth_broadcast.py',
                                         'synth_broadcast3.py', 'synth_clock.py', 'metrica_labels.py')},
  'v2_validation_models': {f: sha(WORK / 'cache' / f) for f in ('models_v2.pkl', 'stack_v2.pkl', 'models_v23.pkl', 'stack_v23.pkl')},
  'v2_released_bundles': {f: sha(REPO / 'models' / f) for f in ('possession-v2.npz', 'possession-v23.npz')},
  'possession_sources': {f: sha(REPO / 'possession' / f) for f in (
      'degrade.py', 'noise.py', 'keeper2.py', 'smooth.py', 'features.py', 'stack.py', 'decode.py', 'pipeline.py', 'trees.py',
      'bundle.py', 'evaluate.py', 'official_metrics.py', 'epts_export.py', 'fusion.py', 'register.py', 'clocksync.py', 'data.py')},
  'smoke_run': sha(V / 'exp_v214_smoke.json'),
 },
 'provided_fixture_used': False,
}
if mode == 'final':
    out = REPO / 'possession-v214-plan.json'
    assert not out.exists(), 'already registered'
else:
    out = V / 'possession-v214-plan-DRAFT.json'
out.write_text(json.dumps(plan, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(out, plan['registered_at'], sha(out))
