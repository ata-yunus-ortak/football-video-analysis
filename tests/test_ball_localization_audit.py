import unittest
from tools.ball_localization_audit import describe


class LocalizationAuditTests(unittest.TestCase):
    def test_duplicate_and_unknown_frame_are_separate(self):
        p = {'box_xyxy': [0, 0, 10, 10], 'confidence': .9}
        r = {'box_xyxy': [0, 0, 10, 10]}
        frames = [{'mode': 'native', 'predictions': [p, p], 'references': [r]},
                  {'mode': 'native', 'predictions': [p], 'references': []}]
        result = describe(frames)['native']
        self.assertEqual(result['duplicate_high_overlap_predictions'], 1)
        self.assertEqual(result['predictions_on_unannotated_ball_frames'], 1)
        self.assertEqual(result['predictions_iou_below_0_1_on_annotated_frames'], 0)
        self.assertEqual(result['one_to_one_matches_by_iou']['0.5'], 1)

    def test_no_detection_is_zero_overlap_without_fabricated_distance(self):
        r = describe([{'mode': 'native', 'predictions': [],
                       'references': [{'box_xyxy': [1, 1, 2, 2]}]}])['native']
        self.assertEqual(r['reference_best_iou_quartiles_and_p90'], [0., 0., 0., 0.])
        self.assertIsNone(r['nearest_centre_error_px_quartiles_and_p90'])
        self.assertEqual(r['centre_error_scored_references'], 0)
