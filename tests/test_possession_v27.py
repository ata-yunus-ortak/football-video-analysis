"""Synthetic checks of the gap-bridging feature candidate (possession v2.7, not selected)."""
import unittest
import numpy as np
try:  # needs scipy (requirements-possession.txt)
    from possession.features import features
    from possession.features3 import features3
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def _match(n=2000):
    rng = np.random.default_rng(0)
    pl = rng.uniform(10, 90, (1, 22, 2)) + np.cumsum(rng.normal(0, .05, (n, 22, 2)), 0)
    ball = pl[:, 3] + rng.normal(0, .2, (n, 2))
    ball[400:450] = np.nan; ball[900:1300] = np.nan
    return dict(fps=25., pitch=np.array([105., 68.]), ball=ball.astype(np.float32), players=pl.astype(np.float32),
                team=np.r_[np.zeros(11), np.ones(11)].astype(np.int8), period=np.r_[np.ones(1000), np.full(n - 1000, 2)].astype(np.int8))


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class Features3Tests(unittest.TestCase):
    def test_v2_columns_unchanged_and_names_unique(self):
        m = _match(); X, names = features3(m); B, bn = features(m)
        self.assertEqual(names[:len(bn)], bn); self.assertEqual(len(set(names)), len(names))
        self.assertTrue(np.array_equal(X[:, :B.shape[1]], B, equal_nan=True))

    def test_bridge_follows_carrier_and_respects_limits(self):
        m = _match(); X, names = features3(m); i = {k: j for j, k in enumerate(names)}
        # ball was carried by home slot 3 through the short gap: bridged distance stays small
        self.assertLess(X[425, i['h_x_di']], 1.5); self.assertLess(X[425, i['h_x_carry_end_d']], 1.5)
        self.assertAlmostEqual(float(X[425, i['x_gap_len']]), 2.04, places=2)
        # the long gap straddles the half change: never bridged across blocks
        self.assertTrue(np.isnan(X[950, i['h_x_di']])); self.assertTrue(np.isnan(X[950, i['x_gap_len']]))
        self.assertEqual(float(X[100, i['x_gap_len']]), 0.0)

    def test_team_swap_symmetry(self):
        m = _match(); X, names = features3(m); Xs, _ = features3(m, swap=True); i = {k: j for j, k in enumerate(names)}
        self.assertTrue(np.allclose(X[:, i['h_x_di']], Xs[:, i['k_x_di']], equal_nan=True))
        self.assertTrue(np.allclose(X[:, i['diff_x_hold_di']], -Xs[:, i['diff_x_hold_di']], equal_nan=True))


if __name__ == '__main__':
    unittest.main()
