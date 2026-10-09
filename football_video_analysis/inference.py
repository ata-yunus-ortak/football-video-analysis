"""Optional YOLO + ByteTrack adapter, deliberately absent from offline imports."""

import math
from pathlib import Path
from .tracks import file_sha256, validate_tracks
from .video import cv_modules


def estimate_translation(previous, current):
    cv2, np = cv_modules()
    old_gray = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)
    new_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    height, width = old_gray.shape
    mask = np.zeros_like(old_gray)
    border = max(1, round(width * 0.12))
    mask[:, :border] = 255
    mask[:, -border:] = 255
    points = cv2.goodFeaturesToTrack(old_gray, maxCorners=150, qualityLevel=0.2, minDistance=7, mask=mask)
    if points is None or len(points) < 5:
        return [0.0, 0.0], False
    new, status, _ = cv2.calcOpticalFlowPyrLK(old_gray, new_gray, points, None, winSize=(21, 21), maxLevel=2)
    if new is None or status is None:
        return [0.0, 0.0], False
    valid = status.reshape(-1).astype(bool)
    valid &= np.isfinite(new.reshape(-1, 2)).all(axis=1)
    if valid.sum() < 5:
        return [0.0, 0.0], False
    shift = (new - points).reshape(-1, 2)[valid]
    median = np.median(shift, axis=0)
    inliers = np.linalg.norm(shift - median, axis=1) < 3.0
    if inliers.sum() < 5 or inliers.mean() < 0.5:
        return [0.0, 0.0], False
    return np.median(shift[inliers], axis=0).astype(float).tolist(), True


def shirt_team(frame, bbox, colors):
    if not colors:
        return 0
    _, np = cv_modules()
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    # Small central upper crop limits grass contamination; still only a heuristic.
    left, right = max(0, round(x1 + (x2 - x1) * 0.25)), min(width, round(x1 + (x2 - x1) * 0.75))
    top, bottom = max(0, round(y1 + (y2 - y1) * 0.2)), min(height, round(y1 + (y2 - y1) * 0.5))
    if left >= right or top >= bottom:
        return 0
    color = np.median(frame[top:bottom, left:right].reshape(-1, 3), axis=0)
    distances = {int(team): float(np.linalg.norm(color - np.asarray(target))) for team, target in colors.items()}
    ordered = sorted(distances, key=distances.get)
    if abs(distances[ordered[0]] - distances[ordered[1]]) < 10:
        return 0
    return ordered[0]


def infer_tracks(video_path, model_path, config, max_frames=300, camera_motion=False, device="cpu"):
    config.validate()
    if type(max_frames) is not int or max_frames < 1:
        raise ValueError("max_frames must be a positive integer")
    video_path, model_path = Path(video_path), Path(model_path)
    if not video_path.is_file():
        raise ValueError("Input video does not exist")
    if not model_path.is_file() or model_path.suffix.lower() != ".pt":
        raise ValueError("Supply an existing trusted local .pt model; automatic downloads are disabled")
    # Local PyTorch model files are executable serialization: use trusted weights only.
    try:
        import supervision as sv
        from ultralytics import YOLO
    except ImportError as error:
        raise RuntimeError("Inference requires: python -m pip install -r requirements-inference.txt") from error
    cv2, _ = cv_modules()
    model = YOLO(str(model_path))
    names = {int(key): value for key, value in model.names.items()}
    if not {"player", "ball"}.issubset(names.values()):
        raise ValueError("Model needs exact class names 'player' and 'ball'; optional 'referee' and 'goalkeeper'")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise ValueError("OpenCV could not open the input video")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        cap.release()
        raise ValueError("Video metadata has no valid FPS; transcode to a constant-FPS clip first")
    tracker = sv.ByteTrack(frame_rate=max(1, round(fps)))
    frames, previous, offset, reference_valid = [], None, [0.0, 0.0], True
    try:
        while len(frames) < max_frames:
            success, frame = cap.read()
            if not success:
                break
            if camera_motion and previous is not None:
                shift, valid = estimate_translation(previous, frame)
                offset = [a + b for a, b in zip(offset, shift)]
                # If cumulative motion becomes uncertain, the fixed reference is lost.
                reference_valid = reference_valid and valid
            previous = frame
            detections = sv.Detections.from_ultralytics(model.predict(frame, conf=config.detection_confidence, device=device, verbose=False)[0])
            ball_ids = [i for i, class_id in enumerate(detections.class_id) if names[int(class_id)] == "ball"]
            ball = None
            if ball_ids:
                best = max(ball_ids, key=lambda i: float(detections.confidence[i]))
                ball = {"bbox": detections.xyxy[best].astype(float).tolist(), "confidence": float(detections.confidence[best])}
            selected = [names[int(class_id)] in ("player", "goalkeeper", "referee") for class_id in detections.class_id]
            import numpy as np
            tracked = tracker.update_with_detections(detections[np.asarray(selected, dtype=bool)])
            record = {"players": {}, "referees": {}, "ball": ball,
                      "camera_offset_px": offset[:], "camera_valid": reference_valid}
            for bbox, _, confidence, class_id, track_id, _ in tracked:
                role, player_id = names[int(class_id)], str(int(track_id))
                box = bbox.astype(float).tolist()
                item = {"bbox": box, "confidence": float(confidence), "role": role}
                if role == "referee":
                    record["referees"][player_id] = item
                else:
                    # Goalkeeper kits often differ: keep unknown unless explicitly configured.
                    item["team"] = config.team_overrides.get(player_id, 0 if role == "goalkeeper" else shirt_team(frame, box, config.team_colors_bgr))
                    record["players"][player_id] = item
            frames.append(record)
        if not frames:
            raise ValueError("Input video contains no decodable frames")
        data = {"schema_version": 1, "fps": fps, "width": previous.shape[1], "height": previous.shape[0],
                "frame_count": len(frames), "source": {"kind": "video", "sha256": file_sha256(video_path),
                "file_name": video_path.name, "camera_model": "cumulative_translation" if camera_motion else "assumed_static",
                "model_sha256": file_sha256(model_path), "max_frames": max_frames}, "frames": frames}
        return validate_tracks(data)
    finally:
        cap.release()
