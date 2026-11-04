"""Audit registered external tracking and partial stoppage-event coverage.

This command does not select a model, assign D, or evaluate the supplied match.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import numpy as np
from development.dead_ball_features import extract
from development.metrica import load_tracking, load_events, candidate_stoppages
from .metrica_data import external_output, sha256, validate_plan, verify_file


def distribution(values):
    finite = np.asarray(values, float).reshape(-1)
    finite = finite[np.isfinite(finite)]
    return {"finite_count": len(finite), "min_q25_median_q75_max":
            np.quantile(finite, [0, .25, .5, .75, 1]).tolist() if len(finite) else None}


def _frozen_model(repo):
    model = json.loads((repo / "model.json").read_text(encoding="utf-8"))
    for name, expected in model["source_hashes"].items():
        if sha256(repo / "clean_model" / name) != expected:
            raise ValueError("Frozen inference source changed: " + name)
    return sha256(repo / "model.json")


def run(data, out):
    data = Path(data).resolve()
    plan = json.loads((data / "plan.json").read_text(encoding="utf-8"))
    validate_plan(plan)
    plan_hash = sha256(data / "plan.json")
    before = json.loads((data / "before-access.json").read_text(encoding="utf-8"))
    manifest = json.loads((data / "download-manifest.json").read_text(encoding="utf-8"))
    records = {name.replace("\\", "/"): value for name, value in manifest["files"].items()}
    if (before["plan_sha256"] != plan_hash or manifest["plan_sha256"] != plan_hash
            or before["before_tracking_and_event_download"] is not True):
        raise ValueError("External registration hashes differ")
    for fixture in plan["fixtures"]:
        for role, spec in fixture["files"].items():
            relative = Path("raw") / fixture["id"] / (role + ".csv")
            record = records[relative.as_posix()]
            if verify_file(data / relative, spec) != record["sha256"]:
                raise ValueError("External download manifest hash differs")
    repo = Path(__file__).resolve().parents[1]
    baseline_hash = _frozen_model(repo)
    source_paths = [Path(__file__), repo / "tools" / "metrica_data.py",
                    *sorted((repo / "development").glob("*.py"))]
    source_hashes = {path.relative_to(repo).as_posix(): sha256(path) for path in source_paths}
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    registration = {"plan_sha256": plan_hash, "source_sha256": source_hashes,
                    "model_sha256": baseline_hash, "before_audit": True,
                    "selection_performed": False}
    (out / "audit-registration.json").write_text(json.dumps(registration, indent=2), encoding="utf-8")
    reports = []
    for fixture in plan["fixtures"]:
        raw = data / "raw" / fixture["id"]
        inputs = load_tracking(raw / "home.csv", raw / "away.csv", plan["pitch_m"], plan["fps"])
        # Features are computed and written before loading events. Events are
        # evaluation evidence and never enter the inference feature dictionary.
        features = extract(inputs)
        prepared = out / fixture["id"]
        prepared.mkdir()
        np.savez_compressed(prepared / "inputs.npz", **inputs)
        np.savez_compressed(prepared / "features.npz", **features)
        events = load_events(raw / "events.csv")
        intervals, rejected = candidate_stoppages(events, inputs)
        (prepared / "candidate-stoppages.json").write_text(
            json.dumps({"target_kind": "partial_event_timing_proxy", "intervals": intervals,
                        "exhaustive_D_truth": False, "unknown_frames_assigned_D": 0,
                        "unpaired_exit_reasons": rejected}, indent=2), encoding="utf-8")
        mask = np.zeros(len(inputs["frame"]), bool)
        for interval in intervals:
            mask[interval["start_index"]:interval["stop_index_exclusive"]] = True
        restarts = [item for item in events if item["type"] == "SET PIECE"]
        observed_restarts = 0
        for event in restarts:
            index = int(np.searchsorted(inputs["source_frame"], event["start"]))
            if (index < len(mask) and inputs["source_frame"][index] == event["start"]
                    and inputs["period"][index] == event["period"]
                    and features["ball_present"][index]):
                observed_restarts += 1
        report = {
            "id": fixture["id"], "split": fixture["split"],
            "frames": len(mask), "fps": float(inputs["fps"]),
            "tracking_duration_s": len(mask) / float(inputs["fps"]),
            "period_frames": {str(p): int((inputs["period"] == p).sum()) for p in (1, 2)},
            "ball_finite_export_frames": int(features["ball_present"].sum()),
            "ball_missing_export_frames": int((~features["ball_present"]).sum()),
            "ball_outside_point_frames": int(features["ball_outside_point"].sum()),
            "observed_exit_steps": int(features["observed_exit_step"].sum()),
            "observed_return_steps": int(features["observed_return_step"].sum()),
            "feature_distributions": {name: distribution(features[name]) for name in (
                "ball_edge_margin_m", "ball_speed_mps", "median_player_speed_mps",
                "ball_missing_run_s", "observed_outside_run_s")},
            "event_type_counts": dict(Counter(item["type"] for item in events)),
            "restart_type_counts": dict(Counter(item["subtype"] for item in restarts)),
            "restart_ball_finite_export_count": observed_restarts,
            "paired_candidate_stoppages": len(intervals),
            "paired_restart_types": dict(Counter(item["restart_type"] for item in intervals)),
            "unpaired_exit_reasons": rejected,
            "candidate_interval_duration_s": distribution([item["duration_s"] for item in intervals]),
            "candidate_interval_frames": int(mask.sum()),
            "candidate_interval_ball_present_frames": int((mask & features["ball_present"]).sum()),
            "candidate_interval_outside_point_frames": int((mask & features["ball_outside_point"]).sum()),
            "prepared_sha256": {name: sha256(prepared / name) for name in (
                "inputs.npz", "features.npz", "candidate-stoppages.json")},
        }
        reports.append(report)
        print(json.dumps({"audited": fixture["id"], "frames": len(mask),
                          "candidate_intervals": len(intervals)}), flush=True)
    if (_frozen_model(repo) != baseline_hash
            or any(sha256(repo / name) != value for name, value in source_hashes.items())):
        raise ValueError("Source changed during audit")
    result = {
        "version": "dead-ball-coverage-v1", "plan_sha256": plan_hash,
        "repository": plan["repository"], "commit": plan["commit"],
        "source_sha256": source_hashes, "baseline_model_sha256": baseline_hash,
        "selection_performed": False, "model_promoted": False,
        "frozen_inference_sources_verified": True, "provided_fixture_used": False,
        "target_provenance": "Publisher events; annotation method not independently verified",
        "exhaustive_D_truth": False,
        "unknown_frames_assigned_D": 0, "official_competition_score": False,
        "fixtures": reports,
        "limitations": [
            "BALL OUT endpoints are provider event timestamps; whistle/boundary accuracy is unverified.",
            "Only exit/restart pairs without intervening recorded live actions are retained.",
            "Fouls, advantage, unpaired goal-kick recoveries and retakes need a separate target protocol.",
            "Ball/player finite flags do not establish independent visual detection confidence.",
            "No exhaustive live-play negatives, D targets, visual validation or held-out test are available.",
            "No numerical settings were selected; feature quantiles are descriptive coverage only.",
        ],
        "next_gate": "Validate independent D/live-play targets and event boundaries on external fixtures before D selection or promotion.",
    }
    (out / "report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.data, args.out)
