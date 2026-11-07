import copy
import json
from pathlib import Path
import tempfile
import unittest

from development.ball_tracking_support import SupportConfig, assess, cross_check, project_ground_ball
from tools.ball_support_experiment import run
from tools.metrica_data import sha256


CONFIG = SupportConfig(.02, .005, .02)


def packet(frame=0, source='tactical', positions=((100, 100), (400, 200))):
    rows, tracks = [], []
    for i, (x, y) in enumerate(positions):
        key = f'{source}/{frame}/{i}'
        rows.append({'kind': 'ball_candidate', 'detection_id': key, 'image_xy_px': [x, y],
                     'box_xyxy_px': [x-2, y-2, x+2, y+2], 'confidence': .8})
        tracks.append({'track_id': f'{source}/ball/{i}', 'state': 'observed', 'measurement': True,
                       'detection_id': key, 'measured_position_px': [x, y], 'predicted_position_px': None})
    return {'source_id': source, 'source_frame': frame, 'video_time_s': frame / 25,
            'camera_epoch': 0, 'image_size_px': [1000, 500], 'objects': rows,
            'ball_tracking': {'tracks': tracks}, 'fusion_eligible': False, 'possession': None}


def hint(p):
    return {**{k: p[k] for k in ('source_id', 'source_frame', 'video_time_s', 'camera_epoch')},
            'tracking_source_id': 'automatic-epts', 'tracking_sample_id': 'sample-0',
            'tracking_sha256': 'a'*64, 'origin': 'automatic_tracking', 'measurement': True,
            'alignment_validated': True, 'clock_error_bound_s': .01,
            'calibration_validated': True, 'ground_validated': True,
            'frame_kind': 'live', 'projected_xy_px': [101, 100]}


class TrackingSupportTests(unittest.TestCase):
    def test_candidate_is_supported_without_changing_raw_or_ownership(self):
        p = packet(); original = copy.deepcopy(p)
        result = assess(p, hint(p), CONFIG)
        self.assertEqual(result['candidate_detection_id'], 'tactical/0/0')
        self.assertEqual(p, original)
        self.assertTrue(result['measurement'])
        self.assertFalse(result['selected_in_play_ball'])
        self.assertFalse(result['fusion_eligible'])
        self.assertIsNone(result['possession'])

    def test_missing_support_never_fabricates_measurement(self):
        result = assess(packet(), None, CONFIG)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIsNone(result['candidate_detection_id'])
        self.assertFalse(result['measurement'])

    def test_unverified_geometry_clock_replay_and_estimates_abstain(self):
        p = packet()
        cases = [('calibration_validated', False), ('ground_validated', False),
                 ('alignment_validated', False), ('measurement', False),
                 ('clock_error_bound_s', .03), ('video_time_s', .1),
                 ('source_frame', 1), ('source_id', 'other'), ('camera_epoch', 1),
                 ('frame_kind', 'replay'), ('frame_kind', 'close_up'),
                 ('projected_xy_px', [-1, 100]), ('projected_xy_px', None)]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                result = assess(p, dict(hint(p), **{key: value}), CONFIG)
                self.assertEqual(result['status'], 'rejected')
                self.assertIsNone(result['candidate_detection_id'])

    def test_forecast_and_tentative_cannot_be_tracking_supported_observations(self):
        for state in ('predicted', 'tentative', 'lost', 'ambiguous'):
            p = packet(positions=((100, 100),))
            p['ball_tracking']['tracks'][0]['state'] = state
            self.assertEqual(assess(p, hint(p), CONFIG)['reason'], 'no_confirmed_measured_ball')

    def test_conflicting_and_ambiguous_candidates_abstain(self):
        p = packet(positions=((103, 100), (104, 100)))
        self.assertEqual(assess(p, hint(p), CONFIG)['status'], 'ambiguous')
        p = packet(positions=((400, 100),))
        self.assertEqual(assess(p, hint(p), CONFIG)['reason'], 'tracking_image_disagreement')

    def test_reference_inputs_and_nonboolean_evidence_rejected(self):
        p = packet()
        for changes in ({'origin': 'reference_annotations'}, {'labels': []},
                        {'measurement': 1}, {'tracking_sha256': 'bad'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                assess(p, dict(hint(p), **changes), CONFIG)

    def test_current_measurement_binding_required(self):
        p = packet(); p['ball_tracking']['tracks'][0]['measured_position_px'] = [99, 100]
        with self.assertRaises(ValueError): assess(p, hint(p), CONFIG)

    def test_resolution_scaling_preserves_decision(self):
        p = packet(); h = hint(p)
        a = assess(p, h, CONFIG)
        p['image_size_px'] = [2000, 1000]
        for row in p['objects']: row['image_xy_px'] = [x*2 for x in row['image_xy_px']]
        for row in p['ball_tracking']['tracks']: row['measured_position_px'] = [x*2 for x in row['measured_position_px']]
        h['projected_xy_px'] = [x*2 for x in h['projected_xy_px']]
        b = assess(p, h, CONFIG)
        self.assertEqual(a['candidate_distances'], b['candidate_distances'])

    def test_projection_direction_and_singular_or_missing_geometry(self):
        self.assertEqual(project_ground_ball([52.5, 34], [105, 68], [[1000,0,0],[0,500,0],[0,0,1]]), [500,250])
        self.assertIsNone(project_ground_ball([1,1], [105,68], [[0,0,0]]*3))
        with self.assertRaises(ValueError): project_ground_ball([float('nan'),1], [105,68], [[1,0,0],[0,1,0],[0,0,1]])

    def test_cross_camera_requires_exact_pair_and_common_tracking_sample(self):
        a, b = packet(), packet(40, 'broadcast')
        primary, secondary = assess(a, hint(a), CONFIG), assess(b, hint(b), CONFIG)
        pair = {'primary_source_id': 'tactical', 'primary_frame': 0, 'primary_epoch': 0,
                'secondary_source_id': 'broadcast', 'secondary_frame': 40, 'secondary_epoch': 0,
                'verified': True, 'error_bound_s': .01}
        self.assertEqual(cross_check(primary, secondary, pair, CONFIG)['status'], 'corroborated_candidate')
        for change in ({'verified': False}, {'secondary_frame': 41}, {'error_bound_s': .03}):
            self.assertEqual(cross_check(primary, secondary, dict(pair, **change), CONFIG)['status'], 'rejected')
        secondary['tracking_sample_id'] = 'another'
        self.assertEqual(cross_check(primary, secondary, pair, CONFIG)['reason'], 'different_tracking_observations')


class SupportRunnerTests(unittest.TestCase):
    def make_analysis(self, root, source='tactical'):
        path = root/source; path.mkdir()
        (path/'registration.json').write_text(json.dumps({'provided_fixture_used': False, 'fixture': {
            'id': 'synthetic-pair', 'provided_fixture_used': False, 'source_kind': 'synthetic_fixture'}}))
        (path/'frames.jsonl').write_text(json.dumps(packet(source=source))+'\n')
        (path/'summary.json').write_text(json.dumps({'frames': 1, 'output_sha256': sha256(path/'frames.jsonl')}))
        return path

    def bundle(self, root, analysis, source='tactical'):
        tracking = root/'tracking.txt'
        tracking.write_text('synthetic automatic tracking, not reference annotation')
        p = packet(source=source); h = dict(hint(p), tracking_sha256=sha256(tracking))
        projections = root/(source+'-projections.jsonl'); projections.write_text(json.dumps(h)+'\n')
        bundle = root/(source+'-support.json')
        bundle.write_text(json.dumps({'origin': 'automatic_tracking', 'provided_fixture_used': False,
            'reference_annotations_as_inputs': False, 'fixture_id': 'synthetic-pair',
            'tracking_path': str(tracking), 'tracking_sha256': sha256(tracking),
            'projections_path': str(projections), 'projections_sha256': sha256(projections)}))
        return bundle

    def test_end_to_end_enabled_disabled_and_cross_camera(self):
        plan = Path(__file__).resolve().parents[1]/'ball-support-plan.json'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); a = self.make_analysis(root)
            off = run(a, plan, root/'off')
            self.assertEqual(off['support_reasons'], {'no_automatic_tracking': 1})
            bundle = self.bundle(root, a)
            enabled = run(a, plan, root/'on', bundle)
            self.assertEqual(enabled['support_reasons'], {'observed_track_agrees_with_tracking': 1})
            before = json.loads((a/'frames.jsonl').read_text())
            after = json.loads((root/'on/frames.jsonl').read_text()); after.pop('tracking_support')
            self.assertEqual(before, after)
            b = self.make_analysis(root, 'broadcast')
            run(b, plan, root/'secondary', self.bundle(root, b, 'broadcast'))
            mapping = root/'pairs.jsonl'
            mapping.write_text(json.dumps({'primary_source_id': 'tactical', 'primary_frame': 0, 'primary_epoch': 0,
                'secondary_source_id': 'broadcast', 'secondary_frame': 0, 'secondary_epoch': 0,
                'verified': True, 'error_bound_s': .01})+'\n')
            result = run(a, plan, root/'paired', bundle, root/'secondary', mapping)
            self.assertEqual(result['cross_check_reasons'], {'two_camera_observations_agree_with_same_tracking_sample': 1})

    def test_tampered_and_reference_support_rejected(self):
        plan = Path(__file__).resolve().parents[1]/'ball-support-plan.json'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); a = self.make_analysis(root); b = self.bundle(root, a)
            spec = json.loads(b.read_text()); spec['reference_annotations_as_inputs'] = True
            b.write_text(json.dumps(spec))
            with self.assertRaises(ValueError): run(a, plan, root/'bad-reference', b)
            b = self.bundle(root, a); (root/'tracking.txt').write_text('changed')
            with self.assertRaises(ValueError): run(a, plan, root/'bad-hash', b)
