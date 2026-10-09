"""Deterministic, invented tracking data. No real footage or trained model."""

from .config import Config


def demo_config():
    return Config(calibration={
        "pixel_points": [[60, 110], [900, 110], [900, 518], [60, 518]],
        "pitch_points_m": [[0, 0], [105, 0], [105, 68], [0, 68]],
    }, team_colors_bgr={"1": [255, 180, 80], "2": [90, 130, 255]})


def sample_tracks():
    frames = []
    for index in range(100):
        players = {}
        for player_id, team, x, y in (
            ("11", 1, 23 + index * 0.05, 28),
            ("12", 1, 41 + index * 0.025, 49),
            ("21", 2, 66 - index * 0.04, 38),
            ("22", 2, 78 - index * 0.02, 16),
        ):
            px, py = 60 + x * 8, 110 + y * 6
            players[player_id] = {"bbox": [round(px - 10, 4), round(py - 38, 4), round(px + 10, 4), round(py, 4)], "team": team}
        ball = None
        if index not in {0, 1, 10, 11} and not 36 <= index <= 50:
            owner = "11" if index < 60 else "21"
            bbox = players[owner]["bbox"]
            bx, by = bbox[2] + 3, bbox[3] - 2
            # Visible loose-ball interval: no carry-forward is allowed here.
            if 56 <= index < 60:
                bx, by = 480, 260
            ball = {"bbox": [round(bx - 3, 4), round(by - 3, 4), round(bx + 3, 4), round(by + 3, 4)]}
        frames.append({"players": players, "referees": {}, "ball": ball,
                       "camera_offset_px": [0, 0], "camera_valid": True})
    return {
        "schema_version": 1, "fps": 25.0, "width": 960, "height": 640,
        "frame_count": len(frames),
        "source": {"kind": "synthetic", "description": "Invented four-player scene; seedless deterministic arithmetic; no model inference or match data"},
        "frames": frames,
    }
