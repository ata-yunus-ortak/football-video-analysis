import csv
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock
import numpy as np
from development.homography import FrameHomographies
from development.vision_measurements import SceneChangeConfig, SceneContinuity, VisionMeasurements
from tools.vision_experiment import run
from tools.metrica_data import sha256
from tools.vision_preview import run as render_preview


def person(x=30, track=7):
    return {'kind': 'person', 'class_id': 1, 'confidence': .9, 'box_xyxy': [x - 10, 20, x + 10, 80],
            'anchor_xy': [x, 80], 'anchor_kind': 'feet_candidate', 'track_id': track,
            'team': None, 'measurement': True, 'ball_height_known': False}


def context(epoch=0, reset=False):
    return {'camera_epoch': epoch, 'continuity_reset': reset, 'frame_kind': 'unknown'}


def homographies(path, matrices, flags):
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream);writer.writerow(FrameHomographies.COLUMNS)
        for frame, (matrix, flag) in enumerate(zip(matrices, flags)):
            writer.writerow([frame, *np.asarray(matrix).reshape(-1), .2, flag])


class VisionMeasurementTests(unittest.TestCase):
    def test_scene_change_resets_epoch_without_claiming_replay_or_live(self):
        monitor = SceneContinuity(25., SceneChangeConfig(.2, .6, .08))
        black, white = np.zeros((8, 8, 3), np.uint8), np.full((8, 8, 3), 255, np.uint8)
        self.assertFalse(monitor.observe(black, 0, 0.)['continuity_reset'])
        frame = monitor.observe(white, 1, .04)
        self.assertTrue(frame['scene_change_candidate']);self.assertEqual(frame['camera_epoch'], 1)
        self.assertEqual(frame['frame_kind'], 'unknown');self.assertFalse(frame['live_or_replay_classified'])
        self.assertTrue(monitor.observe(white, 3, .12)['continuity_reset'])
        with self.assertRaises(ValueError): monitor.observe(white, 2, .16)

    def test_pixel_motion_stops_at_gaps_disappearance_or_camera_epoch(self):
        stream = VisionMeasurements(25.)
        stream.annotate([person()], 0, 0., 200, 100, context())
        rows, evidence = stream.annotate([person(32)], 1, .04, 200, 100, context())
        np.testing.assert_allclose(rows[0]['pixel_velocity_px_s'], [50., 0.])
        self.assertEqual(rows[0]['track_key'], '0:7');self.assertIsNone(rows[0]['team'])
        self.assertFalse(evidence['hybrid_ready'])
        stream.annotate([], 2, .08, 200, 100, context())
        rows, _ = stream.annotate([person(36)], 3, .12, 200, 100, context())
        self.assertIsNone(rows[0]['pixel_velocity_px_s'])
        rows, _ = stream.annotate([person(38)], 4, .16, 200, 100, context(1, True))
        self.assertEqual(rows[0]['track_key'], '1:7');self.assertIsNone(rows[0]['pixel_velocity_px_s'])
        rows, _ = stream.annotate([person(40)], 6, .24, 200, 100, context(1))
        self.assertIsNone(rows[0]['pixel_velocity_px_s'])

    def test_projection_is_source_indexed_and_ball_height_remains_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'geometry.csv'
            homographies(path, [np.diag([100, 50, 1]), np.full((3, 3), np.nan),
                               np.diag([200, 100, 1]), np.diag([200, 100, 1])], [1, 0, 1, 1])
            stream = VisionMeasurements(25., FrameHomographies(path), [100, 50])
            rows, _ = stream.annotate([person()], 2, .08, 200, 100, context())
            np.testing.assert_allclose(rows[0]['pitch_xy_m'], [15, 40])
            rows, _ = stream.annotate([person(32)], 3, .12, 200, 100, context())
            np.testing.assert_allclose(rows[0]['pitch_velocity_mps'], [25, 0])
            self.assertFalse(rows[0]['calibration_validated'])
            ball = dict(person(), kind='sports ball', class_id=37, track_id=None, anchor_kind='image_ball_center')
            stream = VisionMeasurements(25., FrameHomographies(path), [100, 50])
            rows, evidence = stream.annotate([ball, dict(ball, confidence=.7)], 0, 0., 200, 100, context())
            self.assertEqual(evidence['ball_candidate_count'], 2)
            self.assertTrue(all(row['pitch_xy_m'] is None and not row['ball_ground_valid'] for row in rows))
            stream = VisionMeasurements(25., FrameHomographies(path), [100, 50])
            rows, _ = stream.annotate([person()], 1, .04, 200, 100, context())
            self.assertIsNone(rows[0]['pitch_xy_m'])

    def test_truncated_anchors_and_duplicate_tracks_do_not_create_ground_or_motion(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'geometry.csv';homographies(path, [np.diag([200, 100, 1])], [1])
            stream = VisionMeasurements(25., FrameHomographies(path), [100, 50])
            rows, _ = stream.annotate([person(10)], 0, 0., 200, 100, context())
            self.assertEqual(rows[0]['projection_status'], 'anchor_truncated')
            self.assertIsNone(rows[0]['pitch_xy_m'])
        stream = VisionMeasurements(25.)
        stream.annotate([person()], 0, 0., 200, 100, context())
        rows, _ = stream.annotate([person(32), person(70)], 1, .04, 200, 100, context())
        self.assertTrue(all(row['track_identity_ambiguous'] and row['track_key'] is None for row in rows))
        self.assertTrue(all(row['pixel_velocity_px_s'] is None for row in rows))

    def setup_config(self, root):
        video, weights = root / 'synthetic.mp4', root / 'synthetic.pth'
        video.write_bytes(b'synthetic-video');weights.write_bytes(b'synthetic-weight-never-loaded')
        spec = {'fixture': {'id': 'synthetic-v2', 'source_kind': 'synthetic_fixture',
                    'provided_fixture_used': False, 'provenance': 'Generated unit fixture', 'video_sha256': sha256(video)},
            'rationale': 'Synthetic adapter test, no parameter selection',
            'weights': {'path': str(weights), 'sha256': sha256(weights), 'size': 'nano',
                        'license': 'Apache-2.0', 'source_url': 'synthetic-test'},
            'start_frame': 0, 'max_frames': 2,
            'scene_change_parameters': {'pixel_difference_threshold': .2, 'changed_fraction_threshold': .6, 'max_pair_gap_s': .08},
            'parameters': dict(size='nano', threshold=.3, sliced=False, slice_height=256, slice_width=256,
                overlap_ratio=.2, track_activation_threshold=.3, track_matching_threshold=.8,
                lost_track_s=1., min_consecutive_frames=1)}
        config = root / 'config.json';config.write_text(json.dumps(spec))
        return video, config, spec

    def test_runner_resets_tracker_on_cut_and_retains_empty_frame_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);video, config, _ = self.setup_config(root)
            reset = Mock();engine = SimpleNamespace(process=lambda _: [], reset_tracking=reset)
            frames = lambda _: iter([(0, 0., 25., np.zeros((8, 8, 3), np.uint8)),
                (1, .04, 25., np.full((8, 8, 3), 255, np.uint8))])
            summary = run(video, config, root / 'out', frame_reader=frames, factory=lambda *_: engine)
            reset.assert_called_once();self.assertEqual(summary['tracking_resets'], 1)
            rows = [json.loads(line) for line in (root / 'out' / 'observations.jsonl').read_text().splitlines()]
            self.assertEqual(rows[1]['objects'], []);self.assertEqual(rows[1]['frame_evidence']['camera_epoch'], 1)

    def test_missing_registered_frame_and_wrong_geometry_provenance_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);video, config, spec = self.setup_config(root)
            frames = lambda _: iter([(0, 0., 25., np.zeros((8, 8, 3), np.uint8)),
                (2, .08, 25., np.zeros((8, 8, 3), np.uint8))])
            with self.assertRaises(ValueError):
                run(video, config, root / 'gap', frame_reader=frames, factory=lambda *_: SimpleNamespace(process=lambda _: []))
            self.assertFalse((root / 'gap' / 'summary.json').exists())
            path = root / 'geometry.csv';homographies(path, [np.eye(3)], [1])
            spec['geometry'] = {'path': str(path), 'sha256': sha256(path), 'pitch_m': [100, 50],
                                'fixture_id': 'another-fixture', 'source_video_sha256': spec['fixture']['video_sha256']}
            config.write_text(json.dumps(spec));factory = Mock()
            with self.assertRaises(ValueError): run(video, config, root / 'wrong', factory=factory)
            factory.assert_not_called()

    def test_preview_refuses_provided_fixture_or_incomplete_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for source_kind, count in [('provided_fixture', 2), ('permitted_external_video', 1)]:
                (root / 'registration.json').write_text(json.dumps({'provided_fixture_used': False,
                    'config': {'fixture': {'source_kind': source_kind, 'provided_fixture_used': False}, 'max_frames': 2}}))
                (root / 'summary.json').write_text(json.dumps({'processed_frames': count}))
                with self.assertRaises(ValueError): render_preview(root, root / 'out')
                self.assertFalse((root / 'out').exists())
