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
  Sole exceptions: `models/possession-v2.npz`, `models/possession-v23.npz` (trees) and
  `models/possession-tcn-v215.npz` (network weights of the second model), whitelisted in `.gitignore`,
  trained only on CC-BY Sportec/DFL data, needed to regenerate the submission.
  Private artifacts live under `C:/Users/Abra/FootballPrivate/`.
- Separate "it runs / tests pass" from "it was measured to be accurate". Synthetic tests
  are not football accuracy; provider-teacher agreement is a proxy, not human truth.

## Layout

- `possession/` — the submission system (H/A/D). Frozen inference sources are listed with their
  SHA-256 in `possession-v211-release.json` (every inference source and both bundles); `possession-v211g-release.json`
  and `possession-v211k-release.json` chain to it and add `run211g.py`, `kickoff.py` and `run211k.py`;
  `possession-v215-release.json` adds `run215.py`, `pooling.py`, `tcn/*.py` and the network weights;
  `possession-v216-release.json` adds `playerfill.py` and `run216.py`. Lower ladder steps
  have their own manifests (`-v29g-`, `-v29-`, `-v25-`, `-v25c-`). `possession-release.json` names the release and its
  technical fall-backs (`possession-release-graded-windows.json` = the same ladder without the Smart Tagging kick-off rule).
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
python -m unittest discover -s tests -v            # run after any change (about 6 min; current counts in the status snapshot)
python -m tools.possession_deliver --data-dir <bundle> --private <dir> --team <name>   # USER ONLY, local: whole delivery chain
python -m possession.run216 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local
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

## Status snapshot (17 Nov 2026, 00:40 — verify before relying on it)

- **Submission system: still `possession-v2.16`** (`python -m possession.run216`). Nothing of the release changed on 16 Nov.
- **K021 (16 Nov 23:31 - 17 Nov 00:24): the chain ran OK on commit cc62a5f** (K019-K020 records; every step OK;
  `TESLIM ... onceki teslim dosyasi ile AYNI`; `TEMIZ KLON AYNI`; GitHub Actions run 16 succeeded). **Documents only since
  then:** at the team lead's request Section 6 of `TECHNICAL_DOCUMENT.md` (the delivered document) now has the four items
  the organisers' reply of 3 Nov asks for (rules snapshot, what happened, affected stages, how the selection was re-done)
  and says what that reply answered (a "good-faith situation"; the team may continue and be evaluated as normal on four
  conditions) and what was done for each condition. One sentence of `TECHNICAL_DOCUMENT_V2.md` Section 2 was corrected (the
  team worked from its old `RULES.md` until the end of October). The provider-side cleanup is written as the team lead
  stated it on 16 Nov (he verified it himself; no agent saw that check; `REMEDIATION.md` records it as his statement and
  keeps its earlier entries). Keep to that form: say what was done and where it is recorded. **Still open:** one more
  chain run by the team lead so that `LittleSickle.md` carries the new Section 6, then the Form.
- **K020, a fourth attempt with the second model, against a written statement: FAILED its gates.** The v2.15 plan and the
  documents said that no further candidate with the second model would be registered. On 16 Nov the team member who
  wrote the network pushed eight new members (branch `mtah-possession`, commit `74bedbf`) with his development numbers;
  the team lead decided at 12:24 to have them validated. Plan `possession-v217-plan.json` (registered 12:47:22, before any
  row; the same seven gates and thresholds, against the release). Results `possession-v217-results.json`: tactical
  0.6704 -> 0.6848 (+0.0144; 14 better, 2 worse); fills +0.0125 / +0.0050; other simulator +0.0110; six gates
  passed, G4 failed (one copy at -0.0182; limit -0.010; the gate v2.14 had failed). Not released. The plan says:
  **whatever the outcome, no further candidate with the second model is registered before the deadline.** Scripts and
  the prepared, unreleased integration: `experiments/possession_v2/v219/`. If the team lead asks to deliver the
  candidate anyway: the gates are not relaxed after the fact (AGENTS.md), and a system that failed its registered
  validation is not presented as selected.
- **K019 (16 Nov 00:13-01:04): the chain ran OK on the team's computer with v2.16** (commit 1c31412; GitHub Actions
  succeeded; `PLATFORM AYNI` on eleven variants; `TEMIZ KLON AYNI`), and its status line
  `TESLIM ... onceki teslim dosyasi ile AYNI` says that **the v2.16 file is byte-identical to the v2.15 file** of 15 Nov:
  on the provided match the added-players step changed no label (not applied, or nothing to add, or what was added
  changed no decision; Appendix R says which and is not read here). A hash comparison, not an accuracy measurement and
  not a selection input.
- **Form:** the team lead submitted the Google Form on 15 Nov at about 18:45 with the v2.15 files (the same bytes as the
  v2.16 file). The Form can be sent again through the same link (not recorded in the repository: it was mailed to
  participants only); the last response before the deadline counts (SUBMISSION.md). Only the team lead fills it in.
  The technical document changed on 16 Nov (Section 3: the fourth attempt; Section 6: the extended disclosure, K021): the
  Form is sent again with the `LittleSickle.md` of the chain run that follows the K021 commit.
- **Deadline:** Tue 17 Nov 23:59 CET = Wed 18 Nov 01:59 Istanbul.

## Earlier status (15 Nov 2026, evening)

- **Submission system: `possession-v2.16`** (`python -m possession.run216`, manifest `possession-v216-release.json`,
  frozen 2026-11-15 17:05) = v2.15 + one step (`possession/playerfill.py`): when the broadcast files are present and
  the accuracy gate of the ball fill is open, a registered broadcast player with no tactical player of either team
  within 1.5 m is added to the tracking the models see (one extra slot per broadcast track, team of that track); the
  goalkeeper check then runs on tactical + added players. Tactical positions are never moved. Without broadcast files,
  with the gate closed or with `add_players=False` (test switch) `run216` writes the bytes of `run215` (tested).
  `run216.py` is derived from `run215.py` by exact text replacements (`experiments/possession_v2/v218/port/make_run216.py`).
  Ladder in `possession-release.json`: v2.16 -> v2.15 -> v2.11k -> v2.11g -> v2.9g -> v2.5b -> v2.5b tactical only.
  Do not edit `playerfill.py` or `run216.py` (hash-frozen); a change needs a new version and a new plan.
- **Where it came from (K016, exploration):** the team lead asked whether the broadcast camera should take priority where
  it agrees with the tactical one. On development copies with a simulated second camera, taking the ball or the players
  from the broadcast stream where both agree changed the score by -0.005 to +0.002, even with a stream five times as
  precise (`possession-k016-camera-priority.json`); without the second camera the score is 0.036-0.043 lower. Adding the
  players the tactical copy has lost was the one variant with a gain (+0.0057 / +0.0097 on four copies).
- **Validation (K017):** `possession-v216-plan.json` registered 15:01:19 before the first validation row; 16 new
  copies with a simulated second camera, both arms on the same copy and stream: 0.6864 -> 0.6968 (+0.0104;
  DFL +0.0098, Metrica +0.0111; 13 better, 3 worse, worst -0.0056); medium stream +0.0073; stream that loses and
  invents players +0.0044 (one copy -0.0148); copies of the other simulator +0.0004 (3 of 4 lower). All seven
  gates (the thresholds of the earlier plans) passed; G7 by 0.0004. **Say these margins whenever the result is quoted.**
  The plan says no further candidate that takes players from the broadcast tracking is registered before the deadline.
- **Conditions of the registered decision rule** (otherwise v2.15 stays), to be met by 16 Nov 23:59 Istanbul: runs under
  Python 3.10 / numpy 1.26.4 (done); eleven synthetic bundles byte-identical under 3.10 / 1.26.4 and 3.13 / 2.5.3 (done; two
  new variants with added players, one per model path); full test suite (done: 467 tests, 15 skipped under 3.10 with the
  pins; 467, 4 skipped under 3.13); full-size chain rehearsal (done: `possession-v216-rehearsal.json`, all steps OK in
  1006 s, peak 2.2 GB; 67,338 positions added on that synthetic bundle; spellF1 0.7826 against 0.7721 for
  the v2.15 chain file; a wiring check, not an accuracy claim); documents (done). **Still open: the delivery chain must
  run OK on the team's computer** with `URETIM` and `TESLIM` naming `possession-v2.16`; if they name a lower step, that
  step is what is delivered and the documents must be brought in line before the Form is filled.
- **Limits to keep in every description:** the second camera is simulated and its players come from clean positions;
  the provided broadcast tracking was not examined (a referee it carries under a team and the tactical tracking lacks
  would be added as a player); the step was picked among seven variants on four development copies on a day on which
  three other ideas were examined on the same matches.
- **Delivery chain:** `PLATFORM` compares eleven synthetic variants; Appendix R has a "Players added from the broadcast
  camera" row (category only). `GIT-YUKLE-V2.cmd` now calls git with `--no-pager` (on 15 Nov the team lead's window
  stopped for hours at the pager's "(END)" until he pressed q) and asks for no key when `TESLIM-TEK-TIK.cmd` starts it
  (`POSSESSION_NO_PAUSE`); the data-type guard is unchanged.
- **The team lead's runs on 15 Nov:** `TESLIM-TEK-TIK.cmd` started 11:34 (all nine files placed), the upload went through
  at 16:28 (commit 668fc04: v2.15, records K007-K014; GitHub Actions succeeded on it), and the chain then ran from 16:28
  to 17:31 with v2.15 as the first step: **every step OK** (Windows 10, Python 3.10.11; `PLATFORM AYNI` on nine
  variants; `VERI` videos and Smart Tagging present; `URETIM` / `TESLIM` possession-v2.15 with the clock anchor; same bytes
  without clock, on a second run and from a fresh clone; organisers' validator and the public pass/fail check OK;
  `SONUC: TESLIM HAZIR`; log entry K018). So a valid v2.15 delivery exists in `FootballPrivate\teslim` (`LittleSickle.csv`,
  `LittleSickle.md`) and the last condition of K013 is met. The v2.16 files and the K015-K018 records are copied to the PC
  only when no launcher is running there (never overwrite a `.cmd` file that may be running), and reach GitHub with
  the next run of `TESLIM-TEK-TIK.cmd` or `GIT-YUKLE-V2.cmd`.
- **Asked and refused on 15 Nov 14:06:** integrating a ready-made video model and judging it by eye on the provided
  video. Checking output against the provided video is forbidden by the organisers' clarification of 3 Nov; ready-made
  "possession from video" tools use the nearest-player rule on weaker detections than the provided tracking, and
  action-spotting models could not be measured together with our system on any external match in the time left.
- Everything in the snapshot below still holds except the name of the release and what is listed here.

## Earlier status (15 Nov 2026, early morning to afternoon)

- **Submission system: `possession-v2.15`** (`python -m possession.run215`, manifest `possession-v215-release.json`,
  frozen 2026-11-15 02:33) = v2.11k + a second model family on the core model path (v2.1, measured noise at most
  0.30 m): the second-stage probabilities of the tree models are averaged with those of a temporal convolution
  network, weight 0.2 for the network (`possession/pooling.py`), rounded to 6 decimals and decoded by the unchanged v2
  decoder; the kick-off rule follows. On the v2.3 path nothing is averaged and the output is that of v2.11k (tested:
  with the pooling off `run215` writes the bytes of `run211k`). Network: `possession/tcn/` = byte copies of the
  inference modules of a team member (branch `mtah-possession`, commit 167dc7b); weights
  `models/possession-tcn-v215.npz` = three members trained by us. Ladder in `possession-release.json`: v2.15 -> v2.11k ->
  v2.11g -> v2.9g -> v2.5b -> v2.5b tactical only. `possession-release-graded-windows.json` is unchanged (the v2.11g
  ladder: no kick-off rule, no second model). Log entries K012 and K013. Do not edit `possession/tcn/*.py`,
  `pooling.py`, `run215.py` or the weights (hash-frozen); a change needs a new version and a new plan.
- **Three registered attempts with the second model, always the same gates** (the documents say so; a pass at the
  third attempt is weaker evidence than at the first):
  v2.13 (K010; his committed weights, weight 0.5, his single-cost decoder): 3 of 6 gates failed.
  v2.14 (K012; weights re-trained here on both corruption simulators, three members, weight 0.5, our decoder):
  16 new copies +0.0201, 15 better, but one copy -0.0160: the gate on single copies (G4) failed, not released.
  v2.15 (K013; the same with weight 0.2, chosen on 42 development copies by a rule written while the v2.14 validation
  was running): 16 further new copies 0.6447 -> 0.6559 (+0.0112), 14 better, 0 worse, 2 equal (v2.3 path);
  DFL +0.0126, Metrica +0.0097, broadcast fills +0.0106 / +0.0114, copies of the other simulator +0.0197; all seven gates passed.
  The v2.15 plan says: **no further candidate with the second model is registered before the deadline.**
- **Weights:** PyTorch could not be installed in the agent session; the team member's `train.py` was re-implemented
  in JAX (`experiments/possession_v2/v214/tcn_jax.py`; checked against his NumPy inference, largest probability
  difference 7.9e-7). Training data: the six DFL matches of the tree bundles only, twelve corrupted copies of every
  half (six per simulator). `dfl4_both_s0-2` (four matches) served the DFL validation rows, `dfl6_both_s0-2` are the
  released members. A re-run is not bit-identical: never replace the npz. The member files (hashes in the plans) are
  backed up on the user's PC under `FootballPrivate/sportec-development-20261107/possession-validation-models/tcn-v214`
  (external data only, not in git). Running notes with the clock times at which the selection rules were written:
  `experiments/possession_v2/v214/NOTES.md`.
- **Reported after the decisions, never decision inputs:** one new copy of Metrica game 3 (v2.15: tactical +0.0222) and
  PFF game 3839 (no published licence, kept outside the repository): v2.11 0.6289, v2.15 0.6542.
- **Conditions of the registered decision rule for delivering v2.15** (otherwise v2.11k stays), to be met by 16 Nov
  23:59 Istanbul: inference under Python 3.10 / numpy 1.26.4 (done); nine synthetic bundles byte-identical under
  3.10 / 1.26.4 and 3.13 / 2.5.3 (done; `tests/test_possession_crossplatform.py`, two variants with the network); full
  test suite (done: 448 tests, 15 skipped, under 3.10 with the pins; 448, 4 skipped, under 3.13; 448, 115 skipped,
  with scipy / pandas blocked, which is what CI shows while its workflow installs only `requirements.txt`); a full-size
  chain rehearsal (done: `possession-v215-rehearsal.json`, all steps OK in 761 s, peak 1.53 GB; on that synthetic
  bundle spellF1 0.7721 against 0.7641 for the v2.11k chain file; a wiring check, not an accuracy claim); documents
  describe the second model, its training data and the three attempts (done). **Still open: the delivery chain must
  run OK on the team's computer** (the `URETIM` and `TESLIM` lines must name `possession-v2.15`; if they name a lower
  step, that step is what is delivered and the documents must be brought in line before the Form is filled).
- **K014 (15 Nov, reporting only; release unchanged):** error-pattern study asked for by the team lead on the 42
  development copies (`possession-k014-error-patterns.json`, `experiments/possession_v2/v216/`): true possessions under
  2 s are 29% of the labels and 38% of the lost score (70% missed; neither model family shows them); 29% of the loss is
  timing of found possessions (the decision switches while the ball is still travelling to the new team). Decoder
  constants, contact evidence and a reception re-timing rule changed the score by at most 0.003; a minimum possession
  length costs 0.008 at 1 s on the external labels and pays only if the competition labels ignore short touches (not
  measurable externally, not adopted); a
  learned combination of both families (leave one match out, exploration) gained +0.0095 with a worst copy of -0.023
  and was NOT registered (the v2.15 plan says no further attempt with the second model). The organisers state that
  differences below about 0.04 are noise on one match. Do not present any of this as a validation.
- **K015 (15 Nov, reporting only; release unchanged):** the team lead asked whether a Smart Tagging set-piece tag
  without a `D` of ours around it should force a dead-ball stretch (`possession-k015-tag-rescue.json`,
  `experiments/possession_v2/v217/`; simulated tags on the 42 development copies, the provided tag file was not read).
  The decision already has `D` on 93% of the stretches before a restart; the published tag counts (57 without the
  start kick-offs, only 5 free kicks) cover about half of the restarts, so the case occurs 2.4 times per copy. Ceiling
  +0.0029; the rule (force the decoder through `D` where it costs least, cost limit 120) +0.0005 to +0.0016; without
  the limit false tags cost up to -0.0045. Not registered (a tenth of the +0.008 gain gate). Do not present it
  as tested on real tags, and do not re-open it without new evidence about the real tags (which cannot be looked at).
- **Final-test plan NOT re-registered:** `possession-final-test-plan.json` stays registered for `possession-v2.11k`
  (the release without the second model; `tests/test_possession_final_test.py` checks exactly that). The network's
  designer used J03WMX during his development, so a run of v2.15 on it could not be reported as a fresh test. The
  released weights were trained without it and the process that built the release has not downloaded it. A result of
  `SON-TEST.cmd` is a result of v2.11k (steps 1-8) and is reported as that.
- **Delivery chain:** `PLATFORM` compares nine synthetic variants; Appendix R has a "Second model" row (category only:
  used / not used on this path / not part of this entry point). `TESLIM-HAZIRLA.cmd` needs no option.
- **One double-click (15 Nov, the user could not place the files himself):** `TESLIM-TEK-TIK.cmd` = (1)
  `tools/possession_place_files.py` (stdlib; finds the nine shipped files by name in Downloads / Desktop / Documents /
  Videos / OneDrive / FootballPrivate / other drives' top levels, also inside .zip, copies only missing ones into the
  bundle, never replaces; exit 0 all, 2 only videos missing, 1 required file missing -> stop; prints names, folders and
  status words only; tests `tests/test_possession_place_files.py`) -> (2) `GIT-YUKLE-V2.cmd` -> (3) the chain with
  `--team LittleSickle` -> (4) copies `FootballPrivate\teslim\PAYLASILABILIR-durum.txt` (only the chain's shareable lines)
  and the placement status to `Desktop\logs` (a connected folder) so the assistant can read the status instead of the
  user pasting it. The assistant must never copy the match files itself: the bridge would route them through the cloud.
- GitHub: remote branch still at a152fa2 (11 Nov 21:58) when this was written. K007-K013, v2.11k, v2.15 and the
  weights are pushed only when the user runs `GIT-YUKLE-V2.cmd` (this session has read-only access).
- **15 Nov 11:34:** the user started `TESLIM-TEK-TIK.cmd`; `Desktop\logs\DOSYA-durum.txt` says all nine files are in the
  bundle (`SONUC: TAMAM`; the two videos were copied from Desktop and Downloads, the rest was already there). At 12:16
  the remote branch was still at a152fa2 and no `PAYLASILABILIR-durum.txt` existed: the launcher was probably waiting
  for a key in the upload step. The K015 records (log entry, JSON, `experiments/possession_v2/v217/`, document sentences,
  launcher message) were written in the agent copy at 12:15 and are copied to the PC only after that run has ended:
  never overwrite a `.cmd` file while it may be running (cmd.exe reads batch files from disk as it goes), and a
  document changed mid-run would show up as a locally modified file in the run record.
- Still pending (user): the three files in the bundle folder (two videos, Smart Tagging) -> `GIT-YUKLE-V2.cmd` ->
  Actions -> `TESLIM-HAZIRLA.cmd` -> paste the `[..]` lines and `SONUC` -> Google Form (one member submits; team name
  `LittleSickle`; deadline 17 Nov 23:59 CET = 18 Nov 01:59 Istanbul). Optional: `SON-TEST.cmd` (v2.11k only).
- **Standing rule, repeated:** aggregates computed on the provided match (scores, label shares, tag positions) are
  not inputs to any choice and are not copied into any file; only the chain's status lines are shared. The organisers'
  published constants (DATA.md, FAQ.md, games.py, starter code) are public documentation, not such aggregates.

## Earlier status (13 Nov 2026 afternoon)

- **Submission system: `possession-v2.11k`** (`python -m possession.run211k`, manifest `possession-v211k-release.json`,
  frozen 13 Nov 12:33) = v2.11g + one rule (`possession/kickoff.py`): in every graded block, the frames before the
  first automatic Smart Tagging "Kick Off (Start)" tag (code SET PIECES, group Type, case-insensitive; frame =
  round(seconds x fps)) are written `D` if that tag starts less than 10 minutes after the block's first frame.
  File missing / unreadable / no usable tag -> byte-identical to v2.11g. Ladder in `possession-release.json`:
  v2.11k -> v2.11g -> v2.9g -> v2.5b -> v2.5b tactical only; no step uses the FAQ frame 113,742.
  `possession-release-graded-windows.json` is the same ladder without the rule. `possession.run211` (FAQ frame) stays
  frozen and unused. Log entry K011. Do not edit `kickoff.py` / `run211k.py` (hash-frozen); a change needs a new version.
- **Why:** the organisers' answer of 12 Nov did not allow hard-coding the FAQ frame explicitly ("anything that is not
  explicitly allowed is not permitted"); Smart Tagging as input is explicitly allowed. The rule was taken unchanged
  from a team member's branch (`mtah-possession`, commit 4b32747); `tests/test_possession_kickoff.py` compares the two
  implementations on 300 random synthetic cases. Public support: DATA.md lists 2 such tags; the organisers'
  `starter/load_smart_tagging.py` says each tagged kick-off is a window of about 5 s that contains the real kick-off
  (so the rule should write `D` only before the kick-off and leave the last moments before it to the models). It
  cannot be measured externally: tests are synthetic, plus one chain rehearsal on the synthetic bundle of K003 with an
  invented tag file (all steps OK, spellF1 0.764 like the v2.11 chain on that bundle, 0.759 without the rule; without a tag file the delivered file is byte-identical to the v2.11g chain file; `possession-v211k-rehearsal.json`).
- **Delivery chain:** `VERI` now also says `smart tagging VAR/YOK` when the release reads that file (step flag
  `"smart_tagging": true` in `possession-release.json`) and warns when it is missing: without it the team's file is the
  v2.11g output while the organisers' regeneration from the whole bundle would apply the rule. `GIRDI OKUMA` has 28
  checks (new: `tagging_reader_runs`, `tagging_kickoff_start_tags` = the 2 tags DATA.md lists; SKIP without the file).
  Appendix R has a "Kick-off rule" row (category only, no frame, no count). On 11 Nov the user's chain run reported
  `videolar YOK` (K006): the two videos and the Smart Tagging file must be in the bundle folder
  (`tactical/BAR-ATH_tactical.mp4`, `tactical/BAR-ATH_tactical_smart_tagging.xml`, `broadcast/BAR-ATH_broadcast.mp4`);
  the user copies them, never an agent.
- **v2.13 NOT selected** (log entry K010): the release's second-stage probabilities averaged with a team member's
  temporal convolution network (branch `mtah-possession`, commit 167dc7b; his `fuse.py` unchanged: weight 0.5, one
  Viterbi pass with switch cost 6). Registered `possession-v213-plan.json` (13 Nov 12:12) before any score of the
  fusion or of the committed weights existed here; results `possession-v213-results.json`: tactical camera only, 16 new copies +0.0063 spellF1 (DFL -0.0045, Metrica +0.0172, worst copy -0.0295); broadcast fill +0.0107 / +0.0143; TCN alone 0.6257 against 0.6598. 3 of six gates failed (G1, G2, G4).
  Reported, not gates: 4 copies of the TCN author's simulator +0.0277 (there the TCN alone beats v2.11 on 3 of 4, on
  none of our 16); after the decision, one copy of Metrica game 3 -0.0015 (fill -0.0154 / +0.0173) and PFF game 3839
  0.629 -> 0.632. The fusion is uneven, not useless; any further attempt needs a new registered plan.
  Scripts and byte copies of his modules: `experiments/possession_v2/v213/`. His weights are not in this branch.
- **Final-test plan re-registered for v2.11k** (13 Nov 12:48, `experiments/possession_v2/register_final_test_v211k.py`).
  On J03WMX the output equals that of v2.11 (no Smart Tagging, play blocks = halves). J03WMX has not been downloaded by
  the process that built the release (checked on 13 Nov: not under the user's `sportec-development-20261107/prepared-v1`,
  no final-test log); a team member used it while developing his separate model, so write "reserved for the release",
  never "untouched by the team". `SON-TEST-GECE.cmd` / `SON-TEST-ZAMANLA.*` on the user's PC are stale helpers of
  11 Nov (scheduled time passed, no log of a run exists, not in git); `SON-TEST.cmd` is the launcher.
- Tests: 435 (15 skipped) under Python 3.10 with the pins and 435 (4 skipped) under Python 3.13 / numpy 2.5.3, both run on the final code of 13 Nov. The seven-variant cross-platform check is unchanged (the kick-off rule has no floating-point part).
- GitHub: remote branch still at a152fa2 (11 Nov 21:58). K007-K011, v2.11k and the v2.13 records are pushed only when
  the user runs `GIT-YUKLE-V2.cmd` (this session has read-only access). No Form link e-mail as of 13 Nov 13:10 Istanbul.
- Still pending (user): put the three files above into the bundle folder -> `GIT-YUKLE-V2.cmd` -> Actions ->
  `TESLIM-HAZIRLA.cmd` (no option: the default is v2.11k) -> paste the `[..]` lines and `SONUC` -> Google Form.
  Optional before 17 Nov: `SON-TEST.cmd`.
- **Standing rule, repeated:** aggregates computed on the provided match (scores, label shares, tag positions) are
  not inputs to any choice and are not copied into any file; only the chain's status lines are shared. The organisers'
  published constants (DATA.md, FAQ.md, games.py, starter code) are public documentation, not such aggregates.

## Earlier status (12 Nov 2026 evening)

- **Submission system unchanged: `possession-v2.11`** (`check_release()` passes). The 11 Nov afternoon snapshot
  below still holds except for what is listed here.
- **v2.12 NOT selected** (log entry K008): touch / control-change columns (`possession/touch.py`, 36 columns) for
  the short possessions K007 found missing. Registered plan `possession-v212-plan.json` (12 Nov 02:16), results
  `possession-v212-results.json`: DFL +0.0125 (all 8 copies better), Metrica -0.0077, broadcast-fill conditions
  negative; 4 of 6 gates failed. `touch.py` and its test stay as an unreleased candidate; the prepared entry point,
  pipeline and training script are under `experiments/possession_v2/v212/integration_not_released/` (never run).
- **Organisers' answer to the kick-off question** (e-mail, 12 Nov 11:21 UTC): no yes or no; they repeated the
  3 Nov clarification and added "anything that is not explicitly allowed is not permitted". Keeping v2.11
  (FAQ frame 113,742 hard-coded) or delivering the reserve v2.11g (`TESLIM-HAZIRLA.cmd --release-config
  possession-release-graded-windows.json`) is the team's decision; not taken when this snapshot was written.
  Either way `TECHNICAL_DOCUMENT.md` item 7 and the kick-off limitation must say what was done and why.
- **K009, inspection only:** the frozen v2.11 decision (no second camera) on PFF FC World Cup 2022 game 3839
  (Spain–Germany; data from PFF's sign-up form, no published licence, kept outside the repository) against a
  proxy built from PFF events: spellF1 0.629, macroF1 0.898. Most disagreement is "dead" while the ball is off
  screen; restarts seen about 1.8 s late; short possessions merged (236 vs 360 spells). Not a selection input;
  scripts in `experiments/possession_v2/pff_viewer/`.
- Still pending (user): `GIT-YUKLE-V2.cmd` -> Actions -> `TESLIM-HAZIRLA.cmd` (with the chosen config) -> Form
  (link expected by e-mail by 14 Nov). Optional before 17 Nov: `SON-TEST.cmd` (J03WMX still untouched).

## Earlier status (11 Nov 2026 afternoon)

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
