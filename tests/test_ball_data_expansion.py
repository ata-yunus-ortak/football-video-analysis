import unittest
from tools.ball_data_expansion import frame_numbers


class SparseDataTests(unittest.TestCase):
    def test_sparse_native_frame_numbers_not_consecutive_clock(self):
        n=frame_numbers({'frame_start':0,'frame_stop':750,'frame_stride':10})
        self.assertEqual(len(n),75)
        self.assertEqual(n[:3],[1,11,21]);self.assertEqual(n[-1],741)

    def test_invalid_intervals_fail(self):
        for a,b,s in [(0,750,0),(0,751,10),(-1,100,10),(100,10,1),(0,750,1.5)]:
            with self.assertRaises(ValueError):frame_numbers({'frame_start':a,'frame_stop':b,'frame_stride':s})
