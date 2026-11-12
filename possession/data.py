"""Loaders that bring every source into one layout.

A match is a list of halves; a half is a dict with
    ball   (T, 2 or 3) float32, metres, pitch centre origin, NaN where unseen
    team0  (T, N, 2)   home
    team1  (T, N, 2)   away
    label  (T,) int8   0 home, 1 away, 2 dead   (external matches only)
    first  int         video frame of row 0     (competition match only)
"""
import csv
import json
import os
import xml.etree.ElementTree as ET

import numpy as np


# --- open DFL dataset (converted by possession.dfl) ------------------------------------------

def load_dfl(npz_path):
    data = np.load(npz_path)
    return [{"ball": data["ball_%d" % h], "team0": data["home_%d" % h],
             "team1": data["away_%d" % h], "label": data["label_%d" % h]} for h in (1, 2)]


# --- Metrica FIFA/EPTS export (the competition ATD and Metrica's public Sample_Game_3) --------

def _strip(tag):
    return tag.rsplit("}", 1)[-1]


def epts_layout(meta_path):
    """Read the FIFA/EPTS metadata: who the players are and how each raw line is laid out.

    Returns (player_team, specs). player_team maps playerId -> 0 (home, first team in the file)
    or 1. specs is a list of (start_frame, end_frame, groups), one per DataFormatSpecification;
    groups is, for each ';'-separated group of a line, (playerId, index of x, index of y). The
    layout can change between frame ranges (substitutions), so it is never assumed to be fixed.
    """
    root = ET.parse(meta_path).getroot()
    nodes = {}
    for node in root.iter():
        nodes.setdefault(_strip(node.tag), []).append(node)
    team_ids = [team.get("id") for team in nodes["Team"]]
    player_team = {p.get("id"): (0 if p.get("teamId") == team_ids[0] else 1)
                   for p in nodes["Player"]}
    channel = {c.get("id"): (c.get("playerId"), c.get("channelId"))
               for c in nodes.get("PlayerChannel", [])}
    specs = []
    for spec in nodes["DataFormatSpecification"]:
        groups = []
        for outer in spec:
            if _strip(outer.tag) != "SplitRegister":
                continue
            inner = [g for g in outer if _strip(g.tag) == "SplitRegister"]
            if not inner:  # a bare register is the ball group, handled positionally below
                continue
            for group in inner:
                refs = [channel[r.get("playerChannelId")] for r in group
                        if _strip(r.tag) == "PlayerChannelRef"]
                if not refs:
                    continue
                kinds = [kind for _, kind in refs]
                groups.append((refs[0][0], kinds.index("x"), kinds.index("y")))
        specs.append((int(spec.get("startFrame")), int(spec.get("endFrame")), groups))
    return player_team, sorted(specs)


def epts_parameter(meta_path, name):
    root = ET.parse(meta_path).getroot()
    for param in root.iter():
        if _strip(param.tag) == "ProviderParameter":
            values = {_strip(c.tag): c.text for c in param}
            if values.get("Name") == name and values.get("Value"):
                return int(values["Value"])
    return None


def _number(text):
    return float(text) if text[:1] not in ("N", "n", "") else np.nan


def load_epts(meta_path, raw_path):
    """Whole recording as (frame_ids, ball (T,2), team0 (T,N0,2), team1 (T,N1,2)).

    Raw line: "<frame>:<group>;<group>;...:<ball>", each group "x,y" or "x,y,speed", normalised
    to 0-1. Output is metres on a nominal 105 x 68 pitch with the centre at the origin.
    """
    player_team, specs = epts_layout(meta_path)
    players = sorted(player_team, key=lambda pid: (player_team[pid], pid))
    column = {pid: i for i, pid in enumerate(players)}
    n_players = len(players)
    frames, rows = [], []
    spec_index = 0
    with open(raw_path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split(":")
            if len(parts) != 3:
                continue
            frame = int(parts[0])
            while spec_index + 1 < len(specs) and frame > specs[spec_index][1]:
                spec_index += 1
            if frame < specs[spec_index][0]:
                spec_index = max(i for i, s in enumerate(specs) if s[0] <= frame) \
                    if any(s[0] <= frame for s in specs) else 0
            layout = specs[spec_index][2]
            row = np.full((n_players + 1, 2), np.nan, np.float32)
            for (pid, ix, iy), group in zip(layout, parts[1].split(";")):
                values = group.split(",")
                if len(values) > max(ix, iy):
                    row[column[pid]] = (_number(values[ix]), _number(values[iy]))
            ball = parts[2].split(",")
            if len(ball) >= 2:
                row[n_players] = (_number(ball[0]), _number(ball[1]))
            frames.append(frame)
            rows.append(row)
    data = np.stack(rows)
    data[..., 0] = (data[..., 0] - 0.5) * 105.0
    data[..., 1] = (data[..., 1] - 0.5) * 68.0
    team = np.array([player_team[pid] for pid in players])
    return (np.array(frames), data[:, n_players], data[:, :n_players][:, team == 0],
            data[:, :n_players][:, team == 1])


# --- Metrica public sample data (possession derived from the published event files) ----------

OWNING_EVENTS = {"PASS", "SHOT", "RECOVERY", "SET PIECE", "BALL LOST", "BALL OUT"}


def _labels_from_events(n, ball_seen, events):
    """Dead where the corrected ball track is absent; otherwise the team of the latest on-ball
    event. `events` is [(row_index, team)] sorted by row."""
    owner = np.full(n, -1, np.int8)
    for (row, team), nxt in zip(events, events[1:] + [(n, None)]):
        owner[max(row, 0):max(nxt[0], 0)] = team
    if events:
        owner[:max(events[0][0], 0)] = events[0][1]
    return np.where(ball_seen, owner, 2).astype(np.int8)


def load_metrica_csv(folder, game):
    stem = os.path.join(folder, "Sample_Game_%d" % game)
    sides = []
    for side in ("Home", "Away"):
        raw = np.genfromtxt("%s_RawTrackingData_%s_Team.csv" % (stem, side), delimiter=",",
                            skip_header=3, dtype=np.float32)
        sides.append(raw)
    period, frame = sides[0][:, 0].astype(int), sides[0][:, 1].astype(int)
    ball = sides[0][:, -2:]
    teams = [side[:, 3:-2].reshape(len(side), -1, 2) for side in sides]
    events = []
    with open(stem + "_RawEventsData.csv") as handle:
        for row in csv.DictReader(handle):
            if row["Type"] in OWNING_EVENTS:
                events.append((int(row["Start Frame"]), 0 if row["Team"] == "Home" else 1))
    return _metrica_halves(period, frame, ball, teams, events)


def load_metrica_epts(folder, game=3):
    stem = os.path.join(folder, "Sample_Game_%d" % game)
    frame, ball, team0, team1 = load_epts(stem + "_metadata.xml", stem + "_tracking.txt")
    ball = ball / np.array([105.0, 68.0]) + 0.5
    teams = [team0 / np.array([105.0, 68.0]) + 0.5, team1 / np.array([105.0, 68.0]) + 0.5]
    split = epts_parameter(stem + "_metadata.xml", "second_half_start")
    period = np.where(frame < split, 1, 2)
    with open(stem + "_events.json") as handle:
        raw = json.load(handle)["data"]
    root = ET.parse(stem + "_metadata.xml").getroot()
    home = [node.get("id") for node in root.iter() if _strip(node.tag) == "Team"][0]
    events = [(e["start"]["frame"], 0 if e["team"]["id"] == home else 1) for e in raw
              if e["type"]["name"] in OWNING_EVENTS]
    return _metrica_halves(period, frame, ball, teams, events)


def _metrica_halves(period, frame, ball, teams, events):
    scale = np.array([105.0, 68.0], np.float32)
    halves = []
    for half in (1, 2):
        rows = np.flatnonzero(period == half)
        lo, hi = rows[0], rows[-1] + 1
        first = frame[lo]
        mine = sorted((f - first, team) for f, team in events if first <= f <= frame[hi - 1])
        b = ((ball[lo:hi] - 0.5) * scale).astype(np.float32)
        halves.append({
            "ball": b,
            "team0": ((teams[0][lo:hi] - 0.5) * scale).astype(np.float32),
            "team1": ((teams[1][lo:hi] - 0.5) * scale).astype(np.float32),
            "label": _labels_from_events(hi - lo, ~np.isnan(b[:, 0]), mine),
        })
    return halves
