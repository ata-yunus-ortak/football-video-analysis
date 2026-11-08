import unittest
from tools.ball_confidence_calibration import select_threshold, threshold_packets


class ConfidenceCalibrationTests(unittest.TestCase):
    def test_selection_preserves_baseline_recall_before_optimizing_precision(self):
        rows=[{'threshold':.5,'score':{'matched':9,'unmatched_predictions':0}},
              {'threshold':.2,'score':{'matched':10,'unmatched_predictions':8}},
              {'threshold':.1,'score':{'matched':11,'unmatched_predictions':12}}]
        self.assertEqual(select_threshold(rows,{'matched':10})['threshold'],.2)
        self.assertIsNone(select_threshold(rows,{'matched':12}))

    def test_threshold_does_not_modify_frozen_input(self):
        packets=[{'image_id':1,'predictions':[{'confidence':.2},{'confidence':.3}]}]
        self.assertEqual(len(threshold_packets(packets,.3)[0]['predictions']),1)
        self.assertEqual(len(packets[0]['predictions']),2)
        with self.assertRaises(ValueError):threshold_packets(packets,0.)
