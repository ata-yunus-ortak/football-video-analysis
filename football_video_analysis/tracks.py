"""A validated JSON interchange format. Pickle files are never loaded."""

import hashlib
import json
import math
from pathlib import Path
import re


def finite_vector(value, size, name):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ValueError(f"{name} must contain {size} numbers")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in value):
        raise ValueError(f"{name} must contain finite numbers")
    return value


def validate_bbox(value):
    finite_vector(value, 4, "bbox")
    if value[0] >= value[2] or value[1] >= value[3]:
        raise ValueError("bbox must have positive width and height")


def validate_tracks(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported tracking schema; expected schema_version 1")
    fps = data.get("fps")
    if type(fps) not in (int, float) or not math.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be finite and positive")
    for field in ("width", "height"):
        if type(data.get(field)) is not int or data[field] <= 0:
            raise ValueError(f"{field} must be a positive integer")
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("Tracking data must have at least one frame")
    if type(data.get("frame_count")) is not int or data["frame_count"] != len(frames):
        raise ValueError("frame_count does not match the tracking frames")
    source = data.get("source")
    if not isinstance(source, dict) or source.get("kind") not in ("synthetic", "video"):
        raise ValueError("source.kind must be synthetic or video")
    if source["kind"] == "video" and not re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")):
        raise ValueError("A video cache requires the source file SHA-256 fingerprint")
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("Each frame must be an object")
        finite_vector(frame.get("camera_offset_px", [0, 0]), 2, "camera_offset_px")
        if type(frame.get("camera_valid", True)) is not bool:
            raise ValueError("camera_valid must be a boolean")
        for field in ("players", "referees"):
            objects = frame.get(field, {})
            if not isinstance(objects, dict):
                raise ValueError(f"{field} must be keyed by track ID")
            for track_id, obj in objects.items():
                if not isinstance(track_id, str) or not isinstance(obj, dict):
                    raise ValueError("Track IDs must be strings with object values")
                validate_bbox(obj.get("bbox"))
                if type(obj.get("team", 0)) is not int or obj.get("team", 0) not in (0, 1, 2):
                    raise ValueError("team must be 0 (unknown), 1 or 2")
        ball = frame.get("ball")
        if ball is not None:
            if not isinstance(ball, dict):
                raise ValueError("ball must be null or an object")
            validate_bbox(ball.get("bbox"))
    return data


def reject_constant(value):
    raise ValueError(f"Non-finite JSON constant is not supported: {value}")


def load_tracks(path):
    path = Path(path)
    if path.suffix.lower() != ".json":
        raise ValueError("Only JSON tracking caches are accepted; pickle is not supported")
    if path.stat().st_size > 20_000_000:
        raise ValueError("Tracking cache exceeds the 20 MB safety limit; use shorter clips")
    with path.open(encoding="utf-8") as handle:
        return validate_tracks(json.load(handle, parse_constant=reject_constant))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
