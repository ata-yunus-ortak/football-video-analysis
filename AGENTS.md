# Clean development instructions

- Read `docs/OTONOM_GELISTIRME_TR.md`: the 3 November 12:23 UTC organizer
  clarification takes precedence over earlier web/document/email guidance.
  Do not compare supplied-match outputs against its video, even for a claimed
  viewing-only diagnostic. No supplied data uploads to AI services. External
  training/selection continues; automatic frozen inference remains allowed.
  Earlier local-review documents are historical, not authorization to resume
  those comparisons. Do not erase the history or claim blanket compliance.

- Read `README.md`, `TECHNICAL_REPORT.md`, `REMEDIATION.md`, `model.json`,
  `docs/GELISTIRME_TR.md` and the latest entry in `docs/DENEY_KAYDI_TR.md`.
- Keep `main` and the frozen `model.json` / `clean_model/` bytes as the baseline.
  On the shared GitHub repository, its default `main` is an older portfolio
  history: use tag `baseline/remediated-external-v1` (commit `8962134`) as the
  clean baseline. The current working branch is `feature/external-possession-selection`
  (it continues `develop/dead-ball-data-audit`); the possession release lives there.
  Develop new experiments on a separate branch under `development/`. A later
  selected release needs its own explicit version, source freeze and provenance.
  Do not refresh baseline hashes merely to bypass its integrity checks.
- Make all model, threshold and version choices on permitted external fixtures.
  Do not read/recover legacy supplied-fixture annotations, derivatives, match
  images or old public scores for development. The supplied public window is
  only a final check after a new pipeline has been selected and frozen; do not
  start another selection cycle from that check.
- Keep raw match data, frame-level arrays and predictions outside this repository.
  Record source commit/content hashes, fixture splits, settings and selection
  rationale for each experiment. Record uncertainty about previous exposure.
- X, missing coordinates and out-of-pitch point estimates are not D targets.
  Event-paired intervals are partial proxies, not exhaustive D truth. D001 found
  zero finite ball coordinates in all 78 paired Metrica stoppage intervals; do
  not turn this source-specific absence into a validated general D classifier.
- Keep D, ball-reliability and possession-transition experiments separate.
  Compute tracking features without event/label inputs. Before D promotion,
  establish evaluable D/live-play targets and validate timing boundaries.
- For changes to adapters/features/auditing, run
  `python -m unittest discover -s tests -v`. Keep frozen-source integrity checks.
- Do not claim all organizer/remediation conditions are complete; provider-side
  conversation/upload cleanup remains unverified in the handoff.

- Possession (`possession/`): the submission system is `possession-v2.16`, entry point
  `python -m possession.run216`, release manifest `possession-v216-release.json`; the release and its
  technical fall-backs (the next ones are `possession-v2.15`, `possession.run215`, and
  `possession-v2.11k`, `possession.run211k`) are named in `possession-release.json`.
  v2.16 = v2.15 + players the tactical tracking has lost, added from the broadcast tracking when the
  accuracy gate of the broadcast fill is open (`possession/playerfill.py`; a registered broadcast
  player with no tactical player of either team within 1.5 m; tactical positions are never moved;
  log entries K016 and K017, `possession-v216-plan.json`, `-results.json`). `playerfill.py` and
  `run216.py` are hash-frozen like every other release file: a change needs a new version and plan.
  v2.15 = v2.11k + a second model family on the core path: the second-stage
  probabilities are averaged with those of a temporal convolution network (`possession/tcn/`, byte
  copies of a team member's modules; `models/possession-tcn-v215.npz`, three members trained by us on
  the six DFL matches with both corruption simulators; `possession/pooling.py`) before the unchanged
  decoder (weight 0.2 for the network); nothing is averaged on the v2.3 path (log entries
  K012, K013). v2.11k = frozen v2.1 core + noise gate with the v2.3 path (v2.4) + gated
  broadcast ball fill with clock-anchored alignment (v2.5b) + broadcast ball registered through
  players seen by both cameras (`register.py`, v2.9) + goalkeeper team check before the features
  (`keeper2.py`, v2.11), run on the organisers' graded windows (v2.11g: the kick-off frame published
  in the FAQ is not used) + dead ball before the Smart Tagging kick-off tag (`kickoff.py`). It follows the
  rules above: external-only
  training/selection (`possession-v2-plan.json` ... `possession-v215-plan.json`), frozen
  bundles with source hashes (`models/possession-v2.npz`, `models/possession-v23.npz`,
  `models/possession-tcn-v215.npz`), local-only
  inference on the provided match, no output/video comparison. Changes to frozen `possession/*.py`
  files invalidate the release checks; any new version needs a new plan, a new entry point or
  retraining, and a new version string.
- Local chain: `python -m tools.possession_deliver` (Windows `TESLIM-HAZIRLA.cmd`) runs environment,
  hash check, tests, generation, validation and reproducibility checks on the team's computer and
  prints status words only. Never ask for, read or paste its private log, `run.json`,
  `OZEL-kayit.json`, the CSV or the run record appended to the document copy. The public five
  minutes are used only by `possession/public_check.py` (pass/fail, thresholds registered in
  `possession-final-check-plan.json`), never to choose anything.
- The chain's `GIRDI OKUMA` step (`possession/inputs_check.py`) compares what the release's readers
  return with the aggregate facts DATA.md publishes and with a second, starter-style reading of the
  tracking files. A reported name (for example `tactical_agrees_with_starter_reading__team_counts`
  or `tactical_reader_runs__ValueError`) is a format question for the reader: it never justifies a
  change of model, threshold or release, and a fix of a frozen reader needs a new version whose
  output is shown to be unchanged on every external fixture.
- The final test on the reserved DFL match J03WMX (`possession-final-test-plan.json`,
  `tools/possession_final_test.py`) is run once, by the team. Its result is reported as measured and
  never used to change, retrain or re-select the release. Do not download or read that match for
  any other purpose. The plan is registered for `possession-v2.11k`, the release without the second
  model, and was not re-registered for v2.15: the network's designer had used that match, so a run
  of v2.15 on it would not be a fresh test. Report its result as a result of v2.11k (steps 1-8).
- `possession/keeper.py` is the first version of the goalkeeper check (v2.10). It passed its
  registered gates and was not released (it moved outfield players when the far goalkeeper was not
  tracked; log entry K004). Keep the file, its plan and its results as they are; do not use it.
  Whether the provided tracking has goalkeeper id errors is not to be looked at; `run.json` and
  Appendix R on the team's computer record whether the check moved anything.
- Metrica proxy labels (`experiments/possession_v2/metrica_labels.py`) must be computed with the stable
  sort that file now uses (log entry K005: with the default sort the labels depended on the pandas /
  numpy build, and three reporting-only records had to be recomputed). Any record that scores against
  external labels states the Python, pandas and numpy versions it ran under.
- `possession.run211` (second half started at the kick-off frame published in the FAQ) stays frozen and
  is not used: the organisers' answer of 12 Nov 2026 to our question did not allow the constant
  explicitly. `possession-release-graded-windows.json` is the reserve ladder without the Smart
  Tagging kick-off rule and without the second model (`possession.run211g` first). Do not switch
  between them because of an output.
- The Smart Tagging file is read only for its "Kick Off (Start)" tags (`possession/kickoff.py`, frozen
  with `possession-v211k-release.json` and `possession-v215-release.json`). The delivery chain's `VERI`
  line says whether the file is in the bundle (without it the rule is not applied and the models'
  labels stand), and `GIRDI OKUMA` compares the
  number of those tags with DATA.md. Where the tags lie in the provided file is not to be asked for
  or reported; Appendix R on the team's computer records only whether a tag was used. Rule written
  before the chain ran on the provided files with v2.11k (log entry K011): if `tagging_reader_runs` or
  `tagging_kickoff_start_tags` fails there, the reserve ladder without the rule is delivered.
- Three candidates failed their registered gates and are not part of any release: touch / control-change
  columns (`possession/touch.py`, v2.12, log entry K008) and two ways of averaging the release's
  probabilities with a team member's temporal convolution network: his committed weights with his
  single-cost decoder (v2.13, log entry K010; scripts and byte copies of his modules under
  `experiments/possession_v2/v213/`), and weights re-trained by us with the v2 decoder and equal
  weights (v2.14, log entry K012: better on 15 of 16 new copies, but the gate on single copies
  failed). Keep the files and records. v2.15 (log entry K013), the second model of the release, was
  the third attempt; its plan and these documents called it the last and said that no further
  candidate with the second model would be registered before the deadline. That statement was set
  aside once, by a decision of the team lead on 16 Nov after a team member had pushed eight new
  network members with his development numbers: a fourth registered attempt (the v2.17 candidate,
  log entry K020; `possession-v217-plan.json`, `-results.json`; scripts under
  `experiments/possession_v2/v219/`) failed the gate on single copies (better on 14 of 16 new copies,
  one copy 0.018 lower) and is not part of any release.
  Its plan says that whatever the outcome no further candidate with the second model is registered
  before the deadline. Do not register one. None of the earlier records was changed.
- The network weights of v2.15 were trained in an agent session on external data
  (`experiments/possession_v2/v214/tcn_jax.py`). A re-run is not bit-identical: never replace
  `models/possession-tcn-v215.npz`; a new training is a new version with a new plan. The files
  under `possession/tcn/` are byte copies of commit `167dc7b` of branch `mtah-possession` and are
  frozen with the release.
- Before stating that copies, fixtures or seeds are "new" or "unused", check every earlier plan and
  results file for them (log entry K002). Quote the organisers' pages from a local clone with line
  numbers, not from a web summary.
