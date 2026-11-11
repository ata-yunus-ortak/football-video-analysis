"""Synthetic checks for the v2.4 noise gate (possession/noise.py) and its entry point; no accuracy claims."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession.noise import high_freq_sd, estimate_noise, choose_path, THRESHOLD_M
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
try:
    import sklearn  # noqa: F401
    HAVE_SK = True
except ImportError:
    HAVE_SK = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')


def match(n=3000, s=6, seed=0, player_sd=0.0, ball_sd=0.0):
    """Smooth running players (AR(1) velocity) and a ball that follows one of them, plus i.i.d. noise."""
    rng = np.random.default_rng(seed)
    v = np.zeros((n, s, 2))
    e = rng.normal(0, 0.01, (n, s, 2))
    for t in range(1, n):
        v[t] = 0.98 * v[t - 1] + e[t]
    p = np.array([30.0, 30.0]) + rng.uniform(-10, 10, (1, s, 2)) + np.cumsum(v, 0)
    owner = np.repeat(rng.integers(0, s, n // 250 + 1), 250)[:n]
    ball = p[np.arange(n), owner] + 0.3
    p = p + rng.normal(0, player_sd, p.shape) if player_sd else p
    ball = ball + rng.normal(0, ball_sd, ball.shape) if ball_sd else ball
    period = np.r_[np.zeros(100), np.ones(1400), np.zeros(100), np.full(n - 1600, 2)].astype(np.int8)
    return {'fps': 25.0, 'ball': ball.astype(np.float32), 'players': p.astype(np.float32),
            'team': np.r_[np.zeros(s // 2), np.ones(s - s // 2)].astype(np.int8), 'period': period}


@NEEDS
class NoiseTests(unittest.TestCase):
    def test_recovers_known_iid_noise_and_ignores_smooth_motion(self):
        self.assertLess(estimate_noise(match())['players_m'], 0.02)
        for sd in (0.1, 0.3, 0.5):
            est = estimate_noise(match(player_sd=sd, ball_sd=sd, seed=1))
            self.assertAlmostEqual(est['players_m'], sd, delta=0.1 * sd)
            self.assertAlmostEqual(est['ball_m'], sd, delta=0.1 * sd)

    def test_rare_jumps_and_missing_frames_do_not_move_the_estimate(self):
        m = match(player_sd=0.2, ball_sd=0.2, seed=2)
        base = estimate_noise(m)
        m['ball'][::40] += 15.0                    # 2.5% false detections far away
        m['players'][300:340] = np.nan             # gaps
        est = estimate_noise(m)
        self.assertAlmostEqual(est['ball_m'], base['ball_m'], delta=0.03)
        self.assertAlmostEqual(est['players_m'], base['players_m'], delta=0.02)

    def test_no_difference_across_block_edges_and_too_few_values_give_nan(self):
        self.assertTrue(np.isnan(high_freq_sd(np.zeros((100, 2)))))
        m = match(seed=3)
        m['players'][1600:] += 50.0                # a jump between the two blocks only
        self.assertLess(estimate_noise(m)['players_m'], 0.02)

    def test_choice_rule(self):
        self.assertEqual(choose_path({'players_m': 0.2, 'ball_m': 0.25})[0], 'v2.1')
        self.assertEqual(choose_path({'players_m': THRESHOLD_M + 0.01, 'ball_m': 0.1}), ('v2.3', ['players_m']))
        self.assertEqual(choose_path({'players_m': 0.1, 'ball_m': 0.5}), ('v2.3', ['ball_m']))
        self.assertEqual(choose_path({'players_m': float('nan'), 'ball_m': float('nan')})[0], 'v2.1')


def write_atd(root, m, game='SYN'):
    tac = root / 'bundle' / 'tactical'
    tac.mkdir(parents=True)
    pitch = np.array([105.0, 68.0])
    players, ball = m['players'] / pitch, m['ball'] / pitch
    (tac / f'{game}_tactical_atd.xml').write_text(
        '<main><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height></FieldSize>'
        '<Team id="h"/><Team id="a"/>' + ''.join(f'<Player teamId="{"ha"[t]}"/>' for t in m['team']) + '</main>')
    lines = []
    for i in range(len(ball)):
        groups = ';'.join(f'{x:.5f},{y:.5f},1.0' for x, y in players[i])
        lines.append(f'{i + 1}:{groups}:{ball[i, 0]:.5f},{ball[i, 1]:.5f},2.0')
    (tac / f'{game}_tactical_atd.txt').write_text('\n'.join(lines) + '\n')
    return root / 'bundle'


HALVES = [(1, 100, 1499), (2, 1600, 2999)]


@NEEDS
@unittest.skipUnless(HAVE_SK, 'scikit-learn (training only) not installed')
class Run24Tests(unittest.TestCase):
    def _bundles(self, root, card23):
        from sklearn.ensemble import HistGradientBoostingClassifier
        from possession import features, trees, bundle
        m = match(seed=5)
        m['pitch'] = np.array([105.0, 68.0])
        X, names = features.features(m)
        dec = {'switch': 5.0, 'out_cost': 5.0, 'in_cost': 5.0, 'bias_dead': 0.0}
        out = []
        for k, (card, y) in enumerate((({'version': 'synthetic-v21'}, np.arange(len(X)) % 50 < 10),
                                       (card23, np.arange(len(X)) % 70 < 20))):
            t = trees.export_hgb(HistGradientBoostingClassifier(max_iter=3).fit(np.nan_to_num(X), y.astype(int)))
            path = root / f'model{k}.npz'
            bundle.save(path, t, t, names, dec, card)
            out.append(path)
        return out

    def test_low_noise_input_runs_v21_unchanged_and_noisy_input_takes_v23(self):
        from possession import run24, validate
        from possession import run as run21
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            b21, b23 = self._bundles(root, {'version': 'synthetic-v23', 'smooth_half': 2})
            quiet = write_atd(root / 'q', match(seed=6))
            rep = run24.run(quiet, root / 'out24', b21, b23, game='SYN', halves=HALVES, expected_v21_sha256=None)
            self.assertEqual(rep['path'], 'v2.1')
            ref = run21.run(quiet, root / 'out21', b21, game='SYN', halves=HALVES)
            self.assertEqual(rep['submission_sha256'], ref['submission_sha256'])
            noisy = write_atd(root / 'n', match(seed=6, player_sd=0.5))
            rep = run24.run(noisy, root / 'outn', b21, b23, game='SYN', halves=HALVES, expected_v21_sha256=None)
            self.assertEqual(rep['path'], 'v2.3')
            self.assertEqual(rep['gate']['triggered_by'], ['players_m'])
            ok, info = validate.check(root / 'outn' / 'submission.csv', rows=3000)
            self.assertTrue(ok, info)

    def test_refuses_changed_source_wrong_v21_bundle_and_missing_smoothing(self):
        from possession import run24
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = write_atd(root, match(seed=7))
            (root / 'a').mkdir()
            b21, b23 = self._bundles(root / 'a', {'version': 'x', 'smooth_half': 2, 'source_sha256': {'noise.py': '0' * 64}})
            with self.assertRaises(ValueError):
                run24.run(data, root / 'o1', b21, b23, game='SYN', halves=HALVES, expected_v21_sha256=None)
            (root / 'b').mkdir()
            b21, b23 = self._bundles(root / 'b', {'version': 'x'})
            with self.assertRaises(ValueError):
                run24.run(data, root / 'o2', b21, b23, game='SYN', halves=HALVES, expected_v21_sha256=None)
            (root / 'c').mkdir()
            b21, b23 = self._bundles(root / 'c', {'version': 'x', 'smooth_half': 2})
            with self.assertRaises(ValueError):
                run24.run(data, root / 'o3', b21, b23, game='SYN', halves=HALVES)   # synthetic v2.1 bundle != frozen


@NEEDS
class FrozenBundles24Tests(unittest.TestCase):
    """The committed v2.1 and v2.3 bundles + current sources (hash-checked by run24) on a synthetic ATD."""
    def test_frozen_v24_runs_on_synthetic_atd(self):
        from possession import run24, validate
        if not (run24.V21_MODEL.exists() and run24.V23_MODEL.exists()):
            self.skipTest('models/possession-v2.npz or possession-v23.npz not present')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for tag, sd in (('q', 0.0), ('n', 0.5)):
                data = write_atd(root / tag, match(seed=8, player_sd=sd))
                rep = run24.run(data, root / f'out{tag}', game='SYN', halves=HALVES)
                ok, info = validate.check(root / f'out{tag}' / 'submission.csv', rows=3000)
                self.assertTrue(ok, info)
                self.assertEqual(rep['path'], 'v2.1' if tag == 'q' else 'v2.3')


if __name__ == '__main__':
    unittest.main()
