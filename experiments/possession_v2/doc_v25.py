"""Apply the v2.5 documentation changes to TECHNICAL_DOCUMENT_V2.md (after the v2.5b verdict).
Usage: doc_v25.py USE_CLOCK(0/1)"""
import sys, json
from pathlib import Path
S = Path('/home/claude/sc')
use_clock = sys.argv[1] == '1'
b = json.loads(Path('/home/claude/work/exp_v25b.json').read_text())
bs = b['summary']
p = S / 'TECHNICAL_DOCUMENT_V2.md'
t = p.read_text()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


rep('# Possession v2.4 — technical document', '# Possession v2.5 — technical document')
rep('Submission file regenerated with `python -m possession.run24` (see Reproduction).',
    'Submission file regenerated with `python -m possession.run25` (see Reproduction).')
rep('''"v2.3 path"). Every model, feature, threshold and decoder choice was made on **external
matches**''', '''"v2.3 path"). The submitted version, `possession-v2.5`, also reads the **broadcast tracking**:
it aligns the broadcast frames to the tactical timeline''' + (''' (anchored on the match clock that
both videos show, read automatically by OCR)''' if use_clock else '') + ''' and fills tactical frames
whose ball is missing with the broadcast ball, but only when the two cameras agree closely where both
see the ball (Section 6). Every model, feature, threshold and decoder choice was made on **external
matches**''')
rep('''+0.072 with larger player error; on the reserved match 0.665 against 0.637 (Section 8). These
are agreement scores with other providers' labels on other matches, not competition scores.''',
    '''+0.072 with larger player error; on the reserved match 0.665 against 0.637. With simulated
broadcast streams the fill adds +0.024 when the broadcast tracking is accurate and changes nothing
when it is not (the gate closes) (Section 8). These are agreement scores with other providers'
labels on other matches, not competition scores.''')
rep('''| tactical video, broadcast video/ATD, homography | no (broadcast ATD tested, not selected) | see Section 9 |''',
    '''| broadcast ATD + broadcast homography `valid` flags | yes (v2.5) | aligned to the tactical frames; fills missing tactical balls behind an accuracy gate (Section 6) |
| tactical and broadcast video | ''' + ('''only the on-screen match clock (v2.5b) | automatic OCR of the clock every 5 s anchors the alignment; no other pixel is used |''' if use_clock else '''no | see Section 9 |''') + '''
| tactical homography | no | |''')
rep('''- **v2.3 path** (`possession/smooth.py`, `models/possession-v23.npz`).''',
    '''- **Broadcast ball fill (v2.5, `possession/fusion.py`, alignment from `possession/broadcast.py`).**
  The broadcast ATD is mapped to tactical frames per half''' + (''' starting from the lag given by the match
  clock (below) and refined''' if use_clock else ''' from the masked cross-correlation of the two
  ball tracks, refined''') + ''' in 60 s windows by matching the visible broadcast players to the
  tactical players of the same team; a broadcast frame is accepted only if at least 3 players lie within
  2 m (median), which rejects replays and close-ups. The fill is used only if, where both cameras have a
  ball, the median distance is at most **0.50 m** over at least 120 s, with at least 5% of the broadcast
  frames accepted (thresholds registered before any result; the distance includes the tactical error, so
  it bounds the broadcast error). Then only tactical frames without a ball are filled, never replacing a
  tactical ball, with a speed plausibility check against nearby tactical balls. The noise gate is
  measured on the raw tactical tracking before the fill.
''' + ('''- **Clock anchor (v2.5b, `possession/clocksync.py`, OCR `tools/possession_clock.py`).** Both videos
  show the match clock. An OCR pass (RapidOCR, one key frame every 5 s, top-left 45% x 22% of the
  picture, confidence 0.8; parameters registered before the provided videos were first read) gives
  (video time, clock) pairs; consistent runs of each video are paired by clock value, ambiguous values
  (first-half added time vs. second half) are skipped, and the median lag per half (>= 10 anchors,
  IQR <= 1.5 s) replaces the trajectory search; orientation and refinement then run around it (+-40
  frames). Without clock files the tracking-only alignment is used.
''' if use_clock else '') + '''- **v2.3 path** (`possession/smooth.py`, `models/possession-v23.npz`).''')
good, med, bad = bs['good'], bs['medium'], bs['bad']
rows_b = (f"| v2.5b: clock-anchored alignment (designed after one v2.5 alignment failure) | v2.5 rules on 16 NEW copies, not below v2.5, no more alignment failures | "
          f"good {good['v2_5b'] - good['v2_4']:+.3f} (v2.5 {good['v2_5'] - good['v2_4']:+.3f}), alignment failures {good['alignment_failures']['v2_5b']} vs {good['alignment_failures']['v2_5']} | "
          f"{'**yes**' if b['selected'] else 'no'} |")
rep('''| v2.4: noise gate choosing v2.1 or the v2.3 path (designed after the v2.3 result) | +0.010 over 24 FRESH copies and at most -0.005 on the original-type copies | +0.039, identical on the original-type copies | **yes** |''',
    '''| v2.4: noise gate choosing v2.1 or the v2.3 path (designed after the v2.3 result) | +0.010 over 24 FRESH copies and at most -0.005 on the original-type copies | +0.039, identical on the original-type copies | **yes** |
| v2.5: broadcast ball fill behind the accuracy gate | good broadcast >= +0.010, medium >= -0.005, bad >= -0.002 (16 fresh copies each) | +0.024 / +0.004 / 0.000 | **yes** |
''' + rows_b + '''
| v2.6: learned switch hazard -> frame-dependent switch cost | +0.010 on 8 fresh copies and not worse on >= 5 of 8 | +0.002, not worse on 4 of 8 | no |''')
rep('''The v2.1 bundle reproduced its earlier reserved-test values exactly (0.6253 and 0.7021).

## 9. Limitations''', '''The v2.1 bundle reproduced its earlier reserved-test values exactly (0.6253 and 0.7021).

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
but did no harm''' + ('''; v2.5b anchors the lag on the match clock to prevent this. On 16 new
copies with simulated clock readings (50-95% readable, 1-3% misread, added-time clocks repeated) the
good-regime means were v2.4 ''' + f"{good['v2_4']:.3f}, v2.5 {good['v2_5']:.3f}, v2.5b {good['v2_5b']:.3f}" + ''' with ''' + f"{good['alignment_failures']['v2_5']} and {good['alignment_failures']['v2_5b']}" + ''' alignment failures
(`possession-v25b-results.json`).''' if use_clock else '''. A clock-anchored variant (v2.5b) did not meet its registered rule
(`possession-v25b-results.json`).''') + '''

**Where the remaining error is (reporting only, validation matches).** On clean (uncorrupted)
tracking v2.1 scores 0.748; with the automatic-tracking corruption 0.610; with the same corruption but
no missing ball 0.700, so about two thirds of the loss comes from missing ball positions. Replacing
P(dead) by the provider labels raises 0.631 to only 0.647, replacing P(home | alive) raises it to
0.912: team decisions during play, not stoppages, limit the score. A learned switch hazard (v2.6)
did not help enough; better ball information (the broadcast fill) did.

## 9. Limitations''')
rep('''- **Not used by the submitted system:** video, broadcast camera, homography and Smart Tagging.
  No external data with comparable automatic tags exists, so any weighting of the tags had to
  be validated on simulated tags (next bullets) rather than tuned on the provided game.''',
    '''- **Not used by the submitted system:** Smart Tagging, the tactical homography and''' + (''' every video
  pixel except the clock readings.''' if use_clock else ''' the videos.''') + ''' No external data with comparable automatic tags exists, so any
  weighting of the tags had to be validated on simulated tags (next bullets) rather than tuned on the
  provided game.
- **The broadcast fill was validated on simulated streams only.** Whether the real broadcast tracking
  is accurate enough is decided at run time by the gate (median tactical-broadcast ball distance <=
  0.50 m); we have not seen that value. Real artefacts outside the simulator (zoom-dependent errors,
  replays flagged valid, partial views that confuse the team mapping) may make the gate open on a
  mapping that is wrong; the player-position acceptance check is the protection.''')
rep('''- **The broadcast camera was tested and not selected** (`possession-v4-plan.json`,''',
    '''- **The first broadcast attempt (v4) was not selected** (`possession-v4-plan.json`,''')
rep('''  -0.037 on DFL copies, +0.025 on Metrica copies): possession attribution is very sensitive to
  ball-player distances.''', '''  -0.037 on DFL copies, +0.025 on Metrica copies): possession attribution is very sensitive to
  ball-player distances. v2.5 therefore adds the accuracy gate.''')
rep('''```
python -m pip install -r requirements-possession.txt
python -m possession.run24 --data-dir <bundle root containing tactical/> --out <new folder>
python -m possession.validate <new folder>/submission.csv
```

`run.json` states which path the gate took. When it says `v2.1`, `python -m possession.run`
(the v2.1 system alone) writes the same file.''', ('''```
# optional clock readings (separate OCR environment, requirements-sync-lock.txt):
python -m tools.possession_clock --video <bundle>/tactical/BAR-ATH_tactical.mp4 --out <clock>/tactical
python -m tools.possession_clock --video <bundle>/broadcast/BAR-ATH_broadcast.mp4 --out <clock>/broadcast
''' if use_clock else '''```
''') + '''python -m pip install -r requirements-possession.txt
python -m possession.run25 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder>''' + (''' \\
    --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast''' if use_clock else '') + '''
python -m possession.validate <new folder>/submission.csv
```

`run.json` states which path the noise gate took and whether the broadcast fill was used. Without
broadcast files, or when the accuracy gate is closed, `python -m possession.run24` writes the same
file; when the noise gate also chose `v2.1`, so does `python -m possession.run`.''')
p.write_text(t)
print('ok', 'clock' if use_clock else 'no clock')
