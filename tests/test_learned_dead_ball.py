import unittest
import numpy as np
from development.learned_dead_ball import (features,fit,probability,corrupt,classify,boundary_score,temporal_mean)


def sample(n=40):
    return {'ball':np.tile([30.,20.],(n,1)),'players':np.tile([[30.,20.],[31.,21.],[32.,22.],[33.,23.]],(n,1,1)),
            'teams':np.array([0,0,1,1]),'period':np.ones(n,int),'frame':np.arange(n),'fps':np.array(25.),
            'pitch':np.array([105.,68.]),'ball_observed':np.ones(n,bool),'player_detected':np.ones((n,4),bool)}


class LearnedDeadBallTests(unittest.TestCase):
    def test_labels_events_and_match_clock_cannot_enter_features(self):
        x=sample()
        for field in ('BallStatus','BallPossession','labels','events','match_clock'):
            with self.assertRaises(ValueError):features({**x,field:np.zeros(40)})

    def test_no_mutation_and_team_roster_permutation_invariance(self):
        x=sample();original=x['players'].copy();a,_=features(x)
        x['players']=x['players'][:,::-1];x['teams']=x['teams'][::-1]
        b,_=features(x);np.testing.assert_allclose(a,b,equal_nan=True)
        np.testing.assert_array_equal(x['players'][:,::-1],original)

    def test_missing_is_not_dead_and_dropout_does_not_modify_source(self):
        x=sample();v=corrupt(x,3,1.,1.);raw,usable=features(v)
        self.assertFalse(usable.any());self.assertTrue(np.isfinite(x['ball']).all())
        state=classify(np.ones(40),usable,x,.5,.5)
        self.assertTrue(np.all(state=='X'))

    def test_windows_do_not_cross_period_or_frame_gaps(self):
        z=np.array([[1.],[1.],[9.],[9.]])
        for p,f in [(np.array([1,1,2,2]),np.arange(4)),(np.ones(4),np.array([0,1,5,6]))]:
            np.testing.assert_array_equal(temporal_mean(z,p,f,10),z)

    def test_fit_recovers_synthetic_relation_and_is_deterministic(self):
        rng=np.random.default_rng(33);x=rng.normal(size=(300,24));y=(x[:,0]+x[:,1]>0).astype(float)
        x[:20,3]=np.nan
        a=fit(x,y,np.ones(300),.001);b=fit(x,y,np.ones(300),.001)
        self.assertEqual(a,b);self.assertGreater(np.mean((probability(x,a)>.5)==y),.95)

    def test_temporal_dead_boundary_and_one_to_one_boundary_score(self):
        x=sample(100);p=np.r_[np.full(25,.05),np.full(50,.95),np.full(25,.05)]
        state=classify(p,np.ones(100,bool),x,.5,.1)
        self.assertEqual(state.tolist(),['L']*25+['D']*50+['L']*25)
        y=np.where(state=='D','D','H');r=boundary_score(y,state,x['period'],25.)
        self.assertEqual(r['f1'],1.);self.assertEqual(r['matched'],2)
        shifted=np.r_[['L']*10,state[:-10]];r=boundary_score(y,shifted,x['period'],25.)
        self.assertAlmostEqual(r['matched_median_error_s'],.4)


if __name__=='__main__':unittest.main()
