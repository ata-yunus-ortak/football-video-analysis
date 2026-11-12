"""Train the learned H/A possession model on IDSSE, select decoding by spellF1 on validation,
freeze, then check the holdout once. D comes from the frozen learned dead-ball model.

    python -m tools.train_learned_possession --plan learned-dead-ball-plan.json --data /private/idsse \
        --dball /private/learned-dead-ball-v2 --scorer /private/organizer-eval --out /private/learned-possession-v1

Target: DFL BallPossession (1 home -> H, 2 away -> A) on live frames (BallStatus == 1).
Augmentation per train match: clean + 3 copies with random player and ball damage.
Validation/holdout are scored with the organizer scorer on a ball feed that is missing during
stoppages (Metrica-like), clean and with heavy simulated damage. Same split as the D study.
"""
import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from development.learned_dead_ball import corrupt, predict_mask
from development.learned_possession import corrupt_ball, decode, features
from tools.idsse_spell_eval import baseline, load_ball, with_separator

FPS, SEED = 25.0, 0
PITCH = np.array([105.0, 68.0])
HEAVY = {"players": dict(missing_frac=0.3, jitter_m=0.8), "ball": dict(missing_frac=0.3, jitter_m=0.5)}
GRID = [(w, m, s) for w in (0.5, 1, 2) for m in (0.0, 0.1, 0.2) for s in (0, 0.5, 1, 2)]
REPO = Path(__file__).resolve().parents[1]
SOURCES = ("development/learned_possession.py", "development/learned_dead_ball.py",
           "tools/train_learned_possession.py")


def load_match(data, fx):
    z = np.load(Path(data) / "npz" / f"{fx['id']}.npz")
    ball = load_ball(Path(data) / fx["files"]["positions"]["local_name"])
    return {"players": z["players"].astype(float), "teams": z["teams"], "period": z["period"],
            "dead": z["dead"], "home": z["possession"] == 1, "ball": ball}


def damaged(m, rng, level):
    """(players, ball) centred metres, optionally damaged."""
    if level is None:
        return m["players"], m["ball"]
    return (corrupt(m["players"], rng, fps=FPS, **level["players"]),
            corrupt_ball(m["ball"], rng, fps=FPS, **level["ball"]))


def match_inputs(m, rng, level):
    """Repository-style inputs (corner metres, no half info) with the ball missing in stoppages."""
    players, ball = damaged(m, rng, level)
    ball = np.where(m["dead"][:, None], np.nan, ball)
    n = len(players)
    return {"players": players + PITCH / 2, "ball": ball + PITCH / 2, "teams": m["teams"],
            "period": np.ones(n, np.int8), "frame": np.arange(n), "fps": np.array(FPS), "pitch": PITCH,
            "ball_observed": np.isfinite(ball).all(1), "player_detected": np.isfinite(players).all(2)}


def main():
    ap = argparse.ArgumentParser()
    for k in ("plan", "data", "dball", "scorer", "out"):
        ap.add_argument(f"--{k}", required=True)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("possession_metrics", Path(a.scorer) / "possession_metrics.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    plan = json.loads(Path(a.plan).read_text())
    fixtures = {s: [f for f in plan["fixtures"] if f["split"] == s] for s in ("train", "validation", "holdout")}
    dmeta = json.loads((Path(a.dball) / "model.json").read_text())
    dmodel = pickle.loads((Path(a.dball) / "model.pkl").read_bytes())
    dsmooth = tuple(dmeta["smoothing"][k] for k in ("window_s", "threshold", "min_run_s"))

    rng = np.random.default_rng(SEED)
    xs, ys = [], []
    for fx in fixtures["train"]:
        m = load_match(a.data, fx)
        live = ~m["dead"]
        levels = [None] + [{"players": dict(missing_frac=float(rng.uniform(0, 0.5)), jitter_m=float(rng.uniform(0, 1.5))),
                            "ball": dict(missing_frac=float(rng.uniform(0, 0.5)), jitter_m=float(rng.uniform(0, 1.0)))}
                           for _ in range(3)]
        for level in levels:
            players, ball = damaged(m, rng, level)
            x, names = features(players, m["teams"], ball, m["period"], FPS, PITCH, origin="centre")
            keep = np.flatnonzero(live)[::5]
            xs.append(x[keep]); ys.append(m["home"][keep])
        print(f"features done: {fx['id']}", flush=True)
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                           l2_regularization=1.0, random_state=SEED)
    model.fit(np.vstack(xs), np.concatenate(ys).astype(int))
    del xs, ys

    def evaluate(fx, decoding=None):
        m = load_match(a.data, fx)
        truth = np.where(m["dead"], "D", np.where(m["home"], "H", "A"))
        gt = pm.label_codes(with_separator(truth, m["period"]))
        res = {}
        for name, level in (("clean", None), ("heavy", HEAVY)):
            x_in = match_inputs(m, np.random.default_rng(1), level)
            dmask = predict_mask(dmodel, x_in, dsmooth)
            xf, _ = features(x_in["players"], x_in["teams"], x_in["ball"], x_in["period"], FPS, PITCH)
            prob = model.predict_proba(xf)[:, 1]
            base = np.where(dmask, "D", baseline(x_in))

            def score(labels):
                r = pm.evaluate(gt, pm.label_codes(with_separator(labels, m["period"])))
                return {"spell_f1_mean": round(r["spell_f1_mean"], 3), "macro_f1": round(r["macro_f1"], 3),
                        "n_pred_spells": r["n_pred_spells"], "n_gt_spells": r["n_gt_spells"]}
            if decoding is None:
                res[name] = {"baseline_plus_learned_D": score(base),
                             "grid": {g: score(decode(prob, dmask, x_in["period"], FPS, *g))["spell_f1_mean"] for g in GRID}}
            else:
                res[name] = {"baseline_plus_learned_D": score(base),
                             "learned_possession_plus_learned_D": score(decode(prob, dmask, x_in["period"], FPS, *decoding))}
        return res

    val = evaluate(fixtures["validation"][0])
    best = max(GRID, key=lambda g: np.mean([val[k]["grid"][g] for k in val]))
    val_final = evaluate(fixtures["validation"][0], best)
    blob = pickle.dumps(model)
    (out / "model.pkl").write_bytes(blob)
    meta = {"version": "learned-possession-v1", "split": {k: [f["id"] for f in v] for k, v in fixtures.items()},
            "decoding": {"window_s": best[0], "margin": best[1], "min_spell_s": best[2]},
            "dead_ball_model_sha256": dmeta["model_sha256"], "validation": val_final,
            "model_sha256": hashlib.sha256(blob).hexdigest(),
            "source_sha256": {s: hashlib.sha256((REPO / s).read_bytes()).hexdigest() for s in SOURCES}}
    (out / "model.json").write_text(json.dumps(meta, indent=1))
    print("frozen decoding:", meta["decoding"], "validation:", json.dumps(val_final), flush=True)

    hold = evaluate(fixtures["holdout"][0], best)          # once, after freeze
    (out / "checks.json").write_text(json.dumps(hold, indent=1))
    print("holdout:", json.dumps(hold))


if __name__ == "__main__":
    main()
