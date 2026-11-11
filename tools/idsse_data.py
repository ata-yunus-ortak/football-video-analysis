"""Download, verify and convert IDSSE (DFL) matches for the learned dead-ball study.

    python -m tools.idsse_data --plan learned-dead-ball-plan.json --out /private/idsse

Raw XML and prepared NPZ stay outside the repository. Existing raw files are
re-used only when their SHA-256 matches the plan. Per match, the NPZ holds:
  period (F,) 1/2, frame_n (F,), players (F, P, 2) pitch-centred metres (NaN = absent),
  teams (P,) 0 home / 1 away, dead (F,) bool from BallStatus == 0, possession (F,) DFL 1/2.
Ball coordinates are deliberately not written (frozen during dead frames).
"""
import argparse
import hashlib
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HEAD = re.compile(r'GameSection="(\w+)".*TeamId="([^"]+)" PersonId="([^"]+)"')
NUM = re.compile(r'N="(\d+)"')
XY = re.compile(r' X="([-\d.]+)" Y="([-\d.]+)"')
BALL = re.compile(r'BallPossession="(\d)" BallStatus="(\d)"')
SECTIONS = ("firstHalf", "secondHalf")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, dest, expected, attempts=5):
    if dest.exists() and sha256(dest) == expected:
        return
    for attempt in range(attempts):
        try:
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            if sha256(tmp) != expected:
                raise ValueError(f"hash mismatch for {dest.name}")
            tmp.replace(dest)
            return
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(15)


def convert(pos_path, mi_path):
    role = {t.get("TeamId"): t.get("Role") for t in ET.parse(mi_path).getroot().iter("Team")}
    home = [k for k, v in role.items() if v == "home"]
    if len(role) != 2 or len(home) != 1:
        raise ValueError("match information must name one home and one guest team")
    ball, people, cur = {}, {}, None
    with open(pos_path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("<FrameSet"):
                section, team, person = HEAD.search(line).groups()
                if team != "BALL" and team not in role:          # referees
                    cur = None
                    continue
                if team == "BALL":
                    cur = ("ball", section)
                    ball.setdefault(section, [])
                else:
                    cur = ("p", person, team, section)
                    people.setdefault((person, team), [])
            elif cur and line.startswith("<Frame "):
                n = int(NUM.search(line).group(1))
                if cur[0] == "ball":
                    possession, status = map(int, BALL.search(line).groups())
                    ball[cur[1]].append((n, possession, status))
                else:
                    x, y = map(float, XY.search(line).groups())
                    people[(cur[1], cur[2])].append((cur[3], n, x, y))
            elif line.startswith("</FrameSet"):
                cur = None
    if sorted(ball) != sorted(SECTIONS):
        raise ValueError(f"expected two halves, got {sorted(ball)}")
    rows = np.array([(i + 1, *r) for i, s in enumerate(SECTIONS) for r in ball[s]], dtype=np.int64)
    index = {(int(p), int(n)): i for i, (p, n) in enumerate(rows[:, :2])}
    keys = sorted(people, key=lambda k: (k[1] not in home, k[0]))
    players = np.full((len(rows), len(keys), 2), np.nan, np.float32)
    for slot, key in enumerate(keys):
        for section, n, x, y in people[key]:
            i = index.get((SECTIONS.index(section) + 1, n))
            if i is not None:
                players[i, slot] = (x, y)
    return {"period": rows[:, 0].astype(np.int8), "frame_n": rows[:, 1], "players": players,
            "teams": np.array([0 if k[1] in home else 1 for k in keys], np.int8),
            "dead": rows[:, 3] == 0, "possession": rows[:, 2].astype(np.int8)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text())
    out = Path(a.out)
    (out / "npz").mkdir(parents=True, exist_ok=True)
    for fx in plan["fixtures"]:
        f = fx["files"]
        for spec in f.values():
            fetch(plan["download_url_template"].format(**spec), out / spec["local_name"], spec["sha256"])
        data = convert(out / f["positions"]["local_name"], out / f["matchinformation"]["local_name"])
        np.savez_compressed(out / "npz" / f"{fx['id']}.npz", **data)
        print(f"{fx['id']} ({fx['split']}): {len(data['dead'])} frames, dead {data['dead'].mean():.1%}")


if __name__ == "__main__":
    main()
