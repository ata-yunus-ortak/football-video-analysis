"""Score the frozen H/A/X baseline with and without the learned D mask on one IDSSE match,
using the organizer's own scorer (evaluation/possession_metrics.py).

    python -m tools.idsse_spell_eval --plan learned-dead-ball-plan.json --data /private/idsse \
        --dball /private/learned-dead-ball-v2 --scorer /private/organizer-eval [--split validation]

Ground truth per frame from DFL: D where BallStatus == 0, else H/A from BallPossession
(1 home, 2 away). One X frame separates the halves so no spell crosses half-time, as in the
challenge ground truth. Inputs mimic the ATD adapter: corner-origin metres, period = 1 for
every frame (ATD has no half information), fps 25.

Two ball feeds are scored because the challenge feed is unknown:
  raw    - DFL ball as delivered (held still at its last point during stoppages);
  masked - ball removed during stoppages, like Metrica feeds. This uses the target to build
           the input, so it is a feed simulation only, never a model input in training.
Nothing here is selected: model, smoothing and baseline are already frozen.
"""
import argparse
import importlib.util
import json
import math
import pickle
import re
from pathlib import Path

import numpy as np

from clean_model.decoder import DecoderConfig
from clean_model.select import infer
from development.learned_dead_ball import predict_mask
from tools.idsse_data import HEAD, SECTIONS, XY

FPS = 25.0
PITCH = np.array([105.0, 68.0])
REPO = Path(__file__).resolve().parents[1]


def load_ball(pos_path):
    """Ball (F, 2) pitch-centred metres in the same frame order as tools.idsse_data.convert."""
    ball, cur = {}, None
    with open(pos_path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("<FrameSet"):
                section, team, _ = HEAD.search(line).groups()
                cur = section if team == "BALL" else None
                if cur:
                    ball[cur] = []
            elif cur and line.startswith("<Frame "):
                ball[cur].append([float(v) for v in XY.search(line).groups()])
            elif line.startswith("</FrameSet"):
                cur = None
    return np.array([p for s in SECTIONS for p in ball[s]])


def baseline(x):
    frozen = json.loads((REPO / "model.json").read_text())
    cfg = dict(frozen["base_config_at_10fps"])
    for key in ("confirmation_frames", "gap_frames", "hold_frames"):
        cfg[key] = int(math.ceil(cfg[key] * FPS / frozen["training_fps"]))
    return np.asarray(infer(x, DecoderConfig(**cfg), frozen["policy"])).astype("<U1")


def with_separator(labels, period):
    """Insert one X between halves so the scorer treats them as separate runs."""
    cut = int(np.argmax(period == 2))
    return np.concatenate([labels[:cut], ["X"], labels[cut:]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--dball", required=True, help="directory with model.pkl and model.json")
    ap.add_argument("--scorer", required=True, help="directory with organizer possession_metrics.py")
    ap.add_argument("--split", default="validation", choices=("validation", "holdout"))
    a = ap.parse_args()

    spec = importlib.util.spec_from_file_location("possession_metrics", Path(a.scorer) / "possession_metrics.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)

    plan = json.loads(Path(a.plan).read_text())
    fx = next(f for f in plan["fixtures"] if f["split"] == a.split)
    z = np.load(Path(a.data) / "npz" / f"{fx['id']}.npz")
    ball = load_ball(Path(a.data) / fx["files"]["positions"]["local_name"])
    dead, period = z["dead"], z["period"]
    assert len(ball) == len(dead)

    truth = np.where(dead, "D", np.where(z["possession"] == 1, "H", "A"))
    gt = pm.label_codes(with_separator(truth, period))

    meta = json.loads((Path(a.dball) / "model.json").read_text())
    model = pickle.loads((Path(a.dball) / "model.pkl").read_bytes())
    s = meta["smoothing"]
    players = z["players"].astype(float) + PITCH / 2
    n = len(dead)
    common = {"players": players, "teams": z["teams"], "period": np.ones(n, np.int8),
              "frame": np.arange(n), "fps": np.array(FPS), "pitch": PITCH,
              "player_detected": np.isfinite(players).all(2)}
    learned = predict_mask(model, common, (s["window_s"], s["threshold"], s["min_run_s"]))

    rows = []
    for feed in ("raw", "masked"):
        b = ball + PITCH / 2
        if feed == "masked":
            b = np.where(dead[:, None], np.nan, b)
        x = {**common, "ball": b, "ball_observed": np.isfinite(b).all(1)}
        base = baseline(x)
        variants = {"baseline": base,
                    "baseline + learned D": np.where(learned, "D", base),
                    "baseline + true D (oracle)": np.where(dead, "D", base)}
        for name, labels in variants.items():
            r = pm.evaluate(gt, pm.label_codes(with_separator(labels, period)))
            rows.append({"feed": feed, "variant": name, "spell_f1_mean": round(r["spell_f1_mean"], 3),
                         "spell_f1@0.5": round(r["spell_f1_at_headline"], 3), "macro_f1": round(r["macro_f1"], 3),
                         "alive_dead_f1": round(r["alive_dead_f1"], 3), "n_pred_spells": r["n_pred_spells"],
                         "n_gt_spells": r["n_gt_spells"]})
            print(json.dumps(rows[-1]))
    print(f"match {fx['id']} ({a.split}); learned D share {learned.mean():.3f}, true D share {dead.mean():.3f}")


if __name__ == "__main__":
    main()
