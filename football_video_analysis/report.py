"""Portable SVG/CSV reports; no plotting library is needed."""

import csv
from html import escape
from pathlib import Path
from .tracks import write_json


COLORS = {0: "#53677d", 1: "#50b4ff", 2: "#ff825a"}


def write_reports(output, data, result):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", result["summary"])
    with (output / "control.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["frame", "time_seconds", "team", "player_id", "status"])
        writer.writeheader()
        for row in result["control"]:
            writer.writerow({**row, "time_seconds": round(row["frame"] / data["fps"], 6)})
    with (output / "movement.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["frame", "player_id", "team", "x_m", "y_m", "speed_kmh", "distance_m"])
        writer.writeheader()
        for index, frame in enumerate(result["frames"]):
            for player_id, player in frame.get("players", {}).items():
                position = player.get("pitch_position_m") or [None, None]
                writer.writerow({"frame": index, "player_id": player_id, "team": player.get("team", 0),
                                 "x_m": position[0], "y_m": position[1],
                                 "speed_kmh": player.get("speed_kmh"), "distance_m": player.get("distance_m")})
    write_svg(output / "report.svg", data, result)


def write_svg(path, data, result):
    summary, control = result["summary"], result["control"]
    synthetic = data["source"]["kind"] == "synthetic"
    label = "SYNTHETIC DEMO / NO MODEL INFERENCE" if synthetic else "VIDEO TRACKING / HEURISTIC ESTIMATES"
    chosen_index = min(73, len(result["frames"]) - 1)
    frame = result["frames"][chosen_index]
    calibrated = summary["metric_coordinates_available"]
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="810" viewBox="0 0 1200 810" role="img" aria-labelledby="title desc">
<title id="title">Football video analysis — {label}</title>
<desc id="desc">A pitch snapshot, control timeline with unknown intervals, and movement summaries. {'These invented tracks do not measure model accuracy.' if synthetic else 'Heuristic estimates require independent validation.'}</desc>
<rect width="1200" height="810" fill="#0c1524"/>
<g font-family="Arial, sans-serif" fill="#edf3fa">
<text x="42" y="48" font-size="14" fill="#50b4ff" letter-spacing="2">{label}</text>
<text x="42" y="94" font-size="36" font-weight="700">Football video analysis</text>
<text x="42" y="126" font-size="17" fill="#a5b6ca">Tracking → bounded ball repair → control estimates → calibrated movement</text>
<rect x="42" y="154" width="820" height="450" rx="15" fill="#113a36"/>
<text x="68" y="183" font-size="13" fill="#bbdacf">{'Calibrated pitch view' if calibrated else 'Image-coordinate view'} · frame {chosen_index} · {chosen_index / data['fps']:.2f} s</text>
<g stroke="#78a795" stroke-width="2" fill="none">
<rect x="70" y="204" width="764" height="372"/>
<path d="M452 204V576"/>
<circle cx="452" cy="390" r="51"/>
<path d="M70 293H190V487H70M834 293H714V487H834M70 347H108V433H70M834 347H796V433H834"/>
</g>''']
    for player_id, player in frame.get("players", {}).items():
        position = player.get("pitch_position_m")
        if calibrated:
            if position is None:
                continue
            # Scale from the configured metric calibration extent, not fixed stadium coordinates.
            metric = summary["settings"]["calibration"]["pitch_points_m"]
            xmin, xmax = min(p[0] for p in metric), max(p[0] for p in metric)
            ymin, ymax = min(p[1] for p in metric), max(p[1] for p in metric)
            x = 70 + (position[0] - xmin) / (xmax - xmin) * 764
            y = 204 + (position[1] - ymin) / (ymax - ymin) * 372
        else:
            box = player["bbox"]
            x, y = 70 + (box[0] + box[2]) / 2 / data["width"] * 764, 204 + box[3] / data["height"] * 372
        color = COLORS[player.get("team", 0)]
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="13" fill="{color}" stroke="#0c1524" stroke-width="2"/><text x="{x:.2f}" y="{y + 5:.2f}" text-anchor="middle" fill="#0c1524" font-size="12" font-weight="700">{escape(player_id)}</text>')
    owner = control[chosen_index]["player_id"]
    if owner is not None and owner in frame.get("players", {}):
        player = frame["players"][owner]
        pos = player.get("pitch_position_m")
        if pos:
            x = 70 + (pos[0] - xmin) / (xmax - xmin) * 764 + 21
            y = 204 + (pos[1] - ymin) / (ymax - ymin) * 372
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="#fff"/>')
    stats = summary["control"]
    parts.append(f'''<text x="900" y="184" font-size="14" fill="#a5b6ca">CLIP METADATA</text>
<text x="900" y="221" font-size="27" font-weight="700">{summary['duration_seconds']:.1f} seconds</text>
<text x="900" y="248" font-size="16" fill="#a5b6ca">{data['frame_count']} frames · {data['fps']:g} FPS</text>
<text x="900" y="302" font-size="14" fill="#a5b6ca">CONTROL / ALL FRAMES</text>
<text x="900" y="337" font-size="22" fill="#50b4ff">Team 1 · {stats['team_1_percent_all_frames']:.0f}%</text>
<text x="900" y="372" font-size="22" fill="#ff825a">Team 2 · {stats['team_2_percent_all_frames']:.0f}%</text>
<text x="900" y="407" font-size="22" fill="#a5b6ca">Unknown · {100 - stats['known_coverage_percent']:.0f}%</text>
<text x="900" y="457" font-size="14" fill="#a5b6ca">BALL REPAIR</text>
<text x="900" y="490" font-size="21">{summary['ball_interpolated_frames']} interpolated frames</text>
<text x="900" y="517" font-size="14" fill="#a5b6ca">Long and boundary gaps stay missing.</text>
<text x="68" y="559" font-size="13" fill="#bbdacf">{'Invented trajectories; four stable IDs; no detector/tracker benchmark.' if synthetic else 'Configured projection; review calibration and camera assumptions.'}</text>
<text x="42" y="637" font-size="17" font-weight="700">Control timeline</text>
<text x="260" y="637" font-size="13" fill="#a5b6ca">Blue: team 1 · orange: team 2 · slate: unknown · dots: inferred</text>''')
    width = 1100 / len(control)
    for row in control:
        x = 42 + row["frame"] * width
        parts.append(f'<rect x="{x:.3f}" y="653" width="{width + 0.1:.3f}" height="29" fill="{COLORS[row["team"]]}"/>')
        if row["status"] in ("interpolated", "carried"):
            parts.append(f'<circle cx="{x + width / 2:.3f}" cy="667" r="2" fill="#0c1524"/>')
    parts.append(f'<text x="42" y="706" font-size="13" fill="#a5b6ca">0.0 s</text><text x="1142" y="706" text-anchor="end" font-size="13" fill="#a5b6ca">{summary["duration_seconds"]:.1f} s</text>')
    if summary["players"]:
        values = " · ".join(f"ID {escape(player_id)}: {stats['distance_m']:.2f} m / {stats['max_speed_kmh']:.1f} km/h" for player_id, stats in summary["players"].items())
        parts.append(f'<text x="42" y="749" font-size="14">{values}</text>')
    footer = 'Synthetic values verify execution, not real-world accuracy.' if synthetic else 'Heuristic control and movement require independent validation.'
    parts.append(f'<text x="42" y="787" font-size="12" fill="#8396ac">Tutorial-inspired engineering portfolio · {footer}</text></g></svg>')
    Path(path).write_text("\n".join(parts) + "\n", encoding="utf-8")
