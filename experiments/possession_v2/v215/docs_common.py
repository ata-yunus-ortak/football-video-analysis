"""Records that are written whatever the outcome of the v2.15 validation: the experiment archive's README rows and,
when v2.15 was NOT selected, the short passages of the documents that list tried candidates.
Usage: docs_common.py REPO_DIR"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
r214 = json.loads((REPO / 'possession-v214-results.json').read_text())
r215 = json.loads((REPO / 'possession-v215-results.json').read_text())
p215 = json.loads((REPO / 'possession-v215-plan.json').read_text())
sel = bool(r215['selected'])
W = p215['fusion_rule_fixed_before_any_score']['weight']
S4, S5 = r214['summary'], r215['summary']
sg = lambda x: f'{x:+.4f}'
failed5 = [k.split(' ')[0] for k, v in r215['gates'].items() if not v]


def edit(name, pairs):
    p = REPO / name
    s = p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding='utf-8')


# ------------------------------------------------------------------------------------------ experiments README
out5 = 'all seven gates passed: the release' if sel else ('gates failed (' + ', '.join(failed5) + '), not released')
edit('experiments/possession_v2/README.md', [
 ('''| `/home/claude/org/repo` | clone of the organisers' repository, commit `f8f2629`, without `evaluation/gt/` |''',
  '''| `/home/claude/org/repo` | clone of the organisers' repository, commit `f8f2629`, without `evaluation/gt/` |
| `/home/claude/work/v213`, `/home/claude/work/v214`, `/home/claude/work/v215` | the folders `v213/`, `v214/`, `v215/` below; `v214/tcn_cache/` (training copies), `v214/tcn_weights/` (the six trained members and their logs) and `v214/probs/` (stored probabilities of the development copies) are not kept |
| `/home/claude/ata-yunus-ortak/football-video-analysis` | clone of the team repository at commit `167dc7b` of branch `mtah-possession` |'''),
 ('''| superseded, not run | `test_final_wmx.py`''',
  f'''| v2.14 second model re-trained and pooled through the v2 decoder, equal weights (K012), `possession-v214-plan.json`, `possession-v214-results.json`: six of seven gates passed, the gate on single copies failed, not released | in `v214/`: `tcn_jax.py` (JAX re-implementation of the team member's training; `cache` builds the corrupted copies of both simulators, `train` one member), `tcn_training/*.json` (settings of the six runs), `test_tcn_jax.py` (network against his NumPy inference), `bench_jax.py`, `merge_weights.py`; diagnosis and development on copies already scored: `diag1.py` (which corruption component hurts the committed weights), `lib214.py`, `cache_old.py`, `retcn.py`, `retcn2.py` (stored probabilities), `explore.py`, `explore2.py` (pooling rules), `dev_summary.py` and `development_summary.json` (the rule that fixed pool and weight), `check_exp_v214.py`, `xenv_tcn.py`; `NOTES.md` (running notes with the clock times at which the selection rules were written down); validation: `fuse2.py` (the pooling as validated), `register_v214.py`, `exp_v214.py`, `exp_v214_smoke.json`, `assemble_v214.py`, `pff_v214.py`; after the decision: `cache_new.py` (stores the validation copies as development data); `k012.py` (wrote the log entry); not used: `freeze_v214.py`, `docs_v214_en.py`, `port/make_run214.py` (prepared for a release that did not happen) |
| v2.15 the same pooled system with weight {W} for the network (K013), `possession-v215-plan.json`, `possession-v215-results.json`: {out5} | in `v215/`: `explore3.py`, `dev_summary215.py`, `development_summary.json` (the weight by the rule of `v214/NOTES.md`), `pooling.py` (the pooling as validated{'; released as `possession/pooling.py`' if sel else ''}), `register_v215.py`, `exp_v215.py`, `exp_v215_smoke.json`, `assemble_v215.py`, `pff_v215.py`, `k013.py`{', `port/make_run215.py` (derives `possession/run215.py` from the frozen `run211.py`), `freeze_v215.py` (wrote the release manifest), `docs_v215_en.py`, `docs_v215_more.py`' if sel else '; not used: `port/make_run215.py`, `freeze_v215.py`, `docs_v215_en.py`, `docs_v215_more.py` (prepared for a release that did not happen)'} |
| superseded, not run | `test_final_wmx.py`'''),
])
print('experiments README edited')

if not sel:
    T4, T5 = S4['tactical'], S5['tactical']
    edit('TECHNICAL_DOCUMENT.md', [
     ('''`possession-v213-results.json`). An earlier
vision line''', f'''`possession-v213-results.json`). Two further attempts followed a diagnosis on the already-scored
copies (the committed weights broke on the other simulator's false ball detections; the
single-cost decoder dropped our dead-ball costs): the network was re-trained by us on the
corruption of both simulators and the average was decoded by our decoder. With equal weights
(v2.14) it was better on {T4['copies_better']} of 16 new copies ({sg(T4['diff_spell_f1_mean'])}) but one copy was {abs(T4['diff_spell_f1_min']):.3f} worse, which the gate on
single copies does not allow; with weight {W} for the network (v2.15, the last attempt) the
difference was {sg(T5['diff_spell_f1_mean'])} on 16 further copies and {'gate ' if len(failed5) == 1 else 'gates '}{', '.join(failed5)} failed. Neither was released
(`possession-v214-*.json`, `possession-v215-*.json`). An earlier
vision line'''),
    ])
    edit('README.md', [
     ('''the models' probabilities with a team member's temporal convolution network (v2.13, log entry K010).''',
      '''the models' probabilities with a team member's temporal convolution network (v2.13, log entry K010; two
further attempts with re-trained weights and our decoder, v2.14 and v2.15, log entries K012 and K013).'''),
    ])
    edit('AGENTS.md', [
     ('''- Two candidates failed their registered gates and are not part of any release: touch / control-change
  columns (`possession/touch.py`, v2.12, log entry K008) and averaging the release's probabilities with
  a team member's temporal convolution network (v2.13, log entry K010; scripts and byte copies of his
  modules under `experiments/possession_v2/v213/`). Keep the files and records; using either needs a
  new plan registered before any new result.''',
      '''- Four candidates failed their registered gates and are not part of any release: touch / control-change
  columns (`possession/touch.py`, v2.12, log entry K008) and three ways of averaging the release's
  probabilities with a team member's temporal convolution network: his committed weights and decoder
  (v2.13, K010), weights re-trained by us with our decoder and equal weights (v2.14, K012: better on
  15 of 16 copies, one copy clearly worse) and the same with a smaller weight (v2.15, K013). Scripts
  under `experiments/possession_v2/v213/`, `v214/`, `v215/`. Keep the files and records. The plan of
  v2.15 says that no further candidate with the second model is registered before the deadline.'''),
    ])
    edit('DATA_SOURCES.md', [
     ('''`possession-v213-results.json`). The release does not load it and its weights are not in this branch.''',
      '''`possession-v213-results.json`). In two further attempts (log entries K012, K013) his design was
re-trained by us on the same six DFL matches with both corruption simulators of the team
(`experiments/possession_v2/v214/tcn_jax.py`, JAX) and averaged again; neither passed all gates. The
release does not load the network, and no network weights are in this branch.'''),
    ])
    print('documents edited for the not-selected case')
