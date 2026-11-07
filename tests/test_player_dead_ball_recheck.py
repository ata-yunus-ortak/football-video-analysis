import unittest
import numpy as np
from tools.player_dead_ball_recheck import partial_targets


class PartialProxyTests(unittest.TestCase):
    def test_unknown_not_dead_and_conflicts_withheld(self):
        x={'frame':np.arange(10),'source_frame':np.arange(1,11),'period':np.ones(10)}
        intervals=[{'start_index':3,'stop_index_exclusive':7}]
        events=[{'type':'PASS','start':1,'end':4,'period':1},{'type':'SHOT','start':9,'end':10,'period':1}]
        y,c=partial_targets(x,intervals,events)
        self.assertEqual(''.join(y),'HHHXDDDXXX')
        self.assertEqual(c['conflicting_frames_withheld'],1)

    def test_cross_period_pass_rejected(self):
        x={'frame':np.arange(4),'source_frame':np.arange(1,5),'period':np.array([1,1,2,2])}
        y,_=partial_targets(x,[],[{'type':'PASS','start':1,'end':4,'period':1}])
        self.assertTrue(np.all(y=='X'))


if __name__=='__main__':unittest.main()
