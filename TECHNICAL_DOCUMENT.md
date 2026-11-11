# Possession v2.11 — technical document (short version)

This is the document for the submission form. The full record (every candidate, table and
reproducibility check) is `TECHNICAL_DOCUMENT_V2.md`; data sources and licences are in
`DATA_SOURCES.md`; every experiment has a plan file registered before its results
(`possession-v*-plan.json`) and a results file (`possession-v*-results.json`).

## 1. Approach and why

**Input.** The provided tactical automatic tracking (players, ball, team of each track slot) is the
main input; the broadcast tracking is a second ball source behind a gate. No label of the provided
match is used anywhere.

**Pipeline** (`python -m possession.run211`):

1. *Features* (`possession/features.py`, about 230 per frame, positions only): whether the ball is
   seen and for how long it was/will be missing, where it was last and next seen relative to the
   lines and restart spots, ball speed and sudden velocity changes (kicks), tempo of all players
   (stoppages slow the whole field), and for each team the distance of its nearest player to the
   ball, players near the ball, a control indicator (within 1.2 m and moving with the ball), and how
   long the team was/will be nearest over 1-10 s windows.
2. *Two frame models*: gradient-boosted trees for P(ball dead) and P(home has it | ball alive).
   Every training copy is also shown with the teams exchanged and both views are averaged at
   inference, so the system cannot prefer a side.
3. *Second stage*: the same two targets re-estimated from how the stage-1 probabilities evolve over
   the surrounding 0.2-10 s (trained on out-of-fold probabilities, so it sees realistic
   uncertainty).
4. *Decoder*: a three-state (H, A, D) Viterbi path per half with a cost for each team change and
   each stoppage start/end. This turns frame probabilities into possessions: the ranking metric
   matches whole possessions, and a frame-wise argmax scores 0.44 where the decoder scores 0.63 on
   the same external copies.
5. *Noise gate*: the frame-to-frame position noise of the tracking is measured from second
   differences. Up to 0.30 m (the range the core models were trained with) the core models run;
   above it, the same pipeline runs on positions smoothed over +-2 frames with models trained on
   noisier data.
6. *Broadcast ball fill*: the broadcast tracking is aligned to the tactical frames (lag anchored on
   the match clock that both videos show, read by OCR; refined by matching player positions;
   replays and close-ups rejected). The broadcast ball is then *registered*: players seen by both
   cameras measure the calibration error of the broadcast mapping in each frame (difference between
   matched players, weighted towards the ball, median over +-0.5 s), and that error is subtracted
   from the broadcast ball, which is then smoothed over +-2 frames. Missing tactical ball positions
   are filled with this ball only if, where both cameras see the ball, they agree within 0.50 m
   (median). The gate uses ball positions, which the registration never used, so it is an
   independent check.
7. *Second-half kick-off*: the FAQ states that frames 110,808-113,741 are graded and all `D`
   because the second half kicks off at 113,742. Second-half play is started at that published
   frame; the frames before it are written `D`. We asked the organisers whether a constant taken
   from their documentation may be used this way. `possession.run211g` is the same system without
   it (the models run on the whole graded second half) and is kept in reserve for a negative
   answer; Appendix R names the entry point that produced the submitted file.
8. *Goalkeeper team check* (`possession/keeper2.py`, applied to the tracking before step 1). The
   team of a track slot is decided by the tracker, and a goalkeeper does not wear his team's kit.
   If a goalkeeper's track carried the other team's id, the features would see an opponent standing
   in the goal; with both goalkeepers affected, the attacking directions that step 1 derives from
   the mean position of each team come out inverted (external copies: spellF1 0.335 instead of
   0.659). The check finds goalkeeper track pieces from positions only: while play is in the
   other half, the tracked player nearest to a goal and at least 8 m behind everybody else, and
   pieces that continue such a piece in time and place. A piece in a slot of the team that does
   not defend that goal is moved to the defending team if most of that goal's evidence in that
   half is under the other id (mislabelled for the whole half), or if it continues a goalkeeper
   piece (mislabelled for a while). Otherwise nothing changes and the output is that of steps
   1-7 alone. We did not look at whether the provided tracking has such errors; Appendix R says
   whether anything was moved.

**Why this design.** (i) The ball is missing on 41% of graded frames, so the system must reason
from context around gaps; that is what the windowed features and the decoder do. (ii) We were
required to make every choice on other matches (Section 6), and clean external tracking does not
look like automatic tracking. Every external copy was therefore corrupted first (temporally
correlated ball loss that is more likely in crowds and for fast balls, position noise, false ball
detections, player track gaps, wrong-team tracklets) with parameters drawn at random per copy from
broad ranges anchored only on the aggregate statistics published in DATA.md. (iii) Trees on
hand-built geometric features train in an hour on a laptop, are deterministic, and are exported to
plain numpy arrays, which makes exact regeneration realistic.

**Missing and noisy tracking.** *Missing ball:* the models are trained on copies in which the ball
disappears the way an automatic tracker loses it, and the features describe the gap itself (how
long the ball has been and will be missing, where it was last and next seen, which team's players
were nearest before and after). The decoder carries the current possession through a gap unless
the evidence around it says otherwise. A missing ball is never read as a stoppage. *Players:*
track gaps and tracklets with the wrong team are part of the training corruption; track slots that
the metadata assigns to neither team are dropped. *Position noise:* measured on the input itself
and handled by the matching model path (step 5). *Team ids of goalkeepers:* checked against where
the tracks stand and corrected only on clear evidence (step 8). *Second camera:* used only to fill gaps, only
after the agreement gate (step 6); a tactical ball position is never replaced. Without broadcast
files, or with the gate closed, the output is the tactical-only result, and `run.json` records
which path was taken.

## 2. Possession rules as implemented

The rules are learned from the external providers' labels and enforced by the decoder; they are not
hand-written thresholds.

- **Controlled possession.** A team has the ball when one of its players controls it or it is
  travelling between its players. A pass in flight belongs to the passing team.
- **Loose balls.** The last team in possession keeps the label while the ball is loose or not
  visible. The label changes only when the evidence that the other team controls the ball outweighs
  the switch cost (the switch cost of the decoder).
- **Challenges, deflections, blocks, aerial duels.** A touch without subsequent control does not
  change possession. If the challenger comes away with the ball, possession changes at the point
  the decoder places the change, which is close to the moment control becomes evident, not the
  first contact. Very short changes of possession (about a second) are usually not reported; this
  is the main known error (Section 5).
- **Dead ball.** `D` is predicted from the situation, not from a missing ball: the ball last seen
  on or beyond a line, a ball lying still at a restart location, the field slowing down, kick-off
  formation. A tracking gap in open play is not a stoppage. Stoppages with the ball on the pitch
  (fouls, injuries, VAR) are recognised mostly through tempo and are the hardest case.
- **Restarts.** `D` lasts until the ball is played. The first possession after a stoppage goes to
  the team that plays the restart; either team may follow a stoppage at no extra cost.
- **Abstention.** No `X` is written on graded frames. Frames outside play are `D`.

## 3. Assets used, and tried and dropped

| asset | status |
|---|---|
| tactical ATD | used (main input) |
| broadcast ATD + homography `valid` flag | used behind the 0.50 m agreement gate; `run.json` records whether the gate opened |
| videos | only the on-screen match clock (OCR every 5 s) to anchor the broadcast alignment |
| Smart Tagging | tried on simulated tags (no external match has comparable tags), dropped: +0.011 with typical tags but -0.008 without tags, registered gates failed |
| tactical homography | not used |
| public 5-minute ground truth | not used for any choice. After the file is generated, the delivery tool runs one pass/fail check of pipeline correctness on it (valid file, not broken, teams not exchanged; `possession/public_check.py`). The thresholds were registered beforehand (`possession-final-check-plan.json`); no score is printed or stored, and a failure may only lead to a search for an indexing or mapping bug. Appendix R of the submitted copy says whether it ran |
| Sportec/DFL open data (CC BY 4.0) | training and validation, provider's per-frame possession/ball-status flags |
| Metrica sample games 1-3 | validation and a reserved test, proxy labels derived automatically from events |

Tried and dropped, each against a gate written down beforehand: ungated broadcast fill (a second
ball with 0.5-1.5 m error lowered the score), wider noise training alone, a learned switch-hazard
decoder (+0.002), gap-bridging ball features (+0.002), a wide decoder sweep (flat), adding a
Metrica sample game to the training matches (+0.001 on the other Metrica game, -0.011 on DFL), a first
version of the goalkeeper check (passed its gates; replaced before release, see Section 5). An earlier
vision line (ball detector, contact/control state machine, dead-ball layers under `development/`)
is not part of the submission.

## 4. Training data

Nothing from the provided match was used as a label, a correction or a tuning target. Hand
labelling by the team: none. Details and per-match counts are in `DATA_SOURCES.md`.

| dataset and source | labels: what, by whom | amount | use |
|---|---|---|---|
| Sportec/DFL open data (Bassek et al. 2025, *Scientific Data*; CC BY 4.0), six matches, from the Hugging Face mirror `pysport/idsse-data` at commit `a715a38` (files pinned in `sportec-data-plan.json`) | the provider's per-frame `BallStatus` (in / out of play) and `BallPossession` (home / away) flags inside the official tracking files; mapped mechanically to `D` / `H` / `A` | 856,677 frames at 25 fps, about 9.5 hours: 29.7% `H`, 24.9% `A`, 45.4% `D` | training of both model bundles (all six matches); during model selection four were used for training and two for validation |
| Metrica Sports sample data, games 1-3 (github.com/metrica-sports/sample-data, commit `e706dd5`) | no possession labels exist; proxy labels computed automatically from the provider's event files (`experiments/possession_v2/metrica_labels.py`) | three matches | validation (games 1-2) and a reserved test scored once per frozen system (game 3); not used to train the submitted models |

A training row is every sixth frame of three independently corrupted copies of a match, also with
the teams exchanged (856,678 rows per bundle). A seventh DFL match is reserved for one final test
of the frozen release (design registered in `possession-final-test-plan.json`); it had not been
downloaded when this document was written.

## 5. External results and limitations

All numbers are agreement with other providers' labels on corrupted copies of other matches. They
are not competition scores and the fixtures had been accessed before, except where "reserved".

| measurement (spellF1) | baseline logic | our system |
|---|---|---|
| 8 validation copies (2 DFL + 2 Metrica matches), core models | 0.196 | 0.631 |
| reserved Metrica game 3, scored once after freezing | 0.219 | 0.664 |
| 24 fresh copies incl. position error beyond the training range: without / with noise gate | | 0.603 / 0.642 |
| 16 fresh copies with a simulated accurate broadcast: without / with fill | | 0.651 / 0.675 |
| 16 copies not used before, simulated broadcast with medium calibration error (0.2-0.6 m): fill without / with registration | | 0.653 / 0.681 |
| same copies, accurate broadcast: fill without / with registration | | 0.686 / 0.684 |
| 8 copies not used before, team ids as corrupted: without / with the goalkeeper check | | 0.659 / 0.660 |
| same copies, both goalkeepers under the other team's id: without / with | | 0.335 / 0.656 |
| same copies, one goalkeeper under the other id: without / with | | 0.627 / 0.658 |
| same copies, both goalkeepers under the other id 30% of the time: without / with | | 0.642 / 0.659 |
| same copies seen by a camera that does not track players beyond 42 m (35 m) from play, ids correct: without / with | | 0.649 / 0.649 (0.646 / 0.646) |

The registration was first evaluated on 16 copies of which 8 had already served an earlier
candidate (0.647 / 0.678 and 0.683 / 0.681). Our own records audit found this. The 8 were replaced
under an amendment registered before the new results, the same four gates were applied once, and
they passed (`possession-v29-amendment-plan.json`, `-results.json`; the first evaluation is kept
unchanged in `possession-v29-results.json`).

A second finding of our own audit (log entry K005): the rehearsal scores in Section 7 and two
diagnostics (track slots, goalkeeper ids) were first computed in the Python 3.10 environment of the
release, where our label script ordered simultaneous events differently from the provider's files
and lost about half of the dead-ball intervals of the Metrica proxy labels. Every selection, gate,
validation and reserved test had run in the experiment environment, where the labels are in file
order (the possession counts stored with the first validation confirm it), so no choice was
affected. The script now sorts stably, the three records were recomputed, and this document
quotes the recomputed numbers (`possession-label-order-correction.json`; the first numbers are
kept in `possession-rehearsal-results.json` and `possession-v210-plan.json`).

Limitations:

- **Domain gap.** The models never saw the provided tracking. If its missing-ball pattern or
  position error lies outside the simulated ranges, quality drops; slowly varying position bias is
  invisible to the noise gate.
- **Label semantics.** DFL possession flags change on short touches more often than a
  "controlled possession" definition; the Metrica proxies are closer but have approximate stoppage
  boundaries.
- **Short possessions are missed.** On the validation copies most unmatched true possessions last
  about a second; the system predicts about a third fewer team changes than the labels contain.
  With the ball hidden in exactly these moments, tracking alone does not carry the information
  (decoder and feature changes did not help).
- **Broadcast fill and registration** were validated on simulated streams only, built by us; the
  simulator assumes that players and ball share most of the calibration error (plus a spatial warp
  and a ball-only error). With an already accurate broadcast the registration changed the score
  by -0.002 on average and by -0.020 to +0.011 on single copies (lower on 9 of 16), so on one
  match its effect can go either way; with a medium broadcast it was higher on 15 of 16. On the
  provided match the gate decides once, and we have not looked at that value.
- **Second-half kick-off** rests on the organisers' statement; its effect cannot be measured
  externally.
- **Goalkeeper team check.** The id errors and the camera that hides far players are simulated by
  us; the provided tracking may have neither, or errors of another kind (a match official tracked
  under a team id cost 0.004 or less in a diagnostic and is not handled). When the far goalkeeper
  is mostly out of view (35 m window in the simulation) there is too little evidence and wrong ids
  are not corrected; with a 42 m window and both goalkeepers mislabelled the score was 0.557
  without and 0.634 with the check. With correct ids no outfield position was moved to the wrong
  team on the eight copies; with whole-match errors up to 1,299 outfield positions per copy were
  moved as well (a forward taken for the goalkeeper). A first version of the check (v2.10)
  passed its four registered gates, but an analysis of what it had moved showed that it took a
  forward waiting up the pitch for the goalkeeper whenever the goalkeeper was not tracked (14,618
  positions on one copy with the 35 m window, spellF1 -0.001 on average). It was not released;
  the second version was registered and validated with that situation as two additional gates
  (`possession-v210-results.json`, `possession-v211-plan.json`, `possession-v211-results.json`).
- **Track slots.** DATA.md says that slots change identity and that a player is occasionally
  tracked twice; the corruption used for training has neither. In a diagnostic on three Metrica
  games (one corrupted copy each), packing the tracks into 46 anonymous slots or adding duplicated
  tracks changed spellF1 by at most 0.006 on a copy and 0.002 on average
  (`possession-label-order-correction.json`). The real tracker may behave differently from this
  simulation.
- **Not measured against humans.** We did not compare the output with the provided video (see
  Section 6), so there is no visual sanity check of the submitted file beyond automatic format
  checks, aggregate plausibility ranges and the pass/fail check on the public five minutes
  (Appendix R).

With more time: recover the ball in tracking gaps from the tactical video with a detector selected
on other matches (the largest expected gain: with no missing ball the external score rises from
0.61 to 0.70); train on labels closer to the competition definition; validate Smart Tagging
restarts on fixtures with comparable tags; a model that takes the measured noise level as an input
instead of a two-path gate.

## 6. Process disclosure

Before 3 November 2026 the team compared candidates on the public five-minute window, used manual
contact marks from the provided match in diagnostics, and shared extracts of the provided match
with a hosted LLM assistant. The team reported this; the organisers required deletion of those
materials, re-selection of everything on other fixtures, a frozen pipeline and this disclosure.
The submitted system was written from scratch afterwards and uses none of the earlier artefacts;
details, including what could not be verified, are in `TECHNICAL_DOCUMENT_V2.md` Section 2 and
`REMEDIATION.md`. The v2 code was written with an AI coding assistant that only saw source code,
public external data and aggregate external results; the pipeline is run on the provided data
locally by the team.

## 7. Reproduction

Code: repository `https://github.com/ata-yunus-ortak/football-video-analysis`, branch
`feature/external-possession-selection` (the submitted system is on this branch):

```
git clone -b feature/external-possession-selection https://github.com/ata-yunus-ortak/football-video-analysis
```

Python 3.10-3.12; dependencies pinned in `requirements-possession.txt` (numpy 1.26.4, scipy 1.11.4,
pandas 2.1.4). The bundle root is the folder that contains `tactical/` and `broadcast/`.

One command (creates the environment, checks the release hashes, runs the synthetic tests, reads the
clocks, generates and validates the file; on Windows `TESLIM-HAZIRLA.cmd`):

```
python -m tools.possession_deliver --data-dir <bundle root> --private <output folder> --team <team name>
```

The same steps by hand:

```
python -m pip install -r requirements-possession.txt
# clock readings, in a separate environment (python -m pip install -r requirements-sync-lock.txt):
python -m tools.possession_clock --video <bundle root>/tactical/BAR-ATH_tactical.mp4 --out <clock>/tactical
python -m tools.possession_clock --video <bundle root>/broadcast/BAR-ATH_broadcast.mp4 --out <clock>/broadcast
python -m possession.run211 --data-dir <bundle root> --out <new folder> \
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast
python -m possession.validate <new folder>/submission.csv
```

What makes the file regenerable, and what was checked:

- The run verifies the SHA-256 of every inference source file and both model bundles against the
  release manifest and refuses to run if anything changed. `run.json` records input and output
  hashes and every gate decision.
- Tree evaluation is plain numpy with probabilities rounded to 1e-6. On external full-size inputs
  the file was byte-identical under Python 3.10/numpy 1.26 and Python 3.13/numpy 2.5 on Linux.
  `tests/test_possession_crossplatform.py` pins the output hashes of seven synthetic runs (steps
  1-7 on both model paths, with and without the broadcast camera and the clock; the full
  pipeline on two bundles whose goalkeeper tracks carry the other team's id), recorded on Linux;
  the delivery tool runs it on the computer that generates the file.
- The delivery tool generates the file a second time and once more from a fresh clone of the
  pushed branch, and compares the bytes.
- Before generating, the delivery tool checks that the release's readers return the aggregate facts
  that DATA.md publishes about the files (records, track slots, frames with a ball, mean tracked
  objects, usable homography rows), and that they agree on every frame with a second reading done
  the way `starter/baseline.py` reads the tracking files (`possession/inputs_check.py`; pass/fail
  only, result in Appendix R).
- The whole chain was rehearsed on two synthetic bundles with the file names, record counts and
  slot counts of the provided files and the aggregate properties DATA.md publishes (content:
  corrupted Metrica sample games). Every step passed, with the same bytes on a second run. Against
  the external labels the organisers' `run_evaluation.py` and our scorer gave the delivered files
  the same score (spellF1 0.763 and 0.732; 0.007 with the teams exchanged, 0.57 with the rows
  shifted by one second). After the goalkeeper check was added the chain was run again on the
  first bundle (0.764) and on a copy of it in which the goalkeepers' tracks carry the
  other team's id (0.766 with the check, 0.431 without). This checks wiring and size, not
  accuracy on the provided match.
- The clock readings come from OCR of the two videos and are not stored in the repository. They
  only anchor the broadcast alignment within +-1.6 s; the frame-level alignment is decided by
  player positions. The delivery tool also generates the file without clock readings and reports
  whether it is the same.

The outcome of these checks for the submitted file (platform, commit, model path, gate decision,
repeat run, fresh clone, with and without clock) is listed in Appendix R, which the delivery tool
appends to the submitted copy of this document on the team's computer.

Training from the public data: `python -m possession.train` with `possession-v2-config.json` and
`possession-v23-config.json` (see the long document). Experiment scripts:
`experiments/possession_v2/`.
