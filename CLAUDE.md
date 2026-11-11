# CLAUDE.md

Guidance for Claude (and other coding agents) working in this repository.
Read `AGENTS.md` first; it is authoritative on process rules and is not repeated in full here.

## What this is

Team code for **More Than a Hack 2027 — Initial Challenge** (Mobile World Capital
Barcelona, Barça Innovation Hub, Metrica Sports). Task: one label per frame for the
supplied Barcelona–Athletic LaLiga match (199,319 frames, 25 fps; ~158,857 graded).

- Labels: `H` home possession, `A` away possession, `D` dead ball, `X` abstain.
- Output: `frame,label` CSV, exactly 199,319 rows, frames 0..199318, UTF-8, no blanks.
- Ranking metric **spellF1**: possessions = maximal H or A runs, D splits runs; X is
  forward-filled with the last label in the same half (heads back-filled) before
  one-to-one temporal-IoU matching; F1 averaged at IoU 0.3/0.4/0.5/0.6/0.7.
  Tie-break **macroF1** = mean frame F1 of H, A, D (X counts as a miss).
  Organizer `evaluation/possession_metrics.py` is the authoritative spec.
- Published floor: `baseline_smooth50` full-match spellF1 0.2433. Public 5-minute
  window (17 possessions) is a format/alignment check only — never for selection.
- Deliverables (one Google Form, editable until deadline): `<team>.csv`, public repo
  that regenerates the CSV from the data bundle with pinned deps, short technical
  document (`<team>.pdf`/`.md`). Deadline **17 November 2026, 11:59 PM CET** (= 18 Nov 01:59 Istanbul;
  stated in the organisers' e-mail of 20 Oct, not in the repository docs). The Form link comes by e-mail
  "by November 14". Team members had to register with the same team name before 10 Nov.
- Organizer repo: https://github.com/metrica-sports/more-than-a-hack-2027
  (CHALLENGE, DATA, EVALUATION, SUBMISSION, RULES, FAQ).

## Non-negotiable rules (see AGENTS.md, `rules-provenance.json`, docs/OTONOM_GELISTIRME_TR.md)

- The organizer clarification of **3 Nov 2026 12:23 UTC** takes precedence over all
  earlier guidance. Forbidden: comparing supplied-match output with its video, hand
  labelling the supplied match, tuning/selecting on the supplied video or ground truth,
  and **uploading supplied data to AI services**.
- That last point includes this assistant: never read, stage, upload or paste supplied
  match files (videos, tracking `*_atd.txt`, metadata/Smart Tagging XML, homography CSV,
  frame-level outputs, prediction CSVs) into a cloud/agent session. Work only on source,
  synthetic tests, external datasets and aggregate JSON results. Commands that touch the
  supplied match are run by the user locally.
- All model/parameter choices are made on permitted external fixtures (SkillCorner,
  Metrica sample, Sportec/DFL, SoccerNet). Pre-register plans before looking at results;
  never relax acceptance gates after the fact; previously accessed fixtures are not
  "fresh test" data.
- Do not claim remediation (`REMEDIATION.md`) or organizer conditions are complete.
  Keep the historical record; do not rewrite it.
- Never commit raw/derived match data, videos, frames, weights or predictions;
  `.gitignore` blocks `*.csv *.xml *.npz *.mp4 *.pt data/ private/ outputs/` etc.
  Sole exceptions: `models/possession-v2.npz` and `models/possession-v23.npz` (whitelisted in
  `.gitignore`), trees trained only on CC-BY Sportec/DFL data, needed to regenerate the submission.
  Private artifacts live under `C:/Users/Abra/FootballPrivate/`.
- Separate "it runs / tests pass" from "it was measured to be accurate". Synthetic tests
  are not football accuracy; provider-teacher agreement is a proxy, not human truth.

## Layout

- `possession/` — the submission system (H/A/D). Frozen inference sources are listed with their
  SHA-256 in `possession-v211-release.json` (and `-v29-`, `-v25-`, `-v25c-`, reserves `-v211g-`, `-v29g-`);
  `possession-release.json` names the release and its technical fall-backs
  (`possession-release-graded-windows.json` = reserve without the published kick-off frame).
  Non-frozen helpers: `validate.py`, `plausibility.py`, `public_check.py`, `inputs_check.py`,
  `epts_export.py`, `train.py`, `degrade.py`, `evaluate.py`. `models/possession-v2.npz`, `models/possession-v23.npz`
  are the frozen bundles.
- `experiments/possession_v2/` — byte copies of the scratch experiment scripts (archive).
- `clean_model/` + `model.json` — **frozen** H/A/X baseline (`remediated-external-v1`,
  tracking-only, numpy). `run.py` verifies SHA-256 of every source file against
  `model.json` and refuses to run if changed. Do not edit these bytes or refresh hashes.
- `development/` — unselected experimental modules (sequence DP possession, motion /
  contact / control state machine, dead-ball layers, long-ball, vision measurements,
  ball tracking, homography, clock/video sync, hybrid tactical+broadcast fusion).
  Nothing here is wired into the frozen release.
- `tools/` — runnable entry points (`python -m tools.<name>`): external data
  acquisition/preparation, selection and recheck studies, vision training/eval,
  local viewers, `validate_output.py`.
- `tests/` — synthetic unittest suite (no match data or weights needed).
- `viewer/` — static HTML/JS for the loopback-only local viewers.
- Root `*-plan.json` = pre-registered experiment plans; `*-results-v*.json` = aggregate
  external results; `dead-ball-promotion-decisions.json` = promotion verdicts.
- `docs/*_TR.md` — Turkish design notes; `docs/DENEY_KAYDI_TR.md` is the experiment log
  (newest entry at the top: IDs like S00x sequence, D00x dead-ball, V0xx vision,
  C00x control). Add a log entry for every experiment.

## Commands

```
python -m pip install -r requirements.txt -r requirements-possession.txt
python -m unittest discover -s tests -v            # run after any change (399 tests, 15 skipped, about 6 min)
python -m tools.possession_deliver --data-dir <bundle> --private <dir> --team <name>   # USER ONLY, local: whole delivery chain
python -m possession.run211 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local
python -m clean_model.run --meta <atd.xml> --tracking <atd.txt> --model model.json --out <new dir>
python -m tools.validate_output <csv> --frames 199319
python -m tools.sequence_selection --local-plan <external>/local-plan.json --out <private dir>
python -m tools.tracking_viewer --demo --port 8766  # synthetic UI demo
```

Optional environments (never mixed into the frozen runtime): `requirements-vision*.txt`
(RF-DETR Nano, SAHI, supervision, torch CPU / CUDA 11.8 training),
`requirements-sync*.txt` (RapidOCR clock reading). Two to three AV/vision tests skip
when PyAV/torch are absent. CI (`.github/workflows/tests.yml`) runs the suite on
Ubuntu/Py3.12 and Windows/Py3.10. Output directories must not already exist.

## Code conventions

- Dense, compact Python (short names, `;`-joined statements) — match the surrounding
  style; numpy only in frozen paths. Windows-first (`.cmd` launchers, PowerShell).
- Every experiment tool writes provenance: source/plan/input SHA-256, split, settings,
  `provided_fixture_used: false`, and explicit "not a competition score" flags.
- Missing ball coordinates or provider `X` are never turned into `D`. Forecasts are
  never treated as measurements. Evidence resets at camera cuts, gaps and half changes.

## Git

- Remote `ata-yunus-ortak/football-video-analysis`. Default `main` is an unrelated older
  portfolio history. Clean baseline: tag `baseline/remediated-external-v1` (8962134).
- Active branch: `feature/external-possession-selection`. Keep experiments on separate
  branches; a selected release needs its own version, source freeze and provenance.

## Status snapshot (11 Nov 2026 afternoon — verify before relying on it)

- **Submission system: `possession-v2.11`** (`python -m possession.run211`, manifest
  `possession-v211-release.json`) = v2.9 + goalkeeper team check (`possession/keeper2.py`) applied to the
  tracking the models see. Ladder in `possession-release.json`: v2.11 -> v2.9 -> v2.5c -> v2.5c tactical only.
  Reserve without the published kick-off frame: `possession.run211g` (`possession-v211g-release.json`;
  ladder v2.11g -> v2.9g -> v2.5b -> v2.5b tactical). No frozen v2.9 file changed. Log entry K004.
- **Why:** team ids come from the tracker and goalkeepers wear another kit. Diagnostic
  (`experiments/possession_v2/stress_roles.py`, reporting only; re-run numbers of K005): one goalkeeper
  under the other id for the whole match -0.023 spellF1, both -0.317 (the mean-based
  `features.attack_dirs` inverts), 30% of the time -0.014, a referee under a team id -0.004 at
  worst (not handled).
- **v2.10 (`possession/keeper.py`) passed its four registered gates and was NOT released**
  (`possession-v210-plan.json`, `-results.json`). A reporting analysis of what it moved found 3 outfield
  pieces among 80; with a simulated camera window that hides the far goalkeeper it moved 1,700-8,400
  outfield positions per training match. Keep the file and records; do not use it.
- **v2.11 rule (`keeper2.py`):** evidence = far frames in which a piece is nearest to a goal by at least
  8 m; a piece under the other id is moved only if that goal's evidence in the half is mostly (>= 50%,
  >= 2,500 frames) under the other id, or if it continues a goalkeeper piece. Validation
  (`possession-v211-plan.json`, `-results.json`; 8 new copies, six gates, all passed): ids as corrupted
  0.6594 -> 0.6596; both goalkeepers wrong 0.3354 -> 0.6565; one 0.6274 -> 0.6576; 30% of the time
  0.6417 -> 0.6591; camera window 42 m / 35 m with correct ids 0.6492 -> 0.6492 / 0.6464 -> 0.6464;
  window 42 m with both wrong 0.5570 -> 0.6344 (reported, not a gate). Simulated errors and camera; whether
  the provided tracking has any of this is unknown and must not be looked at. Limit: with the far
  goalkeeper mostly out of view (35 m window) nothing is corrected.
- **Follow-up** (`possession-v211-followup.json`): reserved Metrica game 3 rows, development counts,
  full-size rehearsals: chain on bundle A with v2.11 0.764 (v2.9: 0.763); bundle with the
  goalkeepers' tracks under the other id: 0.766 with the check, 0.431 without; one v2.11 generation
  270 s, peak 1.53 GB.
- **Records correction K005** (`possession-label-order-correction.json`): `metrica_labels.labels_from_events`
  sorted tied events unstably. In the Python 3.10 environment the Metrica proxy labels lost about half of
  their dead-ball intervals; in the experiment environment (Python 3.13 / pandas 3.0.5) they were in file
  order. All selections, gates, validations and reserved tests ran in the experiment environment (stored
  possession counts match the file-order labels only). Affected and recomputed: K003 rehearsal scores
  (bundle A 0.763, B 0.732; first reported 0.715 / 0.686), K003 slot / duplicate diagnostic (now at most
  0.0060 on a copy, 0.0021 on average), the goalkeeper diagnostic. The script now uses a stable
  sort. **Rule: score against Metrica proxy labels only with the current script, and record the Python /
  pandas / numpy versions of any such run.** `possession-rehearsal-results.json` and
  `possession-v210-plan.json` keep the first numbers.
- **Chain changes:** PLATFORM compares seven synthetic variants (five v2.9 runs with unchanged recorded
  hashes + two `run211` runs on bundles with exchanged goalkeeper ids; a differing goalkeeper-bundle
  input gives `BELIRSIZ (kaleci varyantlari...)`); Appendix R has a "Goalkeeper team correction" row
  (moved / not moved, no counts). `tools/possession_final_test.py` now calls the entry point named in
  the plan; **the final-test plan was re-registered for v2.11** (history kept in the file; J03WMX still
  untouched). After any further edit of the tool or of `epts_export.py`, re-register again with
  `experiments/possession_v2/register_final_test_v211.py`-style script and say so in the log.
- Tests: 411 (15 skipped) under Python 3.10 with the pins, 411 (102 skipped) with numpy only; the seven-variant cross-platform check is SAME under Python 3.10 and 3.12 (numpy 1.26.4) and 3.13 (numpy 2.5.3).
- Still pending (user): optional workflow line -> `GIT-YUKLE-V2.cmd` -> Actions -> `TESLIM-HAZIRLA.cmd`
  -> paste the `[..]` lines and `SONUC` -> Google Form. Optional, any day before 17 Nov: `SON-TEST.cmd`.
  Windows has never run any of this. No answer from the organisers to the kick-off question as of the
  last check (see the log).

## Earlier status (11 Nov 2026 midday; its rehearsal scores and slot-diagnostic numbers were recomputed in K005)

- **Submission system unchanged: `possession-v2.9`.** Nothing was selected or tuned on 11 Nov after
  K002; the work below is about running correctly on the real files (log entry K003).
- **Reader audit.** Frozen `read_epts` agrees frame by frame with kloppy 3.18.0 (the organisers'
  loader) on Metrica sample game 3 and with the logic of `starter/baseline.py` on a synthetic
  competition-like file (`tests/test_possession_reader_reference.py`). No int32 overflow candidate
  for Windows was found by reading the frozen inference code.
- **`possession/inputs_check.py`** (chain step `GIRDI OKUMA`, 26 checks, PASS/FAIL/SKIP + name only):
  DATA.md aggregates through the release's readers; raw-file syntax without the release's reader;
  a starter-style second reading compared frame by frame. A failed comparison names the aspect
  (`__team_counts`, ...), a reader error names the class (`__ValueError`). A FAIL is a reader
  question, never a reason to change a model or threshold.
- **Full-size rehearsal** (`possession-rehearsal-results.json`, scripts in
  `experiments/possession_v2/prova_build.py` etc.): two synthetic bundles with the provided files'
  names, record counts (199,319 / 164,488) and slot counts (46 / 51), trimmed to DATA.md's
  aggregates; content = corrupted Metrica games 3 + 2. The whole chain passed on both (about 11 min
  on 2 CPUs without OCR/clone, peak memory 1.55 GB, one generation about 3.3 min). Delivered files
  vs external labels: spellF1 0.715 (v2.1 path) and 0.686 (v2.3 path), identical in the organisers'
  `run_evaluation.py`; teams exchanged 0.005; rows shifted 1 s 0.54. Slot packing + duplicated
  tracks changed the score by -0.0002 / +0.0007. Wiring and size check, not an accuracy claim.
- **Slot identity / duplicated tracks** (documented in DATA.md, absent from `degrade`): reporting-only
  diagnostic on Metrica 1-3: mean change 0 to -0.0024, largest single change -0.0068. No fix added.
- **Reserve `possession-v2.9g`** (`possession.run29g`, `possession-v29g-release.json`,
  `possession-release-graded-windows.json`): v2.9 without frame 113,742; ladder v2.9g -> v2.5b ->
  v2.5b tactical only. Use only if the organisers answer "no" to the question e-mailed on 11 Nov
  09:31 (hard-coding the kick-off frame published in FAQ.md). No answer as of 11 Nov 11:16.
  On the rehearsal's invented pre-kick-off segment v2.9g wrote D on 2,625 of 2,934 frames.
- **Final test registered, NOT run:** `possession-final-test-plan.json` + `tools/possession_final_test.py`
  (`SON-TEST.cmd`): reserved DFL match J03WMX (never downloaded), 4 corrupted copies x (tactical only +
  simulated good/medium/bad broadcast) through the real entry point on files written by
  `possession/epts_export.py`; run once by the user (about 420 MB download, about an hour), result
  shareable (external data), written to `possession-final-test-results.json`. Decision rule: none;
  never change the release because of it. The plan pins the tool's SHA-256: after any edit of the tool
  or of `epts_export.py` run `experiments/possession_v2/register_final_test.py` again and say so in
  the log (only possible while the match is still untouched).
- Tests: 399 (15 skipped) under Python 3.10 with the pins; 399 (90 skipped) with numpy only.
- Still pending (user): optional workflow line -> `GIT-YUKLE-V2.cmd` -> Actions -> `TESLIM-HAZIRLA.cmd`
  -> paste the `[..]` lines and `SONUC` -> Google Form. Optional, any day before 17 Nov: `SON-TEST.cmd`.
  Windows has never run any of this.

## Earlier status (11 Nov 2026 morning)

- **Submission system: `possession-v2.9`** (`python -m possession.run29`, manifest
  `possession-v29-release.json`), confirmed on 11 Nov by a registered amendment. A records audit found
  that 8 of the "16 new copies" of the v2.9 validation had been used for v2.6. They were replaced
  (`possession-v29-amendment-plan.json`, registered 07:37 before any new result) and the unchanged gates
  were applied once (`possession-v29-amendment-results.json`): good broadcast 0.6857 -> 0.6836 (limit
  -0.003; lower on 9 of 16, -0.020..+0.011 per copy), medium 0.6527 -> 0.6811 (gate open 0 -> 16),
  bad equal, mean regime gain +0.0088. All four gates passed; v2.9 stays. Log entry K002.
- **One-command local chain:** `TESLIM-HAZIRLA.cmd` = `python -m tools.possession_deliver` (stdlib only).
  Environment, release hash check, synthetic tests, cross-platform byte check, generation with the
  technical ladder of `possession-release.json` (v2.9 -> v2.5c -> v2.5c tactical only; lower step only
  after an error), format + plausibility, copy to `FootballPrivate/teslim/<team>.csv`, OCR clocks and
  clock-anchored rerun, comparison without clock, repeat run, fresh clone of the pushed branch,
  organisers' validator, pass/fail public check, document copy `<team>.md` with run record (Appendix R).
  It prints status words only. **Shareable:** the `[..]` lines and `SONUC` line. **Never ask for:** the
  private log, `run.json`, `OZEL-kayit.json`, the CSV, Appendix R.
- `possession/public_check.py` + `possession-final-check-plan.json`: pass/fail-only pipeline check on the
  public five minutes (valid file; spellF1 >= 0.20 and macroF1 >= 0.50; not better with teams exchanged).
  No score printed or stored. A FAIL may only start a search for a mapping/indexing bug.
- `tests/test_possession_crossplatform.py` pins the output hashes of five synthetic runs (identical under
  Linux py3.10/numpy 1.26.4 and py3.13/numpy 2.5.3). Whether Windows gives the same bytes is unknown until
  CI or the user's chain reports it (`PLATFORM: AYNI/FARKLI`).
- Documents brought up to the organisers' list (SUBMISSION.md 64-73: approach, assets, **training data**,
  rules, limitations, reproduction; OVERVIEW.md: missing/noisy tracking): `TECHNICAL_DOCUMENT.md` sections
  1-7, `DATA_SOURCES.md` (per-match label counts; source = Hugging Face mirror, not figshare).
- CI caveat: the device bridge refuses to write `.github/workflows/tests.yml` (protected file), so the copy
  on the user's PC still installs only `requirements.txt`. Until the USER appends
  ` -r requirements-possession.txt` to its `pip install` line, CI skips every possession test (they skip
  cleanly without scipy/pandas: 383 tests, 76 skipped). Do not claim CI evidence for the release before
  the user reports the Actions result with that line changed.
- `GIT-YUKLE-V2.cmd` rewritten (pathspec list, data-type guard, two commits: possession release; external
  control-reference tooling that was only in the working copy). Remote branch was still at d38df58 on
  11 Nov 06:30; this session has no push access. `.cmd` files could not be run here (no Windows).
- Pending (user, in this order): `GIT-YUKLE-V2.cmd` -> check GitHub Actions (Ubuntu + Windows) ->
  `TESLIM-HAZIRLA.cmd` -> Google Form with `teslim/<team>.csv` and `<team>.md`. Also: team must have 3-5
  members; optional question to the organisers about using the published kick-off frame (FAQ.md:38-40);
  deadline hour is not stated. Optional final test on DFL J03WMX is still not done (needs a download tool
  that accepts the reserved match; `tools/sportec_download.py` refuses it by design).
- Cloud session limits: 6.26 GB memory, ONE feature-heavy job at a time (peak 3.4-5.3 GB), background
  jobs die after 2 h. Validation models are backed up on the user's PC under
  `FootballPrivate/sportec-development-20261107/possession-validation-models` (external data only).

## Earlier status (11 Nov 2026 night)

- **Submission candidate: `possession-v2.9`, entry point `python -m possession.run29`, manifest
  `possession-v29-release.json`** (Windows `SAHIPLIK-V29-URET.cmd`). = v2.5b (below) + (1) second-half
  play block starting at the kick-off frame 113,742 published in the organisers' FAQ (frames
  110,808-113,741 are graded and stated to be all D; fixture constant, not measurable externally; also
  available alone as `possession.run25c`) + (2) `possession/register.py`: broadcast ball corrected by the
  calibration error measured on players seen by both cameras, smoothed, before the unchanged 0.50 m gate.
  Evidence (`possession-v29-*`, 16 copies of which 8 were NOT new, corrected above and in K002; warp simulator): medium broadcast 0.647 -> 0.678 (gate
  open 0 -> 16 of 16), good 0.683 -> 0.681 (lower on 13 of 16), bad unchanged. Simulated streams only.
- Short submission document `TECHNICAL_DOCUMENT.md` (organisers ask for "a few pages": approach, assets
  used/dropped, rules for loose balls/challenges/restarts, limitations, reproduction); long record
  `TECHNICAL_DOCUMENT_V2.md` (addendum for v2.9 at the top); `DATA_SOURCES.md` lists data/licences/tools.
- NOT selected on 10-11 Nov: v2.7 gap-bridging features (`features3.py`, +0.002), v2.8 Metrica game added
  to training (+0.001 held-out Metrica, -0.011..-0.014 DFL). Decoder sweep flat. Log P010-P012, K001, R002.
- `possession/plausibility.py`: PASS/FAIL-only aggregate sanity check of a submission file (not accuracy).
- Background jobs in the cloud session are killed after 2 h (make training resumable) and a third
  feature-heavy process (even a unit test with run25) can OOM-kill a running experiment.
- The v2.5b description below is still accurate for everything except the two v2.9 changes.

## Earlier status (10 Nov 2026 evening)

- **Previous release: `possession-v2.5b`, entry point `python -m possession.run25`,
  manifest `possession-v25-release.json`** (SHA-256 of all inference sources + both bundles;
  `run25.check_release` refuses to run on any change). Pipeline: (1) v2.4 noise gate on the raw
  tactical ATD (`noise.py`: players/ball high-frequency noise > 0.30 m -> v2.3 path with `smooth.py`
  and `models/possession-v23.npz`, else frozen v2.1); (2) broadcast ATD aligned to tactical frames
  (`broadcast.py` v4 alignment, or clock-anchored `fusion.align_at` when OCR clock files of both videos
  are given: `clocksync.py`, OCR wrapper `tools/possession_clock.py`, launcher `SAAT-OKU.cmd`,
  separate env `requirements-sync-lock.txt`); (3) accuracy gate `fusion.fuse_gated`: fill missing
  tactical balls only if median tactical-broadcast ball distance <= 0.50 m over >= 120 s and >= 5%
  frames accepted. No broadcast files / gate closed -> identical to `run24`.
- Evidence: v2.5 (`possession-v25-*`): simulated good/medium/bad broadcast on 16 fresh copies
  0.651 -> 0.675 / 0.655 / 0.651. v2.5b (`possession-v25b-*`, 16 new copies, simulated clock reads):
  good 0.635 -> 0.672, identical to v2.5 there (no alignment failure occurred; selected as not worse).
  v2.6 learned switch hazard (`decode2.py`, `hazard.py`, `possession-v26-*`): +0.002, NOT selected.
  Reporting-only diagnostics: clean tracking 0.748 vs corrupted 0.610 vs no-missing-ball 0.700;
  oracle team decisions 0.912 vs oracle dead-ball 0.647 (team decisions are the main error).
- v2.4 (`possession-v24-*`): noise gate selected; 24 fresh copies v2.1 0.603 -> 0.642; reserved
  Metrica game 3 0.637 -> 0.665.
- Pending (user): run `SAHIPLIK-V2-KURULUM.cmd`, `SAAT-OKU.cmd`, `SAHIPLIK-V25-URET.cmd`, push with
  `GIT-YUKLE-V2.cmd` (remote branch still at d38df58 on 10 Nov), Google Form. Final fresh test on
  DFL J03WMX (never downloaded; HuggingFace is blocked in the cloud session, the user must download
  and prepare it with `tools.sportec_prepare`), then `work/test_final_wmx.py`.
- **Core `possession-v2.1`, frozen.** Tracking-only H/A/D: features from ATD positions -> two
  numpy-evaluated GBDT models (P dead, P home|alive, team-symmetrised) -> second stage on
  out-of-fold stage-1 probabilities (`stack.py`) -> 3-state Viterbi (switch 3, out/in 60, dead bias
  -0.3). Reader follows EPTS `DataFormatSpecification`; home = Barcelona checked by team name.
  Bundle `models/possession-v2.npz` (SHA-256 1cd59ba5c21a5abc2be24f8294b3af3d61d84997b61edfc08c028384a9d550d1,
  6 DFL matches); its card freezes `possession/{data,features,trees,decode,pipeline,bundle,run,stack,tags}.py`.
  The v2.3 bundle card additionally freezes `smooth.py`, `noise.py`, `run24.py`. Editing any frozen
  file makes `run.py`/`run24.py` refuse to run (a new version is needed).
- External numbers (not competition scores): v2.1 validation 0.631 vs baseline logic 0.196;
  reserved Metrica game 3 0.664 vs 0.219. Docs `TECHNICAL_DOCUMENT_V2.md` (describes v2.5),
  `docs/SAHIPLIK_V2_TR.md`, log entries P001-P009 in `docs/DENEY_KAYDI_TR.md`.
- Run locally only: `python -m possession.run25 --data-dir <bundle> --out <new dir> [--tactical-clock
  <dir> --broadcast-clock <dir>]` then `python -m possession.validate <csv>` (Windows:
  `SAHIPLIK-V2-KURULUM.cmd`, `SAAT-OKU.cmd`, `SAHIPLIK-V25-URET.cmd`, `GIT-YUKLE-V2.cmd`). Never run
  it in a cloud/agent session; the user shares only OK/FAIL (not run.json values).
- Tests: `python -m unittest tests.test_possession_v2 tests.test_possession_v23 tests.test_possession_v24
  tests.test_possession_v25 tests.test_possession_v25c tests.test_possession_v26 tests.test_possession_v27
  tests.test_possession_v29 tests.test_possession_plausibility -v` (synthetic; no accuracy claims); scikit-learn
  tests skip in the inference-only environment. Full suite under Python 3.10: 354 tests, 14 skipped.
- Tested, NOT selected (pre-registered gates): Smart Tagging evidence v3.0/v3.1 (`smarttags.py`,
  `possession-v3-*`), broadcast ball fill v4 (`broadcast.py`, `possession-v4-*`), wider ball-noise
  training v2.2 (`possession-v22-*`), v2.3 alone (`possession-v23-*`: +0.014 overall but -0.014 on
  the original copies), switch hazard v2.6 (`possession-v26-*`). Memory limit of this cloud session is
  about 6.3 GB: never run more than two feature-heavy jobs at once (three were OOM-killed on 10 Nov).
- Plan files' clock times were corrected on 10 Nov from file-system times (agent had typed
  estimates); originals kept under `timestamp_correction`. Always read the clock before writing one.
- `tests/test_ball_patch_data.py` skips when Pillow (optional vision extra) is absent.
- GitHub: as of 10 Nov 10:00 the remote branch was still at d38df58 (8 Nov); the possession work is
  pushed by the user with `GIT-YUKLE-V2.cmd` (this session has no GitHub push access).
- Frozen legacy release `clean_model/` + `model.json` unchanged (H/A/X only).
- Experiment scratch (feature caches, pickles) lives outside the repo; `possession.train`
  rebuilds the bundle from the prepared external data.
