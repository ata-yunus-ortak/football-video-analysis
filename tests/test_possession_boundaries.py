import unittest
import numpy as np
from development.possession_boundaries import transitions,match_times,evaluate,timeline


class BoundaryTests(unittest.TestCase):
    def test_spells_do_not_assign_missing_time_and_use_exclusive_end(self):
        result=timeline(list('HHXAAA'),[1]*6,np.arange(6),10)
        a,b=result['spells']
        self.assertEqual((a['start_s'],a['end_s_exclusive']),(0,.2))
        self.assertEqual((b['start_s'],b['end_s_exclusive']),(.3,.6))
        self.assertTrue(a['end_censored']);self.assertTrue(b['start_censored'])
        self.assertFalse(result['unknown_is_dead_ball'])

    def test_direct_change_is_shared_endpoint_not_two_separate_events(self):
        result=timeline(list('HHAA'),[1]*4,np.arange(4),10)
        a,b=result['spells']
        self.assertEqual(a['end_s_exclusive'],b['start_s'])
        self.assertFalse(a['end_censored']);self.assertFalse(b['start_censored'])
        self.assertEqual(len(result['exact_adjacent_label_changes']),1)

    def test_gap_is_interval_not_exact_boundary(self):
        exact,uncertain=transitions(list('HHXXAA'),[1]*6,np.arange(6),10)
        self.assertEqual(exact,[])
        self.assertEqual((uncertain[0]['earliest_s'],uncertain[0]['latest_s']),(.2,.4))

    def test_direction_duplicates_and_unknown_targets(self):
        r=evaluate(list('HHHAAA'),list('HHAAAA'),[1]*6,np.arange(6),10)
        self.assertEqual(r['tolerances_s']['0.2']['matched'],1)
        self.assertAlmostEqual(r['tolerances_s']['0.2']['mean_signed_error_s'],-.1)
        r=evaluate(list('HHXXAA'),list('HHHAAA'),[1]*6,np.arange(6),10)
        self.assertEqual(r['tolerances_s']['0.2']['reference'],0)
        self.assertEqual(r['tolerances_s']['0.2']['predicted'],0)

    def test_one_to_one_optimal_matching_and_clock_breaks(self):
        self.assertEqual(len(match_times([1.,1.3],[.8,1.1],.3)),2)
        self.assertEqual(len(match_times([1.],[.9,1.1],.2)),1)
        self.assertEqual(transitions(list('HA'),[1,2],[0,1],10),([],[]))
        self.assertEqual(transitions(list('HA'),[1,1],[0,3],10),([],[]))

    def test_prediction_gap_never_gets_exact_credit(self):
        r=evaluate(list('HHHAAA'),list('HHXXAA'),[1]*6,np.arange(6),10)
        self.assertEqual(r['tolerances_s']['0.5']['matched'],0)
        self.assertEqual(r['uncertain_predicted_changes'],1)
