import unittest
from development.vision_box_audit import iou, match_boxes


class BoxAuditTests(unittest.TestCase):
    def test_duplicate_predictions_do_not_double_count_reference(self):
        rows = [{'box_xyxy': [0, 0, 10, 10], 'confidence': score} for score in [.5, .9]]
        result = match_boxes(rows, [{'box_xyxy': [0, 0, 10, 10]}], .5)
        self.assertEqual(result['matches'][0]['prediction'], 1)
        self.assertEqual(result['unmatched_predictions'], 1)

    def test_no_detections_or_no_targets_are_explicit(self):
        self.assertEqual(match_boxes([], [{'box_xyxy': [0, 0, 2, 2]}], .5)['unmatched_references'], 1)
        self.assertEqual(match_boxes([], [], .5)['matches'], [])
        self.assertAlmostEqual(iou([0, 0, 2, 2], [1, 0, 3, 2]), 1 / 3)

    def test_invalid_geometry_and_threshold_rejected(self):
        with self.assertRaises(ValueError): iou([0, 0, 0, 3], [0, 0, 2, 2])
        with self.assertRaises(ValueError): match_boxes([], [], float('nan'))
