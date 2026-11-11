"""Apply the v2.11 changes to the two English technical documents; numbers are read from possession-v211-results.json
and possession-v211-followup.json (rehearsal). Refuses unless v2.11 was selected. Usage: docs_patch.py"""
import json
import os
from pathlib import Path

R = Path(os.environ.get('SC_DIR', '/home/claude/sc'))
res = json.loads((R / 'possession-v211-results.json').read_text())
assert res['selected'] == 'possession-v2.11'
S = res['summary']
f3 = lambda x: f'{x:.3f}'
sp = lambda k, s: f3(S[k]['spell_f1'][s])
follow = json.loads((R / 'possession-v211-followup.json').read_text())
reh = follow['full_size_rehearsal']
K5 = json.loads((R / 'possession-label-order-correction.json').read_text())['corrected']
k3 = K5['full_size_rehearsal_of_K003']
k3s = lambda b: k3[f'bundle {b}']['delivered file of the K003 chain (possession-v2.9)']['against_file_order_labels']['spell_f1_mean']
ctl = k3['negative_controls_bundle_A_against_file_order_labels']
slots = K5['slot_and_duplicate_diagnostic']['rerun_python_3_13_file_order_labels']
slot_single = max(abs(x) for v in slots['difference_to_base_per_match'].values() for x in v.values())
slot_mean = max(abs(x) for x in slots['difference_to_base'].values())
roles = K5['goalkeeper_diagnostic']['rerun_python_3_13_file_order_labels']
rd = roles['difference_to_base']
ref_cost = max(abs(rd['ref_home']), abs(rd['ref_mixed']))
worst_false = max(max(S[k]['outfield_positions_moved_to_the_wrong_team_per_copy']) for k in ('gk_one', 'gk_both', 'view42_gk_both'))
none_false = max(max(S[k]['outfield_positions_moved_to_the_wrong_team_per_copy']) for k in ('none', 'view42_none', 'view35_none'))
v10 = {k: S[k]['v2_10_reported_only'] for k in ('view42_none', 'view35_none')}


def patch(path, pairs):
    p = R / path
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:70], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


# ---------------------------------------------------------------------------------- short document
patch('TECHNICAL_DOCUMENT.md', [
    ('# Possession v2.9 — technical document (short version)', '# Possession v2.11 — technical document (short version)'),
    ('**Pipeline** (`python -m possession.run29`):', '**Pipeline** (`python -m possession.run211`):'),
    ('''   from their documentation may be used this way. `possession.run29g` is the same system without
   it (the models run on the whole graded second half) and is kept in reserve for a negative
   answer; Appendix R names the entry point that produced the submitted file.
''', f'''   from their documentation may be used this way. `possession.run211g` is the same system without
   it (the models run on the whole graded second half) and is kept in reserve for a negative
   answer; Appendix R names the entry point that produced the submitted file.
8. *Goalkeeper team check* (`possession/keeper2.py`, applied to the tracking before step 1). The
   team of a track slot is decided by the tracker, and a goalkeeper does not wear his team's kit.
   If a goalkeeper's track carried the other team's id, the features would see an opponent standing
   in the goal; with both goalkeepers affected, the attacking directions that step 1 derives from
   the mean position of each team come out inverted (external copies: spellF1 {sp('gk_both', 'v2_9')} instead of
   {sp('none', 'v2_9')}). The check finds goalkeeper track pieces from positions only: while play is in the
   other half, the tracked player nearest to a goal and at least 8 m behind everybody else, and
   pieces that continue such a piece in time and place. A piece in a slot of the team that does
   not defend that goal is moved to the defending team if most of that goal's evidence in that
   half is under the other id (mislabelled for the whole half), or if it continues a goalkeeper
   piece (mislabelled for a while). Otherwise nothing changes and the output is that of steps
   1-7 alone. We did not look at whether the provided tracking has such errors; Appendix R says
   whether anything was moved.
'''),
    ('''and handled by the matching model path (step 5). *Second camera:* used only to fill gaps, only''',
     '''and handled by the matching model path (step 5). *Team ids of goalkeepers:* checked against where
the tracks stand and corrected only on clear evidence (step 8). *Second camera:* used only to fill gaps, only'''),
    ('''Metrica sample game to the training matches (+0.001 on the other Metrica game, -0.011 on DFL). An earlier''',
     '''Metrica sample game to the training matches (+0.001 on the other Metrica game, -0.011 on DFL), a first
version of the goalkeeper check (passed its gates; replaced before release, see Section 5). An earlier'''),
    ('''| same copies, accurate broadcast: fill without / with registration | | 0.686 / 0.684 |
''', f'''| same copies, accurate broadcast: fill without / with registration | | 0.686 / 0.684 |
| 8 copies not used before, team ids as corrupted: without / with the goalkeeper check | | {sp('none', 'v2_9')} / {sp('none', 'v2_11')} |
| same copies, both goalkeepers under the other team's id: without / with | | {sp('gk_both', 'v2_9')} / {sp('gk_both', 'v2_11')} |
| same copies, one goalkeeper under the other id: without / with | | {sp('gk_one', 'v2_9')} / {sp('gk_one', 'v2_11')} |
| same copies, both goalkeepers under the other id 30% of the time: without / with | | {sp('gk_part', 'v2_9')} / {sp('gk_part', 'v2_11')} |
| same copies seen by a camera that does not track players beyond 42 m (35 m) from play, ids correct: without / with | | {sp('view42_none', 'v2_9')} / {sp('view42_none', 'v2_11')} ({sp('view35_none', 'v2_9')} / {sp('view35_none', 'v2_11')}) |
'''),
    ('''  tracks changed spellF1 by at most 0.007 on a copy and 0.002 on average
  (`possession-rehearsal-results.json`). The real tracker may behave differently from this
  simulation.''',
     f'''  tracks changed spellF1 by at most {slot_single:.3f} on a copy and {slot_mean:.3f} on average
  (`possession-label-order-correction.json`). The real tracker may behave differently from this
  simulation.'''),
    ('''they passed (`possession-v29-amendment-plan.json`, `-results.json`; the first evaluation is kept
unchanged in `possession-v29-results.json`).
''', '''they passed (`possession-v29-amendment-plan.json`, `-results.json`; the first evaluation is kept
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
'''),
    ('''- **Second-half kick-off** rests on the organisers' statement; its effect cannot be measured
  externally.
''', f'''- **Second-half kick-off** rests on the organisers' statement; its effect cannot be measured
  externally.
- **Goalkeeper team check.** The id errors and the camera that hides far players are simulated by
  us; the provided tracking may have neither, or errors of another kind (a match official tracked
  under a team id cost {ref_cost:.3f} or less in a diagnostic and is not handled). When the far goalkeeper
  is mostly out of view (35 m window in the simulation) there is too little evidence and wrong ids
  are not corrected; with a 42 m window and both goalkeepers mislabelled the score was {sp('view42_gk_both', 'v2_9')}
  without and {sp('view42_gk_both', 'v2_11')} with the check. With correct ids no outfield position was moved to
  the wrong team on the eight copies{'' if none_false == 0 else f' except {none_false} frames on one'}; with whole-match errors up to {worst_false:,} outfield positions
  per copy were moved as well (a forward taken for the goalkeeper). A first version of the check (v2.10) passed its four
  registered gates, but an analysis of what it had moved showed that it took a forward waiting up
  the pitch for the goalkeeper whenever the goalkeeper was not tracked ({max(v10['view35_none']['outfield_positions_moved_to_the_wrong_team_per_copy']):,} positions on one
  copy with the 35 m window, spellF1 {v10['view35_none']['mean_difference']:+.3f} on average). It was not released; the second
  version was registered and validated with that situation as two additional gates
  (`possession-v210-results.json`, `possession-v211-plan.json`, `possession-v211-results.json`).
'''),
    ('''python -m possession.run29 --data-dir <bundle root> --out <new folder> \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast''',
     '''python -m possession.run211 --data-dir <bundle root> --out <new folder> \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast'''),
    ('''  `tests/test_possession_crossplatform.py` pins the output hashes of five synthetic runs (both
  model paths, with and without the broadcast camera and the clock), recorded on Linux; the
  delivery tool runs it on the computer that generates the file.''',
     '''  `tests/test_possession_crossplatform.py` pins the output hashes of seven synthetic runs (steps
  1-7 on both model paths, with and without the broadcast camera and the clock; the full
  pipeline on two bundles whose goalkeeper tracks carry the other team's id), recorded on Linux;
  the delivery tool runs it on the computer that generates the file.'''),
    ('''  the same score (spellF1 0.715 and 0.686; 0.005 with the teams exchanged, 0.54 with the rows''',
     f'''  the same score (spellF1 {f3(k3s('A'))} and {f3(k3s('B'))}; {f3(ctl['teams exchanged']['spell_f1'])} with the teams exchanged, {ctl['rows shifted by +25 frames']['spell_f1']:.2f} with the rows'''),
    ('''  shifted by one second). This checks wiring and size, not accuracy on the provided match.''',
     f'''  shifted by one second). After the goalkeeper check was added the chain was run again on the
  first bundle ({f3(reh['bundle_A_chain_v2_11']['spell_f1'])}) and on a copy of it in which the goalkeepers' tracks carry the
  other team's id ({f3(reh['bundle_G1_v2_11']['spell_f1'])} with the check, {f3(reh['bundle_G1_v2_9']['spell_f1'])} without). This checks wiring and size, not
  accuracy on the provided match.'''),
])

# ---------------------------------------------------------------------------------- long document
patch('TECHNICAL_DOCUMENT_V2.md', [
    ('# Possession v2 — technical document (full record; current release: v2.9)', '# Possession v2 — technical document (full record; current release: v2.11)'),
    ('Submission file regenerated with `python -m possession.run29` (see the addendum and Reproduction).',
     'Submission file regenerated with `python -m possession.run211` (see the two addenda and Reproduction).'),
    ('''> Also tested since and not selected: gap-bridging ball features (v2.7, +0.002) and adding a Metrica
> sample game to the training matches (v2.8, +0.001 on the held-out Metrica game, -0.011 to -0.014 on
> DFL copies).
''', f'''> Also tested since and not selected: gap-bridging ball features (v2.7, +0.002) and adding a Metrica
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
>    the whole match {rd['gk_one']:+.3f} spellF1, both {rd['gk_both']:+.3f} ({roles['mean_spell_f1']['base']:.3f} -> {roles['mean_spell_f1']['gk_both']:.3f}), both for 30% of the time {rd['gk_part']:+.3f}; a
>    match official tracked under a team id {min(rd['ref_home'], rd['ref_mixed']):+.3f} at worst. (Numbers of the re-run against the
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
>    | team ids as corrupted, whole pitch in view | {S['none']['spell_f1']['v2_9']:.4f} | {S['none']['spell_f1']['v2_11']:.4f} | G1: mean difference >= -0.002, no copy below -0.005 |
>    | both goalkeepers under the other id | {S['gk_both']['spell_f1']['v2_9']:.4f} | {S['gk_both']['spell_f1']['v2_11']:.4f} | G2: within 0.015 of the first row |
>    | one goalkeeper under the other id | {S['gk_one']['spell_f1']['v2_9']:.4f} | {S['gk_one']['spell_f1']['v2_11']:.4f} | G3: within 0.010 of the first row and at least +0.008 |
>    | both goalkeepers wrong 30% of the time | {S['gk_part']['spell_f1']['v2_9']:.4f} | {S['gk_part']['spell_f1']['v2_11']:.4f} | G4: within 0.010 of the first row and not below v2.9 |
>    | camera window 42 m, ids as corrupted | {S['view42_none']['spell_f1']['v2_9']:.4f} | {S['view42_none']['spell_f1']['v2_11']:.4f} | G5: as G1 |
>    | camera window 35 m, ids as corrupted | {S['view35_none']['spell_f1']['v2_9']:.4f} | {S['view35_none']['spell_f1']['v2_11']:.4f} | G6: as G1 |
>    | camera window 42 m, both goalkeepers wrong (reported) | {S['view42_gk_both']['spell_f1']['v2_9']:.4f} | {S['view42_gk_both']['spell_f1']['v2_11']:.4f} | none |
>
>    Reported alongside: v2.10 in the two window rows scored {v10['view42_none']['spell_f1']:.4f} and {v10['view35_none']['spell_f1']:.4f}
>    (mean difference to v2.9 {v10['view42_none']['mean_difference']:+.4f} and {v10['view35_none']['mean_difference']:+.4f}, worst copy {min(v10['view42_none']['worst_copy_difference'], v10['view35_none']['worst_copy_difference']):+.4f}); goalkeeper
>    positions under a wrong id went from {S['gk_both']['goalkeeper_positions_with_wrong_id_before_after'][0]:.0%} to {S['gk_both']['goalkeeper_positions_with_wrong_id_before_after'][1]:.1%} (both wrong), {S['gk_one']['goalkeeper_positions_with_wrong_id_before_after'][0]:.0%} to {S['gk_one']['goalkeeper_positions_with_wrong_id_before_after'][1]:.1%} (one), {S['gk_part']['goalkeeper_positions_with_wrong_id_before_after'][0]:.0%} to
>    {S['gk_part']['goalkeeper_positions_with_wrong_id_before_after'][1]:.1%} (30% of the time) and from 100% to {S['view42_gk_both']['goalkeeper_positions_with_wrong_id_before_after'][1]:.0%} with the 42 m window.
> 5. **Records correction found during this work (K005).** The full-size rehearsal of K003, its
>    slot / duplicate diagnostic and the goalkeeper diagnostic above had been scored in the Python 3.10
>    environment, where `metrica_labels.py` sorted simultaneous events in another order than the
>    provider's files and lost about half of the dead-ball intervals of the Metrica proxy labels.
>    Every selection, gate, validation and reserved test ran in the experiment environment
>    (Python 3.13), where the labels are in file order; the possession counts stored in
>    `possession-v2-results.json` match those labels only. The script now sorts stably and gives the
>    same labels in both environments; the three records were recomputed
>    (`possession-label-order-correction.json`): rehearsal bundle A {f3(k3s('A'))} (first reported 0.715),
>    bundle B {f3(k3s('B'))} (0.686); slot / duplicate diagnostic at most {slot_single:.3f} on a copy and {slot_mean:.3f}
>    on average (0.007 and 0.002).
> 6. **Limits.** The errors and the camera window are simulated by us. When the far goalkeeper is mostly
>    out of view nothing is corrected. The validation matches were not fresh for this design (the v2.10
>    analysis on them prompted it). The check was validated with the tactical camera only; the broadcast
>    path uses the ids as given. Whether the provided tracking has any of this was not looked at;
>    `run.json` on the team's computer records what was moved (aggregates only).
'''),
    ('''python -m possession.run29 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \\''',
     '''python -m possession.run211 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \\'''),
    ('''broadcast files, or when the accuracy gate is closed, the release (`possession.run29`) writes the''',
     '''broadcast files, or when the accuracy gate is closed, the release (`possession.run211`) writes the'''),
    ('''`possession.run29` (like `possession.run25`) reads `tactical/BAR-ATH_tactical_atd.xml` and `_atd.txt`,''',
     '''`possession.run211` (like `possession.run29` and `possession.run25`) reads `tactical/BAR-ATH_tactical_atd.xml` and `_atd.txt`,'''),
])
patch('DATA_SOURCES.md', [
    ('''piece; frames whose state cannot be derived are unscored. Games 1-2 were used for validation and''',
     '''piece; frames whose state cannot be derived are unscored. Events with the same start frame are
kept in the order of the provider's file (a set piece before the pass that takes it; explicit
since log entry K005). Games 1-2 were used for validation and'''),
])
print('documents patched')
