import unittest
import numpy as np
from development.set_piece_dead_ball import DeadBallConfig, apply, restart_kind
from development.motion_possession import predict
from test_motion_possession import CONFIG


# Synthetic engineering settings, not selected football thresholds.
CFG = DeadBallConfig(2., 1., .3, .2, .1, 2., .2, .2, 60., 1., 5.)


def sample(kind='Free Kick', point=(11., 30.), direction=(4., 0.)):
    n, fps = 40, 10.
    ball = np.tile(point, (n, 1)).astype(float)
    ball[:4, 0] = point[0] - np.array([1., .7, .4, .1])
    ball[20:] = np.asarray(point) + np.arange(1, 21)[:, None] * np.asarray(direction) / fps
    players = np.tile([point, [80., 50.]], (n, 1, 1)).astype(float)
    inputs = {'ball': ball, 'players': players, 'teams': np.array([0, 1]),
              'ball_observed': np.ones(n, bool), 'player_detected': np.ones((n, 2), bool),
              'period': np.ones(n, int), 'frame': np.arange(n), 'fps': np.array(fps),
              'pitch': np.array([105., 68.])}
    tag = {'id': 0, 'code': 'SET PIECES', 'start_s': 1.8, 'end_s': 2.2,
           'tags': {'Type': [kind], 'Team': ['N/A']}}
    return inputs, tag


class SetPieceTests(unittest.TestCase):
    def infer(self, x, tags):
        return apply(x, np.full(len(x['frame']), 'X'), tags, CFG)

    def test_measured_wait_is_D_but_tag_span_and_restart_are_not(self):
        x, tag = sample()
        r = self.infer(x, [tag])
        self.assertEqual(r['dead_ball_events'][0]['status'], 'supported_dead_ball_candidate')
        self.assertTrue(np.all(r['labels'][5:20] == 'D'))
        self.assertEqual(r['labels'][20], 'X')
        self.assertEqual(r['labels'][0], 'X')
        self.assertFalse(r['dead_ball_events'][0]['exact_whistle_time_verified'])

    def test_all_five_restart_types_and_regions(self):
        fixtures = [('Throw-in', (40., 0.), (0., 4.)), ('Goal Kick', (3., 30.), (4., 0.)),
                    ('Free Kick', (11., 30.), (4., 0.)), ('Corner Kick', (0., 0.), (4., 4.)),
                    ('Kick Off (After Goal)', (52.5, 34.), (4., 0.))]
        for kind, point, direction in fixtures:
            with self.subTest(kind=kind):
                x, tag = sample(kind, point, direction)
                self.assertTrue(self.infer(x, [tag])['dead_ball_mask'].any())
        x, tag = sample('Throw-in')  # middle of pitch, not a throw-in location
        self.assertFalse(self.infer(x, [tag])['dead_ball_mask'].any())

    def test_tag_alone_or_missing_ball_never_becomes_D(self):
        x, tag = sample()
        x['ball'][:] = np.nan
        x['ball_observed'][:] = False
        self.assertFalse(self.infer(x, [tag])['dead_ball_mask'].any())
        x, tag = sample()
        self.assertFalse(self.infer(x, [])['dead_ball_mask'].any())
        tag['code'] = 'BUILD UP'
        self.assertFalse(self.infer(x, [tag])['dead_ball_mask'].any())

    def test_missing_measurement_and_period_boundary_are_not_bridged(self):
        x, tag = sample()
        x['ball_observed'][12] = False
        r = self.infer(x, [tag])
        self.assertFalse(r['dead_ball_mask'][12])
        self.assertFalse(r['dead_ball_mask'][:13].any())
        x, tag = sample()
        x['period'][15:] = 2
        r = self.infer(x, [tag])
        self.assertFalse(r['dead_ball_mask'][:16].any())

    def test_no_wait_or_no_player_or_no_launch_is_unresolved(self):
        for mode in ('wait', 'player', 'launch'):
            x, tag = sample()
            if mode == 'wait': x['ball'][:, 0] = 11 + np.arange(40) * .4
            elif mode == 'player': x['player_detected'][:] = False
            else: x['ball'][20:] = x['ball'][19]
            self.assertFalse(self.infer(x, [tag])['dead_ball_mask'].any())

    def test_ambiguous_multiple_restarts_or_retaken_restart_are_unresolved(self):
        x, tag = sample()
        x['ball'][25:31] = [13.4, 30.]
        x['players'][25:31, 0] = [13.4, 30.]
        x['ball'][31:] = [13.4, 30.] + np.arange(1, 10)[:, None] * np.array([.4, 0])
        tag['end_s'] = 3.3
        r = self.infer(x, [tag])
        self.assertFalse(r['dead_ball_mask'].any())
        self.assertEqual(r['dead_ball_events'][0]['reason'], 'multiple_possible_restarts')
        x, tag = sample('Free Kick-Retaken')
        self.assertIsNone(restart_kind(tag))
        self.assertFalse(self.infer(x, [tag])['dead_ball_mask'].any())

    def test_impossible_ball_jump_is_not_a_restart(self):
        x, tag = sample()
        x['ball'][20] = [100., 60.]
        self.assertFalse(self.infer(x, [tag])['dead_ball_mask'].any())

    def test_fps_transfer_and_type_normalization(self):
        tag = {'code': 'set_pieces', 'tags': {'type': ['THROW-IN']}}
        self.assertEqual(restart_kind(tag), 'throw in')
        x, tag = sample()
        x['fps'] = np.array(25.)
        tag['start_s'], tag['end_s'] = 18/25, 22/25
        self.assertTrue(self.infer(x, [tag])['dead_ball_mask'].any())

    def test_pipeline_integration_and_clock_validation(self):
        x, tag = sample()
        tags = {'source_kind': 'synthetic_UI_fixture', 'fps': 10., 'frame_count': 40, 'events': [tag]}
        r = predict(x, np.full(40, 'H'), CONFIG, dead_ball_config=CFG, automatic_tags=tags)
        self.assertTrue(np.any(r['labels'] == 'D'))
        self.assertTrue(np.all(r['reasons'][r['dead_ball_mask']] == 'tag_supported_measured_dead_ball'))
        self.assertFalse(any(r['dead_ball_mask'][event['frame']] for event in r['contacts']))
        tags['fps'] = 25.
        with self.assertRaises(ValueError):
            predict(x, np.full(40, 'H'), CONFIG, dead_ball_config=CFG, automatic_tags=tags)
        with self.assertRaises(ValueError): predict(x, np.full(40, 'H'), CONFIG, dead_ball_config=CFG)

    def test_invalid_thresholds_rejected(self):
        with self.assertRaises(ValueError):
            DeadBallConfig(2., 1., .3, 5., .1, 2., .2, .2, 60., 1., 5.)


if __name__ == '__main__':
    unittest.main()
