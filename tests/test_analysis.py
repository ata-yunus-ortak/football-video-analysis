from copy import deepcopy
import unittest

from football_video_analysis.analysis import analyze, interpolate_ball, possession
from football_video_analysis.config import Config
from football_video_analysis.demo import demo_config, sample_tracks
from football_video_analysis.geometry import PitchTransform
from football_video_analysis.tracks import validate_tracks


def frame(ball=None, players=None):
    return {"players": players if players is not None else {"7": {"bbox": [10, 10, 30, 50], "team": 1}}, "ball": ball, "referees": {}}


def ball(x=32, y=48):
    return {"bbox": [x - 2, y - 2, x + 2, y + 2]}


class BallRepairTests(unittest.TestCase):
    def test_fills_only_short_bounded_gap_and_marks_inference(self):
        raw = [frame(), frame(ball(10)), frame(), frame(), frame(ball(40)), frame()]
        fixed = interpolate_ball(raw, 2)
        self.assertIsNone(fixed[0]["ball"])
        self.assertIsNone(fixed[-1]["ball"])
        self.assertEqual(fixed[2]["ball"]["bbox"], [18.0, 46.0, 22.0, 50.0])
        self.assertTrue(fixed[3]["ball"]["interpolated"])
        self.assertIsNone(raw[2]["ball"], "analysis must not modify cached observations")

    def test_does_not_partially_fill_long_gap(self):
        fixed = interpolate_ball([frame(ball()), frame(), frame(), frame(), frame(ball())], 2)
        self.assertTrue(all(item["ball"] is None for item in fixed[1:4]))

    def test_all_missing_and_single_observation_are_safe(self):
        self.assertEqual(interpolate_ball([frame(), frame()], 10), [frame(), frame()])
        fixed = interpolate_ball([frame(), frame(ball()), frame()], 10)
        self.assertIsNone(fixed[0]["ball"])
        self.assertIsNone(fixed[2]["ball"])


class ControlTests(unittest.TestCase):
    def test_initial_unknown_never_reads_empty_history(self):
        rows = possession([frame(), frame(), frame(ball())], Config())
        self.assertEqual([row["team"] for row in rows], [0, 0, 1])

    def test_carry_expires_after_exact_grace(self):
        rows = possession([frame(ball()), frame(), frame(), frame(), frame()], Config(possession_grace_frames=2))
        self.assertEqual([row["status"] for row in rows], ["observed", "carried", "carried", "unknown", "unknown"])

    def test_visible_loose_ball_resets_control(self):
        rows = possession([frame(ball()), frame(ball(200, 200)), frame()], Config())
        self.assertEqual([row["team"] for row in rows], [1, 0, 0])

    def test_missing_owner_cannot_be_carried(self):
        rows = possession([frame(ball()), frame(players={})], Config())
        self.assertEqual(rows[-1]["team"], 0)

    def test_ambiguous_nearest_players_stay_unknown(self):
        players = {"1": {"bbox": [10, 10, 30, 50], "team": 1}, "2": {"bbox": [34, 10, 54, 50], "team": 2}}
        rows = possession([frame(ball(32, 50), players)], Config())
        self.assertEqual(rows[0]["team"], 0)

    def test_unknown_team_is_not_eligible(self):
        players = {"1": {"bbox": [10, 10, 30, 50], "team": 0}}
        self.assertEqual(possession([frame(ball(), players)], Config())[0]["team"], 0)


class MovementTests(unittest.TestCase):
    def test_source_fps_controls_speed_and_duration(self):
        data = sample_tracks()
        result = analyze(data, demo_config())
        self.assertEqual(result["summary"]["duration_seconds"], 4)
        self.assertAlmostEqual(result["summary"]["players"]["11"]["distance_m"], 4.95, places=6)
        self.assertAlmostEqual(result["summary"]["players"]["11"]["max_speed_kmh"], 4.5, places=6)
        data["fps"] = 50
        faster = analyze(data, demo_config())
        self.assertAlmostEqual(faster["summary"]["players"]["11"]["max_speed_kmh"], 9.0, places=6)
        self.assertEqual(faster["summary"]["duration_seconds"], 2)

    def test_no_calibration_omits_metric_claims(self):
        result = analyze(sample_tracks(), Config())
        self.assertFalse(result["summary"]["metric_coordinates_available"])
        self.assertEqual(result["summary"]["players"], {})
        self.assertIsNone(result["frames"][0]["players"]["11"]["pitch_position_m"])

    def test_cumulative_camera_translation_is_removed(self):
        data = sample_tracks()
        for index, item in enumerate(data["frames"]):
            shift = index * 2
            item["camera_offset_px"] = [shift, 0]
            for player in item["players"].values():
                player["bbox"][0] += shift
                player["bbox"][2] += shift
        result = analyze(data, demo_config())
        self.assertAlmostEqual(result["summary"]["players"]["11"]["distance_m"], 4.95, places=6)

    def test_absent_players_do_not_bridge_tracking_gap(self):
        data = sample_tracks()
        del data["frames"][1]["players"]["11"]
        result = analyze(data, demo_config())
        self.assertEqual(result["summary"]["players"]["11"]["valid_segments"], 97)
        self.assertAlmostEqual(result["summary"]["players"]["11"]["distance_m"], 4.85, places=6)

    def test_invalid_camera_frame_breaks_metric_continuity(self):
        data = sample_tracks()
        data["frames"][1]["camera_valid"] = False
        result = analyze(data, demo_config())
        self.assertEqual(result["summary"]["players"]["11"]["valid_segments"], 97)

    def test_single_frame_has_no_zero_duration_division(self):
        data = sample_tracks()
        data["frames"] = data["frames"][:1]
        data["frame_count"] = 1
        result = analyze(data, demo_config())
        self.assertEqual(result["summary"]["players"]["11"]["valid_segments"], 0)
        self.assertIsNone(result["summary"]["control"]["team_1_percent_known_frames"])

    def test_unphysical_jump_is_flagged_and_excluded(self):
        data = sample_tracks()
        data["frames"][1]["players"]["11"]["bbox"] = [700, 240, 720, 278]
        result = analyze(data, demo_config())
        self.assertEqual(result["summary"]["rejected_movement_segments"], 2)

    def test_configurable_override_has_no_specific_id_dependency(self):
        config = demo_config()
        config.team_overrides = {"11": 2}
        result = analyze(sample_tracks(), config)
        self.assertEqual(result["control"][2]["team"], 2)


class GeometryTests(unittest.TestCase):
    def test_known_correspondences_and_outside_point(self):
        transform = PitchTransform(demo_config().calibration)
        self.assertAlmostEqual(transform.point([480, 314])[0], 52.5)
        self.assertAlmostEqual(transform.point([480, 314])[1], 34)
        self.assertIsNone(transform.point([-10, 314]))

    def test_degenerate_and_crossed_calibration_rejected(self):
        with self.assertRaises(ValueError):
            PitchTransform({"pixel_points": [[0, 0]] * 4, "pitch_points_m": [[0, 0]] * 4})
        settings = deepcopy(demo_config().calibration)
        settings["pixel_points"][1], settings["pixel_points"][2] = settings["pixel_points"][2], settings["pixel_points"][1]
        with self.assertRaises(ValueError):
            PitchTransform(settings)


class SchemaTests(unittest.TestCase):
    def test_mismatched_frame_count_invalid_bbox_and_fps(self):
        for mutate in (lambda d: d.update(frame_count=9), lambda d: d.update(fps=0),
                       lambda d: d["frames"][0]["players"]["11"].update(bbox=[0, 0, 0, 2]),
                       lambda d: d["frames"][0]["players"]["11"].update(team=True)):
            data = sample_tracks()
            mutate(data)
            with self.assertRaises(ValueError):
                validate_tracks(data)

    def test_video_cache_requires_fingerprint(self):
        data = sample_tracks()
        data["source"] = {"kind": "video"}
        with self.assertRaises(ValueError):
            validate_tracks(data)
