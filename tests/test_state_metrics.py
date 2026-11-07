import unittest
import numpy as np
from development.state_metrics import evaluate


class StateMetricTests(unittest.TestCase):
    def score(self, y, p):
        return evaluate(np.array(list(y)), np.array(list(p)), np.ones(len(y)))

    def test_exact_HAD(self):
        r = self.score('HHHDDDAAA', 'HHHDDDAAA')
        self.assertEqual(r['macro_f1_HAD'], 1.)
        self.assertEqual(r['external_spell_f1'], 1.)

    def test_dead_period_does_not_mask_false_possession_merge(self):
        r = self.score('HHHHDDDDDDDDHHHH', 'HHHHHHHHHHHHHHHH')
        self.assertEqual(r['external_spell_f1'], 0.)
        self.assertEqual(r['per_class']['D']['recall'], 0.)

    def test_X_abstention_fills_but_D_is_not_forward_filled(self):
        r = self.score('HHHDDDAAA', 'HXXDXXAXX')
        self.assertEqual(r['external_spell_f1'], 1.)
        self.assertLess(r['macro_f1_HAD'], 1.)
        self.assertLess(self.score('HHHDDDAAA', 'HHHDDDDDD')['external_spell_f1'], 1.)

    def test_unknown_target_splits_evaluation(self):
        r = self.score('HHHXXXAAA', 'HXXXXXAXX')
        self.assertEqual(r['external_spell_f1'], 1.)
        self.assertEqual(r['known_target_frames'], 6)

    def test_empty_target_not_perfect(self):
        self.assertEqual(self.score('XXX', 'HHH')['external_spell_f1'], 0.)


if __name__ == '__main__': unittest.main()
