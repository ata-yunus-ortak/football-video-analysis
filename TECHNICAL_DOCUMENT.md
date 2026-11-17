# Possession v2.16 — technical document (short version)

This is the document for the submission form. The full record (every candidate, table and
reproducibility check) is `TECHNICAL_DOCUMENT_V2.md`; data sources and licences are in
`DATA_SOURCES.md`; every experiment has a plan file registered before its results
(`possession-v*-plan.json`) and a results file (`possession-v*-results.json`).

## 1. Approach and why

**Input.** The provided tactical automatic tracking (players, ball, team of each track slot) is the
main input; the broadcast tracking is a second source behind a gate, for the ball and for players
the tactical tracking does not have at a moment. No label of the provided match is used anywhere.

**Pipeline** (`python -m possession.run216`):

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
7. *Second-half kick-off*: the second half is graded from its first video frame, before the
   kick-off, and the FAQ states that the graded frames before the kick-off are all `D`. The
   kick-off frame published there is not used: we asked the organisers whether a constant taken
   from their documentation may be hard-coded, and their answer of 12 November did not allow it
   explicitly. Instead the models and the decoder run on the whole graded second half, and then
   one rule is applied (`possession/kickoff.py`): in a graded
   block, the frames before the first automatic Smart Tagging "Kick Off (Start)" tag are written
   `D`, if that tag starts less than ten minutes after the block begins. Smart Tagging is an
   automatic asset of the bundle that may be used as input; no frame number is stored in the code.
   Without the file or a usable tag the models' labels stand. Appendix R names the entry point
   that produced the submitted file and says whether a tag was used.
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
9. *Second model family* (`possession/tcn/`, `possession/pooling.py`; between steps 3 and 4, on the
   core path of step 5). A dilated temporal convolution network reads 37 team-level quantities per
   frame at 12.5 Hz (ball seen or not, its position, speed and the length of the gap around it;
   for each team the distance of its nearest player to the ball, players near the ball, centroid,
   spread and speed) and sees about 25 s on either side of a frame. It outputs home / away / dead.
   Its probabilities (three trained copies, both team orders averaged) and those of step 3 are
   averaged with weight 0.2 for the network and 0.8 for the trees, and the average goes through
   the decoder of step 4, unchanged. With that weight the network can move each of the three
   probabilities by at most 0.2: it has a say where the trees are undecided and cannot overrule them
   where they are sure.
   The two families use the same tracking differently (trees on hand-built windows of up to 10 s;
   a network with a long memory on raw team geometry), and on new external copies the average was
   better than the trees alone on 14 of 16 copies, equal on the 2 that take the noisier path of step 5
   and worse on 0 (0.6447 -> 0.6559, Section 5). The network's design, features and NumPy inference
   are a team member's; its weights were trained for this release on the six DFL matches of
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
   second camera adds is what the first does not see. Adding the lost players gained +0.0104 on 16
   new copies (0.6864 -> 0.6968; better on 13, worse on 3; Section 5). Without broadcast files, or
   with the gate closed, the output is that of steps 1-9.

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
the metadata assigns to neither team are dropped; a player whom the tactical tracking lacks and the
second camera shows is added (step 10). *Position noise:* measured on the input itself
and handled by the matching model path (step 5). *Team ids of goalkeepers:* checked against where
the tracks stand and corrected only on clear evidence (step 8). *Second camera:* used only to fill gaps (the ball in step 6,
players in step 10), only after the agreement gate; a tactical position is never replaced. Without broadcast
files, or with the gate closed, the output is the tactical-only result, and `run.json` records
which path was taken. *Second model:* the network of step 9 reads the same corrected tracking;
where the ball is missing it is given the position bridged across the gap together with the
length of the gap, and it was trained on copies with the gaps and false detections of both
simulators.

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
| broadcast ATD + homography `valid` flag | used behind the 0.50 m agreement gate: its ball where the tactical ball is missing (step 6) and its players where the tactical tracking has none (step 10); `run.json` records whether the gate opened |
| videos | only the on-screen match clock (OCR every 5 s) to anchor the broadcast alignment |
| Smart Tagging | the "Kick Off (Start)" tags only, for the kick-off rule of step 7. As evidence for the models it was tried on simulated tags (no external match has comparable tags) and dropped: +0.011 with typical tags but -0.008 without tags, registered gates failed. A rule that forces a dead-ball stretch at a set-piece tag where the decision has none was explored on development copies with simulated tags (log entry K015): the decision already has `D` on 93% of the stretches before a restart and the published tag counts cover about half of the restarts, so the ceiling is +0.003 spellF1 and the rule gave +0.0005 to +0.0016; not adopted |
| tactical homography | not used |
| public 5-minute ground truth | not used for any choice. After the file is generated, the delivery tool runs one pass/fail check of pipeline correctness on it (valid file, not broken, teams not exchanged; `possession/public_check.py`). The thresholds were registered beforehand (`possession-final-check-plan.json`); no score is printed or stored, and a failure may only lead to a search for an indexing or mapping bug. Appendix R of the submitted copy says whether it ran |
| Sportec/DFL open data (CC BY 4.0) | training and validation, provider's per-frame possession/ball-status flags |
| Metrica sample games 1-3 | validation and a reserved test, proxy labels derived automatically from events |

Tried and dropped, each against a gate written down beforehand: ungated broadcast fill (a second
ball with 0.5-1.5 m error lowered the score), wider noise training alone, a learned switch-hazard
decoder (+0.002), gap-bridging ball features (+0.002), a wide decoder sweep (flat), adding a
Metrica sample game to the training matches (+0.001 on the other Metrica game, -0.011 on DFL), a first
version of the goalkeeper check (passed its gates; replaced before release, see Section 5), and 36
touch / control-change columns for the core models (ball velocity changes measured against the
tracking noise and credited to the nearest player's team; `possession/touch.py`, v2.12): +0.0125 on 8
new DFL copies (all 8 better) but -0.008 on 8 Metrica copies and -0.020 on Metrica with the broadcast
fill, so four of six registered gates failed and it was not released (`possession-v212-plan.json`,
`possession-v212-results.json`). Last, averaging our second-stage probabilities with a team member's
temporal convolution network (37 features; trained by him on the same six DFL matches, and on five of
them for the copies of the sixth) and decoding the mean with one Viterbi pass (v2.13): on 16 new
copies with the tactical camera only +0.0063
(-0.0045 on DFL, +0.0172 on Metrica, single copies from -0.0295 to +0.0441), with the simulated
broadcast fill +0.0107 and +0.0143, on four copies made with his own corruption simulator +0.0277
(reported, not a gate); the network alone scored 0.626 against 0.660. The gain was not consistent:
3 of six registered gates failed (G1, G2, G4: mean gain, gain on DFL, no copy clearly worse), so it
was not released (`possession-v213-plan.json`, `possession-v213-results.json`). A second attempt changed what a diagnosis on the already-scored
copies pointed at: the network was re-trained on the corruption of both simulators (the committed
weights broke on the other simulator's false ball detections), three trained copies were used on
every row, and the average was decoded by our decoder instead of a single-cost one (v2.14, equal
weights). On 16 new copies it was better on 15 (+0.0201), but one copy was 0.016 worse, and
the gate that allows no copy below -0.010 failed; it was not released (`possession-v214-plan.json`,
`possession-v214-results.json`). The third attempt lowered the network's weight to 0.2 by a
rule written down while the second was still running, was registered before any new result, passed
the same seven gates on 16 further new copies and is step 9 (`possession-v215-plan.json`,
`possession-v215-results.json`). Its plan and our documents called it the last attempt and said
that no further candidate with the second model would be registered before the deadline. We went
back on that statement once. On 16 November the team member who wrote the network pushed eight
newly trained copies of it (four of them reading 71 quantities instead of 37) together with his
own development numbers and the weight he proposed for them, 0.4. The team lead decided to have
them validated, and a fourth validation was registered before any of its results
(`possession-v217-plan.json`): the same seven gates and thresholds, now against the released
system instead of the trees alone, on 16 new copies, run by the process that had not built the
candidate. With the tactical camera the eight
copies scored 0.6848 against 0.6704 for the release (+0.0144; better on 14 copies, worse on 2),
and with the simulated second camera they were +0.0125 (accurate stream) and +0.0050 (medium stream)
higher. Six gates passed. The gate that allows no copy more than 0.010 below the release failed:
one copy was 0.0182 lower. That is the gate the second attempt had failed, so the eight copies
were not released either (`possession-v217-results.json`) and step 9 is unchanged. Giving the broadcast
tracking priority where the two cameras agree (its ball, its players, or the mean of the two balls)
was explored on development copies with a simulated second camera and not adopted (-0.005 to
+0.002; log entry K016); the one use with a gain, adding players the tactical tracking has lost,
was registered, passed the same seven gates on 16 new copies and is step 10
(`possession-v216-plan.json`, `possession-v216-results.json`). An earlier
vision line (ball detector, contact/control state machine, dead-ball layers under `development/`)
is not part of the submission.

## 4. Training data

Nothing from the provided match was used as a label, a correction or a tuning target. Hand
labelling by the team: none. Details and per-match counts are in `DATA_SOURCES.md`.

| dataset and source | labels: what, by whom | amount | use |
|---|---|---|---|
| Sportec/DFL open data (Bassek et al. 2025, *Scientific Data*; CC BY 4.0), six matches, from the Hugging Face mirror `pysport/idsse-data` at commit `a715a38` (files pinned in `sportec-data-plan.json`) | the provider's per-frame `BallStatus` (in / out of play) and `BallPossession` (home / away) flags inside the official tracking files; mapped mechanically to `D` / `H` / `A` | 856,677 frames at 25 fps, about 9.5 hours: 29.7% `H`, 24.9% `A`, 45.4% `D` | training of both model bundles (all six matches); during model selection four were used for training and two for validation |
| Metrica Sports sample data, games 1-3 (github.com/metrica-sports/sample-data, commit `e706dd5`) | no possession labels exist; proxy labels computed automatically from the provider's event files (`experiments/possession_v2/metrica_labels.py`) | three matches | validation (games 1-2) and a reserved test scored once per frozen system (game 3); not used to train the submitted models |

A training row of the tree models is every sixth frame of three independently corrupted copies of
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
averaged system.

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
| 16 new copies (2 DFL + 2 Metrica matches), tactical camera: steps 1-8 / with the second model (step 9) | | 0.645 / 0.656 |
| the 8 DFL copies of these / the 8 Metrica copies | | 0.648 / 0.661 and 0.641 / 0.651 |
| 8 of them with a simulated accurate (medium) broadcast fill: without / with step 9 | | 0.686 / 0.696 (0.674 / 0.685) |
| 4 copies made with the team's other corruption simulator: without / with step 9 | | 0.667 / 0.687 |
| 16 further new copies with a simulated accurate broadcast camera: steps 1-9 / with the added players (step 10) | | 0.686 / 0.697 |
| the 8 DFL copies of these / the 8 Metrica copies | | 0.687 / 0.697 and 0.685 / 0.696 |
| 8 of them, broadcast camera with medium calibration error: without / with step 10 | | 0.686 / 0.693 |
| 8 of them, broadcast camera that itself loses players, invents players and mislabels teams: without / with step 10 | | 0.693 / 0.697 |
| 4 copies made with the team's other corruption simulator, accurate broadcast camera: without / with step 10 | | 0.703 / 0.704 |

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
- **Second model.** The gain of step 9 was measured on new copies of matches that had been used
  before, for this and for every earlier choice, and the network had been shown both corruption
  simulators of the team; whether it holds on tracking corrupted in a way neither simulator
  produces is not known. It passed its gates at the third attempt with the same gates (Section 3),
  which is weaker evidence than a pass at the first attempt. Single copies moved between +0.0000
  and +0.0252. Alone, the network scored 0.650 against 0.645 and was worse than the trees on 7
  of the 16 copies (by up to 0.014); it is used only in the average. Its weights come from one
  training run per seed on our side and nobody else has repeated that training; a re-run does not
  give the same bits. On the noisier model path the step is skipped.
- **Added players.** The gain of step 10 was measured with a simulated second camera whose players
  come from the clean external positions. In three of the four conditions it never loses or
  invents a player inside its window; the fourth is one invented error profile (a tenth of its
  player positions lost, ghost players beside real ones, more tracks under the wrong team), and
  there the gain was +0.0044 with one copy 0.015 lower. We did not examine the provided
  broadcast tracking: how often it loses or invents players is unknown, and a referee carried
  under a team by the broadcast tracking and absent from the tactical tracking would be added as
  a player. On copies made with the team's other simulator, which loses few players, the step
  changed almost nothing (+0.0004; lower on 3 of 4), so that gate passed by the smallest margin.
  Single copies moved between -0.0056 and +0.0261. The step was picked among seven ways of using
  the second camera on four development copies before it was validated on new ones, and it was
  the fourth idea examined on these matches on the same day. On the team's computer the release
  with this step wrote the same bytes as the release without it (status line of the delivery
  tool, 16 November): on the provided match the step changed no label. Either it was not applied
  (the accuracy gate was closed), or it found no player to add, or the players it added changed
  no decision; the row "Players added from the broadcast camera" of Appendix R says which.
- **Label semantics.** DFL possession flags change on short touches more often than a
  "controlled possession" definition; the Metrica proxies are closer but have approximate stoppage
  boundaries.
- **Short possessions are missed.** On the validation copies most unmatched true possessions last
  about a second; the system predicts about a quarter fewer possessions than the labels contain.
  An error breakdown on 42 external development copies (log entry K014,
  `possession-k014-error-patterns.json`): possessions under 2 s are 29% of the labelled
  possessions and 38% of the lost score, and 70% of them are not found. Typically the other team
  has the ball for a second or two inside a longer possession and the decision keeps the first
  team; in those stretches the averaged probability of the right team is only 0.25, although the
  ball is seen in two thirds of their frames, so the information is not in the models' view of
  the tracking (decoder and feature changes did
  not help; touch columns that detect ball velocity changes recovered part of them on DFL labels
  but not on the Metrica proxies, and were not released).
- **Timing of turnovers.** Another 29% of the lost score is the timing and extent of possessions
  that are found. With the ball seen, a turnover between two possessions of at least 2 s is timed
  within 0.5 s in 62% (DFL) and 74% (Metrica) of cases; with the ball unseen in 26-29%. The
  decision tends to switch while the ball is still travelling to the new team, whereas the labels
  switch when that team reaches it. Rules built on these patterns (contact evidence in the decoder,
  re-timing the change to the reception) changed the external score by at most 0.003 either way. A
  minimum possession length lowered it (by 0.008 at 1 s) unless the labels themselves contain no
  short touches, which external data cannot tell. None was adopted.
- **Broadcast fill and registration** were validated on simulated streams only, built by us; the
  simulator assumes that players and ball share most of the calibration error (plus a spatial warp
  and a ball-only error). With an already accurate broadcast the registration changed the score
  by -0.002 on average and by -0.020 to +0.011 on single copies (lower on 9 of 16), so on one
  match its effect can go either way; with a medium broadcast it was higher on 15 of 16. On the
  provided match the gate decides once, and we have not looked at that value.
- **Second-half kick-off.** The rule of step 7 rests on the organisers' statement that the graded
  frames before the kick-off are `D` and on their automatic Smart Tagging. It cannot be measured
  externally (external tracking starts at the kick-off and has no Smart Tagging); its tests are
  synthetic, and the chain was rehearsed on a synthetic bundle with a tag file we invented
  (Section 7). The organisers' `starter/load_smart_tagging.py` says that each tagged kick-off is a
  window of about 5 s that contains the real kick-off. If so, the rule writes `D` only before the
  kick-off and leaves the last moments before it, inside the window, to the models. A tag that
  started after the real kick-off would turn the first moments of play into `D`. Without a usable
  tag the models decide, and what they do before a kick-off was never measured either.
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

**Rules snapshot.** In October the team worked from a local copy of the organisers' `RULES.md`
dated 20 October 2026 (SHA-256 `49eb57f8...2f526ed4`, in full in `rules-provenance.json`). Its wording
allowed small amounts of hand-labelled training or validation data. The organisers changed that
wording with their clarification of 22-23 October; the team went on working from its old copy until
it reviewed the rules at the end of October.

**What happened.** In that time the team compared candidate systems on the public five-minute
window and selected versions from those results, used manually identified contact times and ball
points of the provided match in diagnostic validation, and, from about 20 October, shared frame
extracts of the provided match and those notes with a hosted LLM coding assistant (that
conversation stayed in use until 3 November).

**Reported and answered.** The team disclosed this to the organisers by e-mail on 31 October 2026.
Their reply of 3 November says that the wording had been in their own rules until the clarification,
that they see this as a "good-faith situation", and that the team may continue and its submission
will be evaluated as normal on these conditions: delete every hand annotation of the provided match
and anything derived from it; re-make every parameter, threshold and model-version choice on other
matches, without consulting the public window; freeze the pipeline and generate the file
automatically from the repository; disclose the history in this document. They also asked for a
notice of what had been shared with the hosted assistant; it was sent the same day.

**Affected stages.** Parameter and version selection of the pipelines built in October, their
diagnostic validation, and the visual, throw-in and referee prototypes of that time. None of those
artefacts, numbers or code paths is used by the submitted system.

**What was done, condition by condition.**

1. *Delete the hand annotations and everything derived from them.* All of it (786 items, about
   26 GB) was moved out of the project and deleted; its absence was checked on 3 and 7 November.
   The team's existing Git repositories were reviewed: none had one of those files in its tracked
   source. A new repository without the earlier labels, outputs and presets was started.
2. *Re-make every choice on other matches.* The submitted system was written from scratch in the
   new repository. Sections 3 to 5 say for each part on which external matches it was chosen and
   under which registered plan, and name what could not be measured on external data. In the
   delivery chain the public five-minute window is used only after freezing, as a pass/fail check
   that the pipeline runs (Appendix R). Earlier public-window scores are not presented anywhere as
   validation.
3. *Freeze, then generate.* The release is frozen by SHA-256 (every inference source, both tree
   bundles and the network weights) and refuses to run if a file differs. The file is generated
   automatically from the repository by one command; the delivery tool generates it a second time
   and once more from a fresh clone of the pushed branch and compares the bytes (Section 7). The
   run record of the delivered file is Appendix R.
4. *Disclose the history in this document.* This section; more detail in
   `TECHNICAL_DOCUMENT_V2.md` Section 2 and `REMEDIATION.md`.
5. *Hosted assistant.* The notice was sent on 3 November. The conversation was deleted on
   7 November through the application's own control, and the team lead has since verified the
   deletion on the provider's side himself.

**AI assistance in the submitted system.** The code of steps 1-8 and 10 was written, and the
weights of the network of step 9 were trained, with an AI coding assistant that worked only on
source code, public external data and aggregate external results. The network's design and
inference code were written by a team member on his own branch (`mtah-possession`). The pipeline is
run on the provided data locally by the team.

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
python -m possession.run216 --data-dir <bundle root> --out <new folder> \
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast
python -m possession.validate <new folder>/submission.csv
```

What makes the file regenerable, and what was checked:

- The run verifies the SHA-256 of every inference source file, both tree bundles and the network
  weights against the release manifest and refuses to run if anything changed. `run.json` records input and output
  hashes and every gate decision.
- Tree evaluation is plain numpy with probabilities rounded to 1e-6. On external full-size inputs
  the file was byte-identical under Python 3.10/numpy 1.26 and Python 3.13/numpy 2.5 on Linux.
  `tests/test_possession_crossplatform.py` pins the output hashes of eleven synthetic runs (steps
  1-6 on both model paths, with and without the broadcast camera and the clock; the same with
  step 8 on two bundles whose goalkeeper tracks carry the other team's id; two runs with step 9;
  two runs with step 10 on bundles whose tactical tracking loses players, one on each model path),
  recorded on Linux; the delivery tool runs it on the computer that generates the file. The
  network of step 9 is evaluated in float64 NumPy and its probabilities are rounded to four
  decimals before the averaging and to six after it; its unrounded values differ between NumPy
  builds, the rounded ones did not in our checks. The kick-off rule of step 7 only rewrites labels
  before an integer frame and has no floating-point part.
- The delivery tool generates the file a second time and once more from a fresh clone of the
  pushed branch, and compares the bytes.
- Before generating, the delivery tool checks that the release's readers return the aggregate facts
  that DATA.md publishes about the files (records, track slots, frames with a ball, mean tracked
  objects, usable homography rows, the number of "Kick Off (Start)" tags), and that they agree on
  every frame with a second reading done the way `starter/baseline.py` reads the tracking files
  (`possession/inputs_check.py`; pass/fail only, result in Appendix R). It also reports whether
  the Smart Tagging file is in the bundle, because without it the kick-off rule is not applied.
- The whole chain was rehearsed on two synthetic bundles with the file names, record counts and
  slot counts of the provided files and the aggregate properties DATA.md publishes (content:
  corrupted Metrica sample games). Every step passed, with the same bytes on a second run. Against
  the external labels the organisers' `run_evaluation.py` and our scorer gave the delivered files
  the same score (spellF1 0.763 and 0.732; 0.007 with the teams exchanged, 0.57 with the rows
  shifted by one second). After the goalkeeper check was added the chain was run again on the
  first bundle (0.764) and on a copy of it in which the goalkeepers' tracks carry the
  other team's id (0.766 with the check, 0.431 without). After the kick-off rule of step 7 was
  added the chain was run once more on the first bundle with an
  invented Smart Tagging file whose two kick-off tags are 5 s windows around the bundle's
  kick-offs: every step passed and the file scored 0.764 (0.759 for the same bundle without the
  tag file, where the models label the invented stretch before the second-half kick-off
  themselves). For the release as submitted (with step 9) it was run again on that bundle and
  tag file: every step passed, the file differs from the previous one on 0.6% of the graded
  frames and scored 0.772 (`possession-v215-rehearsal.json`). With step 10 it was run once more on
  the same bundle, whose simulated broadcast stream then also supplies players: every step passed,
  the file differs from the previous one on 0.7% of the graded frames and scored 0.783
  (`possession-v216-rehearsal.json`). This checks wiring and size, not
  accuracy on the provided match; the games in these bundles had been used in development.
- The clock readings come from OCR of the two videos and are not stored in the repository. They
  only anchor the broadcast alignment within +-1.6 s; the frame-level alignment is decided by
  player positions. The delivery tool also generates the file without clock readings and reports
  whether it is the same.

The outcome of these checks for the submitted file (platform, commit, model path, gate decision,
repeat run, fresh clone, with and without clock) is listed in Appendix R, which the delivery tool
appends to the submitted copy of this document on the team's computer.

Training from the public data: the tree bundles with `python -m possession.train` and
`possession-v2-config.json` / `possession-v23-config.json` (see the long document); the network
weights with `experiments/possession_v2/v214/tcn_jax.py` (JAX on CPU; a re-run gives equivalent,
not bit-identical weights, so the release pins the files it was validated with). Experiment
scripts: `experiments/possession_v2/`.
