import unittest

try:
    import numpy as np
    from possession import decode, infer
except ImportError:  # the offline suite runs without site-packages
    np = None


@unittest.skipIf(np is None, "numpy not installed")
class InferTest(unittest.TestCase):
    def weights(self, hidden=16, feats=37):
        rng = np.random.default_rng(0)
        w = {"stem.weight": rng.normal(size=(hidden, feats, 5)) * 0.1, "stem.bias": np.zeros(hidden),
             "head.weight": rng.normal(size=(3, hidden, 1)), "head.bias": np.zeros(3)}
        for b, d in enumerate((1, 4)):
            p = "blocks.%d." % b
            w[p + "conv.weight"] = rng.normal(size=(hidden, hidden, 3)) * 0.1
            w[p + "conv.bias"] = np.zeros(hidden)
            w[p + "mix.weight"] = rng.normal(size=(hidden, hidden, 1)) * 0.1
            w[p + "mix.bias"] = np.zeros(hidden)
            w[p + "norm.weight"] = np.ones(hidden)
            w[p + "norm.bias"] = np.zeros(hidden)
            w[p + "dilation"] = np.int64(d)
        return w

    def test_forward_is_a_distribution_and_repeatable(self):
        x = np.random.default_rng(1).normal(size=(200, 37)).astype(np.float32)
        a, b = infer.forward(self.weights(), x), infer.forward(self.weights(), x)
        self.assertEqual(a.shape, (100, 3))
        self.assertTrue(np.allclose(a.sum(1), 1.0))
        self.assertTrue(np.array_equal(a, b))

    def test_erf_accuracy(self):
        import math
        x = np.linspace(-4, 4, 801)
        self.assertLess(np.abs(infer._erf(x) - np.array([math.erf(v) for v in x])).max(), 2e-7)

    def test_viterbi_removes_single_frame_flicker(self):
        p = np.tile([0.9, 0.05, 0.05], (50, 1))
        p[25] = [0.3, 0.6, 0.1]
        self.assertTrue((decode.decode(p, 6.0) == 0).all())

    def test_dead_and_home_grid(self):
        prob = np.tile([0.6, 0.2, 0.2], (10, 1))
        dead, home = infer.dead_and_home(prob, 20)
        self.assertEqual(len(dead), 20)
        self.assertAlmostEqual(home[0], 0.75)


if __name__ == "__main__":
    unittest.main()
