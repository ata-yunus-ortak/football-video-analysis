"""Bounded ball repair, conservative proximity control, calibrated movement."""

from collections import Counter
from copy import deepcopy
from .geometry import PitchTransform, center, distance, foot
from .tracks import validate_tracks


def interpolate_ball(frames, max_gap):
    """Fill complete interior gaps only; preserve observed boxes and endpoints."""
    result = deepcopy(frames)
    observed = [i for i, frame in enumerate(result) if frame.get("ball") is not None]
    for left, right in zip(observed, observed[1:]):
        gap = right - left - 1
        if not 0 < gap <= max_gap:
            continue
        start, end = result[left]["ball"]["bbox"], result[right]["ball"]["bbox"]
        for index in range(left + 1, right):
            ratio = (index - left) / (right - left)
            result[index]["ball"] = {"bbox": [a + ratio * (b - a) for a, b in zip(start, end)], "interpolated": True}
    return result


def nearest_player(players, ball_bbox, max_distance, ambiguity_margin):
    position = center(ball_bbox)
    candidates = []
    for player_id, player in players.items():
        if player.get("team", 0) not in (1, 2):
            continue
        bbox = player["bbox"]
        value = min(distance(position, (bbox[0], bbox[3])), distance(position, (bbox[2], bbox[3])))
        if value <= max_distance:
            candidates.append((value, player_id))
    candidates.sort()
    if not candidates:
        return None
    if len(candidates) > 1 and candidates[1][0] - candidates[0][0] <= ambiguity_margin:
        return None
    return candidates[0][1]


def possession(frames, config):
    history, last_owner, last_team, missing_count = [], None, 0, 0
    for index, frame in enumerate(frames):
        ball, players = frame.get("ball"), frame.get("players", {})
        owner, team, status = None, 0, "unknown"
        if ball is not None:
            owner = nearest_player(players, ball["bbox"], config.max_player_ball_distance_px, config.ambiguity_margin_px)
            if owner is not None:
                team = players[owner]["team"]
                status = "interpolated" if ball.get("interpolated", False) else "observed"
            # A visible loose/ambiguous ball is evidence against carrying ownership.
            last_owner, last_team, missing_count = owner, team, 0
        else:
            missing_count += 1
            if (last_owner is not None and missing_count <= config.possession_grace_frames
                    and last_owner in players and players[last_owner].get("team", 0) == last_team):
                owner, team, status = last_owner, last_team, "carried"
            else:
                last_owner, last_team = None, 0
        history.append({"frame": index, "team": team, "player_id": owner, "status": status})
    return history


def analyze(data, config):
    validate_tracks(data)
    config.validate()
    frames = interpolate_ball(data["frames"], config.max_ball_gap_frames)
    for frame in frames:
        for player_id, player in frame.get("players", {}).items():
            if player_id in config.team_overrides:
                player["team"] = config.team_overrides[player_id]
    transform = PitchTransform(config.calibration) if config.calibration else None
    movement, previous, rejected_segments = {}, {}, 0
    for index, frame in enumerate(frames):
        current = {}
        for player_id, player in frame.get("players", {}).items():
            stats = movement.setdefault(player_id, {"distance_m": 0.0, "max_speed_kmh": 0.0, "valid_segments": 0})
            raw = foot(player["bbox"])
            camera = frame.get("camera_offset_px", [0, 0])
            point = transform.point([raw[0] - camera[0], raw[1] - camera[1]]) if transform and frame.get("camera_valid", True) else None
            player["pitch_position_m"] = point
            before = previous.get(player_id)
            if point is not None:
                current[player_id] = point
            if point is None or before is None:
                continue
            delta = distance(before, point)
            speed = delta * data["fps"] * 3.6
            if speed > config.max_speed_kmh:
                rejected_segments += 1
                continue
            stats["distance_m"] += delta
            stats["max_speed_kmh"] = max(stats["max_speed_kmh"], speed)
            stats["valid_segments"] += 1
            player["speed_kmh"] = speed
            player["distance_m"] = stats["distance_m"]
        # Never bridge absent players, invalid camera estimates or out-of-pitch points.
        previous = current
    control = possession(frames, config)
    team_counts = Counter(row["team"] for row in control)
    status_counts = Counter(row["status"] for row in control)
    count, fps = len(frames), data["fps"]
    known = team_counts[1] + team_counts[2]
    summary = {
        "source_kind": data["source"]["kind"], "fps": fps, "frame_count": count,
        "duration_seconds": count / fps,
        "metric_coordinates_available": transform is not None,
        "control_definition": "Nearest eligible player's bbox foot corner; heuristic frame-level control, not event possession",
        "control": {"team_1_seconds": team_counts[1] / fps, "team_2_seconds": team_counts[2] / fps,
                    "unknown_seconds": team_counts[0] / fps, "known_coverage_percent": 100 * known / count,
                    "team_1_percent_all_frames": 100 * team_counts[1] / count,
                    "team_2_percent_all_frames": 100 * team_counts[2] / count,
                    "team_1_percent_known_frames": 100 * team_counts[1] / known if known else None,
                    "team_2_percent_known_frames": 100 * team_counts[2] / known if known else None,
                    "status_frames": {name: status_counts[name] for name in ("observed", "interpolated", "carried", "unknown")}},
        "ball_interpolated_frames": sum(bool((frame.get("ball") or {}).get("interpolated", False)) for frame in frames),
        "rejected_movement_segments": rejected_segments,
        "players": {player_id: {**stats, "distance_m": round(stats["distance_m"], 6), "max_speed_kmh": round(stats["max_speed_kmh"], 6)}
                    for player_id, stats in sorted(movement.items())} if transform else {},
        "settings": config.to_dict(),
    }
    return {"frames": frames, "control": control, "summary": summary}
