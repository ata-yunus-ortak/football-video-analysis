import itertools
import unittest
import numpy as np
from development.sequence_possession import SequenceConfig, decode, measurements, predict
from development.sequence_metrics import fill_prediction_gaps, evaluate


class SequenceTests(unittest.TestCase):
    def cfg(self, cost=.3):
        return SequenceConfig(2., 5., .5, cost, 'geometry')

    def run_evidence(self, values, cost=.3, period=None, frame=None, usable=None):
        n = len(values)
        return decode(values, np.ones(n, bool) if usable is None else usable,
                      np.ones(n, int) if period is None else period,
                      np.arange(n) if frame is None else frame, 10., self.cfg(cost))

    def test_short_touch_does_not_split_control(self):
        out = self.run_evidence([1]*15 + [-1] + [1]*15)
        self.assertTrue(np.all(out == 'H'))

    def test_sustained_receiver_changes_at_evidence_boundary(self):
        out = self.run_evidence([1]*15 + [-1]*15)
        self.assertEqual(out.tolist(), ['H']*15 + ['A']*15)

    def test_exact_dynamic_program_matches_bruteforce_objective(self):
        scores = np.array([.7, -.2, -.8, .5, .6, -.4])
        pred = self.run_evidence(scores, .03)
        def objective(path):
            return np.sum(scores*np.where(np.array(path)==0, 1, -1))/10 - .03*np.count_nonzero(np.diff(path))
        optimum = max(objective(p) for p in itertools.product((0, 1), repeat=len(scores)))
        self.assertAlmostEqual(objective(np.where(pred=='H', 0, 1)), optimum)

    def test_team_swap_symmetry(self):
        scores = np.r_[np.full(15, .8), -.3, np.full(15, -.6)]
        a, b = self.run_evidence(scores), self.run_evidence(-scores)
        self.assertTrue(np.all(np.where(a=='H', 'A', np.where(a=='A', 'H', 'X')) == b))

    def test_missing_ball_never_becomes_observation_or_dead_ball(self):
        valid = np.ones(35, bool); valid[15:20] = False
        out = self.run_evidence(np.r_[np.ones(15), np.zeros(5), np.ones(15)], usable=valid)
        self.assertEqual(out[15:20].tolist(), ['X']*5)
        self.assertFalse(np.any(out=='D'))
        self.assertTrue(np.all(self.run_evidence(np.zeros(10), usable=np.zeros(10, bool))=='X'))

    def test_period_and_discontinuous_frame_reset(self):
        for periods, frames in [(np.r_[np.ones(15), np.full(2, 2)], np.arange(17)),
                                (np.ones(17), np.r_[np.arange(15), [30, 31]])]:
            out = self.run_evidence([1]*15+[-1]*2, period=periods, frame=frames, cost=100.)
            self.assertEqual(out[-2:].tolist(), ['A', 'A'])

    def test_long_gap_splits_and_does_not_transfer_old_owner(self):
        out = self.run_evidence(np.r_[np.ones(15), np.zeros(10), -np.ones(2)],
                                cost=100., usable=np.r_[np.ones(15, bool), np.zeros(10, bool), np.ones(2, bool)])
        self.assertEqual(out[-2:].tolist(), ['A', 'A'])

    def test_physical_time_is_fps_invariant(self):
        s = np.r_[np.ones(10), -np.ones(10)]
        a = self.run_evidence(s)
        b = decode(np.repeat(s, 2), np.ones(40, bool), np.ones(40), np.arange(40), 20., self.cfg())
        self.assertEqual(np.repeat(a, 2).tolist(), b.tolist())

    def test_target_fields_rejected_and_unobserved_players_not_used(self):
        x = {'ball': np.tile([10., 10.], (10, 1)), 'players': np.tile([[10., 10.], [20., 20.]], (10, 1, 1)),
             'teams': np.array([0, 1]), 'period': np.ones(10), 'frame': np.arange(10), 'fps': 10.,
             'pitch': np.array([105., 68.]), 'ball_observed': np.ones(10, bool), 'player_detected': np.ones((10, 2), bool)}
        self.assertTrue(np.all(predict(x, self.cfg()) == 'H'))
        with self.assertRaises(ValueError): measurements({**x, 'targets': ['H']*10})
        x['player_detected'][:, 0] = False
        self.assertTrue(np.all(predict(x, self.cfg()) == 'X'))


class ProxyMetricTests(unittest.TestCase):
    def test_fill_does_not_cross_unknown_teacher_or_half(self):
        target = np.array(list('HHHXAAA'))
        pred = np.array(list('HXXXXX A'.replace(' ', '')))
        result = fill_prediction_gaps(target, pred, np.ones(7))
        self.assertEqual(''.join(result), 'HHHXAAA')
        result = fill_prediction_gaps(np.array(list('HHAA')), np.array(list('HXXX')), np.array([1, 1, 2, 2]))
        self.assertEqual(''.join(result), 'HHXX')

    def test_internal_abstention_preserves_spell_but_not_frame_accuracy(self):
        truth = np.array(list('HHHHAAAA'))
        pred = np.array(list('HXHXAXAX'))
        report = evaluate(truth, pred, np.ones(8))
        self.assertEqual(report['provider_filled_spell_f1'], 1.)
        self.assertLess(report['provider_macro_f1_HA'], 1.)
        self.assertFalse(report['competition_score'])


if __name__ == '__main__': unittest.main()
