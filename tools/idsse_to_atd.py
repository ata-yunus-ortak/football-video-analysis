"""Write one IDSSE match in the challenge ATD layout, for end-to-end rehearsal only.

    python -m tools.idsse_to_atd --plan learned-dead-ball-plan.json --data /private/idsse \
        --split validation --out /private/rehearsal [--ball-in-stoppages]

Produces rehearsal_atd.xml + rehearsal_atd.txt (normalised top-left coordinates, speed field 0)
and truth.csv (frame,label from DFL BallStatus/BallPossession) so the produced submission can be
scored. By default the ball is written as missing during stoppages, like Metrica feeds; that
uses the target to build the input and is a feed simulation for rehearsal, never training data.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from tools.idsse_spell_eval import load_ball

PITCH = np.array([105.0, 68.0])


def normalised(p):
    """Pitch-centred metres (y up) -> top-left normalised (y down)."""
    return np.stack([(p[..., 0] + PITCH[0] / 2) / PITCH[0], (PITCH[1] / 2 - p[..., 1]) / PITCH[1]], -1)


def group(xy):
    return "NaN,NaN,0" if not np.isfinite(xy).all() else f"{xy[0]:.5f},{xy[1]:.5f},0"


def main():
    ap = argparse.ArgumentParser()
    for k in ("plan", "data", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--split", default="validation", choices=("validation", "holdout"))
    ap.add_argument("--ball-in-stoppages", action="store_true")
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text())
    fx = next(f for f in plan["fixtures"] if f["split"] == a.split)
    z = np.load(Path(a.data) / "npz" / f"{fx['id']}.npz")
    ball = load_ball(Path(a.data) / fx["files"]["positions"]["local_name"])
    if not a.ball_in_stoppages:
        ball = np.where(z["dead"][:, None], np.nan, ball)
    players, ballxy = normalised(z["players"].astype(float)), normalised(ball)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    roster = "".join(f'<Player id="P{i}" teamId="{"T0" if t == 0 else "T1"}"/>' for i, t in enumerate(z["teams"]))
    (out / "rehearsal_atd.xml").write_text(
        '<?xml version="1.0"?><Main><Metadata><GlobalConfig><FrameRate>25</FrameRate>'
        "<FieldSize><Width>105</Width><Height>68</Height></FieldSize></GlobalConfig>"
        f'<Teams><Team id="T0"/><Team id="T1"/></Teams><Players>{roster}</Players></Metadata></Main>')
    with (out / "rehearsal_atd.txt").open("w") as f:
        for i in range(len(players)):
            f.write(f"{i + 1}:{';'.join(group(p) for p in players[i])}:{group(ballxy[i])}\n")
    truth = np.where(z["dead"], "D", np.where(z["possession"] == 1, "H", "A"))
    with (out / "truth.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["frame", "label"])
        w.writerows(zip(range(len(truth)), truth))
    np.save(out / "period.npy", z["period"])
    print(f"{fx['id']}: {len(truth)} frames written to {out}")


if __name__ == "__main__":
    main()
