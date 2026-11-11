# Experiment scripts of the possession v2 line (archive)

These are the scripts that produced the numbers in `possession-v*-results.json` and in the technical
documents. They are **not needed to regenerate the submission** (that is `python -m possession.run29`
or the release named in `possession-release.json`; see the README in the repository root) and they are
not part of any frozen release. They are kept so that every reported experiment can be inspected.

The files are byte copies of the scratch folder they were run from, so the SHA-256 values that plan
files record for `work/<name>` refer to `experiments/possession_v2/<name>`. Nothing was cleaned up:
some scripts are one-off diagnostics, and a few are superseded drafts.

They ran in a cloud development session that held **only external data**. No script reads the provided
match, and none was ever run on it.

## What they expect

Hard-coded paths of that session (`harness.py`):

| path in the scripts | content |
|---|---|
| `/home/claude/sc` | this repository |
| `/home/claude/work` | the scripts themselves and `cache/` (feature arrays, validation models; several GB, not kept) |
| `/mnt/user-data/uploads/sportec-development-20261107/prepared-v1/<match>` | DFL matches prepared by `tools/sportec_download.py` + `tools/sportec_prepare.py` (`sportec-data-plan.json`) |
| `/home/claude/ext/metrica/data`, `/home/claude/ext/sd/data` | Metrica sample data, commit `e706dd5` |
| `/tmp/claude-0/.../scratchpad/prova` | folder of the full-size rehearsal (K003): the scripts below, the synthetic bundles they wrote (about 300 MB each, not kept) and their logs |
| `/home/claude/org/repo` | clone of the organisers' repository, commit `f8f2629`, without `evaluation/gt/` |

`possession_metrics.py` (the organisers' scorer, imported by some scripts) is not copied here; it is
identical to `possession/official_metrics.py` below that file's three-line header.
Python 3.13 / numpy 2.5.3 / scikit-learn 1.9.1 were used for experiments; the frozen bundles were then
checked under Python 3.10 / numpy 1.26.4 (`repro_*.py`).
The rehearsal of K003 (`after_A.sh`, `after_B.sh`, including `stress_slots.py`) and the first run of
`stress_roles.py` used the Python 3.10 environment (pandas 2.1.4); with the label script as it was then,
that changed the Metrica proxy labels (log entry K005). Scores against Metrica labels belong in the
experiment environment or need the current `metrica_labels.py`.

## Which script belongs to which record

| record (plan / results / log entry) | scripts |
|---|---|
| common | `harness.py` (loading, corrupted copies, feature cache), `metrica_labels.py` (proxy labels from Metrica events), `baselines.py`, `precompute*.py`, `pre24.py`, `pre27.py` |
| v2.1 core, `possession-v2-*` (P001-P003) | `exp1.py`, `train1.py`, `eval1.py`-`eval3.py`, `exp_stack.py`, `eval_stack.py`, `grid2.py`, `grid3.py`, `diagnose.py`, `diag_*.py`, `stress.py`, `stress2.py`, `test_reserved.py`, `e2e_met3.py`, `finalize_config.py`, `assemble_*.py`, `fill_doc.py` |
| v3 Smart Tagging, `possession-v3-*` | `exp_tags.py`, `eval_tags.py`, `tagcols.py`, `exp_v3.py`, `eval_v3tags.py`, `sel_v3.py`, `v31.py`, `sim_check.py` |
| v4 ungated broadcast fill, `possession-v4-*` | `synth_broadcast.py`, `exp_v4.py`, `test_align_one.py`, `upside_fill.py` |
| v2.2 / v2.3 / v2.4 noise, `possession-v22-*` ... `possession-v24-*` | `ballnoise.py`, `playernoise.py`, `noise_est.py`, `eval_v22.py`, `eval_v23.py`, `eval_v23_fair.py`, `eval_v24.py`, `probs24.py`, `finalize_v22.py`-`finalize_v24.py`, `test_reserved22.py`-`test_reserved24.py`, `e2e_met3_v23.py`, `repro_v24.py` |
| v2.5 / v2.5b gated fill and clock anchor, `possession-v25-*`, `possession-v25b-*` | `synth_broadcast2.py`, `synth_clock.py`, `exp_v25.py`, `exp_v25b.py`, `assemble_v25b.py`, `finalize_v25*.py`, `make_release25.py`, `repro_v25.py`, `build_repro25_fixture.py`, `doc_v25*.py` |
| reporting-only diagnostics (R001, R002) | `decomp.py`, `oracle_parts.py`, `plaus_ref.py` |
| v2.6 switch hazard, `possession-v26-*` | `hz_common.py`, `hz_train.py`, `hz_eval.py` |
| v2.7 gap features, v2.8 Metrica training, `possession-v27-*`, `possession-v28-*` | `eval27.py`, `dec_explore.py`, `lane27b.sh`, `v28.py` |
| v2.9 registration, `possession-v29-*` (P012) and its amendment (K002) | `synth_broadcast3.py`, `exp_v29.py`, `repro_v29.py`, `exp_v29k.py`, `eval_v29k.py` |
| full-size rehearsal of the delivery chain and slot / duplicate diagnostic, `possession-rehearsal-results.json` (K003) | `prova_build.py` (synthetic bundle with the file names, sizes and slot counts of the provided files), `after_A.sh`, `after_B.sh` (job chains), `score_prova.py`, `r1.py` (in-memory reference), `rss_run.py` (time and memory of a command), `stress_slots.py`, `assemble_rehearsal.py` |
| final test on the reserved DFL match, `possession-final-test-plan.json` (K003; tool: `tools/possession_final_test.py`) | `register_final_test.py` (writes the plan with the hashes of release, tool and simulators) |
| goalkeeper team check (K004): diagnostic, first version v2.10 (`possession-v210-*`, passed its gates, not released), second version v2.11 (`possession-v211-*`, the release) | `stress_roles.py` and its rows `stress_roles.json` (reporting-only diagnostic); `gk_stats.py`, `gk_dev.py`, `gk_diag.py`, `gk_false.py`, `gk_check.py` (development of the first rule, training matches only); `register_v210.py`, `exp_v210.py`, `assemble_v210.py` (validation and gates of v2.10); `gk_none.py`, `gk_none_detail.py` (what v2.10 moved with correct ids); `camera_view.py` (simulated camera that does not track players far from play), `gk_far_dev.py`, `gk_gap_stats.py`, `gk_margins.py`, `gk_smoke_v211.py` (development of the second rule, training matches only); `register_v211.py`, `exp_v211.py`, `assemble_v211.py` (validation and gates of v2.11); `freeze_v211.py` (manifests and release configurations); `prova_gk.py` (full-size rehearsal bundle with the goalkeepers' tracks under the other team's id), `after_v211.sh` (reserved game and rehearsals), `assemble_followup.py` (`possession-v211-followup.json`); `register_final_test_v211.py` (re-registration of the final test for v2.11); `log_k004.py`, `docs_k004_k005_en.py`, `docs_k004_k005_tr.py` (write the log entry and the document changes from the result files) |
| records correction K005, `possession-label-order-correction.json`: order of simultaneous events in the Metrica proxy labels | `metrica_labels.py` (now sorts stably), `label_order.py` (labels with the old default sort and in file order, per environment), `gt_spells.py` (possession counts of the labels, to compare with stored results), `rescore_k003.py` (rehearsal outputs of K003 against the file-order labels), re-runs of `stress_slots.py` and `stress_roles.py` in the experiment environment, `assemble_k005.py`, `log_k005.py` |
| superseded, not run | `test_final_wmx.py` (draft of the final test written for v2.5; replaced by `tools/possession_final_test.py`) |
| other | `features_v2_backup.py` (copy of the feature module before a refactoring), `run_*.sh`, `make_final.sh` (job chains) |

The grouping follows the file names and dates; the header of each script says what it does.
