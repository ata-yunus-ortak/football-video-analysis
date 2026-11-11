"""Metrica Sample Game 3 (EPTS) loader with event-derived partial D/live proxies.

Evaluation only; nothing is selected on this match. Proxies are not exhaustive truth:
  stoppage = BALL OUT end -> next SET PIECE start, FAULT RECEIVED -> next FREE KICK,
             GOAL shot -> next KICK OFF (same period, no live event in between);
  live     = frames strictly inside PASS / CARRY spans.
Files: Sample_Game_3_{metadata.xml,tracking.txt,events.json} from metrica-sports/sample-data.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from development.learned_dead_ball import features

LIVE_TYPES = {"PASS", "CARRY", "CHALLENGE", "RECOVERY", "SHOT", "BALL LOST"}


def _subtypes(event):
    s = event.get("subtypes")
    return [] if s is None else [x["name"] for x in (s if isinstance(s, list) else [s])]


def load_tracking(directory, pitch):
    root = ET.parse(directory / "Sample_Game_3_metadata.xml").getroot()
    team = {p.get("id"): p.get("teamId") for p in root.iter("Player")}
    channel = {c.get("id"): c.get("playerId") for c in root.iter("PlayerChannel")}
    ids = sorted(team)
    column = {p: i for i, p in enumerate(ids)}
    specs = [(int(s.get("startFrame")), int(s.get("endFrame")),
              [channel[r.get("playerChannelId")] for r in s.iter("PlayerChannelRef")
               if r.get("playerChannelId").endswith("_x")])
             for s in root.iter("DataFormatSpecification")]
    lines = (directory / "Sample_Game_3_tracking.txt").read_text().splitlines()
    players = np.full((len(lines), len(ids), 2), np.nan)
    frames = np.zeros(len(lines), int)
    for i, line in enumerate(lines):
        n, groups, _ball = line.split(":")
        frames[i] = int(n)
        order = next(o for a, b, o in specs if a <= frames[i] <= b)
        for pid, g in zip(order, groups.split(";")):
            players[i, column[pid]] = [float(v) for v in g.split(",")]
    teams_sorted = sorted(set(team.values()))
    teams = np.array([teams_sorted.index(team[p]) for p in ids], np.int8)
    # normalised top-left origin -> corner metres
    players = players * np.asarray(pitch, float)
    return frames, players, teams


def load_game3(directory, fps, pitch):
    frames, players, teams = load_tracking(directory, pitch)
    events = sorted(json.loads((directory / "Sample_Game_3_events.json").read_text())["data"],
                    key=lambda e: e["start"]["frame"])
    index = {n: i for i, n in enumerate(frames)}
    period = np.zeros(len(frames), np.int8)
    for p in (1, 2):
        span = [e[k]["frame"] for e in events if e["period"] == p for k in ("start", "end")]
        period[index[min(span)]:index[max(span)] + 1] = p
    pairs = []
    for i, e in enumerate(events):
        kind, sub = e["type"]["name"], _subtypes(e)
        if kind == "BALL OUT":
            want = lambda x: x["type"]["name"] == "SET PIECE"
        elif kind == "FAULT RECEIVED":
            want = lambda x: x["type"]["name"] == "SET PIECE" and "FREE KICK" in _subtypes(x)
        elif kind == "SHOT" and "GOAL" in sub:
            want = lambda x: x["type"]["name"] == "SET PIECE" and "KICK OFF" in _subtypes(x)
        else:
            continue
        end = e["end"]["frame"]
        for x in events[i + 1:]:
            if x["period"] != e["period"]:
                break
            if want(x):
                pairs.append((index[end] + 1, index[x["start"]["frame"]]))
                break
            if x["type"]["name"] in LIVE_TYPES and x["start"]["frame"] > end:
                break
    stop = np.zeros(len(frames), bool)
    for a, b in pairs:
        stop[a:b] = True
    live = np.zeros(len(frames), bool)
    for e in events:
        if e["type"]["name"] in ("PASS", "CARRY"):
            a, b = index[e["start"]["frame"]], index[e["end"]["frame"]]
            if b - a > 2:
                live[a + 1:b] = True
    live &= ~stop
    keep = period > 0
    remap = np.cumsum(keep) - 1
    pairs = [(int(remap[a]), int(remap[b - 1]) + 1) for a, b in pairs if b > a and keep[a] and keep[b - 1]]
    x, _ = features(players[keep], teams, period[keep], fps, pitch)
    return x, period[keep], stop[keep], live[keep], pairs
