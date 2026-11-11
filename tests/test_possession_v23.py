"""Synthetic checks for the v2.3 candidate's input smoothing (possession/smooth.py); no accuracy claims."""
import unittest
import numpy as np
try:
    from possession.smooth import smooth_positions, _smooth2d
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')


def match(n=400, s=4, seed=0):
    rng = np.random.default_rng(seed)
    players = (np.array([20.0, 30.0]) + np.cumsum(rng.normal(0, 0.05, (n, s, 2)), 0)).astype(np.float32)
    ball = (np.array([50.0, 34.0]) + np.cumsum(rng.normal(0, 0.1, (n, 2)), 0)).astype(np.float32)
    period = np.r_[np.zeros(20), np.ones(180), np.zeros(20), np.full(n - 220, 2)].astype(np.int8)
    return {'fps': 25.0, 'ball': ball, 'players': players, 'team': np.r_[0, 0, 1, 1].astype(np.int8),
            'period': period}


@NEEDS
class SmoothTests(unittest.TestCase):
    def test_constant_and_linear_signals_are_unchanged_inside_a_block(self):
        a = np.c_[np.full(50, 3.0), np.arange(50.0)]
        out = _smooth2d(a, 2)
        np.testing.assert_allclose(out[:, 0], 3.0)
        np.testing.assert_allclose(out[2:-2, 1], np.arange(50.0)[2:-2])   # centred window: exact for a line

    def test_missing_frames_stay_missing_and_are_not_filled(self):
        a = np.c_[np.arange(30.0)]
        a[10:13] = np.nan
        out = _smooth2d(a, 2)
        self.assertTrue(np.isnan(out[10:13]).all())
        self.assertTrue(np.isfinite(np.delete(out, [10, 11, 12], 0)).all())
        self.assertAlmostEqual(float(out[9, 0]), np.mean([7.0, 8.0, 9.0]))   # mean of the finite neighbours only

    def test_iid_noise_is_reduced(self):
        rng = np.random.default_rng(1)
        a = rng.normal(0, 1.0, (20000, 2))
        self.assertLess(np.var(_smooth2d(a, 2)), 0.25)          # 5-frame mean: variance about 1/5

    def test_blocks_are_independent_and_outside_frames_untouched(self):
        m = match()
        out = smooth_positions(m, 2)
        self.assertEqual(out['ball'].dtype, np.float32)
        self.assertEqual(out['players'].shape, m['players'].shape)
        outside = m['period'] == 0
        np.testing.assert_array_equal(out['ball'][outside], m['ball'][outside])
        m2 = dict(m)
        m2['ball'] = m['ball'].copy()
        m2['ball'][220:] += 100.0                                 # change only the second block
        out2 = smooth_positions(m2, 2)
        np.testing.assert_array_equal(out2['ball'][:200], out['ball'][:200])
        self.assertIs(out['team'], m['team'])                     # everything else is passed through


if __name__ == '__main__':
    unittest.main()
