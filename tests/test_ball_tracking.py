import json
from pathlib import Path
import unittest
from dataclasses import replace
from development.ball_tracking import BallTrackingConfig, TemporalBallTracker


CONFIG = BallTrackingConfig(**json.loads((Path(__file__).resolve().parents[1] / 'ball-tracking-plan.json').read_text())['parameters'])


def packet(frame, points=(), epoch=0, width=1000):
    objects = []
    for i, value in enumerate(points):
        x, y, score = value if len(value) == 3 else (*value, .9)
        objects.append({'kind': 'ball_candidate', 'detection_id': f'f{frame}:{i}',
                        'image_xy_px': [x, y], 'box_xyxy_px': [x-2, y-2, x+2, y+2], 'confidence': score})
    return {'source_frame': frame, 'video_time_s': frame / 25, 'fps': 25,
            'image_size_px': [width, 500], 'camera_epoch': epoch, 'objects': objects}


def confirmed(tracker, start=100):
    outputs = [tracker.consume(packet(i, [(start + i * 5, 100)])) for i in range(3)]
    return outputs[-1]['tracks'][0]['track_id']


class BallTrackingTests(unittest.TestCase):
    def test_confidence_participates_in_spatial_association(self):
        cfg = replace(CONFIG, ambiguity_margin=.01)
        tracker = TemporalBallTracker('source', cfg)
        old = tracker.consume(packet(0, [(100,100)]))['tracks'][0]['track_id']
        result = tracker.consume(packet(1, [(90,100,.3),(115,100,.95)]))
        assigned = next(r for r in result['tracks'] if r['track_id'] == old)
        self.assertEqual(assigned['measured_position_px'], [115,100])

    def test_motion_confirmation_and_coasting_are_separate_from_detections(self):
        tracker = TemporalBallTracker('source', CONFIG)
        identity = confirmed(tracker)
        missing = packet(3)
        result = tracker.consume(missing)['tracks'][0]
        self.assertEqual(result['state'], 'predicted')
        self.assertEqual(result['predicted_position_px'], [115., 100.])
        self.assertIsNone(result['measured_position_px'])
        self.assertIsNone(result['detection_id'])
        self.assertFalse(result['measurement'])
        self.assertEqual(missing['objects'], [])
        measured = tracker.consume(packet(4, [(120, 100)]))['tracks'][0]
        self.assertEqual(measured['track_id'], identity)
        self.assertEqual(measured['state'], 'observed')
        self.assertIsNone(measured['predicted_position_px'])
        self.assertFalse(measured['selected_in_play_ball'])

    def test_timeout_never_revives_old_identity(self):
        tracker = TemporalBallTracker('source', CONFIG);old = confirmed(tracker)
        for frame in range(3, 8): tracker.consume(packet(frame))
        rows = tracker.consume(packet(8, [(140,100)]))['tracks']
        self.assertTrue(any(r['state'] == 'lost' and r['track_id'] == old for r in rows))
        self.assertTrue(any(r['state'] == 'tentative' and r['track_id'] != old for r in rows))

    def test_ambiguity_breaks_track_instead_of_choosing_a_ball(self):
        tracker = TemporalBallTracker('source', CONFIG)
        tracker.consume(packet(0, [(100,100)]))
        result = tracker.consume(packet(1, [(95,100),(105,100)]))
        self.assertEqual([r['state'] for r in result['tracks']], ['ambiguous'])
        self.assertTrue(all(r['measured_position_px'] is None and r['predicted_position_px'] is None for r in result['tracks']))
        self.assertFalse(result['in_play_ball_selected'])

    def test_two_tracks_contesting_one_detection_are_not_merged(self):
        tracker = TemporalBallTracker('source', CONFIG)
        tracker.consume(packet(0, [(100,100),(120,100)]))
        result = tracker.consume(packet(1, [(110,100)]))
        self.assertEqual(len(result['tracks']), 2)
        self.assertTrue(all(r['state']=='ambiguous' for r in result['tracks']))

    def test_raw_duplicates_survive_but_do_not_spawn_two_tracks(self):
        tracker = TemporalBallTracker('source', CONFIG)
        frame = packet(0, [(100,100,.9),(100.1,100,.8)])
        result = tracker.consume(frame)
        self.assertEqual(len(frame['objects']), 2)
        self.assertEqual(len(result['tracks']), 1)
        self.assertEqual(result['tracks'][0]['detection_id'], 'f0:0')
        self.assertEqual(result['candidate_exclusions'][0]['reason'], 'overlapping_duplicate')

    def test_camera_resolution_and_clock_discontinuities_reset_motion(self):
        for mode in ('epoch','dimensions','gap','explicit'):
            tracker = TemporalBallTracker('source', CONFIG);old = confirmed(tracker)
            frame = packet(4 if mode == 'gap' else 3, [(500,100)], epoch=1 if mode=='epoch' else 0,
                           width=2000 if mode=='dimensions' else 1000)
            result = tracker.consume(frame, reset=mode=='explicit')
            self.assertIsNotNone(result['reset_reason'])
            self.assertFalse(any(r['state']=='predicted' for r in result['tracks']))
            self.assertTrue(any(r['track_id']==old and r['state']=='lost' for r in result['tracks']))

    def test_low_confidence_and_unconfirmed_gaps_do_not_create_measured_tracks(self):
        tracker = TemporalBallTracker('source', CONFIG)
        self.assertEqual(tracker.consume(packet(0, [(100,100,.1)]))['tracks'], [])
        tracker.consume(packet(1, [(100,100)]))
        self.assertEqual(tracker.consume(packet(2))['tracks'][0]['reason'], 'unconfirmed_gap')

    def test_prediction_outside_image_is_not_clamped_to_edge(self):
        tracker = TemporalBallTracker('source', CONFIG);confirmed(tracker, 980)
        tracker.consume(packet(3))
        result = tracker.consume(packet(4))['tracks'][0]
        self.assertEqual(result['reason'], 'prediction_outside_image')
        self.assertIsNone(result['predicted_position_px'])

    def test_source_namespaces_and_reverse_time(self):
        first, second = TemporalBallTracker('A',CONFIG), TemporalBallTracker('B',CONFIG)
        a,b=first.consume(packet(0,[(100,100)])),second.consume(packet(0,[(100,100)]))
        self.assertNotEqual(a['tracks'][0]['track_id'],b['tracks'][0]['track_id'])
        with self.assertRaises(ValueError): first.consume(packet(0,[(100,100)]))
