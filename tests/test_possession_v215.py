"""Synthetic checks for possession v2.15 (possession/pooling.py, possession/tcn/, possession/run215.py); no accuracy claims."""
import ast
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import run211k, run215, pooling, kickoff
    from possession.tcn import infer as tcn_infer, decode as tcn_decode, features as tcn_features
    from tests.test_possession_v25 import bundle_with_broadcast
    from tests.test_possession_kickoff import tagging, kick
    from tests.test_possession_crossplatform import bundle
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

WINDOWS = [(1, 0, 4199), (2, 4500, 8999)]            # "graded windows": the second starts before a kick-off


def labels(path):
    return np.array([r.split(',')[1] for r in Path(path).read_text().splitlines()[1:]])


class PoolTests(unittest.TestCase):
    """possession/pooling.py needs numpy only."""

    def setUp(self):
        from possession import pooling as f
        self.f = f
        rng = np.random.default_rng(5)
        self.tcn = 0.02 + 0.94 * rng.dirichlet([1.0, 1.0, 1.0], 400)        # rows sum to 1, nothing below the pool's floor
        self.pd, self.ph = rng.random(400), rng.random(400)

    def test_constants_are_fixed(self):
        self.assertIn(self.f.POOL, ('arithmetic', 'geometric'))
        self.assertTrue(0.0 < self.f.WEIGHT < 1.0)

    def test_three_classes_sum_to_one(self):
        v = self.f.three_class(self.pd, self.ph)
        self.assertEqual(v.shape, (400, 3))
        self.assertTrue(np.allclose(v.sum(1), 1.0))
        self.assertTrue(np.allclose(v[:, 2], self.pd))

    def test_weight_zero_and_one(self):
        d, h = self.f.pool(self.tcn, self.pd, self.ph, 0.0, 'arithmetic')
        self.assertTrue(np.array_equal(d, np.round(self.pd, 6)) and np.array_equal(h, np.round(self.ph, 6)))
        for kind in ('arithmetic', 'geometric'):
            d, h = self.f.pool(self.tcn, self.pd, self.ph, 1.0, kind)
            self.assertTrue(np.allclose(d, self.tcn[:, 2], atol=1e-6))
            self.assertTrue(np.allclose(h, self.tcn[:, 0] / (self.tcn[:, 0] + self.tcn[:, 1]), atol=1e-6))

    def test_pool_lies_between_the_two_models(self):
        t3 = np.array([[0.7, 0.2, 0.1], [0.05, 0.05, 0.9]])
        pd_, ph = np.array([0.3, 0.2]), np.array([0.4, 0.5])
        for kind in ('arithmetic', 'geometric'):
            d, h = self.f.pool(t3, pd_, ph, 0.4, kind)
            self.assertTrue(0.1 < d[0] < 0.3 and 0.2 < d[1] < 0.9, (kind, d))
            self.assertTrue(0.4 < h[0] < 0.7 / 0.9 + 1e-9, (kind, h))
            self.assertAlmostEqual(float(h[1]), 0.5, places=6)                 # both models have no team preference

    def test_output_is_rounded_finite_and_exchanges_with_the_teams(self):
        d, h = self.f.pool(self.tcn, self.pd, self.ph)
        self.assertTrue(np.isfinite(d).all() and np.isfinite(h).all())
        self.assertTrue(((d >= 0) & (d <= 1) & (h >= 0) & (h <= 1)).all())
        self.assertTrue(np.array_equal(d, np.round(d, 6)) and np.array_equal(h, np.round(h, 6)))
        d2, h2 = self.f.pool(self.tcn[:, [1, 0, 2]], self.pd, 1.0 - self.ph)
        self.assertTrue(np.allclose(d, d2, atol=1e-6) and np.allclose(h, 1.0 - h2, atol=2e-6))
        z, _ = self.f.pool(np.zeros((3, 3)), np.full(3, 0.5), np.full(3, 0.5))    # rows outside the play blocks
        self.assertTrue(np.isfinite(z).all())

    def test_unknown_pool_is_refused(self):
        with self.assertRaises(ValueError):
            self.f.pool(self.tcn, self.pd, self.ph, 0.3, 'median')


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class NetworkTests(unittest.TestCase):
    def test_weights_file(self):
        members = tcn_infer.load_weights(run215.TCN_MODEL)
        self.assertEqual(len(members), 3)
        for w in members:
            self.assertEqual(w['stem.weight'].shape, (128, tcn_features.N_FEATURES, 5))
            self.assertEqual(w['head.weight'].shape, (3, 128, 1))
            self.assertEqual(sum(1 for k in w if k.endswith('.dilation')), 14)

    def test_probabilities_are_distributions_and_exchange_with_the_teams(self):
        rng = np.random.default_rng(3)
        n = 600
        t0 = np.cumsum(rng.normal(0, 0.1, (n, 6, 2)), 0) + rng.uniform(-30, 0, (1, 6, 2))
        t1 = np.cumsum(rng.normal(0, 0.1, (n, 6, 2)), 0) + rng.uniform(0, 30, (1, 6, 2))
        ball = t0[:, 0] + 0.5
        ball[200:260] = np.nan
        members = tcn_infer.load_weights(run215.TCN_MODEL)
        p = tcn_infer.probabilities(members, ball.astype(np.float32), t0.astype(np.float32), t1.astype(np.float32))
        q = tcn_infer.probabilities(members, ball.astype(np.float32), t1.astype(np.float32), t0.astype(np.float32))
        self.assertEqual(p.shape, (300, 3))
        self.assertTrue(np.allclose(p.sum(1), 1.0, atol=2e-4))
        self.assertTrue(np.allclose(p, q[:, [1, 0, 2]], atol=1e-9))            # averaged over both team orders
        up = tcn_decode.upsample(p, tcn_infer.STRIDE, n)
        self.assertEqual(up.shape, (n, 3))
        self.assertTrue(np.array_equal(up[::2], p))


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class Run214Tests(unittest.TestCase):
    def test_manifest_and_no_frame_constant(self):
        rel = run215.check_release()
        self.assertEqual(rel['version'], 'possession-v2.15')
        self.assertEqual(set(rel['bundle_sha256']), {'v2.1', 'v2.3', 'tcn'})
        for mod in (run215, pooling, kickoff):
            tree = ast.parse(Path(mod.__file__).read_text(encoding='utf-8'))
            numbers = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                       and not isinstance(n.value, bool)]
            self.assertTrue(all(abs(v) < 1000 for v in numbers), numbers)        # no frame number of any match in the code

    def test_pooling_on_the_core_path_and_kickoff_rule(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle_with_broadcast(root / 'b', n=9000, lag=0)
            shutil.rmtree(data / 'broadcast')
            fps = run211k.frame_rate(data / 'tactical' / 'SYN_tactical_atd.xml')
            (data / 'tactical' / 'SYN_tactical_smart_tagging.xml').write_text(tagging([kick(5000 / fps), kick(0.0)]), encoding='utf-8')
            k = run211k.run(data, root / 'k', game='SYN', halves=WINDOWS, release=None, base_release=None, v211_release=None)
            # 1. pooling switched off: the bytes of v2.11k (everything else in run215 is the v2.11k flow)
            off = run215.run(data, root / 'off', game='SYN', halves=WINDOWS, release=None, pooled=False)
            self.assertEqual((root / 'off' / 'submission.csv').read_bytes(), (root / 'k' / 'submission.csv').read_bytes())
            self.assertFalse(off['second_model']['used'])
            # 2. pooling on: the second model is recorded, the labels are H/A/D, the kick-off rule still applies
            on = run215.run(data, root / 'on', game='SYN', halves=WINDOWS, release=None)
            lo, lk = labels(root / 'on' / 'submission.csv'), labels(root / 'k' / 'submission.csv')
            rep = json.loads((root / 'on' / 'run.json').read_text())
            self.assertEqual(rep['path'], 'v2.1')
            self.assertEqual(rep['second_model'], {'used': True, 'weights_sha256': run215.sha256(run215.TCN_MODEL),
                                                   'pool': pooling.POOL, 'weight': pooling.WEIGHT})
            self.assertIn('v2.15', rep['system'])
            self.assertEqual(len(lo), 9000)
            self.assertTrue(set(np.unique(lo)) <= {'H', 'A', 'D'})
            self.assertTrue((lo[4200:4500] == 'D').all() and (lo[4500:5000] == 'D').all())    # between the windows; before the tag
            self.assertTrue((lo != lk).any())                                                  # the second model has a say
            self.assertEqual(rep['kickoff_rule']['used_in_block'], [True, True])
            self.assertEqual(rep['submission_sha256'], on['submission_sha256'])
            self.assertEqual(rep['label_counts_in_play_blocks'],
                             {c: int(np.sum(np.r_[lo[0:4200], lo[4500:9000]] == c)) for c in 'HADX'})
            # 3. the same run again: the same bytes
            run215.run(data, root / 'again', game='SYN', halves=WINDOWS, release=None)
            self.assertEqual((root / 'again' / 'submission.csv').read_bytes(), (root / 'on' / 'submission.csv').read_bytes())

    def test_noisy_path_is_not_pooled(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle(root / 'noisy', player_noise=0.45)
            shutil.rmtree(data / 'broadcast')
            halves = [(1, 0, 4499), (2, 4500, 8999)]
            k = run211k.run(data, root / 'k', game='SYN', halves=halves, release=None, base_release=None, v211_release=None)
            v = run215.run(data, root / 'v', game='SYN', halves=halves, release=None)
            self.assertEqual(v['path'], 'v2.3')
            self.assertFalse(v['second_model']['used'])
            self.assertEqual((root / 'v' / 'submission.csv').read_bytes(), (root / 'k' / 'submission.csv').read_bytes())


if __name__ == '__main__':
    unittest.main()
