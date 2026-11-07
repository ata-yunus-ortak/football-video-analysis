# Remediated external-fixture possession model

**Current development:** see [external evaluation and rule precedence](docs/OTONOM_GELISTIRME_TR.md).
The 3 November organizer clarification prohibits comparing supplied-match
outputs against its video. The earlier Barcelona overlay review services
(8776/8777) have been stopped; their documentation below is historical.
New development uses external fixtures, with the baseline unchanged.

**Team development:** start with [TEAM_START_TR.md](TEAM_START_TR.md).
This branch contains the current clean development code; the repository's
default portfolio branch is a separate project history. Use the branch-specific
clone command in the team guide.

This is a new local source repository. It contains no supplied-match images,
annotations, review payloads, prediction rows, learned patch models, or earlier
public-window scores. It is not a claim that all remediation conditions are
already complete: see REMEDIATION.md.

The frozen model consumes automatic EPTS x/y coordinates and team metadata.
Its parameters and policy were reselected on other fixtures. It outputs H/A/X;
it does not yet include an independently selected image or dead-ball classifier.
Earlier affected visual/throw/referee prototypes are excluded from this release.
New experimental image modules under `development/` remain separate from frozen inference.

The `develop/dead-ball-data-audit` branch starts the next development stage in
`development/`, with a pinned external data plan and tracking/event coverage
tools. This code is unselected and does not alter frozen inference. See
[the Turkish development guide](docs/GELISTIRME_TR.md).

The experimental motion pipeline can additionally consume automatic SET PIECES
tags and measured waiting/restart evidence to produce candidate D intervals.
It does not label whole tag spans or missing ball frames as D. This layer is
not externally selected or part of the frozen release; see
[the dead-ball development notes](docs/DURAN_TOP_KATMANI_TR.md).
An optional LONG BALL layer finds measured fast, long-distance runs inside
automatic tag spans and suppresses proximity-only ownership during flight.
See [the long-ball notes](docs/UZUN_TOP_KATMANI_TR.md); this is also unselected.

The `feature/reachability-vision` branch adds optional symmetric arrival-time
support for ambiguous motion-contact candidates and separate local RF-DETR /
SAHI / ByteTrack measurement tools. Clock matching produces conservative
candidate intervals only. None of these changes is part of the frozen release;
see [the staged implementation plan](docs/UYGULAMA_PLANI_TR.md).
The experimental tactical-first hybrid layer can prefer individually observed
broadcast measurements after validated alignment, visibility, camera and geometry
gates. Other players retain tactical measurements; source continuity prevents
artificial motion/contact at handoffs. Current review mappings remain ineligible.
See [the hybrid source policy](docs/HIBRIT_KAYNAK_POLITIKASI_TR.md).
Local image measurements now include camera-safe person track keys, pixel
motion and optional same-source homography projections for feet candidates.
`tools.vision_preview` renders the registered external/synthetic observations
to a local video; see [image-module instructions](docs/GORUNTU_ISLEME_TR.md).
People/ball candidates are not yet verified players, teams or in-play ball.
Professional broadcast sample acquisition and the staged tracking integration
are documented in [the SoccerNet plan](docs/SOCCERNET_ASAMALARI_TR.md).
`python -m tools.match_analysis` is the experimental project image-analysis
entry point: it accepts a registered video/config or a completed detector run
and exports source-bound image measurements. The review gallery can consume
these project outputs via `--project-analysis`. Person roles/teams remain unknown
and these measurements do not yet update possession; see
[project image integration](docs/GORUNTU_ENTEGRASYONU_TR.md).
Optional `--ball-tracking-config ball-tracking-plan.json` associates ball
candidates over time and separates detections from short motion forecasts.
It does not identify the in-play ball or infer possession; see
[temporal ball tracking](docs/ZAMANSAL_TOP_TAKIBI_TR.md).
`tools.ball_support_experiment` adds read-only automatic-tracking projection
support and optional exact-pair second-camera corroboration. Missing support
preserves image output. Current external gallery runs lack independent automatic
tracking; enabled and two-camera gates have synthetic checks only. See
[tracking-supported ball candidates](docs/TRACKING_DESTEKLI_TOP_TR.md).
The separate `tools.visual_possession_experiment` entry point now implements
experimental **video-led** H/A/X ownership: automatic tracking supplies player
ID/team association only, while current image ball/person observations decide
control candidates. Verified matching broadcast images are preferred, with
tactical fallback and per-player provenance. It does not consume the tracking
ball or the frozen model's owners. Synthetic routing checks pass; real identity,
calibration, camera alignment and possession validation remain outstanding. See
[video-led ownership](docs/GORUNTU_TEMELLI_SAHIPLIK_TR.md).

## Local tracking viewer

The requested first five match minutes are rendered progressively at
`http://127.0.0.1:8777/`, with a large selected-player candidate label and
highlight. This longer review uses the already registered native detector mode,
not the earlier short SAHI demo. Processing status distinguishes ready chunks
from a completed five-minute clip; see [five-minute local review](docs/ILK_BES_DAKIKA_YEREL_TR.md).

The explicit user-requested Barcelona local review is available on this
workstation at `http://127.0.0.1:8776/`: two short annotated videos, metadata
identity candidates and separate strict/assumption-only control displays.
The unvalidated broadcast mapping remains ineligible for final ownership.
See [local integrated review](docs/YEREL_ENTEGRE_INCELEME_TR.md).

Run `TRACKING-IZLE.cmd` on this workstation to view raw tracking circles,
scalar speeds and derived velocity arrows beside the local tactical video.
`YAYIN-IZLE.cmd` opens the broadcast video with its own ATD metadata/tracking
and per-frame homography CSV on port 8767. The details show matrix validity and
the selected point's ground-plane pixel projection. Neither viewer merges the
two cameras or runs image inference. Broadcast Smart Tags are not supplied by
the tactical timeline.
An optional source-bound `--clock-audit` report enables same-frame tracking
point overlays on the local video; see [projection review](docs/IZDUSUM_INCELEME_TR.md).
This checks native clock structure, not independent image alignment or identity.
`ESLESME-IZLE.cmd` opens the paired review on port 8768 after automatic clock
readings and tracking geometry produce candidate mappings. Both videos and
their separate tracking fields follow the tactical clock. Unmapped intervals
pause/hide the broadcast source. This unselected review tool does not fuse
possession; see [paired-view instructions](docs/ESLESTIRME_TR.md).
The viewer is read-only, uses loopback only, and does not run or tune the model.
Its Smart Tagging view lists all automatic source events, filters their fields,
and links event intervals to local video without recording human corrections.
See [viewer instructions](docs/TRACKING_IZLEYICI_TR.md). For synthetic UI testing:
`python -m tools.tracking_viewer --demo --port 8766`.

## Install and run

Python 3.10 or later:

```
python -m pip install -r requirements.txt
python -m clean_model.run --meta /path/to/automatic_atd.xml --tracking /path/to/automatic_atd.txt --model model.json --out /new/private/output
```

The output directory must not exist. The CSV has one row per input frame and
columns `frame,label`, indexed from zero. Source hashes are verified before
reading the supplied measurements. No video, public reference, manual review
file, or old prediction file is an inference input.

Raw EPTS coordinates are normalized by the metadata field dimensions. The third
raw channel is speed, not ball height. Missing coordinates stay missing unless
the externally selected bounded interpolation rule permits a gap. Temporal
durations are transferred from 10 fps calibration with ceiling rounding.

## External selection

The dataset is [SkillCorner Open Data](https://github.com/SkillCorner/opendata),
pinned at the commit in external-selection.json. Twelve previously accessed
external matches are training/calibration data and four are validation data.
They are not described as new held-out data. Four additional fixtures were
reserved before their tracking was downloaded, for a post-freeze proxy check.

217 candidates were compared on validation: nearest ownership and slot/team
confirmation policies with distance, separation, duration, hold and interpolation
choices derived from the external training distribution. Selection uses mean
automatic-provider team-spell agreement, then H/A macro F1. These are not the
official challenge scores and the provider targets are not human ground truth.

The source for selection is clean_model/select.py. tools/fresh_check.py downloads
and verifies public LFS content and performs the post-freeze check. The source
registry records IDs, raw repository provenance and local integrity hashes.
An independent D/visual target is not available in that tracking-only study;
unknown provider labels are not relabelled as D.

To reconstruct external development data and re-run selection in a separate
output directory (large public downloads; never use the supplied match):

```
python -m tools.development_data --registry external-selection.json --out /new/external-data
python -m clean_model.select --plan /new/external-data/local-plan.json --out /new/external-selection
```

Preparation preserves measurement values and missingness. Local serialized NPZ
hashes and path-dependent plan hashes can differ across a rebuild; pinned raw
LFS content hashes verify the public source. Compare selected policy and
parameters rather than claiming the entire metadata JSON is byte-identical.

To repeat only the already-frozen external check without selecting again:

```
python -m tools.fresh_check --plan external-selection.json --model model.json --out /new/external-check
```

The completed four-match check gave mean automatic-provider spell proxy
0.17491946 and H/A macro F1 0.63910663. These are not official challenge scores.
The model was not changed after these results.

Run synthetic integrity checks with:

```
python -m unittest discover -s tests
```

Match data and generated predictions must remain outside the source repository.
Only source, synthetic tests, aggregate external checks and documentation are
published. Do not train/select against the supplied
fixture or revive the deleted annotation-derived artifacts.
