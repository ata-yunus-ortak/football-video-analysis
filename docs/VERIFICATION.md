# Verification record

Local verification uses Windows, Python 3.10.11, NumPy 1.26.4 and OpenCV 4.10.0.84. This record distinguishes software checks from model validation.

Executed successfully:

```bash
python -m unittest discover -s tests -v
python -S -m football_video_analysis demo --out outputs/demo
python -m football_video_analysis demo --render-video --out outputs/video-demo
```

The 29 tests cover bounded/interior-only ball repair; initial and all-missing balls; expiring control carrying; visible loose balls; owner absence; nearest-player ambiguity; unknown teams; source-FPS speed/duration; adjacent movement segments; cumulative camera subtraction; invalid calibration; invalid FPS/boxes/frame counts; JSON-only loading and non-finite rejection; first/last-frame boundaries; private source fingerprints; input/output collision safeguards; deterministic CLI replay without site-packages; featureless optical-flow fallback; and AVI readback.

The video roundtrip decodes exactly 100 frames at declared 25 FPS, 960 × 640. The demo produces 41% team 1, 40% team 2, 19% unknown, and 81% known coverage, with status counts 77 observed / 2 interpolated / 2 carried / 19 unknown. Player 11 covers 4.95 synthetic meters at a maximum 4.5 km/h over 99 valid adjacent segments.

CI is configured for offline Python 3.10 and 3.12, and an OpenCV job on Python 3.10. A clean export of the 32 staged publication files also passed the offline suite with `python -S` (26 passed, 3 optional video tests skipped), the demo, and replay of the included sample. This catches accidental dependencies on untracked/private files and is distinct from a remote clone and hosted CI result. The publication audit found no forbidden model/video/cache/notebook files or credential/absolute-Windows-path pattern matches.

Not validated: real-footage detection/tracking, a `.pt` model, training, class/model quality, team accuracy, possession accuracy, camera estimation accuracy, real-world speed/distance accuracy, GPU/CUDA setup, full-match scale, real-time throughput or variable-frame-rate preservation. Optional YOLO/ByteTrack packages match the inspected local API versions, but no inference result is claimed without licensed/trusted weights and evaluation data. GitHub CI and a remote fresh clone can be confirmed only after publication.
