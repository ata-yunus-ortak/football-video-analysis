import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from development.vision import VisionConfig, ground_projection, observation_rows
from development.video_sync import ClockSyncConfig, clock_candidates
from tools.vision_experiment import run
from tools.metrica_data import sha256
from tools.vision_reference_audit import inspect_reference


# Synthetic API fixtures; these are not externally selected model thresholds.
PARAMS = dict(size='nano', threshold=.3, sliced=False, slice_height=256, slice_width=256,
              overlap_ratio=.2, track_activation_threshold=.3, track_matching_threshold=.8,
              lost_track_s=1., min_consecutive_frames=1)


def reading(t, clock, period=1, confidence=.99):
    return dict(video_time_s=t, clock_s=clock, period=period, confidence=confidence,
                source_kind='automatic_clock_observation')


class ClockTests(unittest.TestCase):
    cfg = ClockSyncConfig(.8, .5, 2., 1.)

    def test_unique_clock_is_candidate_never_frame_accurate_fusion(self):
        r = clock_candidates([reading(2, 61)], [reading(7, 61), reading(7.5, 61)], self.cfg)[0]
        self.assertEqual(r['broadcast_interval_s'], [6.5, 8.])
        self.assertFalse(r['usable_for_possession'])

    def test_replay_repeated_clock_and_frozen_clock_rejected(self):
        for times in ([7, 7.5, 100, 100.5], [7, 7.5, 8, 8.5, 9, 9.5]):
            r = clock_candidates([reading(2, 61)], [reading(t, 61) for t in times], self.cfg)[0]
            self.assertIsNone(r['broadcast_interval_s'])

    def test_halves_unknown_and_low_confidence(self):
        for aux in ([reading(7, 61, period=2)], [reading(7, 61, confidence=.2)], []):
            self.assertIsNone(clock_candidates([reading(2, 61)], aux, self.cfg)[0]['broadcast_interval_s'])
        with self.assertRaises(ValueError):
            clock_candidates([dict(reading(2, 61), source_kind='manual')], [], self.cfg)


class VisionGeometryTests(unittest.TestCase):
    def test_projection_and_horizon_are_explicit(self):
        np.testing.assert_allclose(ground_projection([[4, 8]], np.diag([.5, .25, 1])), [[2, 2]])
        h = np.array([[1, 0, 0], [0, 1, 0], [1, 0, -2.]])
        self.assertTrue(np.isnan(ground_projection([[2, 3]], h)).all())
        with self.assertRaises(ValueError): ground_projection([[2, 3]], np.zeros((3, 3)))

    def test_untracked_players_all_balls_and_clipping_keep_uncertainty(self):
        detections = SimpleNamespace(xyxy=np.array([[-1., 2, 5, 10], [10, 10, 12, 12], [8, 4, 9, 5]]),
            confidence=np.array([.9, .8, .7]), class_id=np.array([1, 37, 37]))
        tracked = SimpleNamespace(xyxy=detections.xyxy[:1], class_id=np.array([1]), tracker_id=np.array([42]))
        rows = observation_rows(detections, tracked, {1: 'person', 37: 'sports ball'}, 20, 20)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['track_id'], 42)
        self.assertEqual(rows[0]['anchor_xy'][1], 10.)
        self.assertEqual(rows[1]['anchor_xy'], [11., 11.])
        self.assertTrue(all(r['team'] is None and not r['ball_height_known'] for r in rows))
        tracked.tracker_id = None
        self.assertIsNone(observation_rows(detections, tracked, {1: 'person', 37: 'sports ball'}, 20, 20)[0]['track_id'])

    def test_invalid_configs(self):
        for changes in ({'size': 'xlarge'}, {'threshold': float('nan')}, {'overlap_ratio': 1.},
                        {'sliced': 1}, {'slice_width': 0}):
            with self.assertRaises(ValueError): VisionConfig(**{**PARAMS, **changes})


class VisionRegistrationTests(unittest.TestCase):
    def test_reference_schema_disagreements_not_silently_reinterpreted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'reference.txt'
            path.write_text('0,7,10,20,5,10,-1,-1,-1,-1\n', encoding='utf-8')
            r = inspect_reference(path, 100, 100, 50)
            self.assertEqual(r['minimum_reference_frame'], 0)
            self.assertFalse(r['matches_documented_mot_contract'])
            self.assertIsNone(r['frame_base_selected'])
            path.write_text('1,7,10,20,5,10,1,1,1,-1\n', encoding='utf-8')
            r = inspect_reference(path, 100, 100, 50)
            self.assertTrue(r['matches_documented_mot_contract'])
            self.assertFalse(r['accuracy_evaluation_approved'])

    def setup_fixture(self, root):
        video, weights = root / 'synthetic.mp4', root / 'test.pth'
        video.write_bytes(b'synthetic-container-placeholder')
        weights.write_bytes(b'fake-never-loaded-test-weight')
        spec = {'fixture': {'id': 'synthetic-test', 'source_kind': 'synthetic_fixture',
                'provided_fixture_used': False, 'provenance': 'Generated unit fixture',
                'video_sha256': sha256(video)}, 'rationale': 'API engineering test, not selection',
                'weights': {'path': str(weights), 'sha256': sha256(weights), 'license': 'Apache-2.0',
                            'size': 'nano', 'source_url': 'synthetic-test-only'},
                'parameters': PARAMS, 'start_frame': 0, 'max_frames': 2}
        config = root / 'config.json';config.write_text(json.dumps(spec), encoding='utf-8')
        return video, config, spec

    def test_registered_runner_keeps_empty_frames_and_pts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);video, config, _ = self.setup_fixture(root)
            engine = SimpleNamespace(process=lambda rgb: [])
            frames = lambda _: iter([(0, 0., 25., np.zeros((8, 8, 3), np.uint8)),
                                     (1, .04, 25., np.zeros((8, 8, 3), np.uint8))])
            r = run(video, config, root / 'out', factory=lambda *args: engine, frame_reader=frames)
            self.assertEqual(r['processed_frames'], 2)
            self.assertFalse(r['accuracy_evaluated'])
            rows = [json.loads(l) for l in (root / 'out' / 'observations.jsonl').read_text().splitlines()]
            self.assertEqual(rows[1]['video_time_s'], .04)
            self.assertEqual(rows[1]['objects'], [])

    def test_provided_fixture_and_changed_hash_fail_before_model_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);video, config, spec = self.setup_fixture(root)
            for changes in ({'source_kind': 'provided_fixture'}, {'video_sha256': 'bad'}):
                spec['fixture'].update(changes)
                config.write_text(json.dumps(spec), encoding='utf-8')
                with patch('tools.vision_experiment.LocalVision') as factory:
                    with self.assertRaises(ValueError): run(video, config, root / 'out', factory=factory)
                    factory.assert_not_called()

    def test_truncated_or_nonmonotonic_video_has_no_success_summary(self):
        for mode in ('truncated', 'nonmonotonic'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp);video, config, _ = self.setup_fixture(root)
                rows = [(0, 0., 25., np.zeros((8, 8, 3), np.uint8))]
                if mode == 'nonmonotonic': rows += [(1, 0., 25., rows[0][3])]
                engine = SimpleNamespace(process=lambda rgb: [])
                with self.assertRaises(ValueError):
                    run(video, config, root / 'out', factory=lambda *args: engine,
                        frame_reader=lambda _: iter(rows))
                self.assertFalse((root / 'out' / 'summary.json').exists())


if __name__ == '__main__':
    unittest.main()
