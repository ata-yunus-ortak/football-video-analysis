"""Convert the open DFL tracking dataset (Bassek et al. 2025, CC-BY 4.0) to compact arrays.

Source: https://doi.org/10.6084/m9.figshare.28196177 -- seven Bundesliga / 2. Bundesliga matches
with 25 Hz positions and, on the ball track, a per-frame BallPossession (1 home, 2 guest) and
BallStatus (1 alive, 0 dead). Those two fields are the external supervision used for training.

Output per match: <out>/<match_id>.npz with, per half h in {1, 2}:
    ball_h   (T, 3) float32   x, y, z in metres, pitch centre origin
    home_h   (T, Nh, 2) float32, NaN where the player is not on the pitch
    away_h   (T, Na, 2) float32
    label_h  (T,) int8        0 home, 1 away, 2 dead
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np

SECTIONS = {"firstHalf": 1, "secondHalf": 2}
FRAMESET = re.compile(r'<FrameSet GameSection="(\w+)" MatchId="[^"]*" TeamId="([^"]*)" PersonId="([^"]*)"')
PLAYER = re.compile(r'<Frame N="(\d+)" T="[^"]*" X="([-\d.]+)" Y="([-\d.]+)"')
BALL = re.compile(r'<Frame N="(\d+)" T="[^"]*" X="([-\d.]+)" Y="([-\d.]+)" Z="([-\d.]+)".*?'
                  r'BallPossession="(\d)" BallStatus="(\d)"')


def team_roles(info_path):
    root = ET.parse(info_path).getroot()
    return {team.get("TeamId"): team.get("Role") for team in root.iter("Team")}


def convert(positions_path, info_path, out_path):
    roles = team_roles(info_path)
    sets = []  # (half, kind, rows)
    current = None
    with open(positions_path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("<Frame "):
                if current is None:
                    continue
                match = (BALL if current[1] == "ball" else PLAYER).match(line)
                if match:
                    current[2].append(match.groups())
            elif line.startswith("<FrameSet"):
                section, team, _ = FRAMESET.match(line).groups()
                half = SECTIONS.get(section)
                if half is None or team == "referee":
                    current = None
                    continue
                kind = "ball" if team.upper() == "BALL" else roles[team]
                current = (half, kind, [])
                sets.append(current)

    out = {}
    for half in (1, 2):
        mine = [(kind, np.array(rows, dtype=np.float64)) for h, kind, rows in sets
                if h == half and rows]
        first = int(min(arr[:, 0].min() for _, arr in mine))
        last = int(max(arr[:, 0].max() for _, arr in mine))
        n = last - first + 1
        ball = np.full((n, 3), np.nan, np.float32)
        label = np.full(n, 2, np.int8)
        teams = {"home": [], "guest": []}
        for kind, arr in mine:
            index = arr[:, 0].astype(np.int64) - first
            if kind == "ball":
                ball[index] = arr[:, 1:4]
                label[index] = np.where(arr[:, 5] == 0, 2, arr[:, 4] - 1)
            else:
                track = np.full((n, 2), np.nan, np.float32)
                track[index] = arr[:, 1:3]
                teams[kind].append(track)
        out["ball_%d" % half] = ball
        out["home_%d" % half] = np.stack(teams["home"], axis=1)
        out["away_%d" % half] = np.stack(teams["guest"], axis=1)
        out["label_%d" % half] = label
    np.savez_compressed(out_path, **out)
    return {key: value.shape for key, value in out.items()}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    only = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(dst, exist_ok=True)
    for positions in sorted(glob.glob(os.path.join(src, "DFL_04_03_positions_raw_observed_*.xml"))):
        match_id = positions.rsplit("DFL-MAT-", 1)[1][:-4]
        if only and match_id != only:
            continue
        info = glob.glob(os.path.join(src, "DFL_02_01_matchinformation_*%s.xml" % match_id))[0]
        print(match_id, convert(positions, info, os.path.join(dst, match_id + ".npz")), flush=True)
