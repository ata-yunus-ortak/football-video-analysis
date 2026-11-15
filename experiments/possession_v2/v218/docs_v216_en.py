"""TECHNICAL_DOCUMENT.md for possession-v2.16 (step 10: players the tactical tracking has lost, added from the broadcast
tracking). Numbers come from possession-v216-results.json. Run once. Usage: docs_v216_en.py REPO_DIR"""
import json, sys
from pathlib import Path
import numpy as np
REPO = Path(sys.argv[1])
R = json.loads((REPO / 'possession-v216-results.json').read_text())
S = R['summary']
rows = lambda c, sel=lambda x: True: [x for x in R['rows'] if x['condition'] == c and sel(x)]
m = lambda c, arm, sel=lambda x: True: float(np.mean([x[arm]['spell_f1'] for x in rows(c, sel)]))
dfl = lambda x: x['copy'].startswith('J03'); met = lambda x: x['copy'].startswith('MET')
f3 = lambda x: f'{x:.3f}'
f4 = lambda x: f'{x:.4f}'
g = S['good']
assert R['selected'] and (g['better'], g['worse']) == (13, 3)


def edit(name, pairs):
    p = REPO / name
    s = p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding='utf-8')


edit('TECHNICAL_DOCUMENT.md', [
 ('# Possession v2.15 — technical document (short version)', '# Possession v2.16 — technical document (short version)'),
 ('''main input; the broadcast tracking is a second ball source behind a gate. No label of the provided
match is used anywhere.''',
  '''main input; the broadcast tracking is a second source behind a gate, for the ball and for players
the tactical tracking does not have at a moment. No label of the provided match is used anywhere.'''),
 ('**Pipeline** (`python -m possession.run215`):', '**Pipeline** (`python -m possession.run216`):'),
 ('''   are a team member's; its weights were trained for this release on the six DFL matches of
   Section 4. On the noisier path of step 5 nothing is averaged, because that was not measured, and
   the output is that of steps 1-8.
''',
  f'''   are a team member's; its weights were trained for this release on the six DFL matches of
   Section 4. On the noisier path of step 5 nothing is averaged, because that was not measured, and
   the output is that of steps 1-8.
10. *Players the tactical tracking has lost* (`possession/playerfill.py`; applied to the tracking
   before steps 8 and 1, only when the gate of step 6 is open). An automatic tracker loses players
   for a second or two, most often where players are close together, and the broadcast camera
   follows the ball and often still shows them. A broadcast player that, after the alignment and
   the registration of step 6 (the same per-frame offset that corrects the broadcast ball), has no
   tactical player of either team within 1.5 m is added to the tracking the models see, under the
   team the broadcast tracking gives it. Tactical positions are never moved or removed, and frames
   without an accepted broadcast frame get nothing.
   The step came out of a question the team asked late: should the closer camera take priority
   where the two agree? On external copies with a simulated second camera it should not: taking
   the ball or the players from the broadcast stream where both cameras see them changed the score
   by -0.005 to +0.002, even with a stream five times as precise as the tactical copy. What the
   second camera adds is what the first does not see. Adding the lost players gained {g['mean_diff']:+.4f} on 16
   new copies ({f4(g['v2_15_mean'])} -> {f4(g['candidate_mean'])}; better on {g['better']}, worse on {g['worse']}; Section 5). Without broadcast files, or
   with the gate closed, the output is that of steps 1-9.
'''),
 ('''track gaps and tracklets with the wrong team are part of the training corruption; track slots that
the metadata assigns to neither team are dropped.''',
  '''track gaps and tracklets with the wrong team are part of the training corruption; track slots that
the metadata assigns to neither team are dropped; a player whom the tactical tracking lacks and the
second camera shows is added (step 10).'''),
 ('''*Second camera:* used only to fill gaps, only
after the agreement gate (step 6); a tactical ball position is never replaced.''',
  '''*Second camera:* used only to fill gaps (the ball in step 6,
players in step 10), only after the agreement gate; a tactical position is never replaced.'''),
 ('| broadcast ATD + homography `valid` flag | used behind the 0.50 m agreement gate; `run.json` records whether the gate opened |',
  '| broadcast ATD + homography `valid` flag | used behind the 0.50 m agreement gate: its ball where the tactical ball is missing (step 6) and its players where the tactical tracking has none (step 10); `run.json` records whether the gate opened |'),
 ('''`possession-v215-results.json`). An earlier
vision line (ball detector, contact/control state machine, dead-ball layers under `development/`)
is not part of the submission.''',
  '''`possession-v215-results.json`). Giving the broadcast
tracking priority where the two cameras agree (its ball, its players, or the mean of the two balls)
was explored on development copies with a simulated second camera and not adopted (-0.005 to
+0.002; log entry K016); the one use with a gain, adding players the tactical tracking has lost,
was registered, passed the same seven gates on 16 new copies and is step 10
(`possession-v216-plan.json`, `possession-v216-results.json`). An earlier
vision line (ball detector, contact/control state machine, dead-ball layers under `development/`)
is not part of the submission.'''),
 ('''| 4 copies made with the team's other corruption simulator: without / with step 9 | | 0.667 / 0.687 |
''',
  f'''| 4 copies made with the team's other corruption simulator: without / with step 9 | | 0.667 / 0.687 |
| 16 further new copies with a simulated accurate broadcast camera: steps 1-9 / with the added players (step 10) | | {f3(g['v2_15_mean'])} / {f3(g['candidate_mean'])} |
| the 8 DFL copies of these / the 8 Metrica copies | | {f3(m('good', 'v2_15', dfl))} / {f3(m('good', 'candidate', dfl))} and {f3(m('good', 'v2_15', met))} / {f3(m('good', 'candidate', met))} |
| 8 of them, broadcast camera with medium calibration error: without / with step 10 | | {f3(S['medium']['v2_15_mean'])} / {f3(S['medium']['candidate_mean'])} |
| 8 of them, broadcast camera that itself loses players, invents players and mislabels teams: without / with step 10 | | {f3(S['good_degraded']['v2_15_mean'])} / {f3(S['good_degraded']['candidate_mean'])} |
| 4 copies made with the team's other corruption simulator, accurate broadcast camera: without / with step 10 | | {f3(S['sim2_good']['v2_15_mean'])} / {f3(S['sim2_good']['candidate_mean'])} |
'''),
 ('''  training run per seed on our side and nobody else has repeated that training; a re-run does not
  give the same bits. On the noisier model path the step is skipped.
''',
  f'''  training run per seed on our side and nobody else has repeated that training; a re-run does not
  give the same bits. On the noisier model path the step is skipped.
- **Added players.** The gain of step 10 was measured with a simulated second camera whose players
  come from the clean external positions. In three of the four conditions it never loses or
  invents a player inside its window; the fourth is one invented error profile (a tenth of its
  player positions lost, ghost players beside real ones, more tracks under the wrong team), and
  there the gain was {S['good_degraded']['mean_diff']:+.4f} with one copy {abs(S['good_degraded']['min']):.3f} lower. We did not examine the provided
  broadcast tracking: how often it loses or invents players is unknown, and a referee carried
  under a team by the broadcast tracking and absent from the tactical tracking would be added as
  a player. On copies made with the team's other simulator, which loses few players, the step
  changed almost nothing ({S['sim2_good']['mean_diff']:+.4f}; lower on {S['sim2_good']['worse']} of 4), so that gate passed by the smallest margin.
  Single copies moved between {g['min']:+.4f} and {g['max']:+.4f}. The step was picked among seven ways of using
  the second camera on four development copies before it was validated on new ones, and it was
  the fourth idea examined on these matches on the same day.
'''),
 ('''`REMEDIATION.md`. The code of steps 1-8 was written, and the weights of the network of step 9
were trained, with an AI coding assistant''',
  '''`REMEDIATION.md`. The code of steps 1-8 and 10 was written, and the weights of the network of step 9
were trained, with an AI coding assistant'''),
 ('''python -m possession.run215 --data-dir <bundle root> --out <new folder> \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast''',
  '''python -m possession.run216 --data-dir <bundle root> --out <new folder> \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast'''),
 ('''  `tests/test_possession_crossplatform.py` pins the output hashes of nine synthetic runs (steps
  1-6 on both model paths, with and without the broadcast camera and the clock; the same with
  step 8 on two bundles whose goalkeeper tracks carry the other team's id; two runs with step 9),''',
  '''  `tests/test_possession_crossplatform.py` pins the output hashes of eleven synthetic runs (steps
  1-6 on both model paths, with and without the broadcast camera and the clock; the same with
  step 8 on two bundles whose goalkeeper tracks carry the other team's id; two runs with step 9;
  two runs with step 10 on bundles whose tactical tracking loses players, one on each model path),'''),
])
print('TECHNICAL_DOCUMENT.md written')
