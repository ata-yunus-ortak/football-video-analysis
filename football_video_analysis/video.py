"""Optional OpenCV rendering; source timing is retained throughout."""

from pathlib import Path
from .tracks import file_sha256


def cv_modules():
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise RuntimeError("Video support requires: python -m pip install -r requirements-video.txt") from error
    return cv2, np


def synthetic_frame(data, frame):
    cv2, np = cv_modules()
    canvas = np.full((data["height"], data["width"], 3), (48, 34, 25), dtype=np.uint8)
    cv2.rectangle(canvas, (60, 110), (900, 518), (55, 95, 45), -1)
    cv2.rectangle(canvas, (60, 110), (900, 518), (160, 200, 160), 2)
    cv2.line(canvas, (480, 110), (480, 518), (160, 200, 160), 2)
    cv2.circle(canvas, (480, 314), 65, (160, 200, 160), 2)
    cv2.putText(canvas, "SYNTHETIC DEMO - invented tracks / no model inference", (30, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (225, 235, 250), 2, cv2.LINE_AA)
    return canvas


def annotate(frame, tracking, control, index, fps, synthetic=False):
    cv2, _ = cv_modules()
    colors = {0: (180, 180, 180), 1: (255, 180, 80), 2: (90, 130, 255)}
    for player_id, player in tracking.get("players", {}).items():
        box = list(map(round, player["bbox"]))
        color = colors[player.get("team", 0)]
        cv2.rectangle(frame, tuple(box[:2]), tuple(box[2:]), color, 2)
        label = f"ID {player_id} / T{player.get('team', 0)}"
        cv2.putText(frame, label, (box[0], max(16, box[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
        if "speed_kmh" in player:
            cv2.putText(frame, f"{player['speed_kmh']:.1f} km/h | {player['distance_m']:.2f} m", (box[0] - 15, box[3] + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (230, 235, 240), 1, cv2.LINE_AA)
    ball = tracking.get("ball")
    if ball:
        box = ball["bbox"]
        point = (round((box[0] + box[2]) / 2), round((box[1] + box[3]) / 2))
        cv2.circle(frame, point, 5, (255, 255, 255), -1)
        if ball.get("interpolated", False):
            cv2.circle(frame, point, 9, (0, 255, 255), 1)
    counts = {team: sum(row["team"] == team for row in control[:index + 1]) for team in (0, 1, 2)}
    label = f"{index / fps:.2f}s | T1 {counts[1]/(index+1):.0%}  T2 {counts[2]/(index+1):.0%}  unknown {counts[0]/(index+1):.0%} | {control[index]['status']}"
    height, width = frame.shape[:2]
    cv2.rectangle(frame, (0, height - 58), (width, height), (48, 34, 25), -1)
    cv2.putText(frame, label, (20, height - 32), cv2.FONT_HERSHEY_SIMPLEX, min(0.65, width / 1600), (230, 235, 245), 1, cv2.LINE_AA)
    cv2.putText(frame, "Heuristic proximity control / unvalidated estimates", (20, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 195, 210), 1, cv2.LINE_AA)
    if not synthetic:
        cv2.putText(frame, "HEURISTIC ESTIMATES", (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return frame


def render_video(output, data, result, source_video=None, preview=None):
    if source_video is not None:
        source_path = Path(source_video).resolve()
        if Path(output).resolve() == source_path or (preview and Path(preview).resolve() == source_path):
            raise ValueError("Video output/preview cannot overwrite the source video")
    if preview and Path(output).resolve() == Path(preview).resolve():
        raise ValueError("Video output and preview must be different files")
    cv2, _ = cv_modules()
    synthetic = data["source"]["kind"] == "synthetic"
    if synthetic and source_video is not None:
        raise ValueError("Synthetic tracks cannot annotate a real source video")
    if not synthetic and source_video is None:
        raise ValueError("A source video is required to render video tracking")
    cap = None
    if source_video is not None:
        if file_sha256(source_video) != data["source"]["sha256"]:
            raise ValueError("Video fingerprint differs from the tracking cache")
        cap = cv2.VideoCapture(str(source_video))
        if not cap.isOpened():
            cap.release()
            raise ValueError("Cannot open source video")
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        if abs(source_fps - data["fps"]) > 0.01 or int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) != data["width"] or int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) != data["height"]:
            cap.release()
            raise ValueError("Video metadata does not match the tracking cache")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() != ".avi":
        if cap:
            cap.release()
        raise ValueError("Use an .avi output path (MJPG codec)")
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"MJPG"), data["fps"], (data["width"], data["height"]))
    if not writer.isOpened():
        if cap:
            cap.release()
        raise RuntimeError("OpenCV could not open the MJPG video writer")
    try:
        for index, tracking in enumerate(result["frames"]):
            if synthetic:
                frame = synthetic_frame(data, tracking)
            else:
                success, frame = cap.read()
                if not success:
                    raise ValueError("Source video ends before the cached tracking frames")
            frame = annotate(frame, tracking, result["control"], index, data["fps"], synthetic)
            writer.write(frame)
            if preview and index == min(73, len(result["frames"]) - 1):
                Path(preview).parent.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(str(preview), frame):
                    raise RuntimeError("Could not write preview image")
    finally:
        writer.release()
        if cap:
            cap.release()
    return output


def render_dashboard(path, data, result):
    """Render a shareable report from the same data, without external art assets."""
    cv2, np = cv_modules()
    canvas = np.full((810, 1200, 3), (36, 21, 12), dtype=np.uint8)
    white, muted = (250, 243, 237), (202, 182, 165)
    colors = {0: (125, 103, 83), 1: (255, 180, 80), 2: (90, 130, 255)}

    def text(value, x, y, size=0.6, color=white, bold=False):
        cv2.putText(canvas, value, (x, y), cv2.FONT_HERSHEY_SIMPLEX, size, color, 2 if bold else 1, cv2.LINE_AA)

    synthetic = data["source"]["kind"] == "synthetic"
    text("SYNTHETIC DEMO / NO MODEL INFERENCE" if synthetic else "VIDEO TRACKING / HEURISTIC ESTIMATES", 42, 45, 0.55, colors[1])
    text("Football video analysis", 42, 95, 1.15, bold=True)
    text("Tracking  >  bounded ball repair  >  control estimates  >  calibrated movement", 42, 128, 0.58, muted)
    cv2.rectangle(canvas, (42, 154), (862, 604), (54, 58, 17), -1)
    index = min(73, len(result["frames"]) - 1)
    text(f"Pitch snapshot / frame {index} / {index / data['fps']:.2f} s", 68, 183, 0.5, (207, 218, 187))
    line_color = (149, 167, 120)
    cv2.rectangle(canvas, (70, 204), (834, 576), line_color, 2)
    cv2.line(canvas, (452, 204), (452, 576), line_color, 2)
    cv2.circle(canvas, (452, 390), 51, line_color, 2)
    for left, right in ((70, 190), (714, 834)):
        cv2.rectangle(canvas, (left, 293), (right, 487), line_color, 2)
    for left, right in ((70, 108), (796, 834)):
        cv2.rectangle(canvas, (left, 347), (right, 433), line_color, 2)
    calibration = result["summary"]["settings"]["calibration"]
    owner = result["control"][index]["player_id"]
    for player_id, player in result["frames"][index].get("players", {}).items():
        point = player.get("pitch_position_m")
        if calibration and point is not None:
            metric = calibration["pitch_points_m"]
            xmin, xmax = min(p[0] for p in metric), max(p[0] for p in metric)
            ymin, ymax = min(p[1] for p in metric), max(p[1] for p in metric)
            x, y = round(70 + (point[0] - xmin) / (xmax - xmin) * 764), round(204 + (point[1] - ymin) / (ymax - ymin) * 372)
        else:
            box = player["bbox"]
            x, y = round(70 + (box[0] + box[2]) / 2 / data["width"] * 764), round(204 + box[3] / data["height"] * 372)
        cv2.circle(canvas, (x, y), 14, colors[player.get("team", 0)], -1, cv2.LINE_AA)
        text(player_id[:4], x - 9, y + 5, 0.4, (36, 21, 12), True)
        if player_id == owner:
            cv2.circle(canvas, (x + 23, y), 5, white, -1, cv2.LINE_AA)
    text("Invented trajectories; no detector/tracker benchmark." if synthetic else "Configured projection; review calibration and camera assumptions.", 68, 559, 0.45, (207, 218, 187))
    summary, control = result["summary"], result["summary"]["control"]
    text("CLIP METADATA", 900, 185, 0.5, muted)
    text(f"{summary['duration_seconds']:.1f} seconds", 900, 224, 0.83, bold=True)
    text(f"{data['frame_count']} frames / {data['fps']:g} FPS", 900, 251, 0.5, muted)
    text("CONTROL / ALL FRAMES", 900, 302, 0.48, muted)
    text(f"Team 1 / {control['team_1_percent_all_frames']:.0f}%", 900, 339, 0.7, colors[1])
    text(f"Team 2 / {control['team_2_percent_all_frames']:.0f}%", 900, 374, 0.7, colors[2])
    text(f"Unknown / {100 - control['known_coverage_percent']:.0f}%", 900, 409, 0.7, muted)
    text("BALL REPAIR", 900, 460, 0.5, muted)
    text(f"{summary['ball_interpolated_frames']} interpolated frames", 900, 494, 0.56)
    text("Long/boundary gaps stay missing.", 900, 521, 0.39, muted)
    text("Control timeline", 42, 638, 0.65, bold=True)
    text("Blue: team 1 / orange: team 2 / slate: unknown / dots: inferred", 263, 638, 0.44, muted)
    width = 1100 / len(result["control"])
    for row in result["control"]:
        x1, x2 = round(42 + row["frame"] * width), round(42 + (row["frame"] + 1) * width)
        cv2.rectangle(canvas, (x1, 653), (x2, 682), colors[row["team"]], -1)
        if row["status"] in ("interpolated", "carried"):
            cv2.circle(canvas, (round((x1 + x2) / 2), 667), 2, (36, 21, 12), -1)
    text("0.0 s", 42, 707, 0.45, muted)
    text(f"{summary['duration_seconds']:.1f} s", 1104, 707, 0.45, muted)
    if summary["players"]:
        values = " / ".join(f"ID {player_id}: {stats['distance_m']:.2f}m, {stats['max_speed_kmh']:.1f}km/h" for player_id, stats in summary["players"].items())
        text(values, 42, 752, 0.44)
    text("Tutorial-inspired engineering portfolio / " + ("Synthetic values verify execution, not real-world accuracy." if synthetic else "Heuristic control and movement require independent validation."), 42, 788, 0.42, muted)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), canvas):
        raise RuntimeError("Could not write dashboard image")
