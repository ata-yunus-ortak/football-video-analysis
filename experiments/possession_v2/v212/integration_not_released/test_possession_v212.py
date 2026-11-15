"""Synthetic checks of the possession v2.12 wiring (possession/pipeline212.py, possession/run212.py).

No match data and no accuracy claims. The checks are about the wiring: the stage-1 input is the 227 base columns
followed by the touch columns in the bundle's order; the touch columns read the goalkeeper-corrected tactical
tracking BEFORE the broadcast fill, while the base columns see the filled ball; inputs that do not belong together
are refused; on the v2.3 path (noisy input) the file is the possession.run211 file.
A tiny hand-made bundle stands in for the trained v2.12 models so that these tests need no scikit-learn.
"""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import numpy as np
try:
    from possession import pipeline212, run211, run212
    from possession import bundle as bundle_io
    from possession.features import features
    from possession.touch import touch_features
    from possession.trees import FIELDS
    from tests.test_possession_crossplatform import bundle, HALVES
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def one_split(index, threshold, low, high):
    """A single tree: column `index` <= threshold -> low, else high (NaN goes high)."""
    m = {'feature': np.array([index, 0, 0], np.int32), 'threshold': np.array([threshold, 0.0, 0.0]),
         'left': np.array([1, 0, 0], np.int32), 'right': np.array([2, 0, 0], np.int32),
         'leaf': np.array([False, True, True]), 'value': np.array([0.0, low, high]),
         'nan_left': np.array([False, False, False])}
    m['offsets'] = np.array([0, 3], np.int64)
    m['baseline'] = np.array(0.0)
    assert set(m) == set(FIELDS) | {'offsets', 'baseline'}
    return m


def tiny_bundle(path, names):
    """Stage 1 splits on a touch column (h_tc_last) and a base column; no second stage; the frozen decoder costs."""
    t = names.index('h_tc_last')
    dead = one_split(names.index(names[0]), 1e9, -3.0, -3.0)                 # P(dead) ~ 0.05 everywhere
    home = one_split(t, 0.5, -1.0, 1.0)                                       # home more likely after a home touch
    bundle_io.save(path, dead, home, names, {'switch': 3.0, 'out_cost': 60.0, 'in_cost': 60.0, 'bias_dead': -0.3},
                   {'version': 'synthetic-v2.12-test'})
    return path


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.root = Path(self.d.name)
        from possession.data import read_epts
        data = bundle(self.root / 'syn')
        m, _ = read_epts(data / 'tactical' / 'SYN_tactical_atd.xml', data / 'tactical' / 'SYN_tactical_atd.txt')
        period = np.zeros(len(m['ball']), np.int8)
        for h, a, b in HALVES:
            period[a:b + 1] = h
        m['period'] = period
        self.m = m
        names = features(m)[1] + touch_features(m)[1]
        self.names = names
        self.b = bundle_io.load(tiny_bundle(self.root / 'tiny.npz', names))

    def tearDown(self):
        self.d.cleanup()

    def test_stage1_columns_are_base_then_touch(self):
        self.assertEqual(len(self.names), 227 + 36)
        self.assertEqual(self.names[:227], features(self.m)[1])
        self.assertTrue(all(n.startswith(('tc_', 'h_tc_', 'k_tc_', 'diff_tc_')) for n in self.names[227:]))
        pd_, ph = pipeline212.frame_probabilities(self.m, self.m, self.b)
        ok = self.m['period'] > 0
        self.assertTrue(np.all(pd_[~ok] == 0.5) and np.all(ph[~ok] == 0.5))
        T, tn = touch_features(self.m)
        Ts, _ = touch_features(self.m, swap=True)
        j = tn.index('h_tc_last')
        s = lambda x: np.where(np.isnan(x) | (x > 0.5), 1.0, -1.0)
        expect = 0.5 * (1 / (1 + np.exp(-s(T[:, j]))) + 1 - 1 / (1 + np.exp(-s(Ts[:, j]))))
        self.assertTrue(np.allclose(ph[ok], np.round(expect[ok], 6)))

    def test_inputs_that_do_not_belong_together_are_refused(self):
        other = dict(self.m, period=np.zeros_like(self.m['period']))
        with self.assertRaises(ValueError):
            pipeline212.frame_probabilities(self.m, other, self.b)
        flipped = dict(self.m, team=(1 - self.m['team']).astype(np.int8))
        with self.assertRaises(ValueError):
            pipeline212.frame_probabilities(self.m, flipped, self.b)
        shorter = dict(self.b, feature_names=self.names[:-1])
        with self.assertRaises(ValueError):
            pipeline212.frame_probabilities(self.m, self.m, shorter)


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class EntryPointTests(unittest.TestCase):
    def test_touch_columns_read_the_tactical_ball_before_the_fill(self):
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            root = Path(d)
            data = bundle(root / 'syn')
            from possession.data import read_epts
            m, _ = read_epts(data / 'tactical' / 'SYN_tactical_atd.xml', data / 'tactical' / 'SYN_tactical_atd.txt')
            names = features(dict(m, period=np.ones(len(m['ball']), np.int8)))[1] + touch_features(dict(m, period=np.ones(len(m['ball']), np.int8)))[1]
            tiny = tiny_bundle(root / 'tiny.npz', names)
            seen = {'touch': [], 'base': []}
            real_touch, real_base = pipeline212.touch_features, pipeline212.features

            def spy_touch(match, swap=False):
                seen['touch'].append(np.array(match['ball']))
                return real_touch(match, swap=swap)

            def spy_base(match, swap=False):
                seen['base'].append(np.array(match['ball']))
                return real_base(match, swap=swap)
            with mock.patch.object(pipeline212, 'touch_features', side_effect=spy_touch), \
                    mock.patch.object(pipeline212, 'features', side_effect=spy_base):
                rep = run212.run(data, root / 'out', game='SYN', halves=HALVES, v212_model=tiny, release=None,
                                 tactical_clock=data / 'clock-tactical', broadcast_clock=data / 'clock-broadcast')
            self.assertEqual(rep['path'], 'v2.1')
            self.assertTrue(rep['broadcast_fill_used'])                       # the fill is exercised
            tac = np.array(m['ball'])
            self.assertEqual(len(seen['touch']), 2)
            for b in seen['touch']:                                            # the tactical ball as given, gaps included
                self.assertTrue(np.array_equal(np.isnan(b), np.isnan(tac)))
                self.assertTrue(np.array_equal(b[~np.isnan(b)], tac[~np.isnan(tac)]))
            for b in seen['base']:                                             # the base columns see the filled ball
                self.assertLess(int(np.isnan(b).any(1).sum()), int(np.isnan(tac).any(1).sum()))
            out = (root / 'out' / 'submission.csv').read_text().splitlines()
            self.assertEqual(out[0], 'frame,label')
            self.assertEqual(len(out) - 1, rep['rows'])
            self.assertIn('touch columns', rep['system'])

    def test_noisy_input_takes_the_v23_path_and_gives_the_v211_file(self):
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            root = Path(d)
            data = bundle(root / 'noisy', player_noise=0.45)
            shutil.rmtree(data / 'broadcast')
            from possession.data import read_epts
            m, _ = read_epts(data / 'tactical' / 'SYN_tactical_atd.xml', data / 'tactical' / 'SYN_tactical_atd.txt')
            one = dict(m, period=np.ones(len(m['ball']), np.int8))
            tiny = tiny_bundle(root / 'tiny.npz', features(one)[1] + touch_features(one)[1])
            ref = run211.run(data, root / 'out211', game='SYN', halves=HALVES, release=None)
            with mock.patch.object(pipeline212, 'touch_features', side_effect=AssertionError('touch columns on the v2.3 path')):
                rep = run212.run(data, root / 'out212', game='SYN', halves=HALVES, v212_model=tiny, release=None)
            self.assertEqual(rep['path'], 'v2.3')
            self.assertEqual(rep['submission_sha256'], ref['submission_sha256'])
            self.assertEqual(rep['touch_columns'], 'not used (v2.3 path)')

    def test_release_check_names_every_v212_source(self):
        for name in ('touch.py', 'pipeline212.py', 'train212.py', 'run212.py', 'keeper2.py', 'run211.py', 'features.py'):
            self.assertIn(name, run212.SOURCES)


if __name__ == '__main__':
    unittest.main()
