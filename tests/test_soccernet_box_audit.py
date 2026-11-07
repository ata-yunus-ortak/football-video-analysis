import unittest
from tools.soccernet_box_audit import reference_rows


class ReferenceSchemaTests(unittest.TestCase):
    def test_person_roles_ball_and_pitch_are_kept_separate(self):
        names = {1: 'player', 3: 'referee', 4: 'ball', 5: 'pitch'}
        labels = {'annotations': [
            {'image_id': 'frame1', 'category_id': cat, 'bbox_image': {'x': 2, 'y': 3, 'w': 4, 'h': 5}}
            for cat in [1, 3, 4]] + [{'image_id': 'frame1', 'category_id': 5},
                                    {'image_id': 'frame2', 'category_id': 1}]}
        rows = reference_rows(labels, 'frame1', names)
        self.assertEqual([r['kind'] for r in rows], ['person', 'person', 'sports ball'])
        self.assertEqual(rows[0]['box_xyxy'], [2, 3, 6, 8])
        self.assertTrue(all('team' not in r and 'bbox_pitch' not in r for r in rows))
