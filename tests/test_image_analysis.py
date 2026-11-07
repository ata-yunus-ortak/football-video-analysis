import copy
import json
from pathlib import Path
import tempfile
import unittest

from development.image_analysis import ImageAnalysis
from tools.match_analysis import integrate, run
from tools.metrica_data import sha256
from tools.vision_review import project_observations


def observation(frame=0, epoch=0):
    row = {'kind': 'person', 'confidence': .9, 'box_xyxy': [1, 2, 10, 20], 'anchor_xy': [5, 20],
           'track_key': f'{epoch}:1', 'camera_epoch': epoch, 'person_role': 'unknown', 'team': None,
           'hybrid_usable': False, 'calibration_validated': False, 'ball_ground_valid': False,
           'measurement': True, 'pixel_velocity_px_s': None, 'pitch_xy_m': None}
    return {'source_frame': frame, 'video_time_s': frame / 25, 'fps': 25, 'width': 100, 'height': 80,
            'objects': [row], 'possession_inferred': False,
            'frame_evidence': {'camera_epoch': epoch, 'teams_assigned': False, 'hybrid_ready': False}}


class ImageContractTests(unittest.TestCase):
    def test_identity_is_source_scoped_and_never_player_or_referee(self):
        a = ImageAnalysis('camera-A').consume(observation())
        b = ImageAnalysis('camera-B').consume(observation())
        self.assertNotEqual(a['objects'][0]['image_track_id'], b['objects'][0]['image_track_id'])
        self.assertEqual(a['objects'][0]['person_role'], 'unknown')
        self.assertIsNone(a['objects'][0]['canonical_player_id'])
        self.assertFalse(a['fusion_eligible'])

    def test_empty_frames_and_all_ball_candidates_survive_without_invented_owner(self):
        engine = ImageAnalysis('source')
        empty = observation();empty['objects'] = []
        self.assertEqual(engine.consume(empty)['objects'], [])
        frame = observation(1)
        ball = dict(frame['objects'][0], kind='sports ball', person_role=None, track_key=None)
        frame['objects'] = [ball, copy.deepcopy(ball)]
        result = engine.consume(frame)
        self.assertEqual(len(result['objects']), 2)
        self.assertTrue(all(not r['selected_in_play_ball'] for r in result['objects']))
        self.assertIsNone(result['possession'])

    def test_duplicate_track_has_no_velocity_and_camera_epoch_cannot_go_back(self):
        engine = ImageAnalysis('source')
        frame = observation(epoch=1)
        frame['objects'][0]['pixel_velocity_px_s'] = [2, 3]
        frame['objects'].append(copy.deepcopy(frame['objects'][0]))
        result = engine.consume(frame)
        self.assertTrue(all(r['image_track_id'] is None and r['image_velocity_px_s'] is None for r in result['objects']))
        with self.assertRaises(ValueError): engine.consume(observation(1, epoch=0))

    def test_reference_labels_forged_roles_and_missing_frames_rejected(self):
        for field in ('labels', 'reference', 'events'):
            frame = observation();frame[field] = []
            with self.subTest(field=field), self.assertRaises(ValueError): ImageAnalysis('source').consume(frame)
        frame = observation();frame['objects'][0]['person_role'] = 'referee'
        with self.assertRaises(ValueError): ImageAnalysis('source').consume(frame)
        engine = ImageAnalysis('source');engine.consume(observation())
        with self.assertRaises(ValueError): engine.consume(observation(2))


class IntegrationTests(unittest.TestCase):
    def test_completed_run_produces_project_frames_without_reference_access(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root);source = root / 'run';source.mkdir()
            video = root / 'synthetic-video.bin';video.write_bytes(b'synthetic source integrity fixture')
            spec = {'start_frame': 0, 'max_frames': 2, 'fixture': {
                'id': 'synthetic', 'source_kind': 'synthetic_fixture', 'provided_fixture_used': False,
                'video_sha256': sha256(video)}}
            repo = Path(__file__).resolve().parents[1]
            reg = {'provided_fixture_used': False, 'config': spec, 'video_path': str(video),
                   'config_sha256': 'a' * 64, 'source_sha256': {name: sha256(repo / name) for name in
                       ('tools/vision_experiment.py', 'development/vision.py',
                        'development/vision_measurements.py', 'development/homography.py')}}
            (source / 'registration.json').write_text(json.dumps(reg))
            (source / 'summary.json').write_text(json.dumps({'processed_frames': 2,
                'possession_inferred': False, 'teams_assigned': False}))
            (source / 'observations.jsonl').write_text('\n'.join(json.dumps(observation(i)) for i in range(2)))
            result = integrate(source, root / 'analysis')
            self.assertEqual(result['frames'], 2)
            self.assertFalse(result['reference_annotations_read'])
            self.assertEqual(len((root / 'analysis/frames.jsonl').read_text().splitlines()), 2)
            temporal = integrate(source, root / 'temporal', repo / 'ball-tracking-plan.json')
            self.assertIn('ball_tracking', temporal)
            temporal_view = project_observations(root / 'temporal', reg, source / 'observations.jsonl')
            self.assertEqual(temporal_view[0]['ball_tracking']['tracks'], [])
            displayed = project_observations(root / 'analysis', reg, source / 'observations.jsonl')
            self.assertEqual(displayed[0]['objects'][0]['box_xyxy'], [1, 2, 10, 20])
            self.assertEqual(displayed[0]['objects'][0]['track_id'], '0:1')
            packets = [json.loads(line) for line in (root / 'analysis/frames.jsonl').read_text().splitlines()]
            packets[0]['objects'][0]['person_role'] = 'referee'
            (root / 'analysis/frames.jsonl').write_text('\n'.join(json.dumps(p) for p in packets))
            result['output_sha256'] = sha256(root / 'analysis/frames.jsonl')
            (root / 'analysis/summary.json').write_text(json.dumps(result))
            with self.assertRaises(ValueError):
                project_observations(root / 'analysis', reg, source / 'observations.jsonl')
            reg['provided_fixture_used'] = True
            (source / 'registration.json').write_text(json.dumps(reg))
            with self.assertRaises(ValueError): integrate(source, root / 'refused')

    def test_two_modes_cannot_be_mixed(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError): run(root, vision_run='run', video='video', config='config')
