import unittest
import numpy as np
from development.reachability import ReachabilityConfig, estimate
from development.motion_possession import predict
from test_motion_possession import sample, CONFIG


# Engineering fixtures only. No football parameter selection implied.
REACH = ReachabilityConfig(.2, 6., 15., 1., .05, 1)


def ambiguous_turn():
    x = sample()
    t = np.arange(20) / 10
    x['players'][:, 0, 0] = 20.2 + 2 * (t - .3)  # nearer, moving away
    x['players'][:, 1, 0] = 19.75 + 2 * (t - .3)  # farther, approaching
    x['players'][:, 2] = [70., 50.]
    x['teams'] = np.array([0, 1, 0])
    return x


class ReachabilityTests(unittest.TestCase):
    def test_direction_resolves_ambiguous_contact_only_with_ball_motion_evidence(self):
        x = ambiguous_turn()
        base = predict(x, np.full(20, 'X'), CONFIG)
        self.assertIsNone(base['contacts'][0]['slot'])
        r = predict(x, np.full(20, 'X'), CONFIG, reachability_config=REACH)
        self.assertEqual(r['contacts'][0]['slot'], 1)
        self.assertEqual(r['contacts'][0]['assignment_evidence'], 'motion_and_arrival_time')
        self.assertEqual(r['labels'][3], 'A')
        self.assertLess(r['arrival_time_s'][3, 1], r['arrival_time_s'][3, 0])
        self.assertFalse(r['selected_release'])

    def test_arrival_alone_never_creates_ownership_or_dead_ball(self):
        x = ambiguous_turn()
        x['ball'][:] = [20., 30.]
        r = predict(x, np.full(20, 'X'), CONFIG, reachability_config=REACH)
        self.assertEqual(r['contacts'], [])
        self.assertTrue(np.all(r['labels'] == 'X'))
        self.assertTrue(np.isfinite(r['arrival_time_s'][3, 1]))

    def test_long_ball_flyby_does_not_acquire_arrival_owner(self):
        from test_long_ball import sample as flight_sample, MOTION, LONG
        x, tag = flight_sample()
        bundle = {'source_kind': 'synthetic_UI_fixture', 'events': [tag],
                  'fps': float(x['fps']), 'frame_count': len(x['frame'])}
        r = predict(x, np.full(len(x['frame']), 'A'), MOTION,
                    reachability_config=REACH, automatic_tags=bundle, long_ball_config=LONG)
        self.assertEqual(r['contacts'], [])
        self.assertEqual(r['labels'][19], 'X')

    def test_equal_arrival_times_preserve_ambiguity(self):
        x = ambiguous_turn()
        x['players'][:, 0] = [20.2, 30.]
        x['players'][:, 1] = [19.8, 30.]
        r = predict(x, np.full(20, 'X'), CONFIG, reachability_config=REACH)
        self.assertIsNone(r['contacts'][0]['slot'])

    def test_missing_nearby_motion_or_insufficient_team_coverage_cannot_break_tie(self):
        for kind in ('missing', 'jump', 'coverage'):
            with self.subTest(kind=kind):
                x = ambiguous_turn()
                cfg = REACH
                if kind == 'missing': x['player_detected'][2, 0] = False
                elif kind == 'jump': x['players'][2, 0] = [80., 40.]
                else: cfg = ReachabilityConfig(.2, 6., 15., 1., .05, 2)
                r = predict(x, np.full(20, 'X'), CONFIG, reachability_config=cfg)
                self.assertNotEqual(r['contacts'][0]['assignment_evidence'], 'motion_and_arrival_time')

    def test_missing_ball_periods_and_jumps_have_no_arrival_measurement(self):
        for kind in ('missing_ball', 'unobserved_ball', 'outside_ball', 'missing_player', 'period', 'jump'):
            x = ambiguous_turn()
            reliable = np.ones(20, bool)
            if kind == 'missing_ball':
                x['ball'][3] = np.nan; reliable[3] = False
            elif kind == 'unobserved_ball': x['ball_observed'][3] = False
            elif kind == 'outside_ball': x['ball'][3] = [-1., 30.]
            elif kind == 'missing_player': x['player_detected'][3, 1] = False
            elif kind == 'period': x['period'][3:] = 2
            else: x['players'][3, 1] = [90., 60.]
            r = estimate(x, reliable, REACH)
            self.assertTrue(np.isnan(r['arrival_time_s'][3, 1]))
            if kind == 'jump': self.assertTrue(np.isnan(r['arrival_time_s'][2, 1]))

    def test_geometry_and_team_symmetry(self):
        x = ambiguous_turn()
        r = predict(x, np.full(20, 'X'), CONFIG, reachability_config=REACH)
        x['teams'] = 1 - x['teams']
        x['players'] = x['pitch'] - x['players']
        x['ball'] = x['pitch'] - x['ball']
        mirrored = predict(x, np.full(20, 'X'), CONFIG, reachability_config=REACH)
        np.testing.assert_allclose(r['arrival_time_s'], mirrored['arrival_time_s'], equal_nan=True)
        self.assertEqual(mirrored['labels'][3], 'H')

    def test_seconds_transfer_to_25fps(self):
        for fps in (10., 25.):
            x = sample()
            x['fps'] = np.array(fps)
            t = np.arange(20) / fps
            x['ball'][:] = [30., 30.]
            x['players'][:, 0, 0] = 20 + 2 * t
            r = estimate(x, np.ones(20, bool), REACH)
            np.testing.assert_allclose(r['arrival_player_velocity_mps'][1:, 0, 0], 2.)
            expected = .2 + abs(30 - (20 + 2 * t[5] + .4)) / 6
            self.assertAlmostEqual(r['arrival_time_s'][5, 0], expected)

    def test_invalid_config_and_target_leakage_rejected(self):
        for settings in ((0., 6., 15., 1., .05, 1), (.2, 6., 5., 1., .05, 1),
                         (.2, 6., 15., .1, .05, 1), (.2, 6., 15., 1., .05, 0)):
            with self.assertRaises(ValueError): ReachabilityConfig(*settings)
        with self.assertRaises(ValueError):
            estimate({**sample(), 'possession': np.zeros(20)}, np.ones(20, bool), REACH)


if __name__ == '__main__':
    unittest.main()
