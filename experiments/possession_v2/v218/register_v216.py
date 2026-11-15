"""Write the registration of the v2.16 validation (players the tactical tracking has lost, added from the broadcast
tracking) before any validation row exists. Usage: /usr/bin/python3 register_v216.py"""
import hashlib, json, os, sys, glob, platform
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
REPO, V = Path('/home/claude/sc'), Path('/home/claude/work/v218')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p in range(4):
    assert not (V / f'exp_v216_{p}.json').exists(), 'registration must come before any validation row'
assert not (REPO / 'possession-v216-results.json').exists()
# the exploration that led here (development copies; cam1 / cam2 / cam3)
rows = []
for f in sorted(glob.glob(str(V / 'cam[123]_*.json'))):
    rows += json.loads(Path(f).read_text())['rows']
by = {(r['copy'], r['condition']): r['fused']['spell_f1'] for r in rows}
def diffs(a, b):
    return {c: round(by[(c, b)] - by[(c, a)], 4) for c in sorted({c for c, k in by if k == b}) if (c, a) in by}
seen = {'sharp stream, F - release': diffs('sharp|A', 'sharp|F'), 'good stream, F - release': diffs('good|A', 'good|F'),
        'good stream with degraded players, F - release': diffs('good_degraded|A', 'good_degraded|F'),
        'sharp stream, PF - release': diffs('sharp|A', 'sharp|PF'), 'good stream, PF - release': diffs('good|A', 'good|PF'),
        'sharp stream, B1 - release': diffs('sharp|A', 'sharp|B1'), 'good stream, B1 - release': diffs('good|A', 'good|B1'), 'medium stream, B1 - release': diffs('medium|A', 'medium|B1'),
        'sharp stream, P - release': diffs('sharp|A', 'sharp|P'), 'good stream, P - release': diffs('good|A', 'good|P'), 'medium stream, P - release': diffs('medium|A', 'medium|P'),
        'sharp stream, B2 - release': diffs('sharp|A', 'sharp|B2'), 'good stream, B2 - release': diffs('good|A', 'good|B2'),
        'sharp stream, C - release': diffs('sharp|A', 'sharp|C'), 'good stream, C - release': diffs('good|A', 'good|C'),
        'sharp stream, no second camera - release': diffs('sharp|A', 'sharp|T')}
wiring = json.loads((V / 'exp_v216_wiring.json').read_text())
w = {r['condition']: round(r['fused']['spell_f1'], 4) for r in wiring['rows']}
assert w == {'good|v2_15': round(by[('J03WN1|23100', 'good|A')], 4), 'good|candidate': round(by[('J03WN1|23100', 'good|F')], 4)}, 'the validation script does not reproduce the exploration rows'
SEEDS = [28100 + 10 * mi + j for mi in range(4) for j in range(4)] + [58100, 68100, 78100, 88100]
hits = []
for root in (REPO, Path('/home/claude/work')):
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in ('/cache', '__pycache__', '/.git', '/probs', '/tcn_cache', '/tcn_weights', '/dev', 'repro25_fixture')):
            continue
        for f in fn:
            if f in ('exp_v216.py', 'register_v216.py', 'assemble_v216.py') or not f.endswith(('.py', '.json', '.md', '.log', '.txt', '.sh')):
                continue
            try:
                text = open(os.path.join(dp, f), errors='ignore').read()
            except OSError:
                continue
            import re
            if any(re.search(r'(?<![0-9.])%d(?![0-9])' % s, text) for s in SEEDS):
                hits.append(os.path.join(dp, f))
plan = {
 'version': 'possession-v2.16-plan',
 'registered_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
 'candidate': 'possession-v2.16 = possession-v2.15 with one added step, possession/playerfill.py: when the broadcast files are present and the accuracy gate of possession/fusion.py is open '
              '(the two cameras agree on the ball), a broadcast player that, after the time alignment and the player-based registration of possession/register.py, has no tactical player of either team '
              'within 1.5 m is added to the tracking the models see, in an extra slot, under the team the broadcast tracking gives it; the goalkeeper team check then runs on the tracking with the added players. '
              'Tactical positions are never moved. Without broadcast files, or with the gate closed, the output is that of v2.15. Models, pooling, decoders, ball fill and the kick-off rule are unchanged.',
 'why': 'Asked by the team lead on 15 Nov 12:24: should the broadcast camera get priority where it agrees with the tactical camera, because it is closer and clearer. Explored on development copies with a simulated '
        'second camera (cam1.py, cam2.py, cam3.py; log entry K016): taking the ball or the players from the broadcast stream where both cameras agree changed the score by -0.005 to +0.002 even with a broadcast stream five '
        'times as precise as the tactical copy; what the second camera adds is what the first does not see. The release uses that for the ball only (+0.036 to +0.043 on these copies). Players the tactical copy '
        'has lost and the broadcast stream sees were the one further use with a gain on the development copies.',
 'rule_fixed_before_any_validation_row': {
     'module': 'possession/playerfill.py (the file that would be released), SHA-256 below',
     'steps': ['offset per accepted broadcast frame at the ball from players seen by both cameras (register.frame_offsets), median over +-0.5 s: exactly the offset that register_ball subtracts from the broadcast ball',
               'registered broadcast player = broadcast player - offset; frames without an accepted broadcast frame or without an offset get nothing',
               'added if no tactical player of either team (tracking as given, before the goalkeeper check) lies within EMPTY_R_M = 1.5 m of it',
               'one extra slot per broadcast track; team = team of the broadcast track after the alignment has oriented the stream',
               'used only when fusion.fuse_gated reports the gate open; then keeper2.correct_goalkeepers runs on tactical + added players and the filled ball is set as in v2.15'],
     'constants_chosen': 'EMPTY_R_M = 1.5 was the only value tried. Variants that also replace positions (P, PF) were tried and not taken (no clear gain over adding alone, and they move tactical positions).'},
 'models_per_match': {'J03WN1, J03WR9 (DFL)': 'v2 side: validation models trained on J03WOH, J03WOY, J03WPY, J03WQQ; network: dfl4_both_s0, s1, s2 (as in the v2.15 validation)',
                      'Metrica games 1, 2': 'the released pair: models/possession-v2.npz, possession-v23.npz and dfl6_both_s0, s1, s2 (= models/possession-tcn-v215.npz)'},
 'seen_on_external_data_before_registration': {
     'what': 'spellF1 differences on development copies (J03WN1, J03WR9, MET1, MET2; copy seeds 23100 + 10 * match_index + j, streams 53100, clocks 63100, stream degradation 73100); v2.15 decision in both arms',
     'rows': seen,
     'also': 'everything listed in possession-v215-plan.json and the K014 / K015 records'},
 'validation': {
     'script': 'v218/exp_v216.py (parts 0-3), which imports v215/exp_v215.py (row_for: the v2.15 decision), v213/exp_v213.py (copies, alignment, registration, gate), v218/cam1.py (stream quality) and v218/cam3.py '
               '(degraded stream) unchanged; gates applied by v218/assemble_v216.py, written before any validation row',
     'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
     'copies': '16 new corrupted copies: possession.degrade, v2 profile (RANGES), seed 28100 + 10 * match_index + j, j = 0..3; packed into 46 anonymous slots; noise gate on the tracking as given; goalkeeper check (keeper2)',
     'conditions': {'good': 'all 16 copies: simulated broadcast stream (synth_broadcast3.simulate_warp), regime good of exp_v25.REGIMES, simulated clock readings; stream seed 58100 + 4 * match_index + j, clock 68100 + 4 * match_index + j',
                    'medium': 'copies j = 0, 1 (8): regime medium; stream seed 58200 + 4 * match_index + j, clock 68200 + 4 * match_index + j',
                    'good_degraded': 'copies j = 0, 1 (8): the stream of condition good of that copy with broadcast players lost (10% of the time and 25% of close encounters), invented (four ghost tracks, copies of '
                                     'visible players displaced by 2-5 m, 30% under the other team) and under the wrong team (two more tracks), cam3.degrade_bro, seed 78100 + 4 * match_index + j',
                    'sim2_good': 'one copy per match made with the team member\'s simulator (seed 88100 + match_index), regime good; stream seed 58400 + 4 * match_index, clock 68400 + 4 * match_index'},
     'arms': {'v2_15': 'the release logic: goalkeeper-checked tactical tracking, ball filled behind the gate, pooled decision', 'candidate': 'the same with the added players'},
     'seeds_found_elsewhere': hits},
 'gates': {
     'G1 gain': 'condition good, all 16 copies: mean(candidate - v2_15) spellF1 >= +0.008',
     'G2 gain on provider flags': 'condition good, the 8 DFL copies: mean >= +0.008',
     'G3 no harm on event proxies': 'condition good, the 8 Metrica copies: mean >= -0.002',
     'G4 no bad copy': 'condition good: every copy has candidate - v2_15 >= -0.010',
     'G5 macroF1': 'condition good, all 16 copies: mean(candidate - v2_15) macroF1 >= -0.003',
     'G6 other streams': 'conditions medium and good_degraded, 8 copies each: mean(candidate - v2_15) spellF1 >= 0.000 in each',
     'G7 other simulator': 'condition sim2_good, 4 copies: mean(candidate - v2_15) spellF1 >= 0.000',
     'note': 'the seven gates and thresholds of possession-v212/-v213/-v214/-v215-plan.json, moved to the conditions in which this candidate differs from the release (it changes nothing without the second camera); '
             'evaluated on unrounded values, once, on all rows'},
 'decision_rule': 'All seven gates pass: the step is selected and integrated as possession-v2.16 (new entry point derived from run215.py, new manifest, v2.15 becomes the next step of the technical ladder). '
                  'It replaces v2.15 in the delivery only if, by 16 Nov 2026 23:59 Istanbul, it runs under Python 3.10 / numpy 1.26.4, the output on synthetic provided-like bundles (variants with added players included) is '
                  'byte-identical across Python 3.10 / numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the full test suite passes, a full-size chain rehearsal ends OK and the documents describe the step; and only if the '
                  'delivery chain then runs OK on the team\'s computer. Otherwise v2.15 stays. Any gate fails: v2.15 stays the release, the candidate is recorded as tried and not used, and no further candidate that takes '
                  'players from the broadcast tracking is registered before the deadline. Nothing is re-run with other seeds, radii or stream settings.',
 'reported_alongside': ['every row; means per source in every condition; the same differences for the decision without the second model (v2.11 logic); numbers and precision of the added positions; gate state per copy'],
 'not_part_of_this_validation': ['The Smart Tagging kick-off rule (unchanged, not measurable externally).', 'The provided match: not read, not run and not scored.',
                                 'Any property of the provided broadcast tracking (how often it loses or invents players, how its team labels behave): unknown and not looked at.'],
 'limits': ['The second camera is simulated. Its players come from the clean external positions with a window, calibration errors and noise; in conditions good, medium and sim2_good it never loses or invents a player inside its window. '
            'Condition good_degraded is one invented error profile. A pass says the step helps under these assumptions.',
            'The step was picked among seven variants on four development copies (two stream draws each), so its development gain is biased upwards; the copies of this validation are new, the matches are not.',
            'A referee or any other non-player that the broadcast tracking carries under a team and the tactical tracking does not would be added as a player. The simulation has no such track.',
            'Fourth candidate of 15 November built on the same matches (K014, K015, K016 explorations). The organisers state that differences below about 0.04 are noise on one match.'],
 'hashes': {'possession/playerfill.py': sha(REPO / 'possession' / 'playerfill.py'), 'possession/register.py': sha(REPO / 'possession' / 'register.py'),
            'possession/fusion.py': sha(REPO / 'possession' / 'fusion.py'), 'exp_v216.py': sha(V / 'exp_v216.py'), 'assemble_v216.py': sha(V / 'assemble_v216.py'),
            'cam1.py': sha(V / 'cam1.py'), 'cam2.py': sha(V / 'cam2.py'), 'cam3.py': sha(V / 'cam3.py'), 'register_v216.py': sha(V / 'register_v216.py'),
            'possession-v215-release.json': sha(REPO / 'possession-v215-release.json')},
 'environment': {'python': platform.python_version(), 'numpy': np.__version__},
 'provided_fixture_used': False}
(REPO / 'possession-v216-plan.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8')
print('registered at', plan['registered_at'], '| seeds found elsewhere:', hits)
print(json.dumps(seen, indent=0)[:1500])
