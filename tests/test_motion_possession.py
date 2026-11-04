import unittest
import numpy as np
from development.motion_possession import MotionConfig, predict


# Engineering fixtures only. These numbers are not selected football settings.
CONFIG = MotionConfig(.1, 3., 60., 4., .5, .3, .1, 3.)


def sample():
    n = 20
    x = np.r_[np.full(4, 20.), np.arange(21., 27.), np.full(10, 26.)]
    return {'ball': np.column_stack((x, np.full(n, 30.))),
            'players': np.tile([[20., 30.], [26., 30.], [23., 30.]], (n, 1, 1)),
            'teams': np.array([0, 0, 1]), 'period': np.ones(n, int),
            'ball_observed': np.ones(n, bool), 'player_detected': np.ones((n, 3), bool),
            'frame': np.arange(n), 'fps': np.array(10.), 'pitch': np.array([105., 68.])}


class MotionTests(unittest.TestCase):
    def test_same_team_contacts_form_candidate_pass_despite_nearby_opponent(self):
        x = sample()
        r = predict(x, np.full(20, 'A'), CONFIG)
        self.assertEqual([e['frame'] for e in r['contacts']], [3, 9])
        self.assertEqual(len(r['passes']), 1)
        self.assertEqual(r['passes'][0]['sender_slot'], 0)
        self.assertEqual(r['passes'][0]['receiver_slot'], 1)
        self.assertEqual(r['labels'][6], 'H')
        self.assertFalse(r['contact_verified'])

    def test_opposing_receiver_does_not_produce_same_team_pass(self):
        x = sample()
        x['teams'][1] = 1
        r = predict(x, np.full(20, 'A'), CONFIG)
        self.assertEqual(r['passes'], [])
        self.assertEqual(r['labels'][6], 'X')  # decoy is at the ball
        self.assertEqual(r['labels'][9], 'A')

    def test_signed_reversal_at_stop_is_detected(self):
        x = sample()
        x['ball'][:, 0] = np.r_[np.arange(17., 21.), 20., np.arange(19., 4., -1.)]
        x['players'][:, 0] = [20., 30.]
        r = predict(x, np.full(20, 'X'), CONFIG)
        self.assertTrue(any(e['slot'] == 0 and e['frame'] in (3, 4) for e in r['contacts']))
        self.assertGreater(r['velocity_mps'][2, 0], 0)
        self.assertLess(r['velocity_mps'][5, 0], 0)

    def test_ambiguous_contact_breaks_pass_evidence(self):
        x = sample()
        x['players'][:, 2] = [20.1, 30.]
        r = predict(x, np.full(20, 'H'), CONFIG)
        self.assertIsNone(r['contacts'][0]['slot'])
        self.assertEqual(r['passes'], [])

    def test_missing_ball_or_player_or_period_change_prevents_pass(self):
        for change in ('ball', 'player', 'period'):
            with self.subTest(change=change):
                x = sample()
                if change == 'ball':
                    x['ball'][6] = np.nan
                    x['ball_observed'][6] = False
                elif change == 'player':
                    x['player_detected'][6, 1] = False
                else:
                    x['period'][6:] = 2
                r = predict(x, np.full(20, 'H'), CONFIG)
                self.assertEqual(r['passes'], [])

    def test_impossible_jump_is_quarantined(self):
        x = sample()
        x['ball'][6] = [100., 60.]
        r = predict(x, np.full(20, 'H'), CONFIG)
        self.assertEqual(r['passes'], [])
        self.assertEqual(r['labels'][6], 'X')
        self.assertFalse(any(e['frame'] == 6 for e in r['contacts']))

    def test_same_slot_cannot_be_a_pass_to_itself(self):
        x = sample()
        x['players'][:, 0] = x['ball']
        x['players'][:, 1:] = [80., 50.]
        r = predict(x, np.full(20, 'H'), CONFIG)
        self.assertEqual(r['passes'], [])

    def test_long_or_unobserved_contact_is_not_a_pass(self):
        x = sample()
        cfg = MotionConfig(.1, 3., 60., 4., .5, .3, .1, .2)
        self.assertEqual(predict(x, np.full(20, 'H'), cfg)['passes'], [])
        x['player_detected'][2:5, 0] = False
        r = predict(x, np.full(20, 'H'), CONFIG)
        self.assertIsNone(r['contacts'][0]['slot'])

    def test_invalid_config_and_target_leakage_are_rejected(self):
        with self.assertRaises(ValueError):
            MotionConfig(.1, 60., 3., 4., .5, .3, .1, 3.)
        with self.assertRaises(ValueError):
            predict({**sample(), 'events': []}, np.full(20, 'H'), CONFIG)


if __name__ == '__main__':
    unittest.main()
