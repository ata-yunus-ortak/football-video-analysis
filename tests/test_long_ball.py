import unittest
import numpy as np
from development.long_ball import LongBallConfig, detect
from development.motion_possession import MotionConfig, predict
from development.player_motion import DribbleConfig


# Synthetic engineering values only; not selected football settings.
LONG = LongBallConfig(5., 60., 15., .5, .9, 45.)
MOTION = MotionConfig(.1, 20., 60., 4., .5, .3, .1, 3.)


def sample():
    n = 50
    ball = np.column_stack((10. + .8 * np.arange(n), np.full(n, 30.)))
    x = {'ball': ball, 'players': np.tile([[5., 30.], [25., 30.]], (n, 1, 1)),
         'teams': np.array([0, 1]), 'ball_observed': np.ones(n, bool),
         'player_detected': np.ones((n, 2), bool), 'frame': np.arange(n),
         'period': np.ones(n, int), 'fps': np.array(10.), 'pitch': np.array([105., 68.])}
    tag = {'id': 1, 'code': 'LONG BALL', 'start_s': .5, 'end_s': 3.5, 'tags': {'Team': ['N/A']}}
    return x, tag


class LongBallTests(unittest.TestCase):
    def bundle(self, x, tag):
        return {'events': [tag], 'fps': float(x['fps']), 'frame_count': len(x['frame']),
                'source_kind': 'synthetic_UI_fixture'}

    def test_fast_long_measured_run_within_tag_and_endpoints_excluded(self):
        x, tag = sample()
        r = detect(x, [tag], LONG)
        self.assertEqual(len(r['long_ball_events']), 1)
        event = r['long_ball_events'][0]
        self.assertEqual((event['start_frame'], event['end_frame']), (5, 34))
        self.assertAlmostEqual(event['displacement_m'], 23.2)
        self.assertTrue(np.all(r['long_ball_flight_mask'][6:34]))
        self.assertFalse(r['long_ball_flight_mask'][5])
        self.assertFalse(r['long_ball_flight_mask'][34])
        self.assertFalse(event['height_verified'])

    def test_nearby_opponent_does_not_acquire_from_flyby(self):
        x, tag = sample()
        r = predict(x, np.full(50, 'A'), MOTION, automatic_tags=self.bundle(x, tag), long_ball_config=LONG)
        self.assertFalse(r['fast_flight'][19])  # long-ball-specific gate is used
        self.assertEqual(r['labels'][19], 'X')
        self.assertEqual(r['reasons'][19], 'long_ball_no_proximity_ownership')
        self.assertEqual(r['contacts'], [])

    def test_no_tag_short_slow_or_jittery_motion_does_not_qualify(self):
        x, tag = sample()
        self.assertEqual(detect(x, [], LONG)['long_ball_events'], [])
        for mode in ('short', 'slow', 'jitter'):
            x, tag = sample()
            if mode == 'short': tag['end_s'] = 1.
            elif mode == 'slow': x['ball'][:, 0] = 10 + .1 * np.arange(50)
            else: x['ball'][:, 0] = 20 + np.arange(50) % 2
            self.assertEqual(detect(x, [tag], LONG)['long_ball_events'], [])

    def test_missing_data_and_period_change_are_not_bridged(self):
        for mode in ('missing', 'period'):
            x, tag = sample()
            if mode == 'missing': x['ball_observed'][20] = False
            else: x['period'][20:] = 2
            # Both remaining pieces are shorter than the required 15 metres.
            r = detect(x, [tag], LONG)
            self.assertEqual(r['long_ball_events'], [])

    def test_impossible_jump_or_blocked_stop_is_not_long_ball(self):
        x, tag = sample()
        x['ball'][20] = [100., 60.]
        self.assertEqual(detect(x, [tag], LONG)['long_ball_events'], [])
        x, tag = sample()
        blocked = np.zeros(50, bool); blocked[20] = True
        self.assertEqual(detect(x, [tag], LONG, blocked)['long_ball_events'], [])

    def test_direction_change_splits_runs_and_keeps_contact_frame(self):
        x, tag = sample()
        x['ball'][20:, 0] = x['ball'][19, 0] - .8 * np.arange(1, 31)
        short = LongBallConfig(5., 60., 5., .5, .9, 45.)
        r = detect(x, [tag], short)
        self.assertEqual(len(r['long_ball_events']), 2)
        self.assertFalse(r['long_ball_flight_mask'][19])

    def test_supported_dribble_not_misclassified_as_long_flight(self):
        x, tag = sample()
        x['players'][:, 0] = x['ball'] - [.2, 0]
        x['players'][:, 1] = [80., 50.]
        dribble = DribbleConfig(.8, .3, .5, 15., .3, .2, 1)
        r = predict(x, np.full(50, 'A'), MOTION, dribble,
                    automatic_tags=self.bundle(x, tag), long_ball_config=LONG)
        self.assertEqual(r['long_ball_events'], [])
        self.assertEqual(r['labels'][19], 'H')

    def test_duplicate_tags_and_25fps_transfer(self):
        x, tag = sample()
        other = {**tag, 'id': 2, 'code': 'long_ball'}
        r = detect(x, [tag, other], LONG)
        self.assertEqual(len(r['long_ball_events']), 1)
        self.assertEqual(r['long_ball_events'][0]['tag_ids'], [1, 2])
        x['fps'] = np.array(25.)
        tag['start_s'], tag['end_s'] = 5/25, 35/25
        r = detect(x, [tag], LONG)
        self.assertAlmostEqual(r['long_ball_events'][0]['mean_speed_mps'], 20.)

    def test_config_and_tag_clock_validation(self):
        with self.assertRaises(ValueError): LongBallConfig(5., 4., 15., .5, .9, 45.)
        with self.assertRaises(ValueError): LongBallConfig(5., 60., 15., .5, 1.1, 45.)
        x, tag = sample()
        tags = self.bundle(x, tag);tags['frame_count'] = 51
        with self.assertRaises(ValueError):
            predict(x, np.full(50, 'H'), MOTION, automatic_tags=tags, long_ball_config=LONG)
        with self.assertRaises(ValueError): predict(x, np.full(50, 'H'), MOTION, long_ball_config=LONG)


if __name__ == '__main__':
    unittest.main()
