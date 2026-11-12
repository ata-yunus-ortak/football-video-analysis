"""Automatic H/A/D submission from ATD tracking with the learned D and possession models.

    python -m tools.predict_submission --meta match_atd.xml --tracking match_atd.txt \
        --dball /private/learned-dead-ball-v2 --possession /private/learned-possession-v1 --out /private/sub-v1

Reads only the automatic ATD metadata and coordinates (same adapter as clean_model.run).
No video, tags, public reference or manual annotation is an input. Model files are checked
against the SHA-256 recorded at freeze time. Writes submission.csv (frame,label; one row per
tracking frame, 0-based) and inference.json. The output directory must not exist.
Inference is deterministic: running it twice gives the same file.
"""
import argparse
import csv
import hashlib
import json
import pickle
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from clean_model.atd import load
from development.learned_dead_ball import predict_mask
from development.learned_possession import decode, features


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen(directory):
    d = Path(directory)
    meta = json.loads((d / "model.json").read_text())
    if sha256(d / "model.pkl") != meta["model_sha256"]:
        raise ValueError(f"model.pkl in {d} does not match its frozen hash")
    return pickle.loads((d / "model.pkl").read_bytes()), meta


def predict_labels(x, dmodel, dmeta, pmodel, pmeta):
    s, dec = dmeta["smoothing"], pmeta["decoding"]
    fps = float(x["fps"])
    dead = predict_mask(dmodel, x, (s["window_s"], s["threshold"], s["min_run_s"]))
    f, _ = features(x["players"], x["teams"], x["ball"], x["period"], fps, x["pitch"])
    prob_home = pmodel.predict_proba(f)[:, 1]
    labels = decode(prob_home, dead, x["period"], fps, dec["window_s"], dec["margin"], dec["min_spell_s"])
    return labels, dead


def main():
    ap = argparse.ArgumentParser()
    for k in ("meta", "tracking", "dball", "possession", "out"):
        ap.add_argument(f"--{k}", required=True)
    a = ap.parse_args()
    dmodel, dmeta = frozen(a.dball)
    pmodel, pmeta = frozen(a.possession)
    if pmeta.get("dead_ball_model_sha256") != dmeta["model_sha256"]:
        raise ValueError("possession model was frozen with a different dead-ball model")

    root = ET.parse(a.meta).getroot()
    fps = float(root.findtext(".//FrameRate"))
    field = root.find(".//FieldSize")
    pitch = [float(field.findtext("Width")), float(field.findtext("Height"))]
    with Path(a.tracking).open(encoding="utf-8-sig") as f:
        frames = sum(1 for _ in f)
    x = load(a.meta, a.tracking, frames, fps, pitch)
    x["player_detected"] = np.isfinite(x["players"]).all(2)

    labels, dead = predict_labels(x, dmodel, dmeta, pmodel, pmeta)
    assert len(labels) == frames and set(labels) <= set("HAD")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    path = out / "submission.csv"
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["frame", "label"])
        w.writerows(zip(range(frames), labels))
    info = {"frames": frames, "fps": fps, "pitch": pitch,
            "dead_ball_model_sha256": dmeta["model_sha256"], "possession_model_sha256": pmeta["model_sha256"],
            "possession_decoding": pmeta["decoding"], "dead_ball_smoothing": dmeta["smoothing"],
            "input_metadata_sha256": sha256(a.meta), "input_tracking_sha256": sha256(a.tracking),
            "prediction_sha256": sha256(path), "public_reference_read": False, "manual_annotations_read": False,
            "video_read": False}
    (out / "inference.json").write_text(json.dumps(info, indent=2))
    print(f"wrote {path} ({frames} rows)")


if __name__ == "__main__":
    main()
