"""Diagnose and re-select possession decoding on the validation match only.

    python -m tools.tune_possession_decoding --plan learned-dead-ball-plan.json --data /private/idsse \
        --dball /private/learned-dead-ball-v2 --possession /private/learned-possession-v1 \
        --scorer /private/organizer-eval --out /private/possession-decoding-v2 [--holdout]

The possession and D models stay frozen; only decode() settings are searched.
Prints which true spells are missed, by duration, for the current decoding.
--holdout scores the selected decoding once on the holdout (second look: v1 already used it).
"""
import argparse
import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np

from development.learned_dead_ball import predict_mask
from development.learned_possession import decode, features
from tools.train_learned_possession import FPS, HEAVY, PITCH, load_match, match_inputs
from tools.idsse_spell_eval import with_separator

GRID = [(w, m, s) for w in (0.04, 0.2, 0.5) for m in (0.0, 0.05, 0.1, 0.2) for s in (0, 0.2, 0.5, 1)]


def prepare(a, fx, pm):
    dmeta = json.loads((Path(a.dball) / "model.json").read_text())
    dmodel = pickle.loads((Path(a.dball) / "model.pkl").read_bytes())
    pmodel = pickle.loads((Path(a.possession) / "model.pkl").read_bytes())
    ds = tuple(dmeta["smoothing"][k] for k in ("window_s", "threshold", "min_run_s"))
    m = load_match(a.data, fx)
    gt = pm.label_codes(with_separator(np.where(m["dead"], "D", np.where(m["home"], "H", "A")), m["period"]))
    feeds = {}
    for name, level in (("clean", None), ("heavy", HEAVY)):
        x = match_inputs(m, np.random.default_rng(1), level)
        f, _ = features(x["players"], x["teams"], x["ball"], x["period"], FPS, PITCH)
        feeds[name] = (pmodel.predict_proba(f)[:, 1], predict_mask(dmodel, x, ds), x["period"])
    return m, gt, feeds


def spell_score(pm, gt, labels, period):
    r = pm.evaluate(gt, pm.label_codes(with_separator(labels, period)))
    return r["spell_f1_mean"], r["macro_f1"], r["n_pred_spells"], r["n_gt_spells"]


def missed_by_duration(pm, gt, labels, period):
    pred = pm.label_codes(with_separator(labels, period))
    runs = pm.valid_runs(gt)
    g, p = pm.possession_spells(gt, runs), pm.possession_spells(pm.fill_abstentions(pred, runs), runs)
    hit = pm.matched_gt_flags(pm.spell_overlaps(g, p), len(g), 0.5)
    dur = np.array([(b - a) / FPS for a, b, _ in g])
    rows = []
    for lo, hi in ((0, 2), (2, 5), (5, 10), (10, 20), (20, 1e9)):
        sel = (dur >= lo) & (dur < hi)
        rows.append(f"{lo}-{hi if hi < 1e9 else 'inf'}s: {int(sel.sum())} spells, matched@0.5 {hit[sel].mean() if sel.any() else 0:.2f}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    for k in ("plan", "data", "dball", "possession", "scorer", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--holdout", action="store_true")
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("possession_metrics", Path(a.scorer) / "possession_metrics.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    plan = json.loads(Path(a.plan).read_text())
    fx = {f["split"]: f for f in plan["fixtures"] if f["split"] != "train"}
    v1 = json.loads((Path(a.possession) / "model.json").read_text())["decoding"]
    v1 = (v1["window_s"], v1["margin"], v1["min_spell_s"])

    m, gt, feeds = prepare(a, fx["validation"], pm)
    prob, dmask, period = feeds["clean"]
    print("v1 decoding", v1, "missed true spells by duration (validation, clean):")
    for row in missed_by_duration(pm, gt, decode(prob, dmask, period, FPS, *v1), period):
        print("  ", row)
    score = {g: np.mean([spell_score(pm, gt, decode(p, d, per, FPS, *g), per)[0] for p, d, per in feeds.values()])
             for g in GRID}
    best = max(score, key=score.get)
    result = {"v1": v1, "v1_mean_val_spell_f1": round(float(score.get(v1, np.nan)), 3) if v1 in score else None,
              "selected": best, "selected_mean_val_spell_f1": round(float(score[best]), 3), "validation": {}}
    for name, (p, d, per) in feeds.items():
        for tag, g in (("v1", v1), ("v2", best)):
            s = spell_score(pm, gt, decode(p, d, per, FPS, *g), per)
            result["validation"][f"{name}_{tag}"] = {"spell_f1_mean": round(s[0], 3), "macro_f1": round(s[1], 3),
                                                     "n_pred_spells": s[2], "n_gt_spells": s[3]}
    print("selected after missed-spell check:")
    for row in missed_by_duration(pm, gt, decode(prob, dmask, period, FPS, *best), period):
        print("  ", row)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "decoding.json").write_text(json.dumps({**result, "decoding": {"window_s": best[0], "margin": best[1],
                                                                          "min_spell_s": best[2]}}, indent=1))
    print(json.dumps(result, indent=1))
    if a.holdout:
        _, gth, fh = prepare(a, fx["holdout"], pm)
        hold = {f"{n}_{tag}": dict(zip(("spell_f1_mean", "macro_f1", "n_pred_spells", "n_gt_spells"),
                                       spell_score(pm, gth, decode(p, d, per, FPS, *g), per)))
                for n, (p, d, per) in fh.items() for tag, g in (("v1", v1), ("v2", best))}
        (out / "holdout.json").write_text(json.dumps(hold, indent=1))
        print("holdout (second look):", json.dumps(hold, indent=1))


if __name__ == "__main__":
    main()
