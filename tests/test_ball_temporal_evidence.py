import copy
import unittest
import numpy as np
from test_ball_tracking import CONFIG
from test_confirmed_ball_filter import frames
from development.temporal_ball_features import fit
from tools.ball_temporal_evidence import attach


class EvidenceAdapterTests(unittest.TestCase):
    def test_evidence_cannot_change_boxes_tracks_or_ownership(self):
        data=frames([[(100+i*5,100)] for i in range(5)]+[[]])
        for p in data:p['possession']={'label':'X'};p['ball_tracking']={'tracks':[]}
        original=copy.deepcopy(data)
        rng=np.random.default_rng(12);raw=rng.normal(size=(20,8))
        model=fit(raw,np.array([0,1]*10),np.ones(20),.1)
        output=attach(data,CONFIG,{'model':model,'threshold':.5})
        self.assertEqual(data,original)
        for p,before in zip(output,original):
            evidence=p['experimental_ball_evidence']
            self.assertFalse(evidence['possession_eligible'])
            self.assertFalse(evidence['selected_in_play_ball'])
            self.assertEqual({k:v for k,v in p.items() if k!='experimental_ball_evidence'},before)
        self.assertEqual(output[-1]['experimental_ball_evidence']['detections'],[])
