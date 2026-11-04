import csv
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from development.dead_ball_features import extract
from development.metrica import load_tracking, candidate_stoppages
from tools.metrica_data import external_output, validate_plan, verify_file
from tools.dead_ball_audit import run as audit, sha256


def tracking(n=20, fps=25.):
    return {"ball": np.tile([20., 30.], (n, 1)),
            "players": np.tile([[20., 29.], [80., 40.]], (n, 1, 1)),
            "ball_observed": np.ones(n, bool), "period": np.ones(n, np.int8),
            "frame": np.arange(n), "source_frame": np.arange(1, n + 1),
            "fps": np.array(fps), "pitch": np.array([105., 68.])}


def event(kind, start, end=None, subtype="", period=1, row=2):
    return {"type": kind, "start": start, "end": start if end is None else end,
            "subtype": subtype, "period": period, "row": row}


class FeatureTests(unittest.TestCase):
    def test_missing_ball_is_not_outside_and_does_not_create_return(self):
        inputs = tracking(4)
        inputs["ball"][:] = [[-1, 20], [np.nan, np.nan], [2, 20], [3, 20]]
        inputs["ball_observed"][1] = False
        result = extract(inputs)
        self.assertFalse(result["ball_outside_point"][1])
        self.assertTrue(np.isnan(result["ball_edge_margin_m"][1]))
        self.assertTrue(np.isnan(result["ball_speed_mps"][2]))
        self.assertFalse(result["observed_return_step"].any())
        self.assertNotIn("labels", result)

    def test_period_boundary_resets_speed_and_wait_duration(self):
        inputs = tracking(4, fps=2.)
        inputs["ball"][:] = [-1, 20]
        inputs["period"][:] = [1, 1, 2, 2]
        inputs["players"][2:] += 100
        result = extract(inputs)
        np.testing.assert_allclose(result["observed_outside_run_s"], [0, .5, 0, .5])
        self.assertTrue(np.isnan(result["ball_speed_mps"][2]))
        self.assertTrue(np.isnan(result["median_player_speed_mps"][2]))

    def test_known_exit_return_and_metric_units(self):
        inputs = tracking(3, fps=2.)
        inputs["ball"][:] = [[1, 20], [-1, 20], [2, 20]]
        result = extract(inputs)
        np.testing.assert_array_equal(result["observed_exit_step"], [False, True, False])
        np.testing.assert_array_equal(result["observed_return_step"], [False, False, True])
        np.testing.assert_allclose(result["ball_speed_mps"][1:], [4, 6])
        np.testing.assert_allclose(result["ball_edge_margin_m"], [1, -1, 2])

    def test_targets_and_discontinuous_frames_are_rejected(self):
        inputs = tracking()
        with self.assertRaises(ValueError):
            extract({**inputs, "events": []})
        inputs["frame"][4] = 99
        with self.assertRaises(ValueError):
            extract(inputs)


class EventPairTests(unittest.TestCase):
    def test_excludes_both_event_boundaries(self):
        events = [event("BALL OUT", 3, 5), event("SET PIECE", 10, subtype="THROW IN", row=3),
                  event("PASS", 10, 12, row=4)]
        intervals, rejected = candidate_stoppages(events, tracking())
        self.assertEqual(rejected, {})
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0]["start_index"], 5)
        self.assertEqual(intervals[0]["stop_index_exclusive"], 9)

    def test_intervening_live_play_prevents_false_stoppage(self):
        events = [event("BALL OUT", 3, 5), event("PASS", 7, 8, row=3),
                  event("SET PIECE", 10, subtype="FREE KICK", row=4)]
        intervals, rejected = candidate_stoppages(events, tracking())
        self.assertEqual(intervals, [])
        self.assertEqual(rejected, {"intervening_live_action": 1})

    def test_does_not_pair_across_periods_or_relabel_unknown(self):
        events = [event("BALL OUT", 3, 5),
                  event("SET PIECE", 10, subtype="KICK OFF", period=2, row=3)]
        intervals, _ = candidate_stoppages(events, tracking())
        self.assertEqual(intervals, [])
        self.assertEqual(candidate_stoppages([], tracking()), ([], {}))

    def test_retaken_restart_is_unevaluated(self):
        events = [event("BALL OUT", 3, 5),
                  event("SET PIECE", 10, subtype="FREE KICK-RETAKEN", row=3)]
        intervals, rejected = candidate_stoppages(events, tracking())
        self.assertEqual(intervals, [])
        self.assertEqual(rejected, {"unsupported_or_retaken_restart": 1})

    def test_another_exit_blocks_pairing_even_with_unsorted_events(self):
        events = [event("SET PIECE", 15, subtype="THROW IN", row=4),
                  event("BALL OUT", 7, 8, row=3), event("BALL OUT", 3, 5)]
        intervals, rejected = candidate_stoppages(events, tracking())
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0]["exit_event_row"], 3)
        self.assertEqual(rejected, {"no_next_restart_before_another_exit": 1})


class AdapterTests(unittest.TestCase):
    def write_team(self, path, rows):
        with path.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerows([["", "", "", "Home", "", "", ""],
                              ["", "", "", "1", "", "", ""],
                              ["Period", "Frame", "Time [s]", "Player1", "", "Ball", ""], *rows])

    def test_normalization_one_based_source_and_missingness(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rows = [[1, 1, .04, .2, .5, 1.01, .5],
                    [1, 2, .08, .2, .5, "NaN", "NaN"]]
            for team in ("home", "away"):
                self.write_team(root / team, rows)
            inputs = load_tracking(root / "home", root / "away")
            np.testing.assert_allclose(inputs["ball"][0], [106.05, 34.])
            np.testing.assert_array_equal(inputs["source_frame"], [1, 2])
            np.testing.assert_array_equal(inputs["frame"], [0, 1])
            self.assertFalse(inputs["ball_observed"][1])

    def test_disagreeing_duplicate_ball_and_invalid_clock_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.write_team(root / "home", [[1, 1, .04, .2, .5, .5, .5]])
            self.write_team(root / "away", [[1, 1, .04, .2, .5, .6, .5]])
            with self.assertRaises(ValueError):
                load_tracking(root / "home", root / "away")
            self.write_team(root / "away", [[1, 1, 999, .2, .5, .5, .5]])
            with self.assertRaises(ValueError):
                load_tracking(root / "home", root / "away")


class ProvenanceTests(unittest.TestCase):
    def test_raw_content_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.csv"
            content = b"external sample\n"
            path.write_bytes(content)
            spec = {"bytes": len(content), "git_blob_sha1": hashlib.sha1(
                f"blob {len(content)}\0".encode() + content).hexdigest()}
            verify_file(path, spec)
            path.write_bytes(b"X" + content[1:])
            with self.assertRaises(ValueError):
                verify_file(path, spec)

    def test_plan_split_and_data_output_location_are_enforced(self):
        repo = Path(__file__).resolve().parents[1]
        plan = json.loads((repo / "dead-ball-data-plan.json").read_text())
        validate_plan(plan)
        plan["fixtures"][1]["split"] = "train"
        with self.assertRaises(ValueError):
            validate_plan(plan)
        with self.assertRaises(ValueError):
            external_output(repo / "outputs")

    def test_original_frozen_sources_still_match(self):
        repo = Path(__file__).resolve().parents[1]
        model = json.loads((repo / "model.json").read_text())
        for name, expected in model["source_hashes"].items():
            content = (repo / "clean_model" / name).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), expected, name)


class AuditIntegrationTests(unittest.TestCase):
    def test_synthetic_pipeline_keeps_partial_intervals_out_of_features(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / "data"
            data.mkdir()
            plan = json.loads((repo / "dead-ball-data-plan.json").read_text())
            plan["purpose"] = "SYNTHETIC integration test, not public sample measurements"
            records = {}
            for fixture in plan["fixtures"]:
                raw = data / "raw" / fixture["id"]
                raw.mkdir(parents=True)
                rows = [[1, frame, frame / 25., .2, .3,
                         "NaN" if 6 <= frame <= 9 else .5,
                         "NaN" if 6 <= frame <= 9 else .5] for frame in range(1, 21)]
                for team in ("home", "away"):
                    AdapterTests().write_team(raw / (team + ".csv"), rows)
                with (raw / "events.csv").open("w", newline="") as stream:
                    csv.writer(stream).writerows([
                        ["Type", "Subtype", "Period", "Start Frame", "End Frame"],
                        ["BALL OUT", "", 1, 3, 5], ["SET PIECE", "THROW IN", 1, 10, 10]])
                for role, spec in fixture["files"].items():
                    path = raw / (role + ".csv")
                    content = path.read_bytes()
                    spec["bytes"] = len(content)
                    spec["git_blob_sha1"] = hashlib.sha1(
                        f"blob {len(content)}\0".encode() + content).hexdigest()
                    records[path.relative_to(data).as_posix()] = {"sha256": sha256(path)}
            (data / "plan.json").write_text(json.dumps(plan))
            plan_hash = sha256(data / "plan.json")
            (data / "before-access.json").write_text(json.dumps({
                "plan_sha256": plan_hash, "before_tracking_and_event_download": True}))
            (data / "download-manifest.json").write_text(json.dumps({
                "plan_sha256": plan_hash, "files": records}))
            with contextlib.redirect_stdout(io.StringIO()):
                result = audit(data, root / "audit")
            self.assertFalse(result["model_promoted"])
            self.assertFalse(result["selection_performed"])
            self.assertEqual(result["unknown_frames_assigned_D"], 0)
            for fixture in result["fixtures"]:
                self.assertEqual(fixture["candidate_interval_frames"], 4)
                self.assertEqual(fixture["candidate_interval_ball_present_frames"], 0)
                with np.load(root / "audit" / fixture["id"] / "features.npz") as features:
                    self.assertNotIn("labels", features.files)
                    self.assertNotIn("events", features.files)
            from tools.motion_experiment import run as motion_run
            from dataclasses import asdict
            from development.motion_possession import MotionConfig
            from development.player_motion import DribbleConfig
            from development.team_transitions import TransitionConfig
            config = root / 'synthetic-config.json'
            config.write_text(json.dumps({'parameters': asdict(MotionConfig(
                .1, 3., 60., 4., .5, .3, .1, 3.)),
                'rationale': 'Synthetic plumbing test only, not selected football settings',
                'dribble_parameters': asdict(DribbleConfig(.8, .3, .5, 15., .3, .2, 1)),
                'transition_parameters': asdict(TransitionConfig(.2, 1., .8, .3, .5, 1))}))
            summaries = motion_run(root / 'audit', config, root / 'motion')
            self.assertEqual(len(summaries), 2)
            registration = json.loads((root / 'motion' / 'registration.json').read_text())
            self.assertFalse(registration['selected_release'])
            self.assertEqual(registration['config_sha256'], sha256(config))
            self.assertIsNotNone(registration['dribble_config'])
            self.assertIsNotNone(registration['transition_config'])
            with np.load(root / 'motion' / 'metrica-sample-1-team-transitions.npz') as transition:
                self.assertIn('team_change_cohort_counts', transition.files)
            with np.load(root / 'motion' / 'metrica-sample-1-player-motion.npz') as motion:
                self.assertIn('team_mean_velocity_mps', motion.files)
                self.assertIn('dribble_slot', motion.files)


if __name__ == "__main__":
    unittest.main()
