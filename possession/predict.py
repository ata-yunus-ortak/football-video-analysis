"""Competition match in, submission CSV out.

    python -m possession.predict --data DATA_DIR --models MODEL_DIR --out TEAM.csv

Reads only the automatic assets of the tactical recording: the ATD (tracking) and the Smart
Tagging. It never opens a ground-truth file. All learned weights and the decoder's switch cost
come from external matches (see possession.train / possession.evaluate).
"""
import argparse
import glob
import os
import xml.etree.ElementTree as ET

import numpy as np

from . import data, features
from .decode import decode
from .train import STRIDE, make_model, predict_symmetric

# Published by the organisers in DATA.md ("Which frames are graded"): the two halves as video
# frames, inclusive. Everything else is never scored and is written as X.
N_VIDEO_FRAMES = 199319
GRADED_BLOCKS = ((11185, 90651), (110808, 190197))
FPS = 25
LETTERS = np.array(["H", "A", "D"])


def kickoff_tag_starts(tagging_path):
    """Start frames of every 'Kick Off (Start)' set piece in the automatic Smart Tagging."""
    starts = []
    for instance in ET.parse(tagging_path).iter("instance"):
        tags = {label.findtext("group"): (label.findtext("text") or "")
                for label in instance.findall("label")}
        if ((instance.findtext("code") or "").strip().lower() == "set pieces"
                and tags.get("Type", "").strip().lower() == "kick off (start)"):
            starts.append(int(round(float(instance.findtext("start")) * FPS)))
    return sorted(starts)


def load_models(model_dir):
    import torch
    models = []
    for path in sorted(glob.glob(os.path.join(model_dir, "model_seed*.pt"))):
        model = make_model()
        model.load_state_dict(torch.load(path, map_location="cpu"))
        models.append(model.eval())
    if not models:
        raise IOError("no model_seed*.pt in %s -- run possession.train final first" % model_dir)
    return models


def half_probabilities(models, ball, team0, team1):
    feats, _ = features.build(ball, team0, team1)
    swapped, _ = features.build(ball, team1, team0)
    return predict_symmetric(models, feats, swapped)


def run(data_dir, model_dir, out_path, switch_cost):
    tactical = os.path.join(data_dir, "tactical")
    meta = os.path.join(tactical, "BAR-ATH_tactical_atd.xml")
    raw = os.path.join(tactical, "BAR-ATH_tactical_atd.txt")
    tagging = os.path.join(tactical, "BAR-ATH_tactical_smart_tagging.xml")

    frame_id, ball, team0, team1 = data.load_epts(meta, raw)
    video_frame = frame_id - 1  # DATA.md: video_frame = frame_id - 1
    row_of = np.full(N_VIDEO_FRAMES, -1, np.int64)
    row_of[video_frame] = np.arange(len(video_frame))

    models = load_models(model_dir)
    kickoffs = kickoff_tag_starts(tagging) if os.path.isfile(tagging) else []
    labels = np.full(N_VIDEO_FRAMES, "X", dtype="<U1")
    for first, last in GRADED_BLOCKS:
        rows = row_of[first:last + 1]
        if (rows < 0).any():
            raise ValueError("tracking does not cover video frames %d..%d" % (first, last))
        prob = half_probabilities(models, ball[rows], team0[rows], team1[rows])
        path = decode(prob, switch_cost, STRIDE, len(rows))
        block = LETTERS[path]
        # The ball cannot be in play before the half has kicked off. The automatic tagging marks
        # a window around each kick-off; everything in the block before that window is dead.
        inside = [k for k in kickoffs if first <= k <= last]
        if inside and inside[0] - first < 10 * 60 * FPS:
            block[:inside[0] - first] = "D"
        labels[first:last + 1] = block

    folder = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(folder, exist_ok=True)
    with open(out_path, "w") as handle:
        handle.write("frame,label\n")
        handle.writelines("%d,%s\n" % (i, label) for i, label in enumerate(labels))
    return labels


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default=os.environ.get("MTAH_DATA_DIR", "data"))
    parser.add_argument("--models", default="models")
    parser.add_argument("--out", required=True)
    parser.add_argument("--switch-cost", type=float, required=True,
                        help="decoder switch cost chosen on external matches")
    args = parser.parse_args()
    run(args.data, args.models, args.out, args.switch_cost)
    print("wrote", args.out)
