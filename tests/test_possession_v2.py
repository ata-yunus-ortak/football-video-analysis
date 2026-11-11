"""Synthetic checks for the possession v2 pipeline (no match data, no model accuracy claims)."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:  # possession v2 needs scipy/pandas (requirements-possession.txt)
    from possession import data, features, trees, decode, bundle
    from possession.degrade import degrade, sample_params
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
try:  # scikit-learn is a training-only dependency (requirements-possession-train.txt)
    import sklearn  # noqa: F401
    HAVE_SK = True
except ImportError:
    HAVE_SK = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession v2 dependencies not installed')
NEEDS_SK = unittest.skipUnless(HAVE_DEPS and HAVE_SK, 'scikit-learn (training only) not installed')


def synthetic_match(n=1500, seed=0):
    """Two teams, ball passed between a home and an away player, a dead stretch in the middle."""
    rng = np.random.default_rng(seed)
    s = 6
    players = np.zeros((n, s, 2), np.float32)
    base = np.array([[30, 20], [40, 40], [50, 30], [60, 25], [70, 45], [55, 50]], np.float32)
    for j in range(s):
        players[:, j] = base[j] + np.cumsum(rng.normal(0, 0.05, (n, 2)), 0)
    team = np.array([0, 0, 0, 1, 1, 1], np.int8)
    ball = np.empty((n, 2), np.float32)
    labels = np.empty(n, '<U1')
    owner = np.where((np.arange(n) // 300) % 2 == 0, 0, 3)
    for t in range(n):
        ball[t] = players[t, owner[t]] + 0.3
        labels[t] = 'H' if owner[t] < 3 else 'A'
    ball[700:800] = (52.5, -1.0)  # out of play
    labels[700:800] = 'D'
    period = np.r_[np.ones(n // 2), np.full(n - n // 2, 2)].astype(np.int8)
    return {'fps': 25.0, 'pitch': np.array([105.0, 68.0]), 'ball': ball, 'players': players,
            'team': team, 'period': period}, labels


@NEEDS
class ReaderTests(unittest.TestCase):
    def test_epts_fast_and_slow_parsers_agree(self):
        text = '1:0.1,0.2,3.5;NaN,NaN,NaN:0.5,0.5,1.2\n2:0.11,0.21,3.4;0.3,0.4,2.0:NaN,NaN,NaN\n'
        for a, b in zip(data._parse_raw(text, 2), data._parse_raw_slow(text, 2)):
            np.testing.assert_array_equal(a, b)

    def test_read_epts_scales_and_ignores_speed(self):
        with tempfile.TemporaryDirectory() as d:
            meta, raw = Path(d) / 'm.xml', Path(d) / 'r.txt'
            meta.write_text('<main><FrameRate>25</FrameRate><FieldSize><Width>100</Width><Height>50'
                            '</Height></FieldSize><Team id="h"/><Team id="a"/><Player teamId="h"/>'
                            '<Player teamId="a"/></main>')
            raw.write_text('1:0.2,0.4,999;0.7,0.6,999:0.21,0.31,999\n2:NaN,NaN,NaN;0.7,0.6,1:NaN,NaN,NaN\n')
            m, info = data.read_epts(meta, raw)
            np.testing.assert_allclose(m['ball'][0], [21, 15.5], rtol=1e-6)
            self.assertTrue(np.isnan(m['ball'][1]).all())
            np.testing.assert_array_equal(m['team'], [0, 1])
            self.assertEqual(m['first_frame_id'], 1)


    def test_read_epts_follows_data_format_specifications(self):
        def spec(a, b, pids, chans=('x', 'y', 'speed')):
            groups = ''.join('<SplitRegister separator=",">' + ''.join(
                f'<PlayerChannelRef playerChannelId="{q}_{c}"/>' for c in chans) + '</SplitRegister>' for q in pids)
            return (f'<DataFormatSpecification startFrame="{a}" endFrame="{b}" separator=":">'
                    '<StringRegister name="frameCount"/><SplitRegister separator=";">' + groups +
                    '</SplitRegister><SplitRegister separator=","><BallChannelRef channelId="x"/>'
                    '<BallChannelRef channelId="y"/></SplitRegister></DataFormatSpecification>')
        pids = ['p1', 'p2', 'p3']
        channels = ''.join(f'<PlayerChannel id="{q}_{c}" playerId="{q}" channelId="{c}"/>'
                           for q in pids for c in ('x', 'y', 'speed'))
        with tempfile.TemporaryDirectory() as d:
            meta, raw = Path(d) / 'm.xml', Path(d) / 'r.txt'
            meta.write_text('<main><FrameRate>25</FrameRate><FieldSize><Width>100</Width><Height>50</Height>'
                            '</FieldSize><Team id="h"/><Team id="a"/><Player id="p1" teamId="h"/>'
                            '<Player id="p2" teamId="a"/><Player id="p3" teamId="h"/><PlayerChannels>' +
                            channels + '</PlayerChannels><DataFormatSpecifications>' +
                            spec(1, 2, ['p2', 'p1']) + spec(3, 3, ['p3', 'p2']) +
                            '</DataFormatSpecifications></main>')
            raw.write_text('1:0.5,0.5,1;0.1,0.2,1:0.3,0.3\n2:0.5,0.6,1;0.1,0.3,1:NaN,NaN\n'
                           '3:0.9,0.9,2;0.4,0.4,2:0.2,0.2\n')
            m, info = data.read_epts(meta, raw)
            self.assertEqual(info['format_specifications'], 2)
            np.testing.assert_array_equal(m['team'], [0, 1, 0])
            np.testing.assert_allclose(m['players'][0], [[10, 10], [50, 25], [np.nan, np.nan]])
            np.testing.assert_allclose(m['players'][2], [[np.nan, np.nan], [40, 20], [90, 45]])
            np.testing.assert_allclose(m['ball'][2], [20, 10])
            self.assertTrue(np.isnan(m['ball'][1]).all())

    def test_read_epts_drops_slots_of_unknown_team_and_reads_names(self):
        with tempfile.TemporaryDirectory() as d:
            meta, raw = Path(d) / 'm.xml', Path(d) / 'r.txt'
            meta.write_text('<main><FrameRate>25</FrameRate><FieldSize><Width>100</Width><Height>50'
                            '</Height></FieldSize><Team id="h"><Name>Barcelona</Name></Team>'
                            '<Team id="a"><Name>Athletic Club</Name></Team><Player teamId="h"/>'
                            '<Player teamId="ref"/><Player teamId="a"/></main>')
            raw.write_text('1:0.2,0.4,1;0.5,0.5,1;0.7,0.6,1:0.21,0.31,1\n'
                           '2:0.2,0.4,1;0.5,0.5,1;0.7,0.6,1:NaN,NaN,NaN\n')
            m, info = data.read_epts(meta, raw)
            np.testing.assert_array_equal(m['team'], [0, 1])
            np.testing.assert_allclose(m['players'][0, 1], [70, 30], rtol=1e-6)
            self.assertEqual(info['team_names'], ['Barcelona', 'Athletic Club'])
            self.assertEqual((info['slots'], info['slots_without_team']), (3, 1))

    def test_home_index_uses_unique_name_match_else_first_team(self):
        from possession.run import home_index
        self.assertEqual(home_index(['Athletic Club', 'FC Barcelona'], 'barcelona')[0], 1)
        self.assertEqual(home_index(['FC Barcelona', 'Athletic Club'], 'barcelona')[0], 0)
        self.assertEqual(home_index(['Team A', 'Team B'], 'barcelona')[0], 0)
        self.assertEqual(home_index(['Barcelona', 'Barcelona B'], 'barcelona')[0], 0)
        self.assertEqual(home_index(['X', 'Y'], None)[0], 0)


@NEEDS
class FeatureTests(unittest.TestCase):
    def test_features_are_finite_layout_and_swap_mirrors_team_blocks(self):
        m, _ = synthetic_match()
        X, names = features.features(m)
        Xs, names_s = features.features(m, swap=True)
        self.assertEqual(names, names_s)
        self.assertEqual(X.shape, (len(m['ball']), len(names)))
        i, j = names.index('h_d'), names.index('k_d')
        np.testing.assert_array_equal(np.nan_to_num(X[:, i]), np.nan_to_num(Xs[:, j]))
        k = names.index('diff_d')
        np.testing.assert_allclose(np.nan_to_num(X[:, k]), -np.nan_to_num(Xs[:, k]), atol=1e-5)

    def test_no_leak_across_blocks(self):
        m, _ = synthetic_match()
        X, names = features.features(m)
        m2 = dict(m)
        m2['ball'] = m['ball'].copy()
        m2['ball'][900:] += 5.0  # change only the second block
        X2, _ = features.features(m2)
        np.testing.assert_array_equal(np.nan_to_num(X[:750]), np.nan_to_num(X2[:750]))

    def test_window_helpers(self):
        x = np.array([1., np.nan, 3., 4.])
        np.testing.assert_allclose(features.wmean(x, -1, 0), [1, 1, 3, 3.5])
        np.testing.assert_allclose(features.since(np.array([0, 1, 0, 0], bool), 1.0, 9), [9, 0, 1, 2])
        np.testing.assert_allclose(features.until(np.array([0, 1, 0, 0], bool), 1.0, 9), [1, 0, 9, 9])


@NEEDS
class DegradeTests(unittest.TestCase):
    def test_degrade_keeps_shape_and_removes_ball(self):
        m, lab = synthetic_match()
        rng = np.random.default_rng(1)
        p = sample_params(rng, {'ball_miss_alive': 0.4, 'team_flip_rate': 0.0})
        dm = degrade(m, lab, rng, p)
        self.assertEqual(dm['players'].shape[0], len(lab))
        self.assertGreater(np.isnan(dm['ball'][:, 0]).mean(), 0.1)


@NEEDS_SK
class TreeTests(unittest.TestCase):
    def test_numpy_trees_match_sklearn(self):
        from sklearn.ensemble import HistGradientBoostingClassifier
        rng = np.random.default_rng(0)
        X = rng.normal(size=(3000, 5)); X[rng.random(X.shape) < .2] = np.nan
        y = (np.nan_to_num(X[:, 0]) > 0).astype(int)
        c = HistGradientBoostingClassifier(max_iter=20, random_state=0).fit(X, y)
        np.testing.assert_allclose(trees.predict_proba(trees.export_hgb(c), X), c.predict_proba(X)[:, 1],
                                   atol=1e-12)


@NEEDS
class DecodeTests(unittest.TestCase):
    def test_viterbi_ignores_short_flicker_and_keeps_long_change(self):
        ph = np.r_[np.full(100, .9), np.full(3, .1), np.full(100, .9), np.full(100, .1)]
        st = decode.viterbi(decode.emissions(np.full(len(ph), .01), ph), 10, 50, 50)
        lab = decode.LETTERS[st]
        self.assertTrue((lab[:203] == 'H').all())
        self.assertTrue((lab[210:] == 'A').all())

    def test_dead_segment(self):
        pd_ = np.r_[np.full(100, .05), np.full(100, .95), np.full(100, .05)]
        st = decode.viterbi(decode.emissions(pd_, np.full(300, .8)), 10, 20, 20)
        self.assertTrue((decode.LETTERS[st][110:190] == 'D').all())
        self.assertTrue((decode.LETTERS[st][:90] == 'H').all())


@NEEDS_SK
class BundleTests(unittest.TestCase):
    def test_bundle_roundtrip_without_pickle(self):
        from sklearn.ensemble import HistGradientBoostingClassifier
        rng = np.random.default_rng(0)
        X = rng.normal(size=(500, 3)); y = (X[:, 0] > 0).astype(int)
        t = trees.export_hgb(HistGradientBoostingClassifier(max_iter=5).fit(X, y))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'b.npz'
            bundle.save(p, t, t, ['a', 'b', 'c'], {'switch': 1.0}, {'version': 'test'})
            b = bundle.load(p)
            self.assertEqual(b['feature_names'], ['a', 'b', 'c'])
            np.testing.assert_allclose(trees.predict_proba(b['dead'], X), trees.predict_proba(t, X))




@NEEDS_SK
class EndToEndTests(unittest.TestCase):
    def test_run_writes_valid_submission_from_synthetic_atd(self):
        from possession import run as runmod
        from possession import validate
        from sklearn.ensemble import HistGradientBoostingClassifier
        m, lab = synthetic_match(n=1200)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tac = root / 'bundle' / 'tactical'
            tac.mkdir(parents=True)
            players = m['players'] / m['pitch']
            ball = m['ball'] / m['pitch']
            meta = ('<main><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height>'
                    '</FieldSize><Team id="h"/><Team id="a"/>' +
                    ''.join(f'<Player teamId="{"ha"[t]}"/>' for t in m['team']) + '</main>')
            (tac / 'SYN_tactical_atd.xml').write_text(meta)
            lines = []
            for i in range(len(ball)):
                groups = ';'.join(f'{x:.5f},{y:.5f},1.0' for x, y in players[i])
                lines.append(f'{i + 1}:{groups}:{ball[i, 0]:.5f},{ball[i, 1]:.5f},2.0')
            (tac / 'SYN_tactical_atd.txt').write_text('\n'.join(lines) + '\n')
            X, names = features.features(m)
            y = (lab == 'D').astype(int)
            t = trees.export_hgb(HistGradientBoostingClassifier(max_iter=3).fit(np.nan_to_num(X), y))
            model = root / 'model.npz'
            bundle.save(model, t, t, names, {'switch': 5.0, 'out_cost': 5.0, 'in_cost': 5.0, 'bias_dead': 0.0},
                        {'version': 'synthetic-test'})
            out = root / 'out'
            rep = runmod.run(root / 'bundle', out, model, game='SYN', halves=[(1, 0, 599), (2, 600, 1199)])
            self.assertEqual(rep['rows'], len(ball))
            ok, info = validate.check(out / 'submission.csv', rows=len(ball))
            self.assertTrue(ok, info)
            self.assertEqual(info['label_counts']['X'], 0)
            self.assertTrue((out / 'run.json').exists())
            with self.assertRaises(FileExistsError):
                runmod.run(root / 'bundle', out, model, game='SYN', halves=[(1, 0, 599), (2, 600, 1199)])


@NEEDS_SK
class StackTests(unittest.TestCase):
    def test_stacked_bundle_runs_and_is_symmetric(self):
        from sklearn.ensemble import HistGradientBoostingClassifier
        from possession import pipeline, stack
        m, lab = synthetic_match(n=1200)
        X, names = features.features(m)
        y = (lab == 'D').astype(int)
        t1 = trees.export_hgb(HistGradientBoostingClassifier(max_iter=3).fit(np.nan_to_num(X), y))
        S, cols = stack.stack_features(np.full(len(lab), .3), np.full(len(lab), .6), m['period'])
        t2 = trees.export_hgb(HistGradientBoostingClassifier(max_iter=3).fit(np.nan_to_num(S), y))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'b.npz'
            bundle.save(p, t1, t1, names, {'switch': 5.0, 'out_cost': 5.0, 'in_cost': 5.0, 'bias_dead': 0.0},
                        {'version': 'stack-test'}, stack=(t2, t2, cols))
            b = bundle.load(p)
            self.assertIn('stack_dead', b)
            labels, pd_, ph = pipeline.predict_labels(m, b)
            self.assertEqual(len(labels), len(lab))
            self.assertTrue(set(np.unique(labels)) <= {'H', 'A', 'D'})

    def test_stack_features_swap_mirrors_team_columns(self):
        from possession import stack
        rng = np.random.default_rng(0)
        pd_, ph = rng.random(500), rng.random(500)
        period = np.ones(500, np.int8)
        S, cols = stack.stack_features(pd_, ph, period)
        Sw, _ = stack.stack_features(pd_, ph, period, swap=True)
        i = cols.index('lh')
        np.testing.assert_allclose(S[:, i], -Sw[:, i], atol=1e-9)
        j = cols.index('pd')
        np.testing.assert_allclose(S[:, j], Sw[:, j])


@NEEDS_SK
class SymmetryTests(unittest.TestCase):
    def test_swapping_teams_mirrors_probabilities_and_labels(self):
        from sklearn.ensemble import HistGradientBoostingClassifier
        from possession import pipeline
        m, lab = synthetic_match(n=1200)
        X, names = features.features(m)
        rng = np.random.default_rng(0)
        y = (rng.random(len(lab)) < 0.5).astype(int)
        t = trees.export_hgb(HistGradientBoostingClassifier(max_iter=5).fit(np.nan_to_num(X), y))
        b = {'dead': t, 'home': t, 'feature_names': names,
             'decoder': {'switch': 3.0, 'out_cost': 10.0, 'in_cost': 10.0, 'bias_dead': 0.0}}
        pd1, ph1 = pipeline.frame_probabilities(m, b)
        m2 = dict(m, team=(1 - m['team']).astype(np.int8))
        pd2, ph2 = pipeline.frame_probabilities(m2, b)
        np.testing.assert_allclose(pd1, pd2, atol=1e-6)
        np.testing.assert_allclose(ph1, 1 - ph2, atol=2e-6)


@NEEDS
class FreezeTests(unittest.TestCase):
    def test_run_refuses_changed_source(self):
        from possession import run as runmod
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'b.npz'
            t = {'feature': np.zeros(1, np.int32), 'threshold': np.zeros(1), 'left': np.zeros(1, np.int32),
                 'right': np.zeros(1, np.int32), 'leaf': np.ones(1, bool), 'value': np.zeros(1),
                 'nan_left': np.ones(1, bool), 'offsets': np.array([0, 1]), 'baseline': np.array(0.0)}
            bundle.save(p, t, t, [], {'switch': 1.0, 'out_cost': 1.0, 'in_cost': 1.0},
                        {'version': 'x', 'source_sha256': {'features.py': 'not-the-real-hash'}})
            with self.assertRaises(ValueError):
                runmod.run(Path(d) / 'nodata', Path(d) / 'out', p)

@NEEDS_SK
class HomeTeamTests(unittest.TestCase):
    def test_reordered_metadata_gives_identical_submission(self):
        from possession import run as runmod
        from sklearn.ensemble import HistGradientBoostingClassifier
        m, lab = synthetic_match(n=1200)
        X, names = features.features(m)
        Xs, _ = features.features(m, swap=True)
        yd = (lab == 'D').astype(int)
        alive = lab != 'D'
        XX = np.nan_to_num(np.r_[X[alive], Xs[alive]])
        yh = np.r_[(lab[alive] == 'H'), (lab[alive] == 'A')].astype(int)
        td = trees.export_hgb(HistGradientBoostingClassifier(max_iter=5).fit(np.nan_to_num(X), yd))
        th = trees.export_hgb(HistGradientBoostingClassifier(max_iter=5).fit(XX, yh))
        players, ball = m['players'] / m['pitch'], m['ball'] / m['pitch']
        lines = []
        for i in range(len(ball)):
            groups = ';'.join(f'{x:.5f},{y:.5f},1.0' for x, y in players[i])
            lines.append(f'{i + 1}:{groups}:{ball[i, 0]:.5f},{ball[i, 1]:.5f},2.0')
        teams = {'h': '<Team id="h"><Name>FC Barcelona</Name></Team>',
                 'a': '<Team id="a"><Name>Athletic Club</Name></Team>'}
        old = dict(runmod.ORGANISER_HOME)
        runmod.ORGANISER_HOME['SYN'] = 'barcelona'
        try:
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                model = root / 'model.npz'
                bundle.save(model, td, th, names, {'switch': 5.0, 'out_cost': 5.0, 'in_cost': 5.0,
                                                   'bias_dead': 0.0}, {'version': 'synthetic-test'})
                outs = []
                for order in ('ha', 'ah'):
                    tac = root / order / 'tactical'
                    tac.mkdir(parents=True)
                    (tac / 'SYN_tactical_atd.xml').write_text(
                        '<main><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height>'
                        '</FieldSize>' + teams[order[0]] + teams[order[1]] +
                        ''.join(f'<Player teamId="{"ha"[t]}"/>' for t in m['team']) + '</main>')
                    (tac / 'SYN_tactical_atd.txt').write_text('\n'.join(lines) + '\n')
                    rep = runmod.run(root / order, root / ('out_' + order), model, game='SYN',
                                     halves=[(1, 0, 599), (2, 600, 1199)])
                    self.assertEqual(rep['teams']['home'], 'FC Barcelona')
                    outs.append((root / ('out_' + order) / 'submission.csv').read_text())
                self.assertEqual(outs[0], outs[1])
                self.assertIn(',H', outs[0])
                self.assertIn(',A', outs[0])
        finally:
            runmod.ORGANISER_HOME.clear()
            runmod.ORGANISER_HOME.update(old)


@NEEDS_SK
class TrainTests(unittest.TestCase):
    def test_train_cli_with_stacking_builds_a_runnable_bundle(self):
        from possession import train
        from possession.pipeline import predict_labels
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for k, name in enumerate(('J03AAA', 'J03BBB')):
                m, lab = synthetic_match(n=1500, seed=k)
                fx = root / 'prepared' / name
                fx.mkdir(parents=True)
                np.savez(fx / 'inputs.npz', ball=np.nan_to_num(m['ball']), ball_observed=np.isfinite(m['ball']).all(1),
                         players=m['players'], player_detected=np.isfinite(m['players']).all(2),
                         fps=np.array(25.0), pitch=m['pitch'], teams=m['team'], period=m['period'])
                np.savez(fx / 'targets.npz', labels=lab)
            hp = {'max_iter': 5, 'learning_rate': 0.1, 'max_leaf_nodes': 7, 'min_samples_leaf': 5,
                  'l2_regularization': 0.0}
            cfg = {'version': 'synthetic-train', 'feature_version': features.FEATURE_VERSION,
                   'train_fixtures': ['J03AAA', 'J03BBB'], 'seeds': [1], 'step': 6, 'hyperparameters': hp,
                   'stack': {'hyperparameters': hp},
                   'decoder': {'switch': 5.0, 'out_cost': 5.0, 'in_cost': 5.0, 'bias_dead': 0.0}}
            (root / 'cfg.json').write_text(json.dumps(cfg))
            train.main(root / 'cfg.json', root / 'prepared', None, root / 'b.npz')
            b = bundle.load(root / 'b.npz')
            self.assertIn('stack_dead', b)
            self.assertEqual(b['card']['stack'], cfg['stack'])
            m, _ = synthetic_match(n=1500, seed=5)
            labels, pd_, ph = predict_labels(m, b)
            self.assertEqual(len(labels), 1500)
            self.assertTrue(set(np.unique(labels)) <= {'H', 'A', 'D'})


@NEEDS
class FrozenBundleTests(unittest.TestCase):
    """The committed bundle + current sources (hash-checked by run) on a synthetic ATD."""
    def test_frozen_bundle_runs_on_synthetic_atd(self):
        from possession import run as runmod
        from possession import validate
        if not runmod.DEFAULT_MODEL.exists():
            self.skipTest('models/possession-v2.npz not present')
        m, _ = synthetic_match(n=1500)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tac = root / 'bundle' / 'tactical'
            tac.mkdir(parents=True)
            players, ball = m['players'] / m['pitch'], m['ball'] / m['pitch']
            (tac / 'SYN_tactical_atd.xml').write_text(
                '<main><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height></FieldSize>'
                '<Team id="h"/><Team id="a"/>' +
                ''.join(f'<Player teamId="{"ha"[t]}"/>' for t in m['team']) + '</main>')
            lines = []
            for i in range(len(ball)):
                groups = ';'.join(f'{x:.5f},{y:.5f},1.0' for x, y in players[i])
                lines.append(f'{i + 1}:{groups}:{ball[i, 0]:.5f},{ball[i, 1]:.5f},2.0')
            (tac / 'SYN_tactical_atd.txt').write_text('\n'.join(lines) + '\n')
            rep = runmod.run(root / 'bundle', root / 'out', game='SYN', halves=[(1, 0, 749), (2, 750, 1499)])
            ok, info = validate.check(root / 'out' / 'submission.csv', rows=len(ball))
            self.assertTrue(ok, info)
            self.assertEqual(rep['model_version'], runmod.load_bundle(runmod.DEFAULT_MODEL)['card']['version'])


if __name__ == '__main__':
    unittest.main()
