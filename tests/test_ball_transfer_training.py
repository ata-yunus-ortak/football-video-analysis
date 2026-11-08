import unittest
from tools.ball_transfer_training import summarize, accepted


class BallTransferEvaluationTests(unittest.TestCase):
    def test_one_reference_cannot_match_duplicate_predictions(self):
        p={'box_xyxy':[0,0,10,10],'confidence':.8}
        coco={'images':[{'id':1}], 'annotations':[{'image_id':1,'bbox':[0,0,10,10]}]}
        result=summarize([{'image_id':1,'predictions':[p,p]}],coco)
        self.assertEqual(result['matched'],1)
        self.assertEqual(result['unmatched_predictions'],1)
        with self.assertRaisesRegex(ValueError,'correspondence'):
            summarize([{'image_id':2,'predictions':[p]}],coco)

    def test_lower_recall_cannot_pass_as_precision_improvement(self):
        base={'matched':10,'unmatched_predictions':10}
        self.assertTrue(accepted(base,{'matched':10,'unmatched_predictions':8}))
        self.assertFalse(accepted(base,{'matched':9,'unmatched_predictions':0}))
        self.assertFalse(accepted(base,{'matched':11,'unmatched_predictions':9}))
