import unittest
import numpy as np
from development import player_dead_ball as model
from test_learned_dead_ball import sample


class PlayerDeadTests(unittest.TestCase):
    def test_ball_geometry_visibility_and_motion_never_affect_features(self):
        x=sample(60);a,u=model.features(x)
        x['ball'][:]=np.random.default_rng(3).normal(size=(60,2))*10000
        x['ball_observed'][:]=False;x['ball_pair_valid']=np.zeros(60,bool)
        b,v=model.features(x)
        np.testing.assert_allclose(a,b,equal_nan=True);np.testing.assert_array_equal(u,v)

    def test_player_only_model_schema_and_probability(self):
        rng=np.random.default_rng(4);raw=rng.normal(size=(200,15));y=(raw[:,0]>0).astype(float)
        m=model.fit(raw,y,np.ones(200),.001)
        self.assertEqual(len(m['feature_names']),15)
        self.assertGreater(np.mean((model.probability(raw,m)>.5)==y),.95)

    def test_reference_state_rejected(self):
        with self.assertRaises(ValueError):model.features({**sample(),'BallStatus':np.zeros(40)})


if __name__=='__main__':unittest.main()
