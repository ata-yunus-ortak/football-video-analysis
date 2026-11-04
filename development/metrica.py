"""Strict adapters for the two pinned Metrica CSV samples, not Sample Game 3."""
import csv
from collections import Counter
from pathlib import Path
import numpy as np


def _team(path, pitch, fps):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.reader(stream)
        next(reader)
        next(reader)
        header = next(reader)
        if header[:3] != ["Period", "Frame", "Time [s]"] or header[-2:] != ["Ball", ""]:
            raise ValueError("Unsupported Metrica tracking header")
        if (len(header) - 5) % 2 or any(header[i + 1] for i in range(3, len(header), 2)):
            raise ValueError("Expected x/y tracking pairs")
        rows = []
        for row in reader:
            if len(row) != len(header):
                raise ValueError("Tracking column count differs")
            rows.append([float(value) if value else np.nan for value in row])
    values = np.asarray(rows, float)
    if (values.ndim != 2 or not len(values) or not np.isfinite(values[:, :3]).all()
            or not np.all(np.isin(values[:, 0], (1, 2)))
            or not np.array_equal(values[:, 1], np.arange(1, len(values) + 1))
            or not np.allclose(values[:, 2], values[:, 1] / fps, rtol=0, atol=1e-7)):
        raise ValueError("Invalid tracking clock, periods or one-based source frames")
    coordinates = values[:, 3:].reshape(len(values), -1, 2) * pitch
    return values[:, :3], coordinates[:, :-1], coordinates[:, -1]


def load_tracking(home_path, away_path, pitch=(105.0, 68.0), fps=25.0):
    pitch = np.asarray(pitch, float)
    home_clock, home, home_ball = _team(home_path, pitch, fps)
    away_clock, away, away_ball = _team(away_path, pitch, fps)
    if not np.array_equal(home_clock, away_clock):
        raise ValueError("Team tracking clocks differ")
    hp = np.isfinite(home_ball).all(axis=1)
    ap = np.isfinite(away_ball).all(axis=1)
    if not np.array_equal(home_ball[hp & ap], away_ball[hp & ap]):
        raise ValueError("Duplicated ball coordinates disagree")
    ball = np.full_like(home_ball, np.nan)
    ball[hp] = home_ball[hp]
    ball[~hp & ap] = away_ball[~hp & ap]
    players = np.concatenate((home, away), axis=1)
    return {
        "players": players, "ball": ball,
        # The CSV has no detection-confidence flag. This means finite in export,
        # not independently verified visual detection or a new contact vote.
        "ball_observed": np.isfinite(ball).all(axis=1),
        "player_detected": np.isfinite(players).all(axis=2),
        "teams": np.r_[np.zeros(home.shape[1], np.int8), np.ones(away.shape[1], np.int8)],
        "period": home_clock[:, 0].astype(np.int8),
        "frame": np.arange(len(ball)),
        "source_frame": home_clock[:, 1].astype(np.int64),
        "fps": np.array(fps), "pitch": pitch,
    }


def load_events(path):
    events = []
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"Type", "Subtype", "Period", "Start Frame", "End Frame"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Missing Metrica event fields")
        for number, row in enumerate(reader, 2):
            event = {"row": number, "type": row["Type"], "subtype": row["Subtype"],
                     "period": int(row["Period"]), "start": int(row["Start Frame"]),
                     "end": int(row["End Frame"])}
            if event["period"] not in (1, 2) or event["start"] < 1:
                raise ValueError("Invalid event period or frame")
            events.append(event)
    return events


def candidate_stoppages(events, inputs):
    """Return partial event-paired intervals only; never a complete D target.

    Exclude the BALL OUT boundary frame; end before the restart frame. Reject
    intervening recorded live actions, another exit, period changes and retakes.
    Foul/advantage and absent goal-kick records are deliberately not filled in.
    """
    source = np.asarray(inputs["source_frame"])
    period = np.asarray(inputs["period"])
    intervals = []
    rejected = Counter()
    boundary_types = {"BALL OUT", "SET PIECE"}
    live_types = {"PASS", "SHOT", "BALL LOST", "RECOVERY"}
    restarts = {"THROW IN", "CORNER KICK", "KICK OFF", "FREE KICK", "PENALTY"}
    for event in sorted(events, key=lambda item: (item["end"], item["row"])):
        if event["type"] != "BALL OUT":
            continue
        end = event["end"]
        if end < event["start"]:
            rejected["invalid_exit_clock"] += 1
            continue
        candidates = [item for item in events if item["period"] == event["period"]
                      and item["type"] in boundary_types and item["start"] > end]
        following = min(candidates, key=lambda item: (item["start"], item["row"]), default=None)
        if following is None or following["type"] != "SET PIECE":
            rejected["no_next_restart_before_another_exit"] += 1
            continue
        if following["subtype"] not in restarts:
            rejected["unsupported_or_retaken_restart"] += 1
            continue
        if any(item["type"] in live_types and item["period"] == event["period"]
               and end < item["start"] < following["start"] for item in events):
            rejected["intervening_live_action"] += 1
            continue
        start = int(np.searchsorted(source, end, side="right"))
        stop = int(np.searchsorted(source, following["start"], side="left"))
        if (start >= stop or stop >= len(source) or source[stop] != following["start"]
                or not np.all(period[start:stop + 1] == event["period"])):
            rejected["uncovered_or_cross_period_interval"] += 1
            continue
        if intervals and start < intervals[-1]["stop_index_exclusive"]:
            rejected["overlapping_interval"] += 1
            continue
        intervals.append({"start_index": start, "stop_index_exclusive": stop,
                          "exit_event_row": event["row"], "restart_event_row": following["row"],
                          "period": event["period"], "restart_type": following["subtype"],
                          "duration_s": (stop - start) / float(inputs["fps"])})
    return intervals, dict(rejected)
