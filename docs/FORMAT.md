# Configuration and tracking interchange

All coordinates use floating-point image pixels. Bounding boxes are `[left, top, right, bottom]` with positive area. Track IDs are strings. Teams are 0 (unknown), 1 or 2. Frames must be contiguous observations, starting at frame 0, at the declared constant FPS. Missing players are omitted; a missing ball is `null`.

The JSON root contains `schema_version: 1`, a positive `fps`, positive integer `width` and `height`, `frame_count`, `source`, and a nonempty `frames` array. The count must equal the array length. JSON NaN and Infinity are rejected. Only `.json` files up to 20 MB are read; no pickle loader exists.

```json
{
  "schema_version": 1,
  "fps": 25.0,
  "width": 960,
  "height": 640,
  "frame_count": 1,
  "source": {"kind": "synthetic", "description": "Invented illustration"},
  "frames": [{
    "players": {"11": {"bbox": [234, 240, 254, 278], "team": 1}},
    "referees": {},
    "ball": null,
    "camera_offset_px": [0, 0],
    "camera_valid": true
  }]
}
```

A real cache uses `source.kind: "video"` and `source.sha256` containing 64 lowercase hexadecimal characters from the complete source video file. Inference also records model SHA-256, a file name, camera model and frame limit. These fingerprints identify files; they do not prove ownership or authenticity. Replaying JSON does not require the source video or model. Rendering requires the original video hash and matching FPS/dimensions.

`camera_offset_px` is cumulative displacement from the calibration reference frame, in the observed image direction. The analysis subtracts it before projection. It must not be an independent per-frame delta. A false `camera_valid` suppresses metric positions for that frame and breaks adjacent-segment continuity. This single-reference translation model cannot represent changing perspective.

## Settings

| Field | Meaning |
|---|---|
| `max_ball_gap_frames` | Maximum complete interior gap to interpolate; zero disables repair |
| `possession_grace_frames` | Frames a visible previous owner may retain control while the ball is missing |
| `max_player_ball_distance_px` | Maximum ball-center to bbox foot-corner distance |
| `ambiguity_margin_px` | Minimum advantage needed over the second-nearest eligible player |
| `max_speed_kmh` | Segment exclusion threshold; rejected segments are counted |
| `team_colors_bgr` | Empty, or both `"1"` and `"2"` BGR triples for optional image inference |
| `team_overrides` | Optional mapping of string track IDs to team 1 or 2 |
| `calibration` | Null, or four matching convex `pixel_points` and `pitch_points_m` |
| `detection_confidence` | Optional inference confidence threshold in (0, 1] |

The [synthetic configuration](../examples/synthetic_config.json) maps image coordinates (60,110), (900,110), (900,518), (60,518) to a 105 × 68 m rectangle. This is an invented orthographic scene. For a real camera, identify four known coplanar landmarks, provide their measured pitch coordinates in matching perimeter order, and check the projection independently. The calibration does not need to encompass the entire pitch. Projected points outside its image quadrilateral are withheld.

Thresholds are in frames or pixels and need adjustment for source FPS/resolution. The default gap of 3 frames is 120 ms at 25 FPS; the default grace of 2 is 80 ms. Real teams do not have stable semantic IDs across independent tracker runs; overrides must be reviewed per run. No global player identity is inferred.

## Reports

`control.csv` has frame, time in seconds, team, player ID and status (`observed`, `interpolated`, `carried`, `unknown`). `movement.csv` has per-player frame records; metric values are blank without calibration or valid adjacent segments. `summary.json` stores settings, source type, timings, coverage, both all-frame and known-frame control percentages, interpolation count, rejected movement segments and per-player metric summaries.

Movement totals sum only adjacent valid segments. A `valid_segments` value of zero means no movement estimate can be established; the accumulated zero must not be interpreted as proof that the player stood still. Full absence of calibration yields an empty summary `players` object. Inference confidence is retained in raw tracking, while analysis uncertainty is represented through explicit states rather than statistical confidence intervals.
