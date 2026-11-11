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

- Possession (`possession/`): the submission system is `possession-v2.11`, entry point
  `python -m possession.run211`, release manifest `possession-v211-release.json`; the release and its
  technical fall-backs (the next one is `possession-v2.9`, `possession.run29`) are named in
  `possession-release.json`. v2.11 = frozen v2.1 core + noise gate with the v2.3 path (v2.4) + gated
  broadcast ball fill with clock-anchored alignment (v2.5b) + second-half kick-off frame published in
  the organisers' FAQ (v2.5c) + broadcast ball registered through players seen by both cameras
  (`register.py`, v2.9) + goalkeeper team check before the features (`keeper2.py`). It follows the
  rules above: external-only
  training/selection (`possession-v2-plan.json` ... `possession-v211-plan.json`), frozen
  bundles with source hashes (`models/possession-v2.npz`, `models/possession-v23.npz`), local-only
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
  any other purpose.
- `possession/keeper.py` is the first version of the goalkeeper check (v2.10). It passed its
  registered gates and was not released (it moved outfield players when the far goalkeeper was not
  tracked; log entry K004). Keep the file, its plan and its results as they are; do not use it.
  Whether the provided tracking has goalkeeper id errors is not to be looked at; `run.json` and
  Appendix R on the team's computer record whether the check moved anything.
- Metrica proxy labels (`experiments/possession_v2/metrica_labels.py`) must be computed with the stable
  sort that file now uses (log entry K005: with the default sort the labels depended on the pandas /
  numpy build, and three reporting-only records had to be recomputed). Any record that scores against
  external labels states the Python, pandas and numpy versions it ran under.
- `possession.run211g` (`possession-release-graded-windows.json`) is a reserve entry point without
  the published kick-off frame. It becomes the release only if the organisers answer that the
  constant may not be hard-coded (question sent on 11 Nov 2026); do not switch for any other reason.
- Before stating that copies, fixtures or seeds are "new" or "unused", check every earlier plan and
  results file for them (log entry K002). Quote the organisers' pages from a local clone with line
  numbers, not from a web summary.
