"""Synthetic checks for possession v2.5c (published second-half kick-off); no accuracy claims."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import run25, run25c
    from tests.test_possession_v25 import bundle_with_broadcast
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')


def labels(path):
    return np.array([r.split(',')[1] for r in Path(path).read_text().splitlines()[1:]])


@NEEDS
class Run25cTests(unittest.TestCase):
    def test_published_constants_and_frozen_manifest(self):
        h = run25c.ORGANISER_PLAY_HALVES[('BAR-ATH', 199319)]
        self.assertEqual(h, [(1, 11185, 90651), (2, 113742, 190197)])
        self.assertEqual(run25c.ORGANISER_DEAD_LEADIN[('BAR-ATH', 199319)], [(110808, 113741)])
        self.assertEqual(113742 - 110808, 2934)
        rel = run25c.check_release()
        self.assertEqual(rel['version'], 'possession-v2.5c')
        run25.check_release()

    def test_leadin_is_dead_and_the_rest_equals_a_run_that_starts_at_the_kickoff(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle_with_broadcast(root / 'b', n=9000, lag=0)
            shutil.rmtree(data / 'broadcast')
            late = [(1, 0, 4199), (2, 5000, 8999)]
            a = run25c.run(data, root / 'a', game='SYN', halves=late, leadin=[(4500, 4999)], release=None, base_release=None)
            b = run25.run(data, root / 'b2', game='SYN', halves=late, release=None)
            self.assertEqual(a['submission_sha256'], b['submission_sha256'])
            la = labels(root / 'a' / 'submission.csv')
            self.assertTrue((la[4200:5000] == 'D').all())
            rep = json.loads((root / 'a' / 'run.json').read_text())
            self.assertEqual(rep['dead_leadin_frames'], [[4500, 4999]])
            self.assertIn('v2.5c', rep['system'])


if __name__ == '__main__':
    unittest.main()
