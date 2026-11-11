"""Train, select and freeze the learned dead-ball model, then run the one-time checks.

    python -m tools.train_learned_dead_ball --plan learned-dead-ball-plan.json \
        --data /private/idsse --out /private/learned-dead-ball-v2 [--metrica3 /private/metrica3]

1. Fit on train matches: each match clean + 3 random corruptions (seeded).
2. Select smoothing on the validation match: mean D F1 over clean / mild / heavy corruption.
3. Write model.pkl and model.json (split, settings, hashes), then evaluate the holdout once
   (clean + heavy) and, optionally, Metrica Sample Game 3 with event-derived partial proxies.
The output directory must not exist. Requires requirements-dball.txt.
"""
import argparse
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from development.learned_dead_ball import corrupt, features, smooth

FPS = 25.0
PITCH = (105.0, 68.0)
SEED = 0
LEVELS = {"clean": None, "mild": dict(missing_frac=0.1, jitter_m=0.3),
          "heavy": dict(missing_frac=0.3, jitter_m=0.8)}
GRID = [(w, t, m) for w in (1, 2, 4) for t in (0.4, 0.5, 0.6) for m in (1, 2, 4)]
REPO = Path(__file__).resolve().parents[1]
SOURCES = ("development/learned_dead_ball.py", "tools/train_learned_dead_ball.py", "tools/idsse_data.py")


def model_features(z, rng=None, level=None):
    players = z["players"] if level is None else corrupt(z["players"], rng, fps=FPS, **level)
    x, _ = features(players, z["teams"], z["period"], FPS, PITCH, origin="centre")
    return x


def runs(mask):
    d = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def report(dead, pred):
    tp = int(np.sum(pred & dead)); fp = int(np.sum(pred & ~dead)); fn = int(np.sum(~pred & dead))
    prec, rec = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    true, found = runs(dead), runs(pred)
    hits, start_err, end_err = 0, [], []
    for a, b in true:
        best = max(found, key=lambda r: min(b, r[1]) - max(a, r[0]), default=None)
        if best is not None and min(b, best[1]) > max(a, best[0]):
            hits += (min(b, best[1]) - max(a, best[0])) / (max(b, best[1]) - min(a, best[0])) >= 0.5
            start_err.append(abs(best[0] - a) / FPS); end_err.append(abs(best[1] - b) / FPS)
    return {"D_precision": round(prec, 3), "D_recall": round(rec, 3),
            "D_f1": round(2 * prec * rec / max(prec + rec, 1e-9), 3),
            "true_stoppages": len(true), "predicted_stoppages": len(found), "stoppages_iou50": int(hits),
            "median_abs_start_error_s": round(float(np.median(start_err)), 2) if start_err else None,
            "median_abs_end_error_s": round(float(np.median(end_err)), 2) if end_err else None}


def metrica3_check(directory, model, smoothing):
    from tools.metrica3_check import load_game3
    x, period, stop, live, pairs = load_game3(Path(directory), FPS, PITCH)
    pred = smooth(model.predict_proba(x)[:, 1], period, FPS, *smoothing)
    hit = [pred[a:b].mean() >= 0.5 for a, b in pairs]
    return {"stoppage_proxy_frame_recall": round(float(pred[stop].mean()), 3),
            "false_D_on_live_proxy": round(float(pred[live].mean()), 3),
            "stoppages_detected": f"{sum(hit)}/{len(hit)}", "predicted_D_share": round(float(pred.mean()), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--metrica3")
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text())
    split = {s: [f["id"] for f in plan["fixtures"] if f["split"] == s] for s in ("train", "validation", "holdout")}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    z = {m: np.load(Path(a.data) / "npz" / f"{m}.npz") for ids in split.values() for m in ids}

    rng = np.random.default_rng(SEED)
    xs, ys = [], []
    for m in split["train"]:
        levels = [None] + [dict(missing_frac=float(rng.uniform(0, 0.5)), jitter_m=float(rng.uniform(0, 1.5)))
                           for _ in range(3)]
        for level in levels:
            xs.append(model_features(z[m], rng, level)[::5]); ys.append(z[m]["dead"][::5])
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                           l2_regularization=1.0, random_state=SEED)
    model.fit(np.vstack(xs), np.concatenate(ys).astype(int))

    v = split["validation"][0]
    prob = {k: model.predict_proba(model_features(z[v], np.random.default_rng(1), lvl))[:, 1]
            for k, lvl in LEVELS.items()}
    score = {g: float(np.mean([report(z[v]["dead"], smooth(prob[k], z[v]["period"], FPS, *g))["D_f1"]
                               for k in LEVELS])) for g in GRID}
    best = max(score, key=score.get)
    validation = {k: report(z[v]["dead"], smooth(prob[k], z[v]["period"], FPS, *best)) for k in LEVELS}

    blob = pickle.dumps(model)
    (out / "model.pkl").write_bytes(blob)
    meta = {"version": plan["version"], "plan_sha256": hashlib.sha256(Path(a.plan).read_bytes()).hexdigest(),
            "split": split, "fps_trained": FPS, "seed": SEED,
            "augmentation": "per train match: clean + 3 copies, missing_frac~U(0,0.5), jitter_m~U(0,1.5)",
            "smoothing": {"window_s": best[0], "threshold": best[1], "min_run_s": best[2]},
            "validation": validation, "model_sha256": hashlib.sha256(blob).hexdigest(),
            "source_sha256": {s: hashlib.sha256((REPO / s).read_bytes()).hexdigest() for s in SOURCES}}
    (out / "model.json").write_text(json.dumps(meta, indent=1))
    print("frozen:", json.dumps(meta["smoothing"]), "validation:", json.dumps(validation))

    # one-time checks after the freeze; never feed these back into selection
    h = split["holdout"][0]
    checks = {f"holdout_{k}": report(z[h]["dead"], smooth(model.predict_proba(
        model_features(z[h], np.random.default_rng(2), LEVELS[k]))[:, 1], z[h]["period"], FPS, *best))
        for k in ("clean", "heavy")}
    if a.metrica3:
        checks["metrica_game3"] = metrica3_check(a.metrica3, model, best)
    (out / "checks.json").write_text(json.dumps(checks, indent=1))
    print("checks:", json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
