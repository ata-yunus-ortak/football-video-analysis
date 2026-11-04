# Clean development instructions

- Read `README.md`, `TECHNICAL_REPORT.md`, `REMEDIATION.md`, `model.json`,
  `docs/GELISTIRME_TR.md` and the latest entry in `docs/DENEY_KAYDI_TR.md`.
- Keep `main` and the frozen `model.json` / `clean_model/` bytes as the baseline.
  On the shared GitHub repository, its default `main` is an older portfolio
  history: use tag `baseline/remediated-external-v1` (commit `8962134`) as the
  clean baseline, and develop from `develop/dead-ball-data-audit`.
  Develop new experiments on a separate branch under `development/`. A later
  selected release needs its own explicit version, source freeze and provenance.
  Do not refresh baseline hashes merely to bypass its integrity checks.
- Make all model, threshold and version choices on permitted external fixtures.
  Do not read/recover legacy supplied-fixture annotations, derivatives, match
  images or old public scores for development. The supplied public window is
  only a final check after a new pipeline has been selected and frozen; do not
  start another selection cycle from that check.
- Keep raw match data, frame-level arrays and predictions outside this repository.
  Record source commit/content hashes, fixture splits, settings and selection
  rationale for each experiment. Record uncertainty about previous exposure.
- X, missing coordinates and out-of-pitch point estimates are not D targets.
  Event-paired intervals are partial proxies, not exhaustive D truth. D001 found
  zero finite ball coordinates in all 78 paired Metrica stoppage intervals; do
  not turn this source-specific absence into a validated general D classifier.
- Keep D, ball-reliability and possession-transition experiments separate.
  Compute tracking features without event/label inputs. Before D promotion,
  establish evaluable D/live-play targets and validate timing boundaries.
- For changes to adapters/features/auditing, run
  `python -m unittest discover -s tests -v`. Keep frozen-source integrity checks.
- Do not claim all organizer/remediation conditions are complete; provider-side
  conversation/upload cleanup remains unverified in the handoff.
