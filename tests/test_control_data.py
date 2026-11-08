import unittest
from tools.soccernet_video import image_members


class ContiguousControlDataTests(unittest.TestCase):
    def manifest(self):
        return {'complete':True,'provided_fixture_used':False,'sparse':False,'frame_numbers':[1,2],
            'acquired_files':[{'member':f'clip/img1/{i:06}.jpg','zip_crc_verified':True} for i in (1,2)]}

    def test_explicit_contiguous_manifest_accepted(self):
        self.assertEqual(len(image_members(self.manifest())),2)

    def test_sparse_and_wrong_member_order_rejected(self):
        for mode in ('sparse','numbers','members'):
            m=self.manifest()
            if mode=='sparse':m['sparse']=True
            elif mode=='numbers':m['frame_numbers']=[1,3]
            else:m['acquired_files'].reverse()
            with self.assertRaises(ValueError):image_members(m)
