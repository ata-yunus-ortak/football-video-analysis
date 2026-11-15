"""Write the registration of the v2.13 validation (fusion of possession-v2.11 with the teammate's temporal convolution
network), before any score of the fusion or of the committed TCN weights on a validation or reserved match.
Usage: /usr/bin/python3 register_v213.py draft            -> v213/possession-v213-plan-DRAFT.json (for the review)
       /usr/bin/python3 register_v213.py final "REVIEW"   -> /home/claude/sc/possession-v213-plan.json (REVIEW: the
                                                             TCN author's answer to the draft, one sentence)"""
import hashlib, json, os, re, subprocess, sys, platform
from pathlib import Path
import numpy as np

REPO, WORK, V = Path('/home/claude/sc'), Path('/home/claude/work'), Path('/home/claude/work/v213')
TCN_REPO = Path('/home/claude/ata-yunus-ortak/football-video-analysis')
COMMIT = '167dc7b198c094c2eb1db5cd7ed8a852f603f867'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mode = sys.argv[1]
assert mode in ('draft', 'final')
smoke = json.loads((V / 'exp_v213_smoke.json').read_text())
assert all('fused' not in r and 'v2_11' not in r for r in smoke['rows']), 'the smoke run must not hold scores'
for f in ('exp_v213_0.json', 'exp_v213_1.json', 'exp_v213_2.json', 'exp_v213_3.json', 'exp_v213_reserved.json'):
    assert not (V / f).exists(), f'{f} exists: registration must come before any validation row'
head = subprocess.check_output(['git', '-C', str(TCN_REPO), 'rev-parse', 'HEAD']).decode().strip()
assert head == COMMIT, head
MODULES = ('__init__.py', 'infer.py', 'features.py', 'decode.py', 'fuse.py', 'degrade.py')
for f in MODULES:      # the harness runs byte copies of the committed modules
    assert sha(V / 'tcn' / f) == sha(TCN_REPO / 'possession' / f), f
WEIGHTS = ('tcn_dfl6.npz', 'tcn_dfl5_without_J03WN1.npz', 'tcn_dfl5_without_J03WR9.npz')
for f in WEIGHTS:
    assert sha(V / 'weights' / f) == sha(TCN_REPO / 'possession' / 'weights' / f), f


def seed_search(seeds):
    """Files of the repository copy and the workspace that contain any of the seeds as a whole number (data fixtures,
    feature caches and the v2.13 validation files themselves excluded)."""
    own = {'exp_v213.py', 'assemble_v213.py', 'register_v213.py', 'pff_fused.py', 'exp_v213_smoke.json', 'exp_v213_smoke.log',
           'possession-v213-plan-DRAFT.json', 'possession-v213-plan.json'}
    hits = {}
    for root in (REPO, WORK, TCN_REPO):
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


SEEDS = (set(range(13100, 13134)) | {b + 100 * r + c for b in (43100, 53100) for r in (0, 1) for c in range(9)}
         | {33103} | {63100 + i for i in (0, 1, 2, 3, 8)})
HITS = seed_search(SEEDS)
assert not HITS, HITS

plan = {
 'version': 'possession-v2.13-plan',
 'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip() if mode == 'final'
                  else 'DRAFT for review by the TCN author; not registered; nothing has been scored',
 'candidate': 'possession-v2.13 = possession-v2.11 (or its variant v2.11g) in which the last step, the v2.11 decoder, is replaced '
              'by the fusion rule of the teammate\'s branch: the second-stage probabilities of v2.11 are averaged with the '
              'probabilities of a temporal convolution network (TCN) and decoded by one Viterbi pass. Everything before that step '
              '(reader, play blocks, noise gate, goalkeeper team check, broadcast alignment, registration, 0.50 m gate, both model '
              'paths and their second stage) is unchanged. The kick-off handling is not part of this validation (see below).',
 'tcn': {
  'author': 'Huseyin Umut Isik (team member)',
  'repository': 'github.com/ata-yunus-ortak/football-video-analysis, branch mtah-possession', 'commit': COMMIT,
  'description': 'docs/POSSESSION_TCN.md of that commit: 37 team-symmetric features per frame (features.py), dilated temporal '
                 'convolution network at 12.5 Hz with three outputs (team 0, team 1, dead), inference in NumPy float64 (infer.py), '
                 'probabilities averaged over ensemble members and both team orders and rounded to 4 decimals',
  'training_data_as_documented_by_the_author': 'open DFL data (Bassek et al. 2025, CC BY 4.0) only, corrupted by the author\'s '
                 'simulator (degrade.py): tcn_dfl6.npz on J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ, J03WR9, three seeds; '
                 'tcn_dfl5_without_<match>.npz on the five other matches of those six, one seed, same recipe. No Metrica game '
                 'and not J03WMX in these weights. Not re-trained or checked by us; taken as documented.',
  'weights_if_selected': 'tcn_dfl6.npz as committed, with the released v2 bundles; nothing is trained after the decision',
 },
 'fusion_rule_fixed_before_any_score': {
  'source': 'possession/fuse.py of the commit (WEIGHT = 0.5, SWITCH_COST = 6.0), nothing chosen by this plan',
  'steps': ['v2.11 side: second-stage P(dead) and P(home | alive), rounded to 6 decimals, exactly what the v2.11 decoder is given; '
            'on the v2.3 path (measured noise above 0.30 m) they come from the smoothed input and the v2.3 models',
            'three classes: home = (1 - P(dead)) * P(home | alive), away = (1 - P(dead)) * (1 - P(home | alive)), dead = P(dead)',
            'TCN probabilities (12.5 Hz) linearly interpolated to the 25 fps frame grid',
            'arithmetic mean at 25 fps, weight 0.5 each',
            'one Viterbi pass over log(clip(p, 1e-6, 1)) with cost 6 for every state change, per play block; D outside the blocks',
            'the v2.11 decoder (switch 3 or 5, out/in 60, dead bias -0.3) is not used in the fused system'],
  'tcn_input': 'the tracking the v2 models see: packed slots, after the goalkeeper team check, with the filled ball when the '
               '0.50 m gate opened; never smoothed (also on the v2.3 path); metres from the pitch centre (our corner-origin '
               'coordinates minus half the pitch size), float32, NaN where missing; team 0 = home slots',
 },
 'models_per_match': {
  'J03WN1, J03WR9 (DFL)': 'v2.11 side: validation models trained on J03WOH, J03WOY, J03WPY, J03WQQ (cache/models_v2.pkl, stack_v2.pkl, '
                          'models_v23.pkl, stack_v23.pkl), as in every earlier validation. TCN side: tcn_dfl5_without_<that match>.npz',
  'Metrica games 1, 2 (and 3, reported)': 'the pair as it would be released: v2 bundles models/possession-v2.npz and possession-v23.npz '
                          '(six DFL matches) through possession.pipeline.predict_labels, and tcn_dfl6.npz. Neither saw a Metrica game. '
                          'This differs from earlier validations, which used the four-match validation models on Metrica as well.',
 },
 'known_asymmetries': [
  'DFL rows: the v2.11 validation models are trained on four matches, the TCN on five (the other validation match included), with one '
  'seed instead of the three of tcn_dfl6.npz. Neither side saw the scored match. The released pair would have six matches each.',
  'The TCN was trained on its author\'s simulator and on tracking as given; here it reads goalkeeper-corrected, slot-packed and (in '
  'the fill conditions) broadcast-filled tracking corrupted by our simulator.',
 ],
 'seen_on_external_data_before_registration': [
  'Development numbers of the TCN author (not registered; his own Metrica labels, not metrica_labels.py; our v2.4 path, not v2.11; '
  'an earlier set of TCN weights; weight 0.3-0.7 and switch cost 4-8 looked at on the same copies): 24 corrupted copies of Metrica '
  'games 1-3, v2.x 0.702, TCN 0.714, 50/50 fusion 0.731-0.734 spellF1; nine mixes 0.720-0.734.',
  'The TCN recipe (features, architecture, training schedule) was developed by its author with cross-validation over all seven DFL '
  'matches and Metrica games 1-3, with scores visible. Our validation matches, Metrica game 3 and J03WMX are therefore not untouched '
  'for the TCN family (the validation matches never were for v2.x either).',
  'According to the author, the committed weights (tcn_dfl6.npz and the two five-match files) were not scored on any external match '
  'before this registration.',
  'exp_v213.py smoke run on training match J03WOH, training seed 1 (in-sample for every model): wiring only, it computes no score '
  '(exp_v213_smoke.json holds label shares and counts of changed frames, nothing compared with labels).',
  'K009 (12 Nov): possession-v2.11 alone on PFF FC World Cup 2022 game 3839 against our proxy from PFF events (spellF1 0.629, '
  'macroF1 0.898; inspection only). Neither the TCN nor the fusion has been run on that game.',
  'No score of the fusion and no score of the committed TCN weights on any external match exists on our side before registration.',
 ],
 'validation': {
  'script': 'v213/exp_v213.py (parts 0-3, one validation match each; helpers harness.py, exp_v25.py, exp_v210.py, camera_view.py, '
            'synth_broadcast3.py, synth_clock.py; byte copies of the commit\'s infer.py, features.py, decode.py, fuse.py, degrade.py '
            'under v213/tcn/); gates applied by v213/assemble_v213.py, written before any validation row',
  'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
  'copies': '16 new corrupted copies: possession.degrade, v2 profile (RANGES), parameters sampled from the seed, seed '
            '13100 + 10 * match_index + j, j = 0..3; tracks packed into 46 anonymous slots, 23 per team (possession/epts_export.pack); '
            'noise gate on the tracking as given; goalkeeper team check (keeper2)',
  'conditions': {
   'tactical': 'all 16 copies, tactical camera only',
   'fill_good': 'copies j = 0, 1 (8): simulated broadcast camera (synth_broadcast3 warp simulator, exp_v25 regime good), simulated '
                'clock readings, alignment, player registration and the 0.50 m gate as possession.run211; stream seed 43100 + '
                '2 * match_index + j, clock seed 53100 + 2 * match_index + j',
   'fill_medium': 'the same with regime medium; stream seed 43200 + 2 * match_index + j, clock seed 53200 + 2 * match_index + j',
   'view42': 'copies j = 0, 1 (8): camera window of +-42 m around the centre of play (camera_view.py), tactical only (reported)',
   'tactical_sim2': 'one copy per match made with the TCN author\'s simulator (degrade.py of the commit, each half on its own, '
                    'random severity, seed 63100 + match_index; our prepared data has no ball height, so its height term is '
                    'inactive), packed and checked like the others (reported)',
   'pff_game_3839_after_decision': 'PFF FC World Cup 2022 game 3839 as converted for K009 (broadcast tracking, ball visible in 41% of '
                                   'the in-play frames, no corruption added; reference = our proxy from PFF events): v2_11 with the '
                                   'released bundles, fused and tcn_alone with tcn_dfl6.npz (v213/pff_fused.py), once, after the '
                                   'decision. Reported, not a gate: the data has no published licence and is not used for selection',
   'metrica_game3_after_decision': 'Metrica game 3, copy seed 33103, copy index 8 (streams 43108 / 43208, clock readings 53108 / '
                                   '53208), the four conditions, and one copy of the author\'s simulator (seed 63108); once, after '
                                   'the decision (reported, not a gate, not an untouched test for the TCN family)'},
  'systems': {'v2_11': 'the release logic after the noise gate, with the models named under models_per_match',
              'fused': 'fusion_rule_fixed_before_any_score',
              'tcn_alone': 'the TCN probabilities through its own decoder (decode.py, switch cost 6); reported, not a gate'},
  'metric': 'spellF1 and macroF1 of the organisers\' possession_metrics (possession.evaluate.score) on the DFL provider labels and '
            'the Metrica proxy labels (experiments/possession_v2/metrica_labels.py, stable sort, K005)',
  'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                  'pandas': __import__('pandas').__version__, 'scikit_learn': __import__('sklearn').__version__},
  'seeds_checked_unused': 'copy seeds 13100-13133, stream / clock seeds 43100-43108, 43200-43208, 53100-53108, 53200-53208, '
                          'simulator seeds 63100-63103 and 63108, 33103: no source, record or log file of the repository copy, the '
                          'workspace or the TCN branch contains any of these numbers (search run by this script)',
 },
 'gates': {
  'G1 gain': 'condition tactical, all 16 copies: mean(fused - v2_11) spellF1 >= +0.008',
  'G2 gain on provider flags': 'condition tactical, the 8 DFL copies: mean(fused - v2_11) spellF1 >= +0.008',
  'G3 no harm on event proxies': 'condition tactical, the 8 Metrica copies: mean(fused - v2_11) spellF1 >= -0.002',
  'G4 no bad copy': 'condition tactical: every copy has fused - v2_11 >= -0.010',
  'G5 macroF1': 'condition tactical, all 16 copies: mean(fused - v2_11) macroF1 >= -0.003',
  'G6 broadcast fill': 'conditions fill_good and fill_medium, 8 copies each: mean(fused - v2_11) spellF1 >= 0.000 in each',
  'note': 'the six gates and thresholds of possession-v212-plan.json, unchanged; evaluated on unrounded values',
 },
 'decision_rule': 'All six gates pass: the fusion is selected and integrated as possession-v2.13 (new entry point and manifest; byte '
                  'copies of the commit\'s inference modules; tcn_dfl6.npz with the registered SHA-256; v2.11 becomes the next step of '
                  'the technical ladder). It replaces v2.11 / v2.11g in the delivery only if, before the freeze (14 Nov 2026 23:59 '
                  'Istanbul), the ported inference runs under Python 3.10 / numpy 1.26.4, the output on the synthetic provided-like '
                  'bundles is byte-identical across Python 3.10 / numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the full test suite '
                  'passes, the delivery chain runs OK on the team\'s computer, and the documents describe the TCN\'s data and its '
                  'development history; otherwise v2.11 / v2.11g stays. Any gate '
                  'fails: v2.11 / v2.11g stays the release and the fusion is recorded as tried and not used. The gates are applied '
                  'once, to all rows; nothing is re-run with other seeds, weights, mixing weights or switch costs.',
 'reported_alongside': [
  'every row; means per source (DFL, Metrica) in every condition; the TCN alone; recall of possessions under 2 s and under 1 s; '
  'transition F1 at 12 / 25 frames; numbers of predicted spells; frames changed; noise path and goalkeeper moves per copy',
  'view42 and tactical_sim2: not gates',
  'Metrica game 3 and PFF game 3839 after the decision (not gates)'],
 'not_part_of_this_validation': [
  'Kick-off handling (the frame published in FAQ.md, the Smart Tagging kick-off tag, or neither): it cannot be measured on external '
  'data. It is decided by the team separately and described in the documents.',
  'The provided match: not read, not run and not scored by this validation.'],
 'limits': [
  'The validation matches were used for every earlier selection of v2.x and for the development of the TCN recipe; only the copies '
  'are new. This is a validation, not a fresh test.',
  'There is no untouched test for the fused system: J03WMX was used in the TCN\'s development. The registered final test of v2.11 on '
  'J03WMX (never downloaded on our side) would not describe a released v2.13; a J03WMX run of the fusion could only be reported as '
  'not fresh.',
  'Corruption, slot packing, camera window and broadcast camera are simulated by us; the provided tracking may differ.',
  'DFL labels are the provider\'s per-frame flags; Metrica labels are our event-derived proxies.',
  'The fused system drops the v2.11 decoder with its dead-ball bias and entry / exit costs, so the character of the output '
  '(number and length of possessions, share of dead ball) changes as a whole, not only where the models disagree.',
  'NumPy matrix products are not guaranteed bit-identical across BLAS builds; the 4-decimal rounding makes a different output '
  'unlikely, not impossible. Checked only by the integration tests named in the decision rule.',
 ],
 'hashes': {
  'tcn_modules_sha256': {f: sha(V / 'tcn' / f) for f in MODULES},
  'tcn_weights_sha256': {f: sha(V / 'weights' / f) for f in WEIGHTS},
  'tcn_documents_sha256': {f: sha(TCN_REPO / 'docs' / f) for f in ('POSSESSION_TCN.md', 'POSSESSION_TCN_VALIDATION_PLAN.md')},
  'validation_scripts': {f: sha(V / f) for f in ('exp_v213.py', 'assemble_v213.py', 'register_v213.py', 'pff_fused.py')},
  'pff_game_3839': {'converted_match_npz': sha('/home/claude/pff/3839_match.npz'),
                    'run_pff.py': sha(REPO / 'experiments/possession_v2/pff_viewer/run_pff.py')},
  'helpers': {f: sha(WORK / f) for f in ('harness.py', 'exp_v25.py', 'exp_v210.py', 'camera_view.py', 'synth_broadcast.py',
                                         'synth_broadcast3.py', 'synth_clock.py', 'metrica_labels.py')},
  'v2_validation_models': {f: sha(WORK / 'cache' / f) for f in ('models_v2.pkl', 'stack_v2.pkl', 'models_v23.pkl', 'stack_v23.pkl')},
  'v2_released_bundles': {f: sha(REPO / 'models' / f) for f in ('possession-v2.npz', 'possession-v23.npz')},
  'possession_sources': {f: sha(REPO / 'possession' / f) for f in (
      'degrade.py', 'noise.py', 'keeper2.py', 'smooth.py', 'features.py', 'stack.py', 'decode.py', 'pipeline.py', 'trees.py',
      'bundle.py', 'evaluate.py', 'official_metrics.py', 'epts_export.py', 'fusion.py', 'register.py', 'clocksync.py', 'data.py')},
  'smoke_run': sha(V / 'exp_v213_smoke.json'),
 },
 'provided_fixture_used': False,
}
if mode == 'final':
    plan['review_by_tcn_author'] = sys.argv[2]
    out = REPO / 'possession-v213-plan.json'
    assert not out.exists(), 'already registered'
else:
    out = V / 'possession-v213-plan-DRAFT.json'
out.write_text(json.dumps(plan, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(out, plan['registered_at'], sha(out))
