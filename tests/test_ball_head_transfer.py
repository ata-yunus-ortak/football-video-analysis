import unittest
import numpy as np
from development.ball_head_transfer import transfer_array


class BallHeadTransferTests(unittest.TestCase):
    def test_ball_logit_is_preserved_exactly_and_unused_slot_suppressed(self):
        rng=np.random.default_rng(7)
        w=rng.normal(size=(91,8)).astype('float32');b=rng.normal(size=91).astype('float32')
        x=rng.normal(size=8).astype('float32')
        tw,tb=transfer_array(w),transfer_array(b)
        self.assertEqual(float(tw[0]@x+tb[0]),float(w[37]@x+b[37]))
        self.assertEqual(float(tw[1]@x+tb[1]),-10.)
        np.testing.assert_array_equal(tw[0],w[37])

    def test_wrong_head_or_nonfinite_source_rejected(self):
        for v in (np.zeros((2,8)),np.full((91,),np.nan),np.zeros((91,2,2))):
            with self.assertRaises(ValueError):
                transfer_array(v)
