import unittest
import numpy as np
from development.ball_patch_geometry import tile_windows,crop_boxes,positive_window


class PatchGeometryTests(unittest.TestCase):
    def test_grid_covers_edges_without_duplicates(self):
        w=tile_windows(1920,1080,384,.2)
        self.assertEqual(len(w),len(set(w)))
        self.assertEqual(w[0],(0,0,384,384));self.assertEqual(w[-1],(1536,696,1920,1080))
        coverage=np.zeros((1080,1920),bool)
        for x,y,a,b in w:coverage[y:b,x:a]=True
        self.assertTrue(coverage.all())

    def test_positive_offsets_preserve_box_and_do_not_force_centre(self):
        rng=np.random.default_rng(731);box=[700,500,10,12]
        windows=[positive_window(box,1920,1080,384,rng) for _ in range(10)]
        self.assertGreater(len(set(windows)),1)
        for w in windows:
            b=crop_boxes([box],w)[0];self.assertEqual(b[2:],[10,12])

    def test_boundary_boxes_are_clipped_and_outside_is_empty(self):
        self.assertEqual(crop_boxes([[5,5,10,10]],(10,10,20,20)),[[0,0,5,5]])
        self.assertEqual(crop_boxes([[0,0,5,5]],(10,10,20,20)),[])
