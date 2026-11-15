# One PFF FC World Cup 2022 game through the frozen v2.11 (inspection only, log entry K009)

These scripts run the decision of the submission system on one external match whose broadcast tracking
PFF FC has released, compare the output with a reference we build from PFF's own event records, and show
both in a self-contained HTML viewer that can be watched next to a replay of the match.

**Nothing here trains, tunes or selects anything, and no number here is a competition score.** The
reference is a proxy built by us from PFF events, not ground truth. The release and its models are used
as frozen (`possession.run211.check_release()` passes on the same checkout).

## Data (not in this repository)

PFF FC 2022 FIFA World Cup dataset, obtained through PFF FC's sign-up form on blog.fc.pff.com on
12 Nov 2026; the form leads to a Google Drive folder (the link is not recorded here). **No licence text is
published with the data**, so it is used only for our own inspection: no data, no frame-level output and
no generated viewer go into this repository, and nothing from it is used for model or parameter choices.
The match video is not part of the dataset.

Game 3839, Spain (home) – Germany, 27 Nov 2022, Al Bayt Stadium. The scripts run in a data folder
**outside the repository** that holds:

| PFF file | name expected by the scripts | SHA-256 of the copy used |
|---|---|---|
| `Tracking Data/3839.jsonl.bz2` (29.97 fps) | `raw/3839.jsonl.bz2` | `9659e3bc94f0445413a443601da62100224b0f7f0d7fcd464fada12968fc2bf4` |
| `Event Data/3839.json` | `raw/3839_events.json` | `872df536145574a6e487630d9b35b2efe469bbccbf88573347b09708b3cfdc71` |
| `Metadata/3839.json` | `raw/3839_metadata.json` | `a1ff32c90d0d0e46e2fb8c3658680deeb4cb70c866c8a4dcca111ce529d583e3` |
| `Rosters/3839.json` (optional, player names in the viewer) | `raw/3839_rosters.json` | list of `player.nickname`, `shirtNumber`, `team.name`; the copy used held only these fields |

`.gitignore` in this folder keeps those names and every output out of git, in case someone runs the
scripts here by mistake.

## Steps

Run from the data folder, with the repository's Python environment (numpy; scikit-learn is not needed):

```
python <repo>/experiments/possession_v2/pff_viewer/convert_pff.py 3839    # -> 3839_match.npz
python <repo>/experiments/possession_v2/pff_viewer/run_pff.py 3839        # -> 3839_labels.npz, 3839_summary.json
python <repo>/experiments/possession_v2/pff_viewer/analyse_pff.py 3839    # -> 3839_analysis.json
python <repo>/experiments/possession_v2/pff_viewer/make_viewer.py 3839    # -> viewer_3839.html (about 5.5 MB)
```

| script | what it does |
|---|---|
| `convert_pff.py` | PFF tracking to our arrays at 25 fps on the video clock, from the first kick-off to the end of the second half. Players: PFF's smoothed positions (seen or estimated off screen), one slot per team and shirt number. Ball: PFF's smoothed ball only where PFF marks it `VISIBLE`, otherwise missing (our models were trained with ball gaps, never with filled-in balls); PFF's estimate is kept separately for the viewer only. Linear interpolation between neighbouring PFF frames, none across holes longer than 3 PFF frames. Corner origin (x 0-105 m, y 0-68 m) as in `possession/features.py`. |
| `run_pff.py` | The decision steps of `possession.run211` when no second camera is given (noise gate on the raw tracking, goalkeeper team check, v2.1 or smoothed v2.3 path, frozen bundles), called directly on the arrays because `run211` itself reads the competition's EPTS files. Periods come from PFF's metadata. Builds the proxy reference and scores it with `possession/evaluate.py` (the organisers' metric code). |
| `analyse_pff.py` | Splits the disagreement: metric parts, kinds of disagreement, agreement with and without a visible ball, dead-ball periods found or missed and their start / end offsets, spell counts and lengths, the longest disagreement stretches with the match clock. Description only. |
| `make_viewer.py`, `viewer_template.html` | One HTML file, no network: pitch animation (5 fps, interpolated; filled ball = visible to the algorithm, dashed = PFF's estimate the algorithm does not get), match clock, our label and the proxy, model probabilities, last PFF event, ±20 s zoom, whole-match strips, the longest disagreements as jump links, and "Dakikaya git" (half + match clock) to line it up with the on-screen clock of a replay. Text in Turkish. |

Proxy reference (`run_pff.reference`): after an on-the-ball event the ball belongs to that player's team until
the next event; after `OUT` (ball out of play or goal) or `END` it is dead until the restart; before a free kick
or drop ball that does not follow `OUT`, the time from 0.5 s after the previous event to the restart is dead;
outside the halves it is dead. PFF's event times and definitions are not the organisers' labels.

## Result on game 3839 (12 Nov 2026; Python 3.13.18, numpy 2.5.3)

Conversion: 176,979 PFF frames -> 148,895 frames at 25 fps (70,961 first half, 76,188 second half,
1,746 between the halves); 31 player slots; on average 22.0 players present; ball visible in 41.2% of the
in-play frames. Path v2.1 (ball noise 0.002 m), goalkeeper check moved nothing.

Agreement with the proxy (organisers' metric code): spellF1 0.629, macroF1 0.898, same label on 90.6% of
in-play frames; alive/dead F1 0.943; team accuracy when both are alive 0.943; transition F1 0.419 within
12 frames and 0.535 within 25 frames (precision 0.649, recall 0.455).

- Same label with the ball visible 96.1%, not visible 86.7%.
- Largest kind of disagreement: we say dead while the proxy says alive (5.4% of in-play frames). Of the
  frames the proxy calls alive, we call dead 1.1% when the ball is visible and 28.4% when it is not.
  Team exchanged while both alive 3.0%; alive in ours, dead in the proxy 1.0%.
- Dead periods longer than 2 s: 97 in the proxy, 92 of them mostly dead in ours; 85 in ours, 79 of them
  mostly dead in the proxy. Start offset (ours minus proxy) median -0.02 s (quartiles -1.05 / +0.12 s);
  end offset median +1.82 s (quartiles +0.23 / +4.38 s), i.e. we see the restart later.
- 236 possession spells in ours against 360 in the proxy (median home spell 9.8 s against 5.3 s). Spells
  are matched one to one, so the count alone caps spellF1 near 0.79 on this proxy.
- 92 disagreement stretches of at least 2 s hold 73.9% of the disagreeing frames; in 12 of the 15
  longest the ball is visible in at most 6% of the frames.

What this does not show: accuracy on the competition match (other camera, other tracking provider, other
ball visibility), or anything comparable with the DFL / Metrica validation numbers. Reasons for the
pattern above are inferences and are discussed in `docs/DENEY_KAYDI_TR.md`, K009.

The scripts above reproduce `3839_summary.json`, `3839_analysis.json`, both `.npz` files and the viewer
byte for byte from the repository location when run with `python -I`.
