"""Update CLAUDE.md for the release possession-v2.15: the whitelist line, the layout and command lines and a new status
snapshot (the snapshot of 13 Nov becomes an "Earlier status" section, unchanged).
Usage: claude_md_v215.py REPO_DIR TESTS_310 SKIPPED_310 TESTS_313 SKIPPED_313"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
N310, S310, N313, S313 = (int(x) for x in sys.argv[2:6])
r4 = json.loads((REPO / 'possession-v214-results.json').read_text())
r5 = json.loads((REPO / 'possession-v215-results.json').read_text())
reh = json.loads((REPO / 'possession-v215-rehearsal.json').read_text())
rel = json.loads((REPO / 'possession-v215-release.json').read_text())
assert r5['selected'] and not r4['selected']
S4, S5 = r4['summary'], r5['summary']
T4, T5 = S4['tactical'], S5['tactical']
sg = lambda x: f'{x:+.4f}'
f4 = lambda x: f'{x:.4f}'
new, old = reh['delivered_file_against_the_bundle_labels'], reh['for_comparison_the_v2.11k_chain_file_13_Nov']
p = REPO / 'CLAUDE.md'
s = p.read_text(encoding='utf-8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


rep('''  Sole exceptions: `models/possession-v2.npz` and `models/possession-v23.npz` (whitelisted in
  `.gitignore`), trees trained only on CC-BY Sportec/DFL data, needed to regenerate the submission.''',
    '''  Sole exceptions: `models/possession-v2.npz`, `models/possession-v23.npz` (trees) and
  `models/possession-tcn-v215.npz` (network weights of the second model), whitelisted in `.gitignore`,
  trained only on CC-BY Sportec/DFL data, needed to regenerate the submission.''')
rep('''  and `possession-v211k-release.json` chain to it and add `run211g.py`, `kickoff.py` and `run211k.py`. Lower ladder steps''',
    '''  and `possession-v211k-release.json` chain to it and add `run211g.py`, `kickoff.py` and `run211k.py`;
  `possession-v215-release.json` adds `run215.py`, `pooling.py`, `tcn/*.py` and the network weights. Lower ladder steps''')
rep('''python -m possession.run211k --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local''',
    '''python -m possession.run215 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local''')

snapshot = f'''## Status snapshot (15 Nov 2026, early morning — verify before relying on it)

- **Submission system: `possession-v2.15`** (`python -m possession.run215`, manifest `possession-v215-release.json`,
  frozen {rel.get('frozen_at', '15 Nov')[:16].replace('T', ' ')}) = v2.11k + a second model family on the core model path (v2.1, measured noise at most
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
  16 new copies {sg(T4['diff_spell_f1_mean'])}, {T4['copies_better']} better, but one copy {sg(T4['diff_spell_f1_min'])}: the gate on single copies (G4) failed, not released.
  v2.15 (K013; the same with weight 0.2, chosen on 42 development copies by a rule written while the v2.14 validation
  was running): 16 further new copies {f4(T5['v2_11']['spell_f1'])} -> {f4(T5['fused']['spell_f1'])} ({sg(T5['diff_spell_f1_mean'])}), {T5['copies_better']} better, {T5['copies_worse']} worse, 2 equal (v2.3 path);
  DFL {sg(S5['tactical_DFL']['diff_spell_f1_mean'])}, Metrica {sg(S5['tactical_Metrica']['diff_spell_f1_mean'])}, broadcast fills {sg(S5['fill_good']['diff_spell_f1_mean'])} / {sg(S5['fill_medium']['diff_spell_f1_mean'])}, copies of the other simulator {sg(S5['tactical_sim2']['diff_spell_f1_mean'])}; all seven gates passed.
  The v2.15 plan says: **no further candidate with the second model is registered before the deadline.**
- **Weights:** PyTorch could not be installed in the agent session; the team member's `train.py` was re-implemented
  in JAX (`experiments/possession_v2/v214/tcn_jax.py`; checked against his NumPy inference, largest probability
  difference 7.9e-7). Training data: the six DFL matches of the tree bundles only, twelve corrupted copies of every
  half (six per simulator). `dfl4_both_s0-2` (four matches) served the DFL validation rows, `dfl6_both_s0-2` are the
  released members. A re-run is not bit-identical: never replace the npz. Running notes with the clock times at which
  the selection rules were written: `experiments/possession_v2/v214/NOTES.md`.
- **Reported after the decisions, never decision inputs:** one new copy of Metrica game 3 (v2.15: tactical +0.0222) and
  PFF game 3839 (no published licence, kept outside the repository): v2.11 0.6289, v2.15 0.6542.
- **Conditions of the registered decision rule for delivering v2.15** (otherwise v2.11k stays), to be met by 16 Nov
  23:59 Istanbul: inference under Python 3.10 / numpy 1.26.4 (done); nine synthetic bundles byte-identical under
  3.10 / 1.26.4 and 3.13 / 2.5.3 (done; `tests/test_possession_crossplatform.py`, two variants with the network); full
  test suite (done: {N310} tests, {S310} skipped, under 3.10 with the pins; {N313}, {S313} skipped, under 3.13); a full-size
  chain rehearsal (done: `possession-v215-rehearsal.json`, all steps OK in {reh['seconds']} s, peak {reh['peak_child_rss_gb']} GB; on that synthetic
  bundle spellF1 {f4(new['graded windows']['spell_f1_mean'])} against {f4(old['graded windows']['spell_f1_mean'])} for the v2.11k chain file; a wiring check, not an accuracy claim); documents
  describe the second model, its training data and the three attempts (done). **Still open: the delivery chain must
  run OK on the team's computer** (the `URETIM` and `TESLIM` lines must name `possession-v2.15`; if they name a lower
  step, that step is what is delivered and the documents must be brought in line before the Form is filled).
- **Final-test plan NOT re-registered:** `possession-final-test-plan.json` stays registered for `possession-v2.11k`
  (the release without the second model; `tests/test_possession_final_test.py` checks exactly that). The network's
  designer used J03WMX during his development, so a run of v2.15 on it could not be reported as a fresh test. The
  released weights were trained without it and the process that built the release has not downloaded it. A result of
  `SON-TEST.cmd` is a result of v2.11k (steps 1-8) and is reported as that.
- **Delivery chain:** `PLATFORM` compares nine synthetic variants; Appendix R has a "Second model" row (category only:
  used / not used on this path / not part of this entry point). `TESLIM-HAZIRLA.cmd` needs no option.
- GitHub: remote branch still at a152fa2 (11 Nov 21:58) when this was written. K007-K013, v2.11k, v2.15 and the
  weights are pushed only when the user runs `GIT-YUKLE-V2.cmd` (this session has read-only access).
- Still pending (user): the three files in the bundle folder (two videos, Smart Tagging) -> `GIT-YUKLE-V2.cmd` ->
  Actions -> `TESLIM-HAZIRLA.cmd` -> paste the `[..]` lines and `SONUC` -> Google Form (one member submits; team name
  `LittleSickle`; deadline 17 Nov 23:59 CET = 18 Nov 01:59 Istanbul). Optional: `SON-TEST.cmd` (v2.11k only).
- **Standing rule, repeated:** aggregates computed on the provided match (scores, label shares, tag positions) are
  not inputs to any choice and are not copied into any file; only the chain's status lines are shared. The organisers'
  published constants (DATA.md, FAQ.md, games.py, starter code) are public documentation, not such aggregates.

## Earlier status (13 Nov 2026 afternoon)
'''
rep('## Status snapshot (13 Nov 2026 afternoon — verify before relying on it)\n', snapshot)
p.write_text(s, encoding='utf-8')
print('CLAUDE.md updated')
