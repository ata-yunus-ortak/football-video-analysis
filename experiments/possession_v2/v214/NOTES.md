# v2.14 work notes (14 Nov 2026, evening) — scratch, to be turned into K012 in docs/DENEY_KAYDI_TR.md

All numbers below are DEVELOPMENT on copies already scored in the v2.13 validation (seeds 131xx / 631xx / 33103) or on
Metrica game 3 copies (seed 7772). None is a validation. Nothing touches the provided match.

## Diagnostics (TCN alone, teammate's tcn_dfl6.npz, Metrica game 3 copy seed 7772, our simulator with one component off)
ours 0.6863 | no_flips 0.6926 | no_dead_extra 0.6863 | low_noise 0.6840 | no_player_miss 0.7072 | no_fp 0.7328 |
short_gaps 0.7001 | clean_all 0.7279 | sim2 (his simulator) 0.7274 | clean (uncorrupted) 0.7418 | ours+box5 0.6748
-> false ball detections of our simulator are the main cause (his simulator: fewer, only on players, frozen position).
In-sample check: tcn_dfl6 on training match J03WOH with our corruption 0.8165 (memorisation; training matches useless for diagnosis).

## Fusion rules with the teammate's weights (explore.py; mean spellF1 difference to v2.11)
DFL 10 copies (8 tactical + 2 his-simulator; single-seed five-match weights):
  v2.13 rule (w 0.5, his decoder cost 6) +0.0007 (min -0.0295) | our decoder w0.2 +0.0135 (min -0.0081, 9/10) |
  w0.3 +0.0140 (min -0.0102) | w0.4 +0.0120 | w0.5 +0.0031 | his decoder w0.3 +0.0082 | TCN alone -0.0335
Metrica 12 copies (MET1 5, MET2 5, MET3 2; tcn_dfl6 three seeds):
  v2.13 rule +0.0191 (min -0.0100) | our decoder w0.2 +0.0139 (12/12, min +0.0053) | w0.3 +0.0158 (min -0.0046) |
  w0.4 +0.0161 | w0.5 +0.0102 | his decoder w0.3 +0.0204 (min -0.0021) | TCN alone -0.0207

## Re-training with JAX (tcn_jax.py; verified against his NumPy inference: max abs diff 7.9e-7)
n1_both_s0 = five matches without J03WN1, replicas of both simulators (6 + 6 per half), 6 epochs, seed 0
(loss 0.39 -> 0.26 -> 0.20 -> 0.17 -> 0.13 -> 0.12; ~2.5 s/step alone, 130 steps/epoch).
On the 5 old J03WN1 copies (4 ours + 1 his simulator), TCN alone: his weights 0.6243 0.5926 0.5767 0.6155 | 0.6366
                                                           new weights 0.6523 0.6463 0.5882 0.6613 | 0.6687  (v2.11: 0.6256 0.6000 0.6383 0.6757 | 0.6691)
Mean difference to v2.11 with new weights: TCN alone +0.0016 (his: -0.0326) | v2.13 rule +0.0173 | our decoder w0.3 +0.0168
(min -0.0032) | w0.4 +0.0231 (min -0.0073) | w0.5 +0.0247 (min -0.0131) | geometric 0.3 +0.0229 (min -0.0032) | geometric 0.5 +0.0269 (min -0.0050)

## Plan
dfl4_both_s{0,1,2} (J03WOH J03WOY J03WPY J03WQQ; for the DFL validation rows, same matches as the v2 validation models),
dfl6_both_s{0,1,2} (six matches; Metrica rows and the release). Then: choose pool/weight on the OLD copies, register
possession-v214-plan.json (same six gates as v2.12/v2.13 + his-simulator gate), run exp_v214.py on NEW copies (seeds 141xx).
v2.3 path: not fused (v2.11 output), fixed before validation.

## State at 20:50 (14 Nov)
Files: fuse2.py (pool; POOL/WEIGHT still placeholders -> fix before smoke/registration), exp_v214.py (validation; imports
exp_v213 for copies; uses fuse2.pool + decode_blocks; v2.3 path not pooled), assemble_v214.py (G1-G6 unchanged + G7 his
simulator >= 0), register_v214.py (needs development_summary.json from dev_summary.py [not written yet], exp_v214_smoke.json),
pff_v214.py (after decision), retcn2.py + explore2.py (dev: member probabilities per copy -> ensemble -> pools),
port/make_run214.py (generator of possession/run214.py from frozen run211.py; staging only).
Dev numbers (10 DFL copies of the v2.13 validation, mean spellF1 difference to v2.11 | worst copy):
 one member dfl4_both_s0: TCN alone -0.0148 (8 tactical) | geo30 +0.0197 | -0.0032 ; geo40 +0.0221 | -0.0029 ; ari40 +0.0190 (tact.) | -0.0076
 two members s0+s1:       TCN alone -0.0033 | -0.0611 ; ari20 +0.0121 | +0.0005 ; ari30 +0.0176 | -0.0049 ; ari40 +0.0208 | -0.0139 ;
                          geo30 +0.0189 | -0.0024 ; geo40 +0.0225 | -0.0091 ; geo50 +0.0230 | -0.0117 ; v2.13 rule +0.0147 | -0.0317
 hardest copy: J03WN1 13102 (TCN alone -0.061).
Training time alone: ~250 s/epoch dfl4 (104 steps), 6 epochs = 26 min; dfl6 est. 40 min.
Queue: dfl4_both_s2 (running, ends ~21:08) -> dfl6_both_s0, s1, s2 (start by hand; each background command < 2 h).
Then: retcn2 for all members (tags d4s0 d4s1 d4s2 on 'J03W*'; d6s0 d6s1 d6s2 on 'MET*'), explore2 final dfl4 tags / dfl6 tags,
choose pool+weight (criterion: best mean with no copy below -0.010, prefer the smaller weight on ties), write dev_summary.py ->
development_summary.json, fix fuse2 constants, smoke run, register (final), run parts 0-3 (two at a time), assemble, decide.
Integration deadline in the plan: 16 Nov 23:59 Istanbul. User message sent 19:55 (status); baseline v2.11k submission still pending on user side.

## Rule for pool and weight (written 14 Nov 21:23, before any Metrica row of the re-trained weights exists; dfl6 members are still training)
Grid: arithmetic 0.2-0.6, geometric 0.3-0.6, unchanged v2 decoder, on the 22 development copies (10 DFL with dfl4 x3, 12 Metrica with dfl6 x3).
1. drop every setting with a development copy below -0.010;
2. among the rest take the largest mean difference to v2.11;
3. settings within 0.001 of it count as equal: the smallest weight wins (same weight in both pools: the larger mean).
Known at this time (DFL 10, three dfl4 members): ari20 +0.0115|-0.0026, ari30 +0.0162|-0.0118, ari40 +0.0204|-0.0084, ari50 +0.0222|-0.0069,
ari60 +0.0204|-0.0176, geo30 +0.0181|-0.0035, geo40 +0.0230|-0.0024, geo50 +0.0233|-0.0069, geo60 +0.0214|-0.0126; TCN alone -0.0020|-0.0515.
Decoder constants (switch 2-5, in/out 50-70, bias -0.1..-0.5) flat or worse on these copies with geo40 -> unchanged.

## 22:55 — seeds changed
The first choice (141xx / 441xx / 541xx / 641xx / 34103) collided with incidental numbers in old files (frame counts 44100, 44200, 44204; a decimal 14109).
New seeds, no number of which appears in any earlier file: copies 16100 + 10*mi + j; stream 46100 (+100*ri + 2*mi + j); clock 56100; his simulator 66100 + mi
(Metrica 3 after decision: copy 36103, index 8, simulator 66108). exp_v214.py / register_v214.py / assemble_v214.py updated.
Two dfl6 members on 12 Metrica dev copies: TCN alone +0.0195 | -0.0090; ari30 +0.0227 | +0.0060; ari40 +0.0277 | -0.0022; ari50 +0.0291 | -0.0017;
geo30 +0.0238 | +0.0027; geo40 +0.0267 | -0.0034; geo50 +0.0305 | +0.0022; v2.13 rule +0.0316 | -0.0000.
check_exp_v214.py: exp_v214's arms reproduce the explore2 numbers on dev copy J03WN1 13100 exactly (v2_11 0.62563, geo40 0.66742, TCN alone 0.64937).
xenv_tcn.py: rounded network probabilities identical under Python 3.13/numpy 2.5.3 and 3.10/numpy 1.26.4 on one dev copy (unrounded differ).
Rehearsal bundle A rebuilt at /home/claude/work/v214/prova/A (the old one in the scratchpad was lost in the restart).

## 23:35 — REGISTERED and validation started
possession-v214-plan.json registered 2026-11-14T23:33:40+03:00 (sha 9f518760...), candidate: ARITHMETIC pool, WEIGHT 0.5 (rule output: ari50; dev 22 copies
+0.0263, worst -0.0069, 21/22 better; DFL 10 +0.0222; Metrica 12 +0.0298; his simulator 5 +0.0369), v2 decoder unchanged, v2.3 path not pooled.
Gates: G1 >= +0.008 (16 tactical), G2 >= +0.008 (8 DFL), G3 >= -0.002 (8 Metrica), G4 every copy >= -0.010, G5 macro >= -0.003, G6 fill_good & fill_medium >= 0, G7 his-simulator copies >= 0.
Running: chain A (bg0b2sj0v): exp_v214.py 0 then 1; chain B (bji85c1du): 2 then 3. Logs exp_v214_{p}.log end with "EXIT <code>"; rows in exp_v214_{p}.json (resumable).
NEXT: when all four logs show EXIT 0 -> /usr/bin/python3 assemble_v214.py (writes /home/claude/sc/possession-v214-results.json, prints gates) ->
after the decision: exp_v214.py reserved (Metrica 3) and (cd /home/claude/pff && /usr/bin/python3 /home/claude/work/v214/pff_v214.py 3839) -> assemble again.
If selected: staging repo /home/claude/work/v214/sc_stage already has possession/tcn/, fuse2.py (copy the FINAL fuse2.py again!), run214.py (regenerate with
port/make_run214.py), tests/test_possession_v214.py, crossplatform test variants (record EXPECTED hashes in both envs), deliver tool rows, release config, .gitattributes/.gitignore.
Then: merge_weights.py -> models/possession-tcn-v214.npz (dfl6 s0,s1,s2), freeze_v214.py REPO, tests in both envs, rehearsal on prova/A (+prova_tagging.py), docs, GIT-YUKLE, sync to PC.
Do not run heavy jobs while the validation runs (2 CPUs, memory).
User messages sent 19:55 and 23:35 (status). No user reply since 18:23.

## Rule for a possible third candidate (written 14 Nov 23:39; known rows of the v2.14 validation at this moment: J03WN1 16100 tactical +0.0102,
## MET1 16120 tactical -0.0160 [=> G4 of v2.14 cannot pass], MET1 16120 fill_good +0.0074; nothing else)
v2.14 (arithmetic 0.5) will be recorded as failed by its own rule whatever the other rows say; its gates are not touched.
A third attempt (v2.15) is made ONLY IF the mean gates of v2.14 (G1, G2, G3, G5) pass on its 16 copies, i.e. the failure is about single copies.
Family: the same six weight files, arithmetic pool, unchanged v2 decoder, v2.3 path not pooled; ONLY the weight changes. Grid: 0.1, 0.2, 0.3.
Development copies: the 22 old ones + the 16 tactical and 4 his-simulator copies of the v2.14 validation (development data after its decision) = 42.
Selection: drop every weight with a development copy below -0.007; among the rest take the largest mean; then require that its mean over the
18 DFL development copies is at least +0.010 (margin over G2's +0.008). If no weight qualifies: stop, v2.11k is final.
Gates of v2.15: G1-G7 of v2.14, unchanged. New copies (third set of seeds). One attempt; no further attempt after it.
PFF is not a decision input (reported only).

## 00:34 (15 Nov) — v2.14 RESULT: NOT SELECTED (G4 only)
possession-v214-results.json written 00:33:42. Tactical 16: +0.0201 (15 better / 1 worse; worst -0.0160 = MET1 16120), DFL 8 +0.0192 (8/8), Metrica 8 +0.0211,
fill_good +0.0122 (worst -0.0109), fill_medium +0.0199, view42 +0.0186, his simulator +0.0292; TCN alone 0.6518 vs v2.11 0.6475. Gates: G4 FAILED, the other six passed.
User told at 00:34 (message): not selected; one more and last attempt with a smaller weight.
THIRD ATTEMPT (v2.15) per the rule of 23:39: running now (b9cyzvkb7, bag4kjzi7): cache_new.py 0-3 + retcn2 for the six members on the new copies
(logs end with DFLNEWDONE / METNEWDONE). Then:
  cd /home/claude/work/v215 && /usr/bin/python3 explore3.py > explore3.log && /usr/bin/python3 dev_summary215.py   (rule -> weight, or stop)
  set WEIGHT in v215/pooling.py -> /usr/bin/python3 exp_v215.py smoke > exp_v215_smoke.log -> register_v215.py draft / final ->
  exp_v215.py 0,1 and 2,3 in two chains -> assemble_v215.py -> decision.
Seeds of v2.15: 19100 / 49100 / 59100 / 69100 / 39103 (checked unused). Scripts ready in /home/claude/work/v215 (exp_v215.py, pooling.py [WEIGHT None],
assemble_v215.py, register_v215.py, pff_v215.py, explore3.py, dev_summary215.py, port/make_run215.py).
Staging /home/claude/work/v214/sc_stage renamed for v2.15 (tests/test_possession_v215.py, crossplatform, deliver, release config, gitattributes/gitignore);
possession/pooling.py, run215.py and models/possession-tcn-v215.npz are NOT yet in staging (regenerate: make_run215.py; merge_weights.py).
After-decision reports still to run (when CPU is free): v2.14: `exp_v214.py reserved`, `cd /home/claude/pff && /usr/bin/python3 /home/claude/work/v214/pff_v214.py 3839`,
then assemble_v214.py again. K012 text generator: k012.py /home/claude/sc (prints; body in k012_body.md) - not yet inserted into the log.

## 01:18 (15 Nov) — v2.15 REGISTERED and validation started
possession-v215-plan.json registered 2026-11-15T01:17:34+03:00 (sha 10b1a134...). Candidate: arithmetic pool, WEIGHT 0.2 (rule of 23:39 on 42 dev copies:
ari10 +0.0079 | -0.0049, ari20 +0.0138 | -0.0035 [chosen], ari30 +0.0193 | -0.0118, ari40 +0.0236 | -0.0084, ari50 +0.0242 | -0.0160; DFL 20: ari20 +0.0135, 16 tactical +0.0125).
Same seven gates. Seeds 19100 / 49100 / 59100 / 69100 / 39103. Running: b91iewxge (parts 0, 1), by4i13c6m (parts 2, 3); logs /home/claude/work/v215/exp_v215_{p}.log end with EXIT.
NEXT: cd /home/claude/work/v215 && /usr/bin/python3 assemble_v215.py -> decision. This is the LAST attempt (plan says so).
After decisions, reports still owed: v2.14: exp_v214.py reserved + pff_v214.py + assemble_v214.py again; v2.15: exp_v215.py reserved + pff_v215.py + assemble_v215.py again.
If selected: integrate as possession-v2.15 (staging sc_stage prepared: see above), pooling.py from v215/, make_run215.py, models/possession-tcn-v215.npz.

## 02:14 (15 Nov) — v2.15 RESULT: SELECTED (all seven gates)
possession-v215-results.json written 2026-11-15T02:13:56+03:00. Tactical 16: +0.0112 (14 better, 0 worse, 2 equal = copies on the v2.3 path: MET1 19123, MET2 19131),
DFL 8 +0.0126 (8/8), Metrica 8 +0.0097, fill_good +0.0106, fill_medium +0.0114, view42 +0.0118, his simulator +0.0197; macro +0.0032.
Decision times (assemble will be re-run after the after-decision rows and will change written_at): v2.14 2026-11-15T00:33:42, v2.15 2026-11-15T02:13:56
(copies of the results files at decision: v214/results_at_decision_v214.json, v215/results_at_decision_v215.json).
User told at 02:14. NOW: integration as possession-v2.15 (see the list in the 01:18 note); after-decision reports running in background.
Final-test plan is NOT re-registered (stays for v2.11k; J03WMX is not untouched for the network's design).

## 03:00 (15 Nov) — v2.15 integrated in the repository copy
Installed: possession/tcn/ (byte copies of commit 167dc7b), possession/pooling.py, possession/run215.py (port/make_run215.py), models/possession-tcn-v215.npz
(merge_weights.py: dfl6_both_s0, s1, s2), possession-v215-release.json (freeze_v215.py, 02:33), tests/test_possession_v215.py, crossplatform variants 8 and 9
(same hashes under Python 3.10 / numpy 1.26.4 and 3.13 / numpy 2.5.3), tools/possession_deliver.py ("Second model" row), possession-release.json (v2.15 first).
tests/test_possession_final_test.py changed: the final-test plan stays registered for v2.11k (second ladder step); it was the one failing test of the first
full-suite run after the installation (448 tests, 1 failure in both environments).
Chain rehearsal 02:46-02:59 on the synthetic bundle of K003 + the invented tag file of K011, Python 3.10: all steps OK, 761 s (v2.11k chain 417 s; one generation
about five minutes longer with the network in this environment), peak 1.53 GB; file differs from the v2.11k chain file on 889 frames; spellF1 0.7721 against 0.7641
(wiring check on games used in development; not a decision input). Record: possession-v215-rehearsal.json (score_k013.py, assemble_rehearsal_v215.py).
Documents: docs_v215_en.py, docs_v215_more.py, docs_common.py, docs_after_rehearsal.py, claude_md_v215.py, gityukle215.py; log entries K013 and K012 (k013.py, k012.py,
log_k012_k013.py). Correction made while writing the documents: the network's convolutions see about 25 s on either side of a frame (stem 5 taps + 14 blocks of
3 taps with dilations 1..128, 1..32 at 12.5 Hz = 320 steps), not 50 s as a first draft said.
Open: the delivery chain on the team's computer (last condition of the decision rule); final-test plan not re-registered.
03:14 - final full-suite runs on the final state: 448 tests OK under Python 3.10 with the pins (15 skipped) and under 3.13 (4 skipped); with scipy / pandas
blocked 448 OK (115 skipped). 88 files copied to the team's computer and read back byte-identical; the seven trained members are backed up there outside the
repository (possession-validation-models/tcn-v214).

## 04:25 (15 Nov) — K014: error-pattern study asked for by the team lead (03:42); release unchanged
Work folder /home/claude/work/v216 (archived as experiments/possession_v2/v216). On the 42 development copies: loss split by possession (errlib.py reproduces
the official score); short possessions (< 2 s) = 29% of labels, 38% of loss, not visible to either family; timing = 29% of loss; decoder constants, contact
evidence, reception rule: within 0.003; minimum length = a bet on the label definition; learned combination (LOMO) +0.0095, worst copy -0.023, NOT registered.
Records: possession-k014-error-patterns.json, log entry K014, TECHNICAL_DOCUMENT.md (two limitation bullets), GIT-YUKLE-V2.cmd (title K007-K014).
28 files copied to the team's computer and read back identical. Still open: the user's steps (bundle files, GIT-YUKLE, Actions, TESLIM-HAZIRLA, Form).
