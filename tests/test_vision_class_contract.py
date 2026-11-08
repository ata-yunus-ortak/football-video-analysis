import unittest
from development.vision import validate_coco_contract, validate_coco_head_shapes


class VisionClassContractTests(unittest.TestCase):
    def test_checkpoint_shape_checked_before_constructor_can_replace_head(self):
        validate_coco_head_shapes([(91,256),(91,)])
        for shapes in ([], [(2,256),(2,)], [(91,256),(2,)]):
            with self.assertRaisesRegex(ValueError,'automatic head replacement'):
                validate_coco_head_shapes(shapes)

    def test_matching_coco_contract_accepted(self):
        validate_coco_contract(['person','sports ball'],90,['person','sports ball'])

    def test_custom_head_and_reordered_names_rejected(self):
        for names, count in [(['ball'],1), (['person','sports ball'],1),
                             (['sports ball','person'],90), ([],90)]:
            with self.assertRaisesRegex(ValueError,'dedicated class mapping'):
                validate_coco_contract(names,count,['person','sports ball'])
