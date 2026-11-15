"""Write the registration of the v2.15 validation (the pooled system of the v2.14 candidate with a smaller weight for
the network), before any score of the candidate on a copy with the third set of seeds.
Usage: /usr/bin/python3 register_v215.py draft   -> v215/possession-v215-plan-DRAFT.json
       /usr/bin/python3 register_v215.py final   -> /home/claude/sc/possession-v215-plan.json"""
import hashlib, json, os, re, subprocess, sys, platform
from pathlib import Path
import numpy as np

REPO, WORK, V, V213, V214 = Path('/home/claude/sc'), Path('/home/claude/work'), Path('/home/claude/work/v215'), Path('/home/claude/work/v213'), Path('/home/claude/work/v214')
TCN_REPO = Path('/home/claude/ata-yunus-ortak/football-video-analysis')
COMMIT = '167dc7b198c094c2eb1db5cd7ed8a852f603f867'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mode = sys.argv[1]
assert mode in ('draft', 'final')
sys.path.insert(0, str(V))
import pooling as fuse2
assert fuse2.POOL == 'arithmetic' and isinstance(fuse2.WEIGHT, float), 'fix the pooling first'
for f in ('exp_v215_0.json', 'exp_v215_1.json', 'exp_v215_2.json', 'exp_v215_3.json', 'exp_v215_reserved.json', 'pff_v215.json'):
    assert not (V / f).exists(), f'{f} exists: registration must come before any validation row'
smoke = json.loads((V / 'exp_v215_smoke.json').read_text())
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
TRAIN = {f: json.loads((V214 / 'tcn_weights' / f.replace('.npz', '.json')).read_text()) for f in DFL4 + DFL6}
for f in DFL4:
    assert TRAIN[f]['matches'] == ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'] and TRAIN[f]['simulators'] == 'both' and TRAIN[f]['epochs'] == 6
for f in DFL6:
    assert sorted(TRAIN[f]['matches']) == ['J03WN1', 'J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ', 'J03WR9'] and TRAIN[f]['simulators'] == 'both' and TRAIN[f]['epochs'] == 6
assert smoke['sha256']['weights'] == {f: sha(V214 / 'tcn_weights' / f) for f in DFL4 + DFL6}, 'weights changed after the smoke run'
assert smoke['sha256']['pooling.py'] == sha(V / 'pooling.py') and smoke['sha256']['exp_v215.py'] == sha(V / 'exp_v215.py'), 'scripts changed after the smoke run'
P214 = json.loads((REPO / 'possession-v214-plan.json').read_text()); R214 = json.loads((REPO / 'possession-v214-results.json').read_text())
assert P214['hashes']['tcn_weights_sha256'] == smoke['sha256']['weights'], 'the weight files are not those of the v2.14 validation'
assert not R214['selected']


def seed_search(seeds):
    """Files of the repository copy and the workspace that contain any of the seeds as a whole number (data fixtures,
    feature caches and the v2.14 validation files themselves excluded)."""
    own = {'exp_v215.py', 'assemble_v215.py', 'register_v215.py', 'pff_v215.py', 'exp_v215_smoke.json', 'exp_v215_smoke.log',
           'possession-v215-plan-DRAFT.json', 'possession-v215-plan.json', 'NOTES.md', 'make_run215.py'}
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


SEEDS = (set(range(19100, 19134)) | {b + 100 * r + c for b in (49100, 59100) for r in (0, 1) for c in range(9)}
         | {39103} | {69100 + i for i in (0, 1, 2, 3, 8)})
HITS = seed_search(SEEDS)
assert not HITS, HITS

DEV = json.loads((V / 'development_summary.json').read_text())        # written by dev_summary215.py from explore3.json
assert DEV['third_attempt'] and abs(DEV['weight'] - fuse2.WEIGHT) < 1e-12, 'the pooling weight is not the one the rule gives'
W = fuse2.WEIGHT
S214, G214 = R214['summary'], R214['gates']
T = DEV['table']
fm = lambda t: f"{t['mean']:+.4f} (worst copy {t['min']:+.4f}, better on {t['better']} of {t['n']})"
ROWS214 = sorted((r for r in R214['rows'] if r['condition'] == 'tactical'), key=lambda r: r['copy'])
plan = {
 'version': 'possession-v2.15-plan',
 'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip() if mode == 'final' else 'DRAFT; not registered',
 'candidate': 'possession-v2.15 = the candidate of possession-v214-plan.json with one change: the weight of the temporal convolution network '
              f'in the arithmetic pool is {W} instead of 0.5. Everything else is identical: possession-v2.11k in which, on the v2.1 path, the '
              'second-stage probabilities of the v2 models are pooled with the probabilities of the re-trained network (the same six weight '
              'files, SHA-256 as registered for v2.14) and decoded by the unchanged v2 decoder; nothing is pooled on the v2.3 path; the Smart '
              'Tagging kick-off rule of v2.11k stays and is not part of this validation.',
 'why_a_third_attempt': 'possession-v2.14 (weight 0.5) was validated on 16 new copies on 14-15 Nov (possession-v214-results.json): tactical '
              f"camera {S214['tactical']['diff_spell_f1_mean']:+.4f} spellF1 on average, better on {S214['tactical']['copies_better']} of 16 copies "
              f"(DFL {S214['tactical_DFL']['diff_spell_f1_mean']:+.4f}, all 8 better; Metrica {S214['tactical_Metrica']['diff_spell_f1_mean']:+.4f}); "
              f"six of seven gates passed. G4 (no copy below -0.010) failed on one copy (MET1 16120: {S214['tactical']['diff_spell_f1_min']:+.4f}), so "
              'v2.14 is not selected; that record and its gates are not changed. The conditions for one more attempt were written down on '
              '14 Nov at 23:39, when three rows of that validation were known (v214/NOTES.md): only if the mean gates of v2.14 (G1, G2, G3, '
              'G5) pass; the same weight files, pool and decoder; only the weight is lowered, chosen from 0.1, 0.2, 0.3 on development '
              'copies by a rule with a margin to G4; unchanged gates; new copies; no further attempt after this one. This is the third '
              'registered attempt to add the second model (v2.13, v2.14, v2.15).',
 'tcn': dict(P214['tcn'], weights_if_selected='dfl6_both_s0, s1, s2 merged into one file (three members), with the released v2 bundles; nothing '
             'is trained after the decision'),
 'fusion_rule_fixed_before_any_score': {
  'source': 'v215/pooling.py (the file that would be released as possession/pooling.py; v214/fuse2.py with another weight and docstring)',
  'pool': fuse2.POOL, 'weight': W,
  'steps': ['v2 side: second-stage P(dead) and P(home | alive), rounded to 6 decimals, exactly what the v2.11 decoder is given',
            'three classes: home = (1 - P(dead)) * P(home | alive), away = (1 - P(dead)) * (1 - P(home | alive)), dead = P(dead)',
            'TCN probabilities (12.5 Hz, 4 decimals) linearly interpolated to the 25 fps frame grid (tcn/decode.upsample), per play block',
            'arithmetic pool: %.1f * TCN + %.1f * v2' % (W, 1 - W),
            'pooled P(dead) = dead / sum, pooled P(home | alive) = home / (home + away), both rounded to 6 decimals',
            'possession.decode: emissions + Viterbi per play block with the constants of the path (v2.1: switch 3, entry / exit 60, '
            'dead bias -0.3); D outside the blocks',
            'v2.3 path (measured noise above 0.30 m): not pooled; the labels are the v2.11 labels'],
  'tcn_input': P214['fusion_rule_fixed_before_any_score']['tcn_input'],
  'how_the_weight_was_chosen': 'Rule of 14 Nov 23:39: on the 42 development copies (the 22 of the v2.14 development and the 16 tactical and 4 '
      'his-simulator copies of the v2.14 validation, which became development data when its decision was recorded), drop every weight '
      'of 0.1, 0.2, 0.3 with a copy below -0.007; among the rest take the largest mean; require a mean of at least +0.010 on the DFL '
      'development copies (the note of 23:39 said 18 of them; there are 20: 16 tactical and 4 of his simulator; the condition was '
      'applied to all 20 and to the 16 tactical ones); otherwise no third attempt. Result: weights without a copy below -0.007: ' +
      ', '.join(DEV['weights_without_a_copy_below_-0.007']) + f"; largest mean among them: {DEV['largest_mean_among_them']} "
      f"({T['all 42'][DEV['largest_mean_among_them']]['mean']:+.4f}); its mean on the 20 DFL copies: {T['DFL 20'][DEV['largest_mean_among_them']]['mean']:+.4f}, "
      f"on the 16 tactical DFL copies: {T['DFL tactical 16'][DEV['largest_mean_among_them']]['mean']:+.4f}.",
 },
 'models_per_match': P214['models_per_match'],
 'known_asymmetries': P214['known_asymmetries'],
 'seen_on_external_data_before_registration': [
  'Everything listed in possession-v214-plan.json under the same heading.',
  'possession-v214-results.json, all rows. Tactical camera, fused - v2.11 per copy: ' +
  ', '.join(f"{r['copy'].replace('|', ' ')} {r['diff_spell_f1']:+.4f}" for r in ROWS214) + '. Gates: ' +
  ', '.join(f"{k.split(' ')[0]} {'passed' if v else 'FAILED'}" for k, v in G214.items()) + '.',
  'Arithmetic pool through the v2 decoder on the 42 development copies, mean spellF1 difference to v2.11: ' +
  '; '.join(f"weight 0.{n[3:4]} {fm(T['all 42'][n])}" for n in ('ari10', 'ari20', 'ari30', 'ari40', 'ari50')) + '. DFL 20: ' +
  '; '.join(f"0.{n[3:4]} {fm(T['DFL 20'][n])}" for n in ('ari10', 'ari20', 'ari30', 'ari40', 'ari50')) + '. Metrica 22: ' +
  '; '.join(f"0.{n[3:4]} {fm(T['Metrica 22'][n])}" for n in ('ari10', 'ari20', 'ari30', 'ari40', 'ari50')) + '. The 20 copies of the v2.14 validation: ' +
  '; '.join(f"0.{n[3:4]} {fm(T['copies of the v2.14 validation 20'][n])}" for n in ('ari10', 'ari20', 'ari30', 'ari40', 'ari50')) +
  '. Copies of his simulator (9): ' + '; '.join(f"0.{n[3:4]} {fm(T['his simulator 9'][n])}" for n in ('ari10', 'ari20', 'ari30', 'ari40', 'ari50')) +
  '. TCN alone on the 42: ' + fm(T['all 42']['tcn_alone']) + '.',
  'exp_v215.py smoke run on training match J03WOH (in-sample for every model): wiring only, it computes no score.',
  'Not seen: any score of any pool on a copy with the third set of seeds; the broadcast-fill and camera-window conditions for any '
  'weight other than 0.5 (those copies of the v2.14 validation were not re-run); the after-decision rows of v2.14 (Metrica game 3, '
  'PFF game 3839), which had not been run when this plan was registered.',
 ],
 'validation': {
  'script': 'v215/exp_v215.py (parts 0-3): v214/exp_v214.py with the pooling module v215/pooling.py and the third set of seeds; it imports '
            'v213/exp_v213.py unchanged for the copies, the conditions and the v2_11 arm. Gates applied by v215/assemble_v215.py, written '
            'before any validation row.',
  'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
  'copies': '16 new corrupted copies: possession.degrade, v2 profile (RANGES), parameters sampled from the seed, seed '
            '19100 + 10 * match_index + j, j = 0..3; tracks packed into 46 anonymous slots, 23 per team; noise gate on the tracking as '
            'given; goalkeeper team check (keeper2)',
  'conditions': {
   'tactical': 'all 16 copies, tactical camera only',
   'fill_good': 'copies j = 0, 1 (8): simulated broadcast camera (regime good), simulated clock readings, alignment, player registration '
                'and the 0.50 m gate as possession.run211; stream seed 49100 + 2 * match_index + j, clock seed 59100 + 2 * match_index + j',
   'fill_medium': 'the same with regime medium; stream seed 49200 + 2 * match_index + j, clock seed 59200 + 2 * match_index + j',
   'view42': 'copies j = 0, 1 (8): camera window of +-42 m around the centre of play, tactical only (reported)',
   'tactical_sim2': 'one copy per match made with the team member\'s simulator (seed 69100 + match_index), packed and checked like the '
                    'others (gate G7)',
   'pff_game_3839_after_decision': 'PFF FC World Cup 2022 game 3839 as converted for K009: v2_11, the pooled system and the TCN alone '
                                   '(v215/pff_v215.py), once, after the decision. Reported, not a gate, not a decision input',
   'metrica_game3_after_decision': 'Metrica game 3, copy seed 39103, copy index 8 (streams 49108 / 49208, clock readings 59108 / 59208), '
                                   'the four conditions, and one copy of the team member\'s simulator (seed 69108); once, after the '
                                   'decision (reported, not a gate)'},
  'systems': {'v2_11': 'the release logic after the noise gate, with the models named under models_per_match',
              'fused': 'fusion_rule_fixed_before_any_score (on a copy that takes the v2.3 path it equals v2_11 and its difference is 0)',
              'tcn_alone': 'the TCN probabilities through tcn/decode.py with switch cost 6; reported, not a gate'},
  'metric': 'spellF1 and macroF1 of the organisers\' possession_metrics (possession.evaluate.score) on the DFL provider labels and '
            'the Metrica proxy labels (experiments/possession_v2/metrica_labels.py, stable sort, K005)',
  'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                  'pandas': __import__('pandas').__version__, 'scikit_learn': __import__('sklearn').__version__},
  'seeds_checked_unused': 'copy seeds 19100-19133, stream / clock seeds 49100-49108, 49200-49208, 59100-59108, 59200-59208, '
                          'simulator seeds 69100-69103 and 69108, 39103: no source, record or log file of the repository copy, the '
                          'workspace or the TCN branch contains any of these numbers (search run by this script)',
 },
 'gates': dict(P214['gates'], note='the seven gates and thresholds of possession-v214-plan.json, unchanged (G1-G6 are those of '
                                   'possession-v212-plan.json and possession-v213-plan.json); evaluated on unrounded values'),
 'decision_rule': 'All seven gates pass: the pooled system with this weight is selected and integrated as possession-v2.15 (new entry '
                  'point and manifest; byte copies of the inference modules of commit 167dc7b; the three dfl6_both members with the '
                  'registered SHA-256; v2.11k becomes the next step of the technical ladder). It replaces v2.11k in the delivery only if, '
                  'by 16 Nov 2026 23:59 Istanbul, the ported inference runs under Python 3.10 / numpy 1.26.4, the output on synthetic '
                  'provided-like bundles is byte-identical across Python 3.10 / numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the full test '
                  'suite passes, a full-size chain rehearsal ends OK, and the documents describe the second model, its training data and '
                  'the three attempts; and only if the delivery chain then runs OK on the team\'s computer. Otherwise v2.11k stays. Any '
                  'gate fails: v2.11k stays the release, the candidate is recorded as tried and not used, and no further candidate with '
                  'the second model is registered before the deadline. The gates are applied once, to all rows; nothing is re-run with '
                  'other seeds, weights, pools or decoder constants.',
 'reported_alongside': P214['reported_alongside'],
 'not_part_of_this_validation': P214['not_part_of_this_validation'],
 'limits': [
  'Third attempt with the same gates. Each validation used new copies, but a gate that looks at single copies (G4) is passed more '
  'easily by a design that is tried again with a more cautious setting; a pass here is weaker evidence than a pass at the first '
  'attempt would have been. The weight was chosen on development copies with a margin, not by trying weights on the copies of this '
  'validation, and no further attempt follows.',
  'The validation matches were used for every earlier selection of v2.x, for the development of the TCN recipe by its author, for the '
  'development of v2.14 and, through the copies of the v2.14 validation, for the choice of this weight. Only the copies are new. This '
  'is a validation, not a fresh test.',
 ] + [x.replace('a released v2.14', 'a released v2.15').replace('the development of this candidate', 'the development of v2.14 and of this candidate')
      for x in P214['limits'] if not x.startswith('The validation matches were used')],
 'hashes': {
  'tcn_modules_sha256': {f: sha(V213 / 'tcn' / f) for f in MODULES},
  'tcn_weights_sha256': {f: sha(V214 / 'tcn_weights' / f) for f in DFL4 + DFL6},
  'validation_scripts': {**{f: sha(V / f) for f in ('exp_v215.py', 'pooling.py', 'assemble_v215.py', 'register_v215.py', 'pff_v215.py')},
                         'exp_v213.py': sha(V213 / 'exp_v213.py'), 'tcn_jax.py': sha(V214 / 'tcn_jax.py')},
  'development_scripts': {**{f: sha(V / f) for f in ('explore3.py', 'dev_summary215.py')},
                          **{f: sha(V214 / f) for f in ('cache_new.py', 'retcn2.py', 'explore2.py', 'lib214.py')}},
  'development_summary': sha(V / 'development_summary.json'),
  'v214_plan': sha(REPO / 'possession-v214-plan.json'), 'v214_results': sha(REPO / 'possession-v214-results.json'),
  'pff_game_3839': {'converted_match_npz': sha('/home/claude/pff/3839_match.npz'),
                    'run_pff.py': sha(REPO / 'experiments/possession_v2/pff_viewer/run_pff.py')},
  'helpers': {f: sha(WORK / f) for f in ('harness.py', 'exp_v25.py', 'exp_v210.py', 'camera_view.py', 'synth_broadcast.py',
                                         'synth_broadcast3.py', 'synth_clock.py', 'metrica_labels.py')},
  'v2_validation_models': {f: sha(WORK / 'cache' / f) for f in ('models_v2.pkl', 'stack_v2.pkl', 'models_v23.pkl', 'stack_v23.pkl')},
  'v2_released_bundles': {f: sha(REPO / 'models' / f) for f in ('possession-v2.npz', 'possession-v23.npz')},
  'possession_sources': {f: sha(REPO / 'possession' / f) for f in (
      'degrade.py', 'noise.py', 'keeper2.py', 'smooth.py', 'features.py', 'stack.py', 'decode.py', 'pipeline.py', 'trees.py',
      'bundle.py', 'evaluate.py', 'official_metrics.py', 'epts_export.py', 'fusion.py', 'register.py', 'clocksync.py', 'data.py')},
  'smoke_run': sha(V / 'exp_v215_smoke.json'),
 },
 'provided_fixture_used': False,
}
if mode == 'final':
    out = REPO / 'possession-v215-plan.json'
    assert not out.exists(), 'already registered'
else:
    out = V / 'possession-v215-plan-DRAFT.json'
out.write_text(json.dumps(plan, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(out, plan['registered_at'], sha(out))
