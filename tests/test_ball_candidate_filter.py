import unittest
import numpy as np
from development import ball_candidate_filter as model
from tools.ball_candidate_selection import evaluate, passes, training_rows


class CandidateFilterTests(unittest.TestCase):
    def test_geometry_is_scale_and_person_order_invariant(self):
        box = [20, 40, 26, 46]; people = [[10, 0, 30, 50], [50, 10, 70, 70]]
        a = model.features(box, .6, people, [100, 100])
        b = model.features(np.asarray(box)*2, .6, [np.asarray(p)*2 for p in people[::-1]], [200, 200])
        np.testing.assert_allclose(a, b)

    def test_missing_person_is_missing_evidence(self):
        x = model.features([1, 1, 3, 3], .4, [], [100, 100])
        self.assertTrue(np.isnan(x[-2:]).all())
        with self.assertRaises(ValueError):
            model.features([1, 1, 1, 3], .4, [], [100, 100])

    def test_fit_requires_both_classes_and_correct_schema(self):
        with self.assertRaises(ValueError):
            model.fit(np.ones((3, 5)), np.ones(3), np.ones(3), .01)
        raw = np.asarray([[x, 0, 0, np.nan, np.nan] for x in (.1, .2, .8, .9)])
        fitted = model.fit(raw, np.array([0, 0, 1, 1]), np.ones(4), .01)
        p = model.probability(raw, fitted)
        self.assertLess(p[0], p[-1])
        self.assertEqual(fitted['feature_names'], model.FEATURE_NAMES)

    def test_empty_references_not_training_negatives_but_scored(self):
        f = {'clip': 'a', 'mode': 'native', 'raw': np.zeros((1, 5)),
             'predictions': [{'box_xyxy': [0, 0, 10, 10], 'confidence': .8}], 'references': []}
        self.assertEqual(len(training_rows([f])[0]), 0)
        self.assertEqual(evaluate([f], {'kind': 'keep_all'})['native']['unmatched_predictions'], 1)

    def test_duplicates_cannot_inflate_matched_count(self):
        pred = {'box_xyxy': [0, 0, 10, 10], 'confidence': .8}
        f = {'mode': 'native', 'raw': np.zeros((2, 5)), 'predictions': [pred, pred],
             'references': [{'box_xyxy': [0, 0, 10, 10]}]}
        score = evaluate([f], {'kind': 'keep_all'})['native']
        self.assertEqual(score['matched'], 1)
        self.assertEqual(score['unmatched_predictions'], 1)

    def test_gate_checks_each_mode_and_recall(self):
        base = {m: {'matched': 100, 'unmatched_predictions': 100} for m in ('native', 'sliced')}
        good = {m: {'matched': 95, 'unmatched_predictions': 80} for m in base}
        self.assertTrue(passes(good, base))
        good['native']['matched'] = 94
        self.assertFalse(passes(good, base))


if __name__ == '__main__':
    unittest.main()
