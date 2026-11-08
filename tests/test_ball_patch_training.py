import unittest
from tools.ball_patch_training import subset


class PatchEvaluationTests(unittest.TestCase):
    def test_native_ids_are_preserved_and_other_references_excluded(self):
        images=[{'id':2,'file_name':'a.jpg'},{'id':17,'file_name':'b.jpg'}]
        coco={'images':images,'annotations':[{'image_id':2},{'image_id':17}]}
        result=subset(coco,[images[1]])
        self.assertEqual(result['images'][0]['id'],17)
        self.assertEqual(result['annotations'],[{'image_id':17}])

    def test_duplicate_or_changed_correspondence_rejected(self):
        image={'id':17,'file_name':'b.jpg'}
        coco={'images':[image],'annotations':[]}
        for bad in ([image,image],[{'id':17,'file_name':'other.jpg'}]):
            with self.assertRaises(ValueError):subset(coco,bad)
