"""Synthetic checks for the frame-dependent switch cost (possession/decode2.py); no accuracy claims."""
import unittest
import numpy as np
try:
    import possession.features                     # noqa: F401  (scipy; used inside the block decoders)
    from possession.decode import viterbi, emissions, decode_blocks
    from possession.decode2 import viterbi_tv, decode_blocks_tv, switch_costs
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')


@NEEDS
class SwitchCostTests(unittest.TestCase):
    def test_constant_cost_and_neutral_hazard_reproduce_the_frozen_decoder(self):
        rng = np.random.default_rng(0)
        lp = emissions(rng.uniform(0, 1, 4000), rng.uniform(0, 1, 4000))
        np.testing.assert_array_equal(viterbi(lp, 3.0, 60.0, 60.0, -0.3), viterbi_tv(lp, np.full(4000, 3.0), 60.0, 60.0, -0.3))
        per = np.r_[np.zeros(50), np.ones(3950)].astype(np.int8)
        a = decode_blocks(lp, per, {'switch': 4.0, 'out_cost': 60.0, 'in_cost': 60.0, 'bias_dead': -0.3})
        b = decode_blocks_tv(lp, np.full(4000, 0.5), per, {'switch_s0': 4.0, 'switch_beta': 2.0, 'out_cost': 60.0,
                                                            'in_cost': 60.0, 'bias_dead': -0.3})
        np.testing.assert_array_equal(a, b)

    def test_costs_fall_with_the_hazard_and_never_go_negative(self):
        c = switch_costs(np.array([0.01, 0.5, 0.99, 1.0]), 4.0, 1.5)
        self.assertTrue(c[0] > c[1] > c[2] >= 0.0)
        self.assertEqual(c[3], 0.0)

    def test_high_hazard_at_the_edges_lets_a_short_weak_possession_through(self):
        n = 300
        p_dead = np.full(n, 0.01)
        p_home = np.full(n, 0.8)
        p_home[140:160] = 0.4                      # 20 weak frames for the away team
        lp = emissions(p_dead, p_home)
        per = np.ones(n, np.int8)
        params = {'switch_s0': 6.0, 'switch_beta': 2.0, 'out_cost': 60.0, 'in_cost': 60.0, 'bias_dead': 0.0}
        flat = decode_blocks_tv(lp, np.full(n, 0.5), per, params)
        self.assertFalse((flat == 'A').any())      # cost 6 twice > 20 * log(0.6/0.4) evidence
        h = np.full(n, 0.05)
        h[135:145] = 0.97
        h[155:165] = 0.97
        peaked = decode_blocks_tv(lp, h, per, params)
        self.assertTrue((peaked[142:158] == 'A').all())
        self.assertTrue((peaked[:130] == 'H').all() and (peaked[170:] == 'H').all())


if __name__ == '__main__':
    unittest.main()
