import unittest
import numpy as np
from test_ball_tracking import CONFIG
from test_confirmed_ball_filter import frames
from development import temporal_ball_features as model
from tools.ball_temporal_selection import score


class TemporalFeatureTests(unittest.TestCase):
    def test_confirmation_is_bounded_and_reference_fields_have_no_effect(self):
        data=frames([[(100+i*5,100)] for i in range(8)])
        before=model.extract(data,CONFIG)
        self.assertEqual(before[0][0,5:].tolist(),[1.,1.,1.])
        short=model.extract(data[:5],CONFIG)
        np.testing.assert_equal(before[0],short[0])
        for p in data:p['reference_ball']=[999,999];p['possession']='H'
        after=model.extract(data,CONFIG)
        for a,b in zip(before,after):np.testing.assert_equal(a,b)

    def test_no_detection_produces_no_feature_row_even_when_track_forecasts(self):
        data=frames([[(100,100)],[(105,100)],[(110,100)],[]])
        raw=model.extract(data,CONFIG)
        self.assertEqual(raw[-1].shape,(0,8))

    def test_unknown_reference_frame_not_counted_as_false_positive(self):
        run={'mode':'native'};rows=frames([[(100,100)],[(105,100)]])
        objects=[[p['objects'][0]] for p in rows]
        result=score([run],[objects],[[None,[{'box_xyxy':[103,98,107,102]}]]])['native']
        self.assertEqual(result['matched'],1)
        self.assertEqual(result['unmatched_predictions'],0)
        self.assertEqual(result['unknown_frames'],1)

    def test_learned_schema_rejects_geometry_temporal_mismatch(self):
        rng=np.random.default_rng(5);raw=rng.normal(size=(20,8));targets=np.array([0,1]*10)
        fitted=model.fit(raw,targets,np.ones(20),.1)
        p=model.probability(raw,fitted)
        self.assertTrue(np.isfinite(p).all())
        self.assertTrue(((p>=0)&(p<=1)).all())
        with self.assertRaises(ValueError):model.probability(raw[:,:5],fitted)
