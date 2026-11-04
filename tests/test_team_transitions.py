import unittest
import numpy as np
from development.team_transitions import TransitionConfig, detect
from development.motion_possession import predict
from test_motion_possession import CONFIG
from test_player_motion import DRIBBLE, running


# Synthetic values only; not externally selected football thresholds.
CFG = TransitionConfig(.2, 1., .8, .3, .5, 2)


def scenario():
    v = np.zeros((20, 4, 2))
    v[:10, :, 0], v[10:, :, 0] = 1., -1.
    direct = np.full(20, -1, int)
    direct[6], direct[12] = 0, 1
    return v, np.array([0, 0, 1, 1]), np.ones(20, int), direct


class TransitionTests(unittest.TestCase):
    def run_case(self, v, teams, period, direct, cfg=CFG):
        return detect(v, teams, period, 10., direct, cfg)

    def test_direction_change_with_same_speed_and_local_team_switch(self):
        r = self.run_case(*scenario())
        self.assertEqual(len(r['team_transition_events']), 1)
        event = r['team_transition_events'][0]
        self.assertEqual(event['frame'], 10)
        self.assertEqual(event['status'], 'supported_turnover_candidate')
        self.assertEqual((event['from_team'], event['to_team']), (0, 1))
        np.testing.assert_allclose(event['speed_change_mps'], 0.)
        np.testing.assert_allclose(event['vector_change_mps'], 2.)

    def test_speed_magnitude_change_is_detected(self):
        v, t, p, d = scenario()
        v[10:, :, 0] = 3.
        event = self.run_case(v, t, p, d)['team_transition_events'][0]
        np.testing.assert_allclose(event['speed_change_mps'], 2.)

    def test_same_team_or_missing_ball_evidence_does_not_confirm_turnover(self):
        for mode in ('same', 'none', 'late'):
            v, t, p, d = scenario()
            if mode == 'same': d[12] = 0
            elif mode == 'none': d[:] = -1
            else: d[12], d[19] = -1, 1
            event = self.run_case(v, t, p, d)['team_transition_events'][0]
            self.assertEqual(event['status'], 'team_motion_change_only')
            self.assertIsNone(event['to_team'])

    def test_visible_roster_change_is_not_team_acceleration(self):
        v, t, p, d = scenario()
        v[:] = 0.
        v[:10, [0, 2], 0] = 10.
        v[10:, [0, 2]] = np.nan
        cfg = TransitionConfig(.2, 1., .8, .3, .5, 1)
        r = self.run_case(v, t, p, d, cfg)
        self.assertEqual(r['team_transition_events'], [])
        np.testing.assert_array_equal(r['team_change_cohort_counts'][10], [1, 1])

    def test_period_boundary_or_missing_measurements_block_change(self):
        for mode in ('period', 'missing'):
            v, t, p, d = scenario()
            if mode == 'period': p[10:] = 2
            else: v[8:12] = np.nan
            self.assertEqual(self.run_case(v, t, p, d)['team_transition_events'], [])

    def test_one_team_changing_or_constant_motion_is_not_joint_signal(self):
        for mode in ('one', 'neither'):
            v, t, p, d = scenario()
            v[:, 2:, 0] = 1.
            if mode == 'neither': v[:, :2, 0] = 1.
            self.assertEqual(self.run_case(v, t, p, d)['team_transition_events'], [])

    def test_missing_old_owner_does_not_invent_turnover(self):
        v, t, p, d = scenario()
        d[6] = -1
        self.assertEqual(self.run_case(v, t, p, d)['team_transition_events'][0]['status'],
                         'team_motion_change_only')

    def test_optional_context_does_not_manufacture_or_overwrite_labels(self):
        x = running()
        base = np.full(12, 'A')
        without = predict(x, base, CONFIG, DRIBBLE)
        with_context = predict(x, base, CONFIG, DRIBBLE, CFG)
        np.testing.assert_array_equal(without['labels'], with_context['labels'])
        self.assertEqual(with_context['team_transition_events'], [])
        with self.assertRaises(ValueError):
            predict(x, base, CONFIG, transition_config=CFG)

    def test_config_and_alignment_validation(self):
        with self.assertRaises(ValueError):
            TransitionConfig(.2, 1., .8, .3, .5, 0)
        v, t, p, d = scenario()
        with self.assertRaises(ValueError):
            detect(v, t, p, 0, d, CFG)
        with self.assertRaises(ValueError):
            detect(v, t, p, 10., d[:-1], CFG)


if __name__ == '__main__':
    unittest.main()
