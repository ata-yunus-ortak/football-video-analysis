"""Score predictions on external matches with the organisers' own metric code.

    python -m possession.evaluate --oof DIR --metrics PATH/TO/evaluation

Reads the out-of-fold probabilities written by `possession.train cv`, sweeps the decoder's
switch cost and reports spellF1 / macroF1 per external match. This is where every decoding
hyper-parameter is chosen -- on other games, never on the competition match.
"""
import argparse
import glob
import os
import sys

import numpy as np

from .decode import decode
from .train import STRIDE, match_of


def score(pm, truth, pred):
    result = pm.evaluate(truth.astype(np.int64), pred.astype(np.int64))
    return result["spell_f1_mean"], result["macro_f1"]


def load_oof(oof_dir, tag):
    out = {}
    for path in sorted(glob.glob(os.path.join(oof_dir, "oof_*_%s.npz" % tag))):
        blob = np.load(path)
        out[os.path.basename(path)[4:-4]] = (blob["p"], blob["y"])
    return out


def sweep(pm, oof, costs):
    rows = {}
    for cost in costs:
        per_match = {}
        for name, (prob, truth) in oof.items():
            pred = decode(prob, cost, STRIDE, len(truth))
            per_match.setdefault(match_of(name), []).append(score(pm, truth, pred))
        rows[cost] = {m: np.mean(v, axis=0) for m, v in per_match.items()}
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oof", required=True)
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--tags", nargs="+", default=["eval2", "eval5", "eval8"])
    parser.add_argument("--costs", nargs="+", type=float, default=[0, 2, 4, 6, 8, 12, 16, 24])
    args = parser.parse_args()
    sys.path.insert(0, args.metrics)
    import possession_metrics as pm

    for tag in args.tags:
        oof = load_oof(args.oof, tag)
        if not oof:
            continue
        rows = sweep(pm, oof, args.costs)
        print("\n%s  (%d halves)" % (tag, len(oof)))
        matches = sorted(next(iter(rows.values())))
        print("cost   spellF1 macroF1 | spellF1 per match: " + " ".join(m[-6:] for m in matches))
        for cost, per in rows.items():
            mean = np.mean(list(per.values()), axis=0)
            print("%5.1f  %.4f  %.4f  | %s" % (cost, mean[0], mean[1],
                                               " ".join("%.3f " % per[m][0] for m in matches)))
