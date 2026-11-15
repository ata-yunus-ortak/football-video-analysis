# Data, models and tools used by the possession system

Everything the submitted system (`possession/`) was built from is public, so the organisers can
access it. No raw or prepared data is stored in this repository; the three model files under
`models/` contain only decision-tree arrays (two bundles) and the weights of one small network.

| asset | where | licence / terms | how it is used | redistributed here? |
|---|---|---|---|---|
| Sportec/DFL open tracking and event data (7 Bundesliga matches; Bassek et al. 2025, *Scientific Data*, doi:10.1038/s41597-025-04505-y) | Hugging Face mirror `pysport/idsse-data`, commit `a715a38dfbaf5f58e431727c2b78d174101a703c`; every file is pinned by URL, size and git blob id in `sportec-data-plan.json` | CC BY 4.0 | training and validation: tracking plus the provider's per-frame `BallStatus` / `BallPossession`; match J03WMX reserved as a final test, not downloaded or used by the process that built the release and trained its weights (a team member used it while he designed the network of the second model) | no (only models trained on it: `models/possession-v2.npz`, `models/possession-v23.npz`, `models/possession-tcn-v215.npz`) |
| Metrica Sports sample data, games 1-3 | github.com/metrica-sports/sample-data, commit `e706dd506b360d69d9d123d5b8026e7294b13996` | no licence file; README: "Please be responsible with the use of this data. If you use it for anything public, please aknowledge the source." | validation (games 1-2) and reserved test (game 3) with possession/stoppage proxy labels derived automatically from the published events | no |
| Competition bundle (BAR-ATH tracking, videos, Smart Tagging, homography) | provided to registered teams | competition licence, not redistributable | inference input only, run locally by the team; never committed, never given to an AI service by the v2 process | no |
| Organisers' published constants (graded windows in `games.py`, home = Barcelona and aggregate ATD statistics in `DATA.md`) | organiser repository | — | play blocks, home/away check, ranges of the corruption simulator. The second-half kick-off frame in `FAQ.md` is used only by `possession.run211`, which is not the release | — |
| Organisers' scorer (`evaluation/possession_metrics.py`) | organiser repository | repository licence | re-implemented in `possession/official_metrics.py` for external validation | — |
| numpy 1.26.4, scipy 1.11.4, pandas 2.1.4 (inference); scikit-learn 1.9.1 (training of the trees only); jax 0.12.0.1 and optax 0.2.9 (training of the network only) | PyPI | BSD-3-Clause; JAX and Optax Apache-2.0 | runtime / training | no |
| RapidOCR (optional clock reading, `requirements-sync-lock.txt`) | PyPI | Apache-2.0 | reads the on-screen match clock of both provided videos, locally | no |

Not part of the submitted system (earlier or experimental work, kept for the record): SkillCorner
open data (`SKILLCORNER_LICENSE.txt`), SoccerNet, RF-DETR/SAHI/Supervision; see
`docs/LISANS_DURUMU_TR.md`. PFF FC 2022 World Cup data (one game, obtained through PFF FC's sign-up form;
no licence text published): used only to watch the frozen release on an external match (log entry K009,
`experiments/possession_v2/pff_viewer/`) and, after the decision of K010 had been taken, to report the
unselected combination on the same game; not for training, tuning or selection, and not redistributed.
The weights a team member trained for his temporal convolution network (branch `mtah-possession` of
the team repository; on the six DFL training matches below, and on five of them for the rows scored on
the sixth) were averaged with the release's probabilities in a registered validation, and that
combination was not selected (log entry K010, `possession-v213-plan.json`,
`possession-v213-results.json`). Those weights are not loaded by the release and are not in this
branch.

**Players added from the broadcast tracking (v2.16).** No new data and nothing trained: the step is a fixed rule
(`possession/playerfill.py`) validated on new corrupted copies of the validation matches below with a simulated
second camera (`possession-v216-plan.json`).

**Second model of the release (v2.15 and v2.16).** Design, features and NumPy inference: the same team member
(branch `mtah-possession`, commit `167dc7b`; byte copies under `possession/tcn/`). He developed the
recipe on all seven DFL matches and Metrica games 1-3. The weights in `models/possession-tcn-v215.npz`
(three members) were trained for the release with `experiments/possession_v2/v214/tcn_jax.py` on the six
DFL training matches below and nothing else: twelve corrupted copies of every half, six made with his
corruption simulator and six with ours, the provider's labels as for the trees. Selection:
`possession-v215-plan.json`, `possession-v215-results.json` (log entry K013; the attempt before it, with the same
weights and equal weighting, is `possession-v214-*`, log entry K012).

## Labelled data: what, by whom, how much

Nothing below comes from the provided match.

**Training (both model bundles): six DFL matches.** Labels are the provider's own per-frame flags
inside the official tracking files: `BallStatus` (0 = ball out of play) and `BallPossession`
(1 = home, 2 = away). They were mapped mechanically (`tools/sportec_prepare.py`): `BallStatus` 0 ->
`D`, otherwise possession 1 / 2 -> `H` / `A`. Nobody in the team labelled or corrected a frame.

| match | frames (25 fps) | `H` | `A` | `D` | role during model selection |
|---|---|---|---|---|---|
| J03WOH | 137,214 | 39,126 | 32,819 | 65,269 | training |
| J03WOY | 142,536 | 37,812 | 38,474 | 66,250 | training |
| J03WPY | 146,211 | 51,192 | 30,268 | 64,751 | training |
| J03WQQ | 142,345 | 37,030 | 47,322 | 57,993 | training |
| J03WN1 | 141,561 | 36,421 | 31,956 | 73,184 | validation |
| J03WR9 | 146,810 | 53,239 | 32,077 | 61,494 | validation |
| total | 856,677 (about 9.5 hours) | 254,820 (29.7%) | 212,916 (24.9%) | 388,941 (45.4%) | the released bundles are trained on all six |

The files cover the two halves only (91.5-97.9 minutes per match); `D` is every frame the provider
marks as ball out of play. A training row is every sixth frame of three independently corrupted
copies of a match, also with the teams exchanged: 856,678 rows per bundle (recorded in the bundle
cards). The network of the second model reads every second frame of twelve corrupted copies of
every half of the same matches. The seventh match of the
dataset, J03WMX, is reserved as a final test; the process that built the release and trained its
weights has not downloaded it (a team member used it while he designed the network of the second
model; the released weights were trained without it).

**Validation and reserved test only: Metrica sample games 1-3.** The dataset has no possession
labels. Proxy labels were computed automatically from the provider's published event files
(`experiments/possession_v2/metrica_labels.py`): a team has the ball from its on-ball event until an
opponent's recovery or a stoppage; a stoppage runs from ball out / foul / goal to the next set
piece; frames whose state cannot be derived are unscored. Events with the same start frame are
kept in the order of the provider's file (a set piece before the pass that takes it; explicit
since log entry K005). Games 1-2 were used for validation and
game 3 as a reserved test scored once per frozen system. No Metrica frame was used to train a
released model (a candidate that did, v2.8, was not selected).

**Hand labelling by the team: none** in the v2 process.

AI assistance: the v2 code was written with a hosted AI coding assistant that worked only on source
code, the public external datasets above and aggregate external results. Provided-match files,
extracts and frame-level outputs were not given to it. The earlier process and
its remediation are disclosed in `TECHNICAL_DOCUMENT_V2.md` Section 2 and `REMEDIATION.md`.
