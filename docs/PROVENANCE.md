# Public-data and asset provenance

| Published material | Origin | Scope |
|---|---|---|
| `football_video_analysis/*.py` | New implementation for this repository | MIT, repository contributors |
| `tests/*.py`, CI and documentation | New regression and publication work | MIT |
| `examples/synthetic_tracks.json` | Deterministic arithmetic in `demo.sample_tracks()` | Invented four-player scene, not derived from a match or model |
| `examples/synthetic_config.json` | `demo.demo_config()` | Invented image-to-pitch mapping |
| `examples/synthetic_summary.json` | Analysis of the invented sample | Expected software results, not accuracy evidence |
| `assets/synthetic-demo.svg` | `report.write_svg()` from synthetic results | Invented pitch snapshot and timeline |
| `assets/synthetic-demo.png` | `video.render_dashboard()` from the same sample | Invented pitch/report dashboard with explicit synthetic label |

The architecture was inspired by Abdullah Tarek / codeinajiffy's [football-analysis project](https://github.com/abdullahtarek/football_analysis) and [YouTube channel](https://www.youtube.com/@codeinajiffy), as acknowledged by the local tutorial-derived source. No original model training, new algorithm, benchmark result, or scientific accuracy is claimed. The local README's MIT statement did not by itself establish a complete source/data license trail, so original source was not copied into this publication directory. New code expresses the general workflow independently.

Excluded completely: original input/output match videos and screenshots, third-party training images/labels, trained weights, training runs, binary pickle tracking/camera caches, training notebooks and their outputs, OS/editor artifacts, and credentials. The notebook was not copied or used as a public artifact. No local pickle was deserialized during preparation. Public sample values come exclusively from the new generator, not aggregate private tracking data.

Reproduce the public files from the repository root:

```bash
python -m football_video_analysis demo --out outputs/demo
python -m football_video_analysis demo --render-video --out outputs/video-demo
```

The second command needs the optional video runtime. `outputs/demo/tracks.json`, `config.json`, `summary.json`, and `report.svg` are the sources for the public example files and SVG. `outputs/video-demo/dashboard.png` is the public PNG. The generated AVI is a local demonstration artifact and is not committed.

If adding a real clip later, record the provider, clip identifier, license, permission to redistribute, model provenance, FPS, calibration method, and any manual corrections. Existing exclusions do not grant rights to redistribute private data or model weights.
