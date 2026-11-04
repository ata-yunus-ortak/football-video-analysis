import unittest
import numpy as np
from development.player_motion import DribbleConfig
from development.motion_possession import predict
from test_motion_possession import CONFIG


# Synthetic fixture settings, not calibrated football thresholds.
DRIBBLE = DribbleConfig(.8, .3, .5, 15., .3, .2, 1)


def running(fps=10., n=12):
    t = np.arange(n) / fps
    ball = np.column_stack((30 + 4 * t, np.full(n, 30.)))
    players = np.empty((n, 2, 2))
    players[:, 0] = ball - [.2, 0]
    players[:, 1] = [80., 50.]
    return {'ball': ball, 'players': players, 'teams': np.array([0, 1]),
            'ball_observed': np.ones(n, bool), 'player_detected': np.ones((n, 2), bool),
            'period': np.ones(n, int), 'frame': np.arange(n),
            'fps': np.array(fps), 'pitch': np.array([105., 68.])}


class PlayerMotionTests(unittest.TestCase):
    def infer(self, x, cfg=DRIBBLE):
        return predict(x, np.full(len(x['frame']), 'A'), CONFIG, cfg)

    def test_running_dribble_overrides_fast_ball_veto(self):
        r = self.infer(running())
        self.assertTrue(r['fast_flight'][5])
        self.assertTrue(np.all(r['labels'][1:] == 'H'))
        self.assertEqual(r['reasons'][5], 'persistent_ball_player_comotion')
        np.testing.assert_allclose(r['player_velocity_mps'][1:, 0], np.tile([4., 0], (11, 1)))

    def test_equal_speed_opposite_direction_is_not_dribbling(self):
        x = running()
        x['players'][:, 0, 0] = 30 - 4 * np.arange(12) / 10
        self.assertTrue(np.all(self.infer(x)['dribble_slot'] == -1))

    def test_stationary_pair_and_far_parallel_runner_are_not_dribbles(self):
        for kind in ('stationary', 'far'):
            x = running()
            if kind == 'stationary':
                x['ball'][:] = [30, 30]
                x['players'][:, 0] = [29.8, 30]
            else:
                x['players'][:, 0, 1] -= 5
            self.assertTrue(np.all(self.infer(x)['dribble_slot'] == -1))

    def test_short_parallel_encounter_does_not_confirm(self):
        x = running(n=3)
        self.assertTrue(np.all(self.infer(x)['dribble_slot'] == -1))

    def test_ambiguous_nearby_opponent_prevents_dribble_assignment(self):
        x = running()
        x['players'][:, 1] = x['ball'] + [.2, 0]
        self.assertTrue(np.all(self.infer(x)['dribble_slot'] == -1))

    def test_missing_measurements_periods_and_jumps_break_runs(self):
        for kind in ('ball', 'player', 'period', 'jump'):
            with self.subTest(kind=kind):
                x = running()
                if kind == 'ball':
                    x['ball_observed'][5] = False
                elif kind == 'player':
                    x['player_detected'][5, 0] = False
                elif kind == 'period':
                    x['period'][5:] = 2
                else:
                    x['players'][5, 0] = [100, 60]
                r = self.infer(x)
                self.assertEqual(r['dribble_slot'][5], -1)

    def test_mean_vector_and_mean_speed_are_different(self):
        x = running()
        x['teams'][:] = 0
        x['players'][:, 1, 0] = 80 - 4 * np.arange(12) / 10
        r = self.infer(x)
        np.testing.assert_allclose(r['team_mean_velocity_mps'][1:, 0], 0., atol=1e-10)
        np.testing.assert_allclose(r['team_mean_speed_mps'][1:, 0], 4.)
        self.assertTrue(np.isnan(r['team_mean_velocity_mps'][:, 1]).all())

    def test_missing_players_not_counted_as_stationary_and_coverage_is_exposed(self):
        x = running()
        x['teams'][:] = 0
        x['player_detected'][:, 1] = False
        r = self.infer(x)
        np.testing.assert_array_equal(r['team_velocity_counts'][1:, 0], 1)
        np.testing.assert_allclose(r['team_mean_velocity_mps'][1:, 0, 0], 4.)
        cfg = DribbleConfig(.8, .3, .5, 15., .3, .2, 2)
        self.assertTrue(np.isnan(self.infer(x, cfg)['team_mean_velocity_mps']).all())

    def test_identical_team_vectors_do_not_determine_which_team_has_ball(self):
        x = running()
        x['players'][:, 1] = x['ball'] + [20, 10]
        home = self.infer(x)
        x['teams'] = 1 - x['teams']
        away = self.infer(x)
        np.testing.assert_allclose(home['team_mean_velocity_mps'], away['team_mean_velocity_mps'], equal_nan=True)
        self.assertEqual(home['labels'][5], 'H')
        self.assertEqual(away['labels'][5], 'A')

    def test_seconds_and_metric_velocities_transfer_to_25fps(self):
        r = self.infer(running(fps=25., n=30))
        self.assertTrue(np.all(r['dribble_slot'][1:] == 0))
        np.testing.assert_allclose(r['player_velocity_mps'][1:, 0, 0], 4.)

    def test_invalid_scales_rejected(self):
        with self.assertRaises(ValueError):
            DribbleConfig(.8, .3, 0., 15., .3, .2, 1)
        with self.assertRaises(ValueError):
            DribbleConfig(.8, .3, .5, 15., .3, .2, 0)


if __name__ == '__main__':
    unittest.main()
