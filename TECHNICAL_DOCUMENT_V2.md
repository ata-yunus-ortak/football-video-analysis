# Possession v2 — technical document (full record; current release: v2.11)

Team repository: `possession/` package, branch `feature/external-possession-selection`.
Submission file regenerated with `python -m possession.run211` (see the two addenda and Reproduction).

> **Addendum, 11 November 2026 (v2.9).** The submitted entry point is now `python -m possession.run29`
> (release manifest `possession-v29-release.json`). It differs from the v2.5b system described below in
> two points; everything else in this document still applies. The short submission document is
> `TECHNICAL_DOCUMENT.md`.
>
> 1. **Second-half kick-off.** The organisers' FAQ states that the second half is graded from frame
>    110,808 but kicks off at 113,742 and that those 2,934 frames are all `D`. The second-half play block
>    now starts at the published kick-off; the frames before it are written `D`. This is a published
>    fixture constant like the graded windows; its effect cannot be measured on external matches.
> 2. **Registered broadcast ball** (`possession/register.py`, plan and results `possession-v29-*.json`).
>    Before the 0.50 m accuracy gate, the aligned broadcast ball is corrected by the calibration error
>    measured on players that both cameras see (mutually nearest same-team pairs within 3 m, weighted
>    towards the ball, trimmed at 1 m, median over +-0.5 s) and smoothed over +-2 frames. On 16
>    copies not used before, with a harder stream simulator (per-shot spatial warp and a ball-only
>    error): medium calibration error 0.653 -> 0.681 (gate open on 0 -> 16 of 16 copies; higher on
>    15), accurate broadcast 0.686 -> 0.684 (lower on 9 of 16 copies, -0.020 to +0.011 per copy,
>    within the registered -0.003 on average), bad broadcast unchanged (gate closed). All four
>    registered gates passed. Simulated streams only.
>
>    *Correction of 11 November (log entry K002).* The first evaluation reported here (0.647 -> 0.678
>    and 0.683 -> 0.681, "16 new copies") contained 8 copies that had already been used for the v2.6
>    candidate. A records audit by the team's coding assistant found this. The 8 copies were replaced
>    under an amendment registered before the new results (`possession-v29-amendment-plan.json`), the
>    unchanged gates were applied once and passed (`possession-v29-amendment-results.json`). The first
>    evaluation is kept unchanged in `possession-v29-results.json`.
>
> Also tested since and not selected: gap-bridging ball features (v2.7, +0.002) and adding a Metrica
> sample game to the training matches (v2.8, +0.001 on the held-out Metrica game, -0.011 to -0.014 on
> DFL copies).

> **Second addendum, 11 November 2026 (v2.11): goalkeeper team check.** The submitted entry point is
> now `python -m possession.run211` (release manifest `possession-v211-release.json`); it is v2.9 with
> one step added before the features. `possession.run29` is unchanged and is the next step of the
> technical fall-back ladder. Log entry K004 has the full record.
>
> 1. **Why.** DATA.md: "You get positions and team membership, nothing more". The team of a track is
>    decided by the tracker, and a goalkeeper wears another kit than his team-mates. Our corruption
>    model only moved a player to the other team for 1-6 s. A reporting-only diagnostic (Metrica games
>    1-3, one corrupted copy each, frozen v2.9 logic; `experiments/possession_v2/stress_roles.py`)
>    measured what would happen if goalkeeper tracks carried the other team's id: one goalkeeper for
>    the whole match -0.023 spellF1, both -0.317 (0.684 -> 0.367), both for 30% of the time -0.014; a
>    match official tracked under a team id -0.004 at worst. (Numbers of the re-run against the
>    file-order labels, log entry K005; the first run, quoted in `possession-v210-plan.json`, gave
>    -0.021, -0.301, -0.011 and -0.003.) The collapse with both goalkeepers comes from
>    `features.attack_dirs`, which takes the attacking direction from the mean x of each team: two
>    goalkeepers under the wrong id invert it.
> 2. **First version, v2.10 (`possession/keeper.py`), not released.** Rule: while play is in the other
>    half the goalkeeper is the tracked player nearest to his goal; such track pieces, and pieces that
>    continue them, are moved to the defending team when they sit in a slot of the other team. Registered
>    plan `possession-v210-plan.json`, 8 new validation copies, four gates, all passed
>    (`possession-v210-results.json`): ids as corrupted 0.6655 -> 0.6655, one goalkeeper wrong 0.6270 ->
>    0.6644, both wrong 0.3271 -> 0.6634, wrong 30% of the time 0.6444 -> 0.6644. A reporting analysis of
>    the 80 pieces it had moved with correct ids then found three outfield players among them: a forward
>    who stood still 13 m from the opponents' goal for the last 2.5 minutes of a match (in both copies of
>    that match), and a forward 26 m from goal for 15 s while the goalkeeper's track was lost. The score
>    was unchanged, but the cause mattered: "nearest tracked player" is no proof of a goalkeeper when the
>    goalkeeper is not tracked, and a camera that follows play may not show the far goalkeeper at all. On
>    training matches seen through a simulated camera window (players further than 42 m / 35 m from the
>    centre of play not tracked) v2.10 moved 1,700-8,400 outfield positions per match to the wrong team.
>    The v2.10 plan had not covered that situation, so v2.10 was not released.
> 3. **Second version, v2.11 (`possession/keeper2.py`).** (i) A frame counts as evidence only if the
>    piece is at least 8 m nearer to the goal than the second-nearest tracked player (true for a
>    goalkeeper in 96-99% of such frames on the training matches). (ii) A piece under the other team's id
>    is no longer moved on its own evidence: either that goal's evidence in that half is mostly under
>    the other id (at least 2,500 frames and at least half of it: mislabelled for the whole half), or
>    the piece continues a goalkeeper piece in time and place (mislabelled for a while). Developed on
>    the four training matches without running a model; with correct ids the evidence under the other
>    id never exceeded 320 frames per goal and half in any camera window.
> 4. **Validation** (`possession-v211-plan.json`, registered before any result of the candidate on a
>    validation or reserved match; `possession-v211-results.json`). 8 new corrupted copies of the four
>    validation matches, tracks packed into 46 anonymous slots, the validation models. Six gates, applied
>    once, all passed:
>
>    | condition | without (v2.9) | with (v2.11) | gate |
>    |---|---|---|---|
>    | team ids as corrupted, whole pitch in view | 0.6594 | 0.6596 | G1: mean difference >= -0.002, no copy below -0.005 |
>    | both goalkeepers under the other id | 0.3354 | 0.6565 | G2: within 0.015 of the first row |
>    | one goalkeeper under the other id | 0.6274 | 0.6576 | G3: within 0.010 of the first row and at least +0.008 |
>    | both goalkeepers wrong 30% of the time | 0.6417 | 0.6591 | G4: within 0.010 of the first row and not below v2.9 |
>    | camera window 42 m, ids as corrupted | 0.6492 | 0.6492 | G5: as G1 |
>    | camera window 35 m, ids as corrupted | 0.6464 | 0.6464 | G6: as G1 |
>    | camera window 42 m, both goalkeepers wrong (reported) | 0.5570 | 0.6344 | none |
>
>    Reported alongside: v2.10 in the two window rows scored 0.6487 and 0.6452
>    (mean difference to v2.9 -0.0004 and -0.0013, worst copy -0.0044); goalkeeper
>    positions under a wrong id went from 100% to 2.6% (both wrong), 50% to 1.5% (one), 32% to
>    2.1% (30% of the time) and from 100% to 27% with the 42 m window.
> 5. **Records correction found during this work (K005).** The full-size rehearsal of K003, its
>    slot / duplicate diagnostic and the goalkeeper diagnostic above had been scored in the Python 3.10
>    environment, where `metrica_labels.py` sorted simultaneous events in another order than the
>    provider's files and lost about half of the dead-ball intervals of the Metrica proxy labels.
>    Every selection, gate, validation and reserved test ran in the experiment environment
>    (Python 3.13), where the labels are in file order; the possession counts stored in
>    `possession-v2-results.json` match those labels only. The script now sorts stably and gives the
>    same labels in both environments; the three records were recomputed
>    (`possession-label-order-correction.json`): rehearsal bundle A 0.763 (first reported 0.715),
>    bundle B 0.732 (0.686); slot / duplicate diagnostic at most 0.006 on a copy and 0.002
>    on average (0.007 and 0.002).
> 6. **Limits.** The errors and the camera window are simulated by us. When the far goalkeeper is mostly
>    out of view nothing is corrected. The validation matches were not fresh for this design (the v2.10
>    analysis on them prompted it). The check was validated with the tactical camera only; the broadcast
>    path uses the ids as given. Whether the provided tracking has any of this was not looked at;
>    `run.json` on the team's computer records what was moved (aggregates only).

## 1. Summary

Per-frame H/A/D labels are produced from the provided **tactical automatic tracking (ATD)**,
with the broadcast tracking as a gated second ball source. The core (`possession-v2.1`): two gradient-boosted tree models estimate P(ball dead) and
P(home in possession | ball alive) from measured ball/player geometry and kinematics, a second
stage re-estimates both from how these probabilities evolve over the surrounding seconds, and a
three-state Viterbi decoder turns the frame probabilities into possessions and stoppages.
Version `possession-v2.4` first **measures the frame-to-frame position noise of the tracking**
(Section 6). If it is within what the core models were trained with (at most
0.30 m for players and ball), the frozen v2.1 system runs unchanged. If it is larger, the same
pipeline runs on positions smoothed over +-2 frames with models trained on noisier data (the
"v2.3 path"). The submitted version, `possession-v2.5`, also reads the **broadcast tracking**:
it aligns the broadcast frames to the tactical timeline (anchored on the match clock that
both videos show, read automatically by OCR) and fills tactical frames
whose ball is missing with the broadcast ball, but only when the two cameras agree closely where both
see the ball. Every model, feature, threshold and decoder choice was made on **external
matches** (Sportec/DFL open data; Metrica sample games). The provided match was used only for
the final automatic run. Before any training or validation, external tracking was corrupted to
resemble automatic, uncorrected tracking (Section 4).

On corrupted external validation copies v2.1 reaches spellF1 0.631 (organisers' baseline logic
on the same copies: 0.196), and 0.664 on a reserved external match evaluated once after
freezing (baseline logic: 0.219). On 24 fresh copies v2.4 scores 0.642 against 0.603 for v2.1:
identical where the noise is within the v2.1 training range, +0.045 with larger ball error and
+0.072 with larger player error; on the reserved match 0.665 against 0.637. With simulated
broadcast streams the fill adds +0.024 and +0.037 (two independent sets of 16 copies) when the
broadcast tracking is accurate and changes nothing when it is not, because the gate closes
(Section 8). These are agreement scores with other providers'
labels on other matches, not competition scores.

## 2. Disclosure of the earlier development process (organiser condition)

The organisers asked this team (reply of 3 November 2026) to keep only general ideas, delete
every hand annotation of the provided game and anything derived from it, re-select every
parameter, threshold and model version on other fixtures, freeze the pipeline, regenerate the
file automatically and disclose the history here. This section is that disclosure.

**What happened.** Until the 22-23 October clarification the team worked from a local copy of
`RULES.md` dated 20 October 2026 (SHA-256 `49eb57f807519f47757162555b19c30cb68bc265606d8289943521842f526ed4`, recorded in
`rules-provenance.json`) whose wording allowed small amounts of hand-labelled training or
validation data. During that period the team (i) compared candidate systems on the public
five-minute window and selected versions from those results, (ii) used manually identified
contact times and ball points from the provided game in diagnostic validation, and (iii) from
about 20 October shared selected frame extracts/screenshots of the provided game and the manual
notes with a hosted LLM coding assistant (OpenAI/Codex). The team disclosed this to the
organisers on 31 October and sent the requested hosted-LLM notice on 3 November.

**Affected stages.** Parameter and version selection of the pre-November pipelines, diagnostic
validation, and the earlier visual/throw-in/referee prototypes. None of those artefacts, numbers
or code paths is used by possession v2.

**What was done.** The affected local annotations and derived experiments (786 targets, ~26 GB)
were inventoried, moved out of active paths and deleted by the user (path absence verified on
3 and 7 November). The known provider-side conversation was deleted on 7 November through the
application's control; deletion of separately uploaded files and provider back-end purging could
not be verified (`REMEDIATION.md`). A fresh source repository without legacy labels, outputs or
presets was created. The first re-selected release (`clean_model/`, `model.json`) was chosen on
SkillCorner open data; possession v2 (this document) was developed from scratch on Sportec/DFL
and Metrica sample data with a pre-registered plan (`possession-v2-plan.json`). The public
five-minute window was not consulted for any v2 choice; it is used only after freezing, to check
that the pipeline runs and the file is well formed. Earlier public-window scores are not
presented anywhere as validation.

**AI assistance in v2.** v2 code was written with an AI coding assistant working only on
source code, external datasets and aggregate external results. No provided-match file, extract,
frame-level output or derived statistic was given to it; the frozen pipeline was run on the
provided data locally by the team.

## 3. Data

| asset | used? | how |
|---|---|---|
| tactical ATD (players + ball, team of each slot) | yes | main inference input (features, and the noise measurement of the v2.4 gate) |
| broadcast ATD + broadcast homography `valid` flags | yes (v2.5) | aligned to the tactical frames; fills missing tactical balls behind an accuracy gate (Section 6) |
| tactical and broadcast video | only the on-screen match clock (v2.5b) | automatic OCR of the clock every 5 s anchors the alignment; no other pixel is used |
| tactical homography | no | |
| Smart Tagging | tested, not selected | simulated-tag experiments did not meet the registered gates; see Section 9 |
| public 5-minute ground truth | final run check only | never consulted for any choice |
| Sportec/DFL open data (CC-BY 4.0; 6 of 7 matches, the 7th reserved and never downloaded) | yes | training/validation, both final bundles on all 6; per-frame BallStatus/BallPossession targets |
| Metrica sample games 1-3 | yes | validation (1-2) and reserved test (3), event-derived proxy targets |

**Labelled data used (none from the provided game).** DFL/Sportec: six Bundesliga matches,
about 140,000 labelled frames each at 25 fps; the per-frame ball status and possession flags
are part of the provider's corrected tracking (Sportec Solutions), not labelled by us. Metrica
sample games 1-3: tracking plus Metrica's own event data; we derived possession/stoppage proxy
labels from these events automatically and used them only for validation and the reserved test.
Nothing was labelled by hand by the team.

## 4. Making external tracking look automatic

External tracking (DFL optical tracking) is clean: the ball is present on every frame and
players are never lost. The provided ATD is automatic: the ball is missing on 41% of graded
frames, tracks fragment and swap, and positions are noisier (DATA.md). A model trained on clean
data would rely on cues that do not exist in the ATD. `possession/degrade.py` therefore corrupts
every training and validation copy with parameters drawn independently per copy from broad
ranges (domain randomisation), anchored only on the organisers' published aggregate statistics:

- ball missingness as a temporally correlated process (0.3-2 s correlation), with a live-play
  marginal of 12-40%, higher probability when 2+ players are within 1.5 m of the ball, when the
  ball is fast, and when it is more than 1 m outside the pitch; an extra, randomly sized
  dead-ball term (0-55%) because the coupling between stoppages and missing ball in the ATD is
  unknown;
- ball position noise (5-30 cm) and short false ball detections (bursts at random locations or
  at a player's feet);
- player track gaps (2-12%, 0.5-4 s correlation), extra occlusion gaps for players within 0.8 m
  of another player, position noise, and short wrong-team tracklets.

No parameter of this simulator was fitted to the provided match. Validation copies use fixed
seeds, so every candidate is compared on identical corrupted inputs. Two artefacts that DATA.md
mentions are not simulated in training: slot identity swaps and duplicated players. Their effect,
together with longer false ball detections, is measured separately as a stress test (Section 8).

## 5. Features

All features are computed inside each half (no leakage across halftime) from positions only;
speeds are recomputed from positions (the ATD speed channel is not used), so external and
provided data are processed identically. About 230 features per frame:

- **ball state:** visibility now and as fractions over past/future windows (0.5-15 s), time
  since/until the ball was last/next seen, last-seen and next-seen position relative to the
  touchlines, goal lines, corners, centre spot, penalty and goal areas, signed distance outside
  the pitch, ball speed, stillness and time since/until the ball last/next moved fast;
- **ball impulses:** peaks of the change of smoothed ball velocity (kicks/touches), counts and
  times since/until, attributed to the team whose nearest player was within 2 m;
- **players:** mean speed of all tracked players and fractions above 2/4 m/s or standing, over
  past/future windows and their differences (stoppages and restarts change the whole field's
  tempo), numbers of tracked players, penalty-area occupancy, players within 9.15 m of the ball,
  kick-off formation (share of players in their own half);
- **per team (home view and away view, plus their difference):** distance of the team's nearest
  player to the ball and its minimum over short windows, players within 1.5/3/5 m, relative
  speed between ball and nearest player, a control indicator (within 1.2 m and moving with the
  ball), share of frames the team was nearest over past/future windows (1-10 s), time since/
  until the team last/next controlled or touched the ball, team centroid and spread in the
  team's own attacking direction (inferred per half from mean team position), forward velocity
  of the team and of the ball.

## 6. Models and decoder

- **Two frame models.** `P(dead)` and `P(home | alive)`, scikit-learn
  `HistGradientBoostingClassifier` (fixed iterations, no early stopping, seeded), trained on
  every 6th frame of several independently corrupted copies of each external training match.
- **Team symmetry.** Each copy is also presented with home and away exchanged (labels
  exchanged too). At inference both views are evaluated and averaged
  (`p_home = (f(x) + 1 - f(swap(x))) / 2`), so the output cannot prefer a side.
- **Numpy inference.** The fitted trees are exported to plain arrays (`possession/trees.py`,
  bundle `models/possession-v2.npz`, no pickle) and evaluated with numpy; results are identical
  to scikit-learn's and independent of its installed version. Probabilities are rounded to
  1e-6 before decoding to remove platform-level floating noise.
- **Second stage (temporal stacking).** A second pair of models with the same two targets
  reads 48 summaries of the stage-1 probabilities around the frame: means over 0.2-10 s before
  and after it, the difference between the two (a sustained change versus a brief dip), and the
  minimum/maximum over +-1 and +-3 s (`possession/stack.py`). Stage 2 is trained on
  *out-of-fold* stage-1 probabilities: every training match is predicted by stage-1 models that
  never saw it (leave-one-match-out), so stage 2 learns from probabilities as uncertain as on a
  new match. It is team-symmetrised in the same way and also evaluated with numpy.
- **Decoder.** A three-state (H, A, D) Viterbi over each half maximises the summed frame
  log-probabilities minus a cost for every team switch, every alive->dead transition and every
  dead->alive transition, plus a dead-ball bias. The four numbers are chosen on the external
  validation copies by the official `spell_f1_mean`; selected: switch 3, alive->dead 60,
  dead->alive 60, dead bias -0.3 (log-probability units).
- **Noise gate (v2.4, `possession/noise.py`).** Inside the graded halves, for every player slot
  and for the ball, the second difference `d2 = x[t+1] - 2 x[t] + x[t-1]` is taken wherever three
  consecutive positions exist, and `sigma = 1.4826 * MAD(d2) / sqrt(6)` estimates the standard
  deviation of independent per-frame position noise (real motion adds well under 1 cm at 25 fps;
  kicks and short false detections are rare outliers that the median ignores). Players: median
  over slots with at least 500 values. On external matches with 0.1/0.3/0.5 m of added noise the
  estimate returns 0.10/0.30/0.50 m; clean DFL and Metrica tracking measures 0.006 and 0.001 m.
  If the player or the ball estimate exceeds **0.30 m** (the largest noise in the v2.1 training
  corruption, fixed before any v2.4 result) the v2.3 path runs; otherwise v2.1 runs and its file
  is byte-identical to `python -m possession.run`. The gate reads no label, video or ground
  truth; `run.json` records the measured noise and the path.
- **Broadcast ball fill (v2.5, `possession/fusion.py`, alignment from `possession/broadcast.py`).**
  The broadcast ATD is mapped to tactical frames per half starting from the lag given by the match
  clock (below) and refined in 60 s windows by matching the visible broadcast players to the
  tactical players of the same team; a broadcast frame is accepted only if at least 3 players lie within
  2 m (median), which rejects replays and close-ups. The fill is used only if, where both cameras have a
  ball, the median distance is at most **0.50 m** over at least 120 s, with at least 5% of the broadcast
  frames accepted (thresholds registered before any result; the distance includes the tactical error, so
  it bounds the broadcast error). Then only tactical frames without a ball are filled, never replacing a
  tactical ball, with a speed plausibility check against nearby tactical balls. The noise gate is
  measured on the raw tactical tracking before the fill.
- **Clock anchor (v2.5b, `possession/clocksync.py`, OCR `tools/possession_clock.py`).** Both videos
  show the match clock. An OCR pass (RapidOCR, one key frame every 5 s, top-left 45% x 22% of the
  picture, confidence 0.8; parameters registered before the provided videos were first read) gives
  (video time, clock) pairs; consistent runs of each video are paired by clock value, ambiguous values
  (first-half added time vs. second half) are skipped, and the median lag per half (>= 10 anchors,
  IQR <= 1.5 s) replaces the trajectory search; orientation and refinement then run around it (+-40
  frames). Without clock files the tracking-only alignment is used.
- **v2.3 path** (`possession/smooth.py`, `models/possession-v23.npz`). Ball and player positions
  are smoothed with a NaN-aware centred moving average over +-2 frames inside each half (a
  missing frame stays missing; no gaps are filled), then the same features, stage 1, stage 2 and
  decoder run with models trained on the same six DFL matches, corrupted with ball noise
  0.05-0.6 m plus a slowly varying ball bias of 0-0.6 m and player noise 0.03-0.6 m, and smoothed
  the same way. Decoder: switch 5, alive->dead 60, dead->alive 60, dead bias -0.3.

## 7. Possession rules implemented

- **Ball in play vs dead.** A stoppage is predicted from the measured situation, not from a
  missing ball alone: last-seen ball beyond or on a line, the ball becoming still at a restart
  location (touchline, corner, goal area, centre), kick-off formation, the whole field slowing
  down, and their reversal at the restart. Tracking gaps without these cues are not stoppages.
- **Loose balls keep the last team.** The decoder's team state persists through missing ball
  observations, passes and loose phases; only sustained evidence of the other team controlling
  the ball changes it (switch cost).
- **Touches without control** (deflections, blocks, contested aerial balls) are not enough to
  pay the switch cost unless followed by control; this follows the organisers' definition.
- **Restarts.** After a stoppage the decoder may enter either team; the team is decided by who
  plays the ball at the restart (nearest/controlling player and team context).
- **Every graded frame gets H, A or D.** No `X` is written inside the graded halves: on the
  ranking metric an abstention equals repeating the previous label, and on macroF1 it is a miss.
- Frames outside the play blocks are written as `D`: the ungraded frames before, between and after
  the halves, and (since v2.5c) the graded frames 110,808-113,741 before the second-half kick-off,
  which the organisers' FAQ states are all `D`.

## 8. Selection protocol and external results

The plan (`possession-v2-plan.json`) was registered before any validation result was seen.
Training: DFL J03WOH, J03WOY, J03WPY, J03WQQ (3 corrupted copies each, both team orientations).
Validation: DFL J03WN1, J03WR9 and Metrica sample games 1-2 (event-derived proxy labels), each
in 2 fixed corrupted copies (seeds 101, 102); score = mean official `spell_f1_mean` over the 8
copies, `macro_f1` as tie-break. All comparators run on the identical corrupted copies.
Amendments recorded in the plan before their results existed added two candidates (temporal
stacking; feature set v3). Each candidate's decoder costs were chosen on the same copies from
the same grid (switch 2-8, out/in cost 30-120, dead bias -0.3/0/0.3).

Candidates (best decoder of each; validation models trained on the four training matches):

| candidate | decoder (switch, out, in, dead bias) | spellF1 all | DFL | Metrica | macroF1 |
|---|---|---|---|---|---|
| stage-1 GBDT, feature set v2 | 5, 120, 120, -0.3 | 0.6218 | 0.6359 | 0.6078 | 0.8577 |
| stage-1 v2 + stage-2 temporal stacking **(selected)** | 3, 60, 60, -0.3 | 0.6312 | 0.6466 | 0.6158 | 0.8607 |
| stage-1 GBDT, feature set v3 (1 s tempo speeds) | 5, 120, 120, 0.3 | 0.6199 | 0.6321 | 0.6078 | 0.8565 |
| stage-1 v3 + stage-2 temporal stacking | 6, 60, 60, -0.3 | 0.6302 | 0.6439 | 0.6166 | 0.8604 |

Selected system against the comparators:

| system (same corrupted validation copies) | spellF1 all | spellF1 DFL | spellF1 Metrica | macroF1 | predicted spells | true spells |
|---|---|---|---|---|---|---|
| organiser baseline_smooth50 logic | 0.196 | 0.172 | 0.220 | 0.556 | 744 | 403 |
| team S001 sequence model | 0.196 | 0.145 | 0.247 | 0.400 | 152 | 403 |
| selected system, frame argmax (no decoder) | 0.440 | 0.453 | 0.426 | 0.858 | 647 | 403 |
| **selected system** | 0.631 | 0.647 | 0.616 | 0.861 | 304 | 403 |

The submitted bundle repeats the selected recipe on all six DFL matches (training + validation),
as the plan allowed; its validation-copy scores are therefore not reported. It was then frozen
and evaluated once on the reserved test (not used for any choice):

Metrica sample game 3, two fixed corrupted copies (seeds 201, 202):

| system | spellF1 | macroF1 |
|---|---|---|
| organiser baseline_smooth50 logic | 0.219 | 0.661 |
| team S001 | 0.265 | 0.421 |
| **v2.1 (frozen bundle)** | 0.664 | 0.836 |

The two copies gave 0.625 and 0.702: the corruption level alone moves the score by several
points, which is also why differences of 0.001-0.002 between candidates are not meaningful.

Stress tests (reporting only; validation matches; models trained on the four training matches):

| condition | selected system spellF1 | organiser baseline logic |
|---|---|---|
| mild corruption (ball missing 12% in play, low noise) | 0.700 | 0.296 |
| harsh (ball missing 40% in play, high noise, false balls) | 0.584 | 0.170 |
| harsh + ball missing much more often in stoppages | 0.621 | 0.188 |
| standard corruption (one copy per match) | 0.610 | - |
| + slot identity swaps | 0.610 | - |
| + duplicated players | 0.610 | - |
| + 1-5 s false ball detections | 0.585 | - |
| + all three | 0.594 | - |

Per match the artefact test added about 140 duplicated tracklets (1-10 s) and about 85 false ball
tracks of 1-5 s; only 0-2 identity swaps occurred, because a swap was only simulated between
team-mates within 2 m (the features are identity-free summaries, so swaps mainly affect speeds,
which are capped at 11 m/s). Long false ball detections are the only artefact with a visible
cost (-0.025).

These are agreement scores with other providers' labels on corrupted copies of other matches,
not competition scores. The organisers' published full-match baseline (spellF1 0.2433) is
higher than the same baseline on our corrupted external copies (about 0.20), which suggests the
simulation is at least as hard as the real data for that baseline; it does not guarantee how
v2 transfers.

**Later candidates (v2.2-v2.6).** A reporting-only check showed that v2.1 depends on sub-0.3 m
positions (Section 9); later diagnostics showed that missing ball positions and team decisions
cause most of the remaining error. Each candidate had a plan registered before its results
(`possession-v22/23/24/25/25b/26-plan.json`) and was judged on copies of the same four validation
matches (fresh corruption seeds where stated), with position error beyond the v2.1 training range
or with simulated broadcast streams:

| candidate | registered rule | result | selected |
|---|---|---|---|
| v2.2: ball noise up to 0.6 m + slowly varying ball bias in training | +0.010 over 16 copies | +0.005 | no |
| v2.3: positions smoothed over +-2 frames; ball and player noise up to 0.6 m in training | +0.010 over 24 copies and at most -0.010 on the original copies | +0.014, but -0.014 on the original copies | no |
| v2.4: noise gate choosing v2.1 or the v2.3 path (designed after the v2.3 result) | +0.010 over 24 FRESH copies and at most -0.005 on the original-type copies | +0.039, identical on the original-type copies | **yes** |
| v2.5: broadcast ball fill behind the accuracy gate | good broadcast >= +0.010, medium >= -0.005, bad >= -0.002 (16 fresh copies each) | +0.024 / +0.004 / 0.000 | **yes** |
| v2.5b: clock-anchored alignment (designed after one v2.5 alignment failure) | v2.5 rules on 16 NEW copies, not below v2.5, no more alignment failures | good +0.037 (v2.5 +0.037), alignment failures 0 vs 0 | **yes** |
| v2.6: learned switch hazard -> frame-dependent switch cost | +0.010 on 8 fresh copies and not worse on >= 5 of 8 | +0.002, not worse on 4 of 8 | no |

v2.4 on 24 fresh copies (new corruption seed for every copy; validation models trained on the
four training matches; decoders fixed beforehand):

| copies (8 each) | v2.1 | v2.4 | path chosen by the gate |
|---|---|---|---|
| v2.1 corruption (ball and player noise up to 0.3 m) | 0.654 | 0.654 | v2.1 on 8 of 8 |
| + ball noise 0.3-0.6 m and slowly varying ball bias 0.2-0.6 m | 0.583 | 0.628 | v2.3 on 8 of 8 |
| + player noise 0.3-0.6 m | 0.572 | 0.644 | v2.3 on 8 of 8 |
| all 24 | 0.603 | 0.642 | |

Using the v2.3 path on every copy would have given 0.638 overall and 0.642 on the first group
(v2.1: 0.654): the gate keeps v2.1 where it is better. The v2.3 bundle was then retrained on all
six DFL matches with the registered recipe and the release frozen (`possession-v24-results.json`).
Reserved test, once after freezing (Metrica sample game 3; frozen bundles; reported, not a gate):

| copies of the reserved match (2 each) | gate | v2.1 | v2.4 |
|---|---|---|---|
| v2.1 corruption (seeds 201, 202) | v2.1, v2.1 | 0.664 | 0.664 |
| + ball noise 0.3-0.6 m and ball bias 0.2-0.6 m (401, 402) | v2.3, v2.3 | 0.645 | 0.660 |
| + player noise 0.3-0.6 m (601, 602) | v2.3, v2.3 | 0.602 | 0.670 |
| all 6 | | 0.637 | 0.665 |

The v2.1 bundle reproduced its earlier reserved-test values exactly (0.6253 and 0.7021).

**Broadcast fill (v2.5).** External matches have no second camera, so broadcast streams were
simulated from the clean external match: cuts, replays (old content), close-ups, slow drift, a
camera window around the ball, per-shot calibration bias and position noise, in three accuracy
regimes. 16 fresh tactical copies (v2.1 corruption and extended player error), each with its own
stream per regime:

| simulated broadcast | v2.4 | v2.5 | gate open |
|---|---|---|---|
| good (bias <= 0.2 m, noise 0.05-0.25 m) | 0.651 | 0.675 | 15 of 16 |
| medium (bias 0.2-0.6 m, noise 0.25-0.5 m) | 0.651 | 0.655 | 1 of 16 |
| bad (bias 0.6-1.5 m, noise 0.5-1.0 m) | 0.651 | 0.651 | 0 of 16 |

With good streams the graded frames with a ball rose from 53% to 63% on average. One good copy failed
to align (the whole-match trajectory search locked onto a wrong axis flip and lag), which lost the gain
but did no harm; v2.5b anchors the lag on the match clock to prevent this. On 16 new
copies with simulated clock readings (50-95% readable, 1-3% misread, added-time clocks repeated) the
good-regime means were v2.4 0.635, v2.5 0.672, v2.5b 0.672 with 0 and 0 alignment failures
(`possession-v25b-results.json`). On these copies both alignments worked, so the benefit of the clock
(avoiding failures like the one above) was not observed again; v2.5b was selected because its
registered rule required it to be no worse than v2.5 and to have no more alignment failures.

**Where the remaining error is (reporting only, validation matches).** On clean (uncorrupted)
tracking v2.1 scores 0.748; with the automatic-tracking corruption 0.610; with the same corruption but
no missing ball 0.700, so about two thirds of the loss comes from missing ball positions. Replacing
P(dead) by the provider labels raises 0.631 to only 0.647, replacing P(home | alive) raises it to
0.912: team decisions during play, not stoppages, limit the score. A learned switch hazard (v2.6)
did not help enough; better ball information (the broadcast fill) did.

## 9. Limitations

- **Domain gap.** The models never saw the provided ATD. The corruption simulator covers broad
  ranges, but the true missing-ball pattern of the ATD (especially its coupling with stoppages)
  is unknown; if it lies outside the simulated ranges, dead-ball and team decisions degrade.
- **Label semantics.** DFL `BallPossession` changes on short touches more often than the
  organisers' "controlled possession" definition; Metrica event-derived proxies are closer to it
  but have approximate stoppage boundaries. The decoder costs were selected on both.
- **External scores are not competition scores.** They are agreement with other providers'
  labels on corrupted copies of other matches, on fixtures the team had accessed before.
- **Not used by the submitted system:** Smart Tagging, the tactical homography and every video
  pixel except the clock readings. No external data with comparable automatic tags exists, so any
  weighting of the tags had to be validated on simulated tags (next bullets) rather than tuned on the
  provided game.
- **The broadcast fill was validated on simulated streams only.** Whether the real broadcast tracking
  is accurate enough is decided at run time by the gate (median tactical-broadcast ball distance <=
  0.50 m); we have not seen that value. Real artefacts outside the simulator (zoom-dependent errors,
  replays flagged valid, partial views that confuse the team mapping) may make the gate open on a
  mapping that is wrong; the player-position acceptance check is the protection.
- **Fouls and stoppages with the ball on the pitch** (fouls, injuries, VAR) are the hardest
  dead-ball cases from tracking alone.
- **Team changes are the weakest part.** On the eight validation copies 94% of the true
  stoppages are found (start within 1 s for 74%, end for 81%), but only about half of the true
  team changes are placed within one second (recall 51%, precision 70%); the system predicts
  about a third fewer team changes than there are, merging quick exchanges and contested balls
  into one possession (`diagnostics` in `possession-v2-results.json`).
- **Simulator gaps.** Slot identity swaps and duplicated players are not simulated in training
  (Section 8 measures their effect).
- **Sensitivity to position error (largest known risk), and what the gate does not cover.**
  v2.1 was trained with ball and player noise of at most 0.3 m. On the four validation matches
  (one copy each) extra i.i.d. ball noise of 0.5 m lowers its spellF1 from 0.610 to 0.537 (1 m:
  0.492), a slowly varying 1 m ball bias to 0.519, and extra i.i.d. player noise of 0.5 m to
  0.495, while a ground-projection error of fast (aerial) balls has no effect (0.611). The
  position error of the provided tracking is unknown. The v2.4 gate switches to the noise-robust
  v2.3 path only when it measures frame-to-frame jitter above 0.30 m. It cannot see slowly
  varying bias or tracker error that has already been smoothed (both leave second differences
  almost unchanged); such input selects v2.1, which is sensitive to them. In validation the
  noise of every copy was either at most 0.29 m or at least 0.34 m, so the gate always chose as
  intended; its behaviour close to 0.30 m, where both paths should be similar, was not measured.
  On the provided match the gate makes one binary choice, which we have not seen.

- **Smart Tagging was tested and not selected** (`possession-v3-plan.json`,
  `possession-v3-results.json`, code in `possession/smarttags.py`). External matches have no
  Metrica tags, so tags were generated from their labels with counts matched to the per-code
  counts published in DATA.md and randomised timing, team and false-tag errors. A second stage
  with tag features plus a run-time consistency gate (tag team vs. tracking-only stage 1; groups
  below 60% agreement dropped) gained +0.011 spellF1 with typical simulated tags and +0.026 with
  accurate ones, but lost 0.008 without tags and 0.006 with noisy tags, failing two registered
  gates. A variant designed afterwards (fallback to v2.1 without usable tags, agreement-weighted
  blend otherwise) was safe on fresh copies (worst -0.004) but gained only +0.002 with typical
  tags (+0.019 with accurate ones) and also missed the +0.010 gate. The provided Smart Tagging
  file was never read; its real error profile, which decides the value, is unknown to us.

- **The first broadcast attempt (v4) was not selected** (`possession-v4-plan.json`,
  `possession-v4-results.json`, `possession/broadcast.py`). An automatic alignment (per-half lag
  from masked cross-correlation of the two ball tracks, refined in 60 s windows by matching the
  visible broadcast players to the tactical ones; replays and close-ups rejected) recovered the
  mapping of synthetic broadcast streams built from external matches (98% of accepted frames
  correct, median lag error 0 frames) and raised ball visibility markedly, but filling tactical
  gaps with a second ball carrying 0.5-1.5 m calibration error lowered spellF1 (0.6312 -> 0.6251;
  -0.037 on DFL copies, +0.025 on Metrica copies): possession attribution is very sensitive to
  ball-player distances. v2.5 therefore adds the accuracy gate.

**With more time** we would (i) validate Smart Tagging restarts as evidence on external
fixtures with comparable automatic tags, (ii) recover ball positions in ATD gaps from the
tactical video with a detector selected on other matches, (iii) learn the missing-ball /
stoppage coupling and the position-error profile from external automatic tracking instead of
randomising them, (iv) replace the two-path gate by models that take the measured noise level
as an input, and (v) add a duration-aware decoder for short possessions.

## 10. Reproduction

Inference (what produced the submitted file; Python 3.10-3.12 with the pinned numpy 1.26.4,
scipy 1.11.4 and pandas 2.1.4; scikit-learn is not needed). On external data, features were
bit-identical under Python 3.10/numpy 1.26 and Python 3.13/numpy 2.5 on the same CPU. Tree
evaluation is plain numpy and probabilities are rounded to 1e-6 before decoding, so the file
should be reproduced exactly; a last-bit difference of a transcendental function between CPU
instruction sets could in principle move a decoder tie, which we consider very unlikely but
cannot rule out without the organisers' machine.

```
# optional clock readings (separate OCR environment, requirements-sync-lock.txt):
python -m tools.possession_clock --video <bundle>/tactical/BAR-ATH_tactical.mp4 --out <clock>/tactical
python -m tools.possession_clock --video <bundle>/broadcast/BAR-ATH_broadcast.mp4 --out <clock>/broadcast
python -m pip install -r requirements-possession.txt
python -m possession.run211 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast
python -m possession.validate <new folder>/submission.csv
# or everything in one command (environment, hash check, tests, clocks, generation, checks):
python -m tools.possession_deliver --data-dir <bundle root> --private <output folder> --team <team name>
```

`run.json` states which path the noise gate took and whether the broadcast fill was used. Without
broadcast files, or when the accuracy gate is closed, the release (`possession.run211`) writes the
file that `python -m possession.run25c` writes from the tactical camera alone. For the v2.5b system described in this document
(`possession.run25`, second-half play from frame 110,808): without broadcast files or with the gate
closed it writes the same file as `python -m possession.run24`, and when the noise gate also chose
`v2.1`, as `python -m possession.run`.

Checks of the frozen v2.5 release: under Python 3.10/numpy 1.26.4 and Python 3.13/numpy 2.5.3,
`possession.run25` wrote byte-identical files for a full-size external pair (Metrica sample game 3
tracking corrupted like the training copies, 143,761 frames, plus a 146,043-frame synthetic broadcast
EPTS stream and simulated clock readings), with the clock anchor and with the tracking-only alignment
(both gave the same file; 3-4 minutes and up to 4.4 GB per run on two CPU cores with 239 track slots).
For v2.4, under the same two interpreters,
`possession.run24` wrote identical files for a synthetic ATD (v2.1 path) and the same ATD with 0.5 m
player noise (v2.3 path), and for a full-size external EPTS file (Metrica sample game 3 tracking;
measured noise below 1 mm, so the v2.1 path; the file equals the one `possession.run` writes);
the v2.3 path on that tracking with 0.5 m of added player noise also gave identical labels
(about 60 s and at most 1.3 GB per run on two CPU cores). The v2.1 bundle alone gave the same output
file (identical SHA-256) under Python 3.10/numpy 1.26.4 and Python 3.13/numpy 2.5.3 for a
synthetic ATD and for a full-size external EPTS file (Metrica sample game 3 tracking, 143,761
frames, 35 slots, 11 data format specifications; 45 s, 1.2 GB peak memory on two CPU cores).

`possession.run211` (like `possession.run29` and `possession.run25`) reads `tactical/BAR-ATH_tactical_atd.xml` and `_atd.txt`,
`broadcast/BAR-ATH_broadcast_atd.xml`, `_atd.txt` and `_homography.csv` (only the `valid` column) and, if
given, the two clock-observation files. It checks every source file and both bundles against the release
manifest `possession-v29-release.json` (`possession-v25-release.json` for `run25`) and the bundle cards, and
writes `submission.csv` plus `run.json` (input, model, source and output hashes, measured noise and path,
alignment mode, gate values, filled frames, team names, aggregate label counts). The graded halves
are taken from the organisers' `games.half_video_blocks("BAR-ATH")`; in the release the second-half play
block starts at the kick-off frame published in the FAQ (113,742). Outside the play blocks `D` is written.
The reader follows the FIFA/EPTS `DataFormatSpecification` of the metadata (which player each
raw `;` group belongs to, per frame range) and falls back to the `Player` list order only when no
specification is present; slots whose team id is neither team are dropped. Home is the first
`Team` (EPTS convention, as in the organisers' baseline); because DATA.md states that home is
Barcelona, the run also checks the team names and would swap sides if a reordered export put
Barcelona second. `run.json` records which rule was applied.

Training (external data only; Python 3.13, `requirements-possession-train.txt`):

```
python -m tools.sportec_prepare ...   # pinned IDSSE files -> prepared NPZ (existing team tool)
python -m possession.train --config possession-v2-config.json --dfl-prepared <prepared dir> --out models/possession-v2.npz
python -m possession.train --config possession-v23-config.json --dfl-prepared <prepared dir> --out models/possession-v23.npz
```

Each configuration includes the second stage, so training fits six leave-one-match-out stage-1
models for the stage-2 inputs before the final models (45-70 minutes each on two CPU cores,
4-5.3 GB of memory). scikit-learn 1.9.1 was used; the bundle stores the exported trees, so inference does
not depend on it.

Selection evidence: `possession-v2-plan.json` (registered before validation results; later
amendments are listed inside it with their times; on 10 November the hand-typed clock times in
all plan files were found to be agent estimates 1-60 minutes later than the real write times and
were replaced by file-system times, originals kept under `timestamp_correction`; the order of
plans, amendments and results is unchanged), `possession-v2-config.json` (selected
configuration), `possession-v2-results.json` (all candidates, validation, reserved-test, stress
and diagnostic numbers, bundle hash); for the robustness work `possession-v22/v23/v24-plan.json`
and `-results.json`, and `possession-v23-config.json` (the v2.3 path of v2.4).

External data: Sportec/DFL open data (CC-BY 4.0; Bassek et al. 2025, Scientific Data,
doi:10.1038/s41597-025-04505-y) and Metrica Sports sample data (github.com/metrica-sports/
sample-data). Both model bundles are derived from the CC-BY data only.
