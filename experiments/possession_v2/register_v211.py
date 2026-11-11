"""Write possession-v211-plan.json (registration of the v2.11 validation, before any result of the candidate on a
validation or reserved match)."""
import hashlib, json, subprocess
from pathlib import Path
REPO, WORK = Path('/home/claude/sc'), Path('/home/claude/work')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
v210 = json.loads((REPO / 'possession-v210-results.json').read_text())
plan = {
 'version': 'possession-v2.11-plan',
 'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
 'background': {
  'v2_10': 'possession-v2.10 (possession/keeper.py) passed its four registered gates (possession-v210-results.json, written '
           + v210['written_at'] + '): correct ids 0.6655 -> 0.6655, one goalkeeper wrong 0.6270 -> 0.6644, both wrong 0.3271 -> 0.6634, '
           'wrong part of the time 0.6444 -> 0.6644. It was NOT released, for the reason below.',
  'found_after_that_decision': 'A reporting analysis of what v2.10 moved on its 8 validation copies with correct ids (work/gk/gk_none.py): '
           '77 of 80 moved pieces were goalkeepers that the corruption had put under the other id for 1-6 s; 3 were outfield players moved to the '
           'wrong team: a forward who stood still 13 m from the opponents\' goal for the last 2.5 minutes of DFL match J03WR9 (both copies; the '
           'goalkeeper stood further out), and a forward 26 m from goal for 15 s while the goalkeeper\'s track was lost (Metrica game 1). spellF1 '
           'was unchanged on those copies. The cause: v2.10 takes "nearest tracked player to the goal while play is in the other half" as proof '
           'of a goalkeeper. That fails when the goalkeeper is not tracked, and a camera that follows play may not show the far goalkeeper at all '
           '(DATA.md: mean 20.5 tracked objects; the tactical homography says the camera "is not pointed at the pitch" at half-time). The v2.10 '
           'plan did not cover that situation.',
  'provided_data': 'Whether the provided tracking shows the far goalkeeper, and whether it has goalkeeper id errors, is not known and is not looked at.',
 },
 'candidate': 'possession-v2.11 = possession-v2.9 with possession/keeper2.py applied to the tactical tracking that the models see (entry point '
              'possession.run211, wiring identical to the v2.10 candidate). Differences of keeper2.py from keeper.py: (1) a frame counts as evidence '
              'only if the piece is at least 8 m nearer to the goal than the second-nearest tracked player; (2) a piece under the other team\'s id '
              'is not moved on its own evidence: either the evidence of that goal in that half is mostly under the other id (at least 2500 frames '
              'and at least half of it), or the piece continues a goalkeeper piece in time and place.',
 'development': {
  'data': 'the four DFL training matches (J03WOH, J03WOY, J03WPY, J03WQQ), one corrupted copy each (seed 6000 + ...), 46-slot layout, no model run '
          '(work/gk2/far_dev.py, gap_stats.py, margins.py). Camera window (work/camera_view.py): players further than a half-width from the median x '
          'of all players (smoothed over 2 s, 2 m hysteresis) are not tracked.',
  'outfield_positions_moved_to_the_wrong_team_with_correct_ids': {
   'keeper2 (v2.11), matches WOH/WOY/WPY/WQQ': {'whole pitch': [0, 0, 0, 0], 'window 50 m': [0, 0, 0, 0], 'window 42 m': [0, 0, 0, 388], 'window 35 m': [0, 0, 0, 0]},
   'keeper (v2.10), matches WOH/WOY': {'whole pitch': [0, 0], 'window 50 m': [0, 0], 'window 42 m': [1671, 4303], 'window 35 m': [4973, 8373]}},
  'goalkeeper_positions_with_wrong_id_after_keeper2': {
   'both goalkeepers wrong (1.0 before)': {'whole pitch': [0.046, 0.021, 0.068, 0.0], 'window 50 m': [0.085, 0.031, 0.091, 0.009],
                                           'window 42 m': [0.259, 0.195, 0.221, 0.065], 'window 35 m': [1.0, 0.939, 0.779, 0.792]},
   'wrong 30% of the time (0.29-0.40 before)': {'whole pitch': [0.042, 0.044, 0.035, 0.0], 'window 50 m': [0.119, 0.082, 0.069, 0.091],
                                                'window 42 m': [0.281, 0.207, 0.165, 0.122], 'window 35 m': [0.362, 0.307, 0.311, 0.272]}},
  'evidence_frames_per_goal_and_half (WOY, WQQ)': 'under the other id with correct ids: at most 320 in every view (threshold 2500); with both '
          'goalkeepers wrong: 20242-42977 (whole pitch, 50 m), 6903-16302 (42 m), 597-2845 (35 m), under 400 (28 m)',
  'depth_gap (WOH, WOY)': 'a true goalkeeper who is the nearest player in a far frame is at least 8 m nearer to the goal than the second nearest '
          'in 96-99% of those frames',
  'smoke_test': 'exp_v211.py on training match J03WOH (in-sample for the validation models, numbers meaningless): window 42 m, correct ids: '
          'v2.9 0.6948, v2.11 0.6948 (no outfield position moved), v2.10 0.6936 (5200 outfield positions moved)',
 },
 'seen_before_registration': 'Everything above; all rows of the v2.10 validation (same four validation matches, other copies) and the analysis of '
          'its moved pieces, which prompted this redesign. No result of keeper2 on a validation or reserved match. The validation matches are '
          'therefore not fresh for this design choice (they never were: used for every earlier selection).',
 'validation': {
  'script': 'experiments/possession_v2/exp_v211.py (camera window: experiments/possession_v2/camera_view.py)',
  'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
  'copies': '8 new corrupted copies: possession.degrade, v2 profile (RANGES), seed 11100 + 10 * match_index + j, j = 0, 1',
  'conditions': {
   'none': 'team ids as corrupted, whole pitch in view',
   'gk_one': 'the home goalkeeper carries the away team\'s id for the whole match',
   'gk_both': 'both goalkeepers carry the other team\'s id for the whole match',
   'gk_part': 'each goalkeeper carries the other team\'s id during random stretches of 30-300 s covering 30% of the match',
   'view42_none': 'camera window of +-42 m around the centre of play, team ids as corrupted',
   'view35_none': 'camera window of +-35 m, team ids as corrupted',
   'view42_gk_both': 'camera window of +-42 m, both goalkeepers under the other id (reported, not a gate)'},
  'error_seeds': '21100 + 100 * condition_index + copy_index',
  'layout': 'tracks packed into 46 anonymous slots, 23 per team (possession/epts_export.pack)',
  'systems': {'v2_9': 'noise gate, then the v2.1 or v2.3 path (tactical camera only)',
              'v2_11': 'the same after possession.keeper2.correct_goalkeepers; the noise gate is decided on the tracking as given',
              'v2_10': 'the same after possession.keeper.correct_goalkeepers, only in view42_none and view35_none (reported, not a gate)'},
  'models': 'the validation models (trained on the four training matches only), work/exp_v25.run_path',
  'metric': 'spellF1 (organisers\' possession_metrics) on the provider / proxy labels',
  'seeds_checked_unused': '11100-11131, 21100-21707, 21199-21799 and 31103 occur in no earlier plan, results file, document or script (searched on registration)',
 },
 'gates': {
  'G1 neutral with correct ids': 'condition none: mean(v2_11 - v2_9) >= -0.002 and no copy below -0.005',
  'G2 both goalkeepers': 'condition gk_both: mean(v2_11) >= mean(v2_9 under condition none) - 0.015',
  'G3 one goalkeeper': 'condition gk_one: mean(v2_11) >= mean(v2_9 under none) - 0.010 and mean(v2_11 - v2_9) >= +0.008',
  'G4 part of the time': 'condition gk_part: mean(v2_11) >= mean(v2_9 under none) - 0.010 and mean(v2_11 - v2_9) >= 0',
  'G5 neutral when the far goalkeeper is often out of view': 'condition view42_none: mean(v2_11 - v2_9) >= -0.002 and no copy below -0.005',
  'G6 neutral when the far goalkeeper is mostly out of view': 'condition view35_none: mean(v2_11 - v2_9) >= -0.002 and no copy below -0.005',
 },
 'decision_rule': 'All six gates pass: possession-v2.11 becomes the release (entry point possession.run211, new manifest; possession-v2.9 stays as the '
                  'next step of the technical ladder). Any gate fails: possession-v2.9 stays the release. possession-v2.10 is not released in '
                  'either case. The gates are applied once, to all rows. G1-G4 are the gates of the v2.10 plan with the same thresholds.',
 'reported_alongside': [
  'every row; goalkeeper positions with a wrong id before and after; outfield positions moved to the wrong team',
  'view42_gk_both: not a gate, because failing to correct is not a loss against possession-v2.9',
  'possession-v2.10 in the two camera-window conditions with correct ids',
  'reserved Metrica game 3, one new copy (seed 31103), the seven conditions, once, after the decision (not a gate)',
  'a full-size rehearsal of the entry point on the synthetic provided-like bundle with both goalkeepers exchanged (wiring, not a gate)'],
 'limits': [
  'The errors and the camera window are simulated by us; the provided tracking may have none of them or a different kind. The candidate is a safeguard, not a measured improvement on the provided match.',
  'If the far goalkeeper is mostly out of view (window of about 35 m or less in the simulation), wrong goalkeeper ids are not corrected: there is no evidence to do it safely.',
  'The correction is validated with the tactical camera only; the broadcast path is unchanged by construction.',
  'Fixtures accessed before; the validation matches have been used for every earlier selection, including the v2.10 validation that prompted this redesign.'],
 'hashes': {'possession/keeper2.py': sha(REPO / 'possession/keeper2.py'), 'possession/keeper.py': sha(REPO / 'possession/keeper.py'),
            'work/exp_v211.py': sha(WORK / 'exp_v211.py'), 'work/camera_view.py': sha(WORK / 'camera_view.py'), 'work/exp_v210.py': sha(WORK / 'exp_v210.py'),
            'possession/epts_export.py': sha(REPO / 'possession/epts_export.py'),
            'possession-v29-release.json': sha(REPO / 'possession-v29-release.json'),
            'possession-v210-plan.json': sha(REPO / 'possession-v210-plan.json'), 'possession-v210-results.json': sha(REPO / 'possession-v210-results.json')},
 'provided_fixture_used': False,
}
assert plan['hashes']['possession/keeper.py'] == json.loads((REPO / 'possession-v210-plan.json').read_text())['hashes']['possession/keeper.py']
(REPO / 'possession-v211-plan.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8')
print(plan['registered_at'], plan['hashes']['possession/keeper2.py'][:16], plan['hashes']['work/exp_v211.py'][:16])
