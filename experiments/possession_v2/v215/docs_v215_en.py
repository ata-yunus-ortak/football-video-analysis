"""English documents for a SELECTED possession-v2.15 (run only after the gates passed and the release was frozen;
numbers of the v2.14 attempt from possession-v214-results.json):
TECHNICAL_DOCUMENT.md, README.md, DATA_SOURCES.md, AGENTS.md of the given repository copy, by exact replacements
(each must match once). Numbers come from possession-v215-results.json. Usage: docs_v214_en.py REPO_DIR"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
res = json.loads((REPO / 'possession-v215-results.json').read_text())
assert res['selected'] and all(res['gates'].values())
r214 = json.loads((REPO / 'possession-v214-results.json').read_text())
plan = json.loads((REPO / 'possession-v215-plan.json').read_text())
W = plan['fusion_rule_fixed_before_any_score']['weight']
T14 = r214['summary']['tactical']
S = res['summary']
f4 = lambda x: f'{x:.4f}'
f3 = lambda x: f'{x:.3f}'
sg = lambda x: f'{x:+.4f}'
worst = min(r['diff_spell_f1'] for r in res['rows'] if r['condition'] == 'tactical')
best = max(r['diff_spell_f1'] for r in res['rows'] if r['condition'] == 'tactical')
_alone = [r['tcn_alone']['spell_f1'] - r['v2_11']['spell_f1'] for r in res['rows'] if r['condition'] == 'tactical']
ALONE_WORSE, ALONE_MIN = sum(d < 0 for d in _alone), min(_alone)
assert ALONE_WORSE == 7 and round(ALONE_MIN, 4) == -0.0145, (ALONE_WORSE, ALONE_MIN)


def edit(name, pairs):
    p = REPO / name
    s = p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding='utf-8')


T = S['tactical']; TD = S['tactical_DFL']; TM = S['tactical_Metrica']; FG = S['fill_good']; FM = S['fill_medium']; S2 = S['tactical_sim2']; V42 = S['view42']

# ------------------------------------------------------------------------------------------ TECHNICAL_DOCUMENT.md
edit('TECHNICAL_DOCUMENT.md', [
 ('# Possession v2.11k — technical document (short version)', '# Possession v2.15 — technical document (short version)'),
 ('**Pipeline** (`python -m possession.run211k`):', '**Pipeline** (`python -m possession.run215`):'),
 ('''   explicitly. Instead the models and the decoder run on the whole graded second half
   (`possession.run211g`), and then one rule is applied (`possession/kickoff.py`): in a graded''',
  '''   explicitly. Instead the models and the decoder run on the whole graded second half, and then
   one rule is applied (`possession/kickoff.py`): in a graded'''),
 ('''   Without the file or a usable tag the models' labels stand (the next step of the technical
   ladder is exactly that). Appendix R names the entry point that produced the submitted file and
   says whether a tag was used.''',
  '''   Without the file or a usable tag the models' labels stand. Appendix R names the entry point
   that produced the submitted file and says whether a tag was used.'''),
 ('''   1-7 alone. We did not look at whether the provided tracking has such errors; Appendix R says
   whether anything was moved.
''', f'''   1-7 alone. We did not look at whether the provided tracking has such errors; Appendix R says
   whether anything was moved.
9. *Second model family* (`possession/tcn/`, `possession/pooling.py`; between steps 3 and 4, on the
   core path of step 5). A dilated temporal convolution network reads 37 team-level quantities per
   frame at 12.5 Hz (ball seen or not, its position, speed and the length of the gap around it;
   for each team the distance of its nearest player to the ball, players near the ball, centroid,
   spread and speed) and sees about 25 s on either side of a frame. It outputs home / away / dead.
   Its probabilities (three trained copies, both team orders averaged) and those of step 3 are
   averaged with weight {W} for the network and {1 - W:.1f} for the trees, and the average goes through
   the decoder of step 4, unchanged. With that weight the network can move each of the three
   probabilities by at most {W}: it has a say where the trees are undecided and cannot overrule them
   where they are sure.
   The two families use the same tracking differently (trees on hand-built windows of up to 10 s;
   a network with a long memory on raw team geometry), and on new external copies the average was
   better than the trees alone on {T['copies_better']} of {T['n']} copies, equal on the {T['n'] - T['copies_better'] - T['copies_worse']} that take the noisier path of step 5
   and worse on {T['copies_worse']} ({f4(T['v2_11']['spell_f1'])} -> {f4(T['fused']['spell_f1'])}, Section 5). The network's design, features and NumPy inference
   are a team member's; its weights were trained for this release on the six DFL matches of
   Section 4. On the noisier path of step 5 nothing is averaged, because that was not measured, and
   the output is that of steps 1-8.
'''),
 ('''`possession-v213-results.json`). An earlier
vision line''', f'''`possession-v213-results.json`). A second attempt changed what a diagnosis on the already-scored
copies pointed at: the network was re-trained on the corruption of both simulators (the committed
weights broke on the other simulator's false ball detections), three trained copies were used on
every row, and the average was decoded by our decoder instead of a single-cost one (v2.14, equal
weights). On 16 new copies it was better on {T14['copies_better']} ({sg(T14['diff_spell_f1_mean'])}), but one copy was {abs(T14['diff_spell_f1_min']):.3f} worse, and
the gate that allows no copy below -0.010 failed; it was not released (`possession-v214-plan.json`,
`possession-v214-results.json`). The third and last attempt lowered the network's weight to {W} by a
rule written down while the second was still running, was registered before any new result, passed
the same seven gates on 16 further new copies and is step 9 (`possession-v215-plan.json`,
`possession-v215-results.json`). An earlier
vision line'''),
 ('''A training row is every sixth frame of three independently corrupted copies of a match, also with
the teams exchanged (856,678 rows per bundle). A seventh DFL match is reserved for one final test
of the frozen release (design registered in `possession-final-test-plan.json`). The process that
built the release has not downloaded it; a team member used it while developing the second model
named in Section 3, which is not part of the release.''',
  '''A training row of the tree models is every sixth frame of three independently corrupted copies of
a match, also with the teams exchanged (856,678 rows per bundle). The network of step 9 was trained
on the same six matches and labels: twelve corrupted copies of every half (six per corruption
simulator of the team, half of them with the teams exchanged), every second frame, in crops of
2,048 steps; three runs with different seeds (`experiments/possession_v2/v214/tcn_jax.py`). During
selection, networks trained on four of the matches were used for the two DFL validation matches.

A seventh DFL match is reserved for one final test of steps 1-8, the release without the second
model (design registered in `possession-final-test-plan.json`). The process that built the release
and trained its weights has not downloaded it. A team member used it, with the other matches, while
he designed the network of step 9; the weights in the release were trained without it. For the
network's design it is therefore not an untouched match, and there is no untouched test for the
averaged system.'''),
 ('''| same copies seen by a camera that does not track players beyond 42 m (35 m) from play, ids correct: without / with | | 0.649 / 0.649 (0.646 / 0.646) |
''', f'''| same copies seen by a camera that does not track players beyond 42 m (35 m) from play, ids correct: without / with | | 0.649 / 0.649 (0.646 / 0.646) |
| 16 new copies (2 DFL + 2 Metrica matches), tactical camera: steps 1-8 / with the second model (step 9) | | {f3(T['v2_11']['spell_f1'])} / {f3(T['fused']['spell_f1'])} |
| the 8 DFL copies of these / the 8 Metrica copies | | {f3(TD['v2_11']['spell_f1'])} / {f3(TD['fused']['spell_f1'])} and {f3(TM['v2_11']['spell_f1'])} / {f3(TM['fused']['spell_f1'])} |
| 8 of them with a simulated accurate (medium) broadcast fill: without / with step 9 | | {f3(FG['v2_11']['spell_f1'])} / {f3(FG['fused']['spell_f1'])} ({f3(FM['v2_11']['spell_f1'])} / {f3(FM['fused']['spell_f1'])}) |
| 4 copies made with the team's other corruption simulator: without / with step 9 | | {f3(S2['v2_11']['spell_f1'])} / {f3(S2['fused']['spell_f1'])} |
'''),
 ('''- **Label semantics.** DFL possession flags''', f'''- **Second model.** The gain of step 9 was measured on new copies of matches that had been used
  before, for this and for every earlier choice, and the network had been shown both corruption
  simulators of the team; whether it holds on tracking corrupted in a way neither simulator
  produces is not known. It passed its gates at the third attempt with the same gates (Section 3),
  which is weaker evidence than a pass at the first attempt. Single copies moved between {sg(worst)}
  and {sg(best)}. Alone, the network scored {f3(T['tcn_alone']['spell_f1'])} against {f3(T['v2_11']['spell_f1'])} and was worse than the trees on {ALONE_WORSE}
  of the {T['n']} copies (by up to {abs(ALONE_MIN):.3f}); it is used only in the average. Its weights come from one
  training run per seed on our side and nobody else has repeated that training; a re-run does not
  give the same bits. On the noisier model path the step is skipped.
- **Label semantics.** DFL possession flags'''),
 ('''python -m possession.run211k --data-dir <bundle root> --out <new folder> \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast''',
  '''python -m possession.run215 --data-dir <bundle root> --out <new folder> \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast'''),
 ('''- The run verifies the SHA-256 of every inference source file and both model bundles against the
  release manifest and refuses to run if anything changed.''',
  '''- The run verifies the SHA-256 of every inference source file, both tree bundles and the network
  weights against the release manifest and refuses to run if anything changed.'''),
 ('''  `tests/test_possession_crossplatform.py` pins the output hashes of seven synthetic runs (steps
  1-6 on both model paths, with and without the broadcast camera and the clock; the same with
  step 8 on two bundles whose goalkeeper tracks carry the other team's id), recorded on Linux;
  the delivery tool runs it on the computer that generates the file. The kick-off rule of step 7
  only rewrites labels before an integer frame and has no floating-point part.''',
  '''  `tests/test_possession_crossplatform.py` pins the output hashes of nine synthetic runs (steps
  1-6 on both model paths, with and without the broadcast camera and the clock; the same with
  step 8 on two bundles whose goalkeeper tracks carry the other team's id; two runs with step 9),
  recorded on Linux; the delivery tool runs it on the computer that generates the file. The
  network of step 9 is evaluated in float64 NumPy and its probabilities are rounded to four
  decimals before the averaging and to six after it; its unrounded values differ between NumPy
  builds, the rounded ones did not in our checks. The kick-off rule of step 7 only rewrites labels
  before an integer frame and has no floating-point part.'''),
 ('''Training from the public data: `python -m possession.train` with `possession-v2-config.json` and
`possession-v23-config.json` (see the long document). Experiment scripts:
`experiments/possession_v2/`.''',
  '''Training from the public data: the tree bundles with `python -m possession.train` and
`possession-v2-config.json` / `possession-v23-config.json` (see the long document); the network
weights with `experiments/possession_v2/v214/tcn_jax.py` (JAX on CPU; a re-run gives equivalent,
not bit-identical weights, so the release pins the files it was validated with). Experiment
scripts: `experiments/possession_v2/`.'''),
])
print('TECHNICAL_DOCUMENT.md edited')

edit('TECHNICAL_DOCUMENT.md', [
 ('''files, or with the gate closed, the output is the tactical-only result, and `run.json` records
which path was taken.''', '''files, or with the gate closed, the output is the tactical-only result, and `run.json` records
which path was taken. *Second model:* the network of step 9 reads the same corrected tracking;
where the ball is missing it is given the position bridged across the gap together with the
length of the gap, and it was trained on copies with the gaps and false detections of both
simulators.'''),
 ('''The v2 code was written with an AI coding assistant that worked only on source
code, public external data and aggregate external results; the pipeline is run on the provided data
locally by the team.''', '''The code of steps 1-8 was written, and the weights of the network of step 9
were trained, with an AI coding assistant that worked only on source code, public external data and
aggregate external results. The network's design and inference code were written by a team member
on his own branch (`mtah-possession`). The pipeline is run on the provided data locally by the
team.'''),
])

# ------------------------------------------------------------------------------------------ README.md
edit('README.md', [
 ('''| `possession-final-test-plan.json` | registered final test of the frozen release on a reserved external match (`python -m tools.possession_final_test`); its results file exists once the team has run it |''',
  '''| `possession-final-test-plan.json` | registered final test of `possession-v2.11k` (the release without the second model) on a reserved external match (`python -m tools.possession_final_test`); its results file exists once the team has run it. It was not re-registered for v2.15: the second model's designer had used that match |'''),
 ('## Submission system: possession v2.11k', '## Submission system: possession v2.15'),
 ('''Release `possession-v2.11k`, entry point `python -m possession.run211k`, manifest
`possession-v211k-release.json`. The release and its technical fall-backs (the next one is
`possession-v2.11g`) are named in `possession-release.json`.''',
  '''Release `possession-v2.15`, entry point `python -m possession.run215`, manifest
`possession-v215-release.json`. The release and its technical fall-backs (the next one is
`possession-v2.11k`, the same system without the second model) are named in `possession-release.json`.'''),
 ('python -m possession.run211k --data-dir <bundle root> --out <new folder> --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast',
  'python -m possession.run215 --data-dir <bundle root> --out <new folder> --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast'),
 ('''Reserve: `possession-release-graded-windows.json` is the same ladder without the Smart Tagging kick-off
rule (`possession.run211g` first): `python -m tools.possession_deliver --release-config possession-release-graded-windows.json ...`.''',
  '''Reserve: `possession-release-graded-windows.json` is the ladder without the Smart Tagging kick-off
rule and without the second model (`possession.run211g` first): `python -m tools.possession_deliver --release-config possession-release-graded-windows.json ...`.'''),
 ('''- **Goalkeeper team check (v2.11):** goalkeeper track pieces that carry the other team's id are moved
  to the team that defends their goal before the features are computed (`possession/keeper2.py`);
  with correct ids nothing changes.
''', f'''- **Goalkeeper team check (v2.11):** goalkeeper track pieces that carry the other team's id are moved
  to the team that defends their goal before the features are computed (`possession/keeper2.py`);
  with correct ids nothing changes.
- **Second model (v2.15):** on the core path, the probabilities of the tree models are averaged with
  those of a temporal convolution network (`possession/tcn/`, `models/possession-tcn-v215.npz`; design
  by a team member, weights trained on the same six DFL matches with both of the team's corruption
  simulators) and the average goes through the unchanged decoder (`possession/pooling.py`). On the
  noisier path nothing is averaged.
'''),
 ('''with correct team ids, 0.335 -> 0.656 with both goalkeepers under the other team's id (simulated). Tested''',
  f'''with correct team ids, 0.335 -> 0.656 with both goalkeepers under the other team's id (simulated);
second model {f3(T['v2_11']['spell_f1'])} -> {f3(T['fused']['spell_f1'])} on 16 new copies (better on {T['copies_better']}, log entry K013). Tested'''),
 ('''(v2.7), Metrica training (v2.8), touch / control-change columns (v2.12, log entry K008), averaging
the models' probabilities with a team member's temporal convolution network (v2.13, log entry K010).''',
  '''(v2.7), Metrica training (v2.8), touch / control-change columns (v2.12, log entry K008), a first
way of averaging the models' probabilities with a team member's temporal convolution network (v2.13,
log entry K010) and a second way with re-trained weights and equal weights (v2.14, log entry K012;
better on 15 of 16 copies but one copy clearly worse; the third way, with a smaller weight, is the
release).'''),
])
print('README.md edited')

# ------------------------------------------------------------------------------------------ DATA_SOURCES.md
edit('DATA_SOURCES.md', [
 ('''access it. No raw or prepared data is stored in this repository; the two model bundles under
`models/` contain only decision-tree arrays.''',
  '''access it. No raw or prepared data is stored in this repository; the three model files under
`models/` contain only decision-tree arrays (two bundles) and the weights of one small network.'''),
 ('''match J03WMX reserved as a final test, not downloaded or used by the process that built the release (a team member used it for a separate model that is not part of the release) | no (only trees trained on it: `models/possession-v2.npz`, `models/possession-v23.npz`) |''',
  '''match J03WMX reserved as a final test, not downloaded or used by the process that built the release and trained its weights (a team member used it while he designed the network of the second model) | no (only models trained on it: `models/possession-v2.npz`, `models/possession-v23.npz`, `models/possession-tcn-v215.npz`) |'''),
 ('''| numpy 1.26.4, scipy 1.11.4, pandas 2.1.4 (inference); scikit-learn 1.9.1 (training only) | PyPI | BSD-3-Clause | runtime / training | no |''',
  '''| numpy 1.26.4, scipy 1.11.4, pandas 2.1.4 (inference); scikit-learn 1.9.1 (training of the trees only); jax 0.12.0.1 and optax 0.2.9 (training of the network only) | PyPI | BSD-3-Clause; JAX and Optax Apache-2.0 | runtime / training | no |'''),
 ('''A team member's temporal convolution network (branch `mtah-possession` of the team repository; weights
trained by him on the six DFL training matches below, and on five of them for the rows scored on the
sixth; recipe developed by him on all seven DFL matches and Metrica games 1-3): its probabilities were
averaged with the release's in a registered validation
and the combination was not selected (log entry K010, `possession-v213-plan.json`,
`possession-v213-results.json`). The release does not load it and its weights are not in this branch.''',
  '''The weights a team member trained for his temporal convolution network (branch `mtah-possession` of
the team repository; on the six DFL training matches below, and on five of them for the rows scored on
the sixth) were averaged with the release's probabilities in a registered validation, and that
combination was not selected (log entry K010, `possession-v213-plan.json`,
`possession-v213-results.json`). Those weights are not loaded by the release and are not in this
branch.

**Second model of the release (v2.15).** Design, features and NumPy inference: the same team member
(branch `mtah-possession`, commit `167dc7b`; byte copies under `possession/tcn/`). He developed the
recipe on all seven DFL matches and Metrica games 1-3. The weights in `models/possession-tcn-v215.npz`
(three members) were trained for the release with `experiments/possession_v2/v214/tcn_jax.py` on the six
DFL training matches below and nothing else: twelve corrupted copies of every half, six made with his
corruption simulator and six with ours, the provider's labels as for the trees. Selection:
`possession-v215-plan.json`, `possession-v215-results.json` (log entry K013; the attempt before it, with the same
weights and equal weighting, is `possession-v214-*`, log entry K012).'''),
 ('''copies of a match, also with the teams exchanged: 856,678 rows per bundle (recorded in the bundle
cards). The seventh match of the
dataset, J03WMX, is reserved as a final test; the process that built the release has not
downloaded it (a team member used it for a separate model that is not part of the release).''',
  '''copies of a match, also with the teams exchanged: 856,678 rows per bundle (recorded in the bundle
cards). The network of the second model reads every second frame of twelve corrupted copies of
every half of the same matches. The seventh match of the
dataset, J03WMX, is reserved as a final test; the process that built the release and trained its
weights has not downloaded it (a team member used it while he designed the network of the second
model; the released weights were trained without it).'''),
])
print('DATA_SOURCES.md edited')

# ------------------------------------------------------------------------------------------ AGENTS.md
edit('AGENTS.md', [
 ('''- The final test on the reserved DFL match J03WMX (`possession-final-test-plan.json`,
  `tools/possession_final_test.py`) is run once, by the team. Its result is reported as measured and
  never used to change, retrain or re-select the release. Do not download or read that match for
  any other purpose.''',
  '''- The final test on the reserved DFL match J03WMX (`possession-final-test-plan.json`,
  `tools/possession_final_test.py`) is run once, by the team. Its result is reported as measured and
  never used to change, retrain or re-select the release. Do not download or read that match for
  any other purpose. The plan is registered for `possession-v2.11k`, the release without the second
  model, and was not re-registered for v2.15: the network's designer had used that match, so a run
  of v2.15 on it would not be a fresh test. Report its result as a result of v2.11k (steps 1-8).'''),
 ('''- Possession (`possession/`): the submission system is `possession-v2.11k`, entry point
  `python -m possession.run211k`, release manifest `possession-v211k-release.json`; the release and its
  technical fall-backs (the next one is `possession-v2.11g`, `possession.run211g`) are named in
  `possession-release.json`. v2.11k = frozen v2.1 core''',
  '''- Possession (`possession/`): the submission system is `possession-v2.15`, entry point
  `python -m possession.run215`, release manifest `possession-v215-release.json`; the release and its
  technical fall-backs (the next one is `possession-v2.11k`, `possession.run211k`) are named in
  `possession-release.json`. v2.15 = v2.11k + a second model family on the core path: the second-stage
  probabilities are averaged with those of a temporal convolution network (`possession/tcn/`, byte
  copies of a team member's modules; `models/possession-tcn-v215.npz`, three members trained by us on
  the six DFL matches with both corruption simulators; `possession/pooling.py`) before the unchanged
  decoder (weight ''' + str(W) + ''' for the network); nothing is averaged on the v2.3 path (log entries
  K012, K013). v2.11k = frozen v2.1 core'''),
 ('''  training/selection (`possession-v2-plan.json` ... `possession-v211-plan.json`), frozen
  bundles with source hashes (`models/possession-v2.npz`, `models/possession-v23.npz`), local-only''',
  '''  training/selection (`possession-v2-plan.json` ... `possession-v215-plan.json`), frozen
  bundles with source hashes (`models/possession-v2.npz`, `models/possession-v23.npz`,
  `models/possession-tcn-v215.npz`), local-only'''),
 ('''  explicitly. `possession-release-graded-windows.json` is the reserve ladder without the Smart
  Tagging kick-off rule (`possession.run211g` first). Do not switch between them because of an output.''',
  '''  explicitly. `possession-release-graded-windows.json` is the reserve ladder without the Smart
  Tagging kick-off rule and without the second model (`possession.run211g` first). Do not switch
  between them because of an output.'''),
 ('''  with `possession-v211k-release.json`). The delivery chain's `VERI` line says whether the file is in
  the bundle (without it the output is that of `possession.run211g`), and `GIRDI OKUMA` compares the''',
  '''  with `possession-v211k-release.json` and `possession-v215-release.json`). The delivery chain's `VERI`
  line says whether the file is in the bundle (without it the rule is not applied and the models'
  labels stand), and `GIRDI OKUMA` compares the'''),
 ('''- Two candidates failed their registered gates and are not part of any release: touch / control-change
  columns (`possession/touch.py`, v2.12, log entry K008) and averaging the release's probabilities with
  a team member's temporal convolution network (v2.13, log entry K010; scripts and byte copies of his
  modules under `experiments/possession_v2/v213/`). Keep the files and records; using either needs a
  new plan registered before any new result.''',
  '''- Three candidates failed their registered gates and are not part of any release: touch / control-change
  columns (`possession/touch.py`, v2.12, log entry K008) and two ways of averaging the release's
  probabilities with a team member's temporal convolution network: his committed weights with his
  single-cost decoder (v2.13, log entry K010; scripts and byte copies of his modules under
  `experiments/possession_v2/v213/`), and weights re-trained by us with the v2 decoder and equal
  weights (v2.14, log entry K012: better on 15 of 16 new copies, but the gate on single copies
  failed). Keep the files and records. v2.15 (log entry K013), the release, is the third and last
  attempt; it changes none of the earlier records, and its plan says that no further candidate with
  the second model is registered before the deadline.
- The network weights of v2.15 were trained in an agent session on external data
  (`experiments/possession_v2/v214/tcn_jax.py`). A re-run is not bit-identical: never replace
  `models/possession-tcn-v215.npz`; a new training is a new version with a new plan. The files
  under `possession/tcn/` are byte copies of commit `167dc7b` of branch `mtah-possession` and are
  frozen with the release.'''),
])
print('AGENTS.md edited')
