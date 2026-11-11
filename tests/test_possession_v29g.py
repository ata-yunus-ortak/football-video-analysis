"""Synthetic checks for the reserve entry point without the published kick-off frame (possession/run29g.py); no accuracy claims."""
import ast
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import run29, run29g
    from possession.run import ORGANISER_HALVES
    from tests.test_possession_v25 import bundle_with_broadcast
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def labels(path):
    return np.array([r.split(',')[1] for r in Path(path).read_text().splitlines()[1:]])


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class Run29gTests(unittest.TestCase):
    def test_manifest_and_play_blocks_without_the_kickoff_frame(self):
        self.assertEqual(run29g.check_release()['version'], 'possession-v2.9g')
        run29.check_release()
        graded = ORGANISER_HALVES[('BAR-ATH', run29g.N_FRAMES['BAR-ATH'])]
        self.assertEqual(graded, [(1, 11185, 90651), (2, 110808, 190197)])           # games.half_video_blocks("BAR-ATH")
        self.assertNotIn(113742, [v for h in graded for v in h])
        tree = ast.parse(Path(run29g.__file__).read_text(encoding='utf-8'))
        self.assertFalse(any(isinstance(n, ast.Constant) and n.value == 113742 for n in ast.walk(tree)))   # no kick-off constant in the code

    def test_same_file_as_run29_on_the_same_play_blocks_and_the_models_run_before_the_kickoff(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle_with_broadcast(root / 'b', n=9000, lag=0)
            shutil.rmtree(data / 'broadcast')
            windows = [(1, 0, 4199), (2, 4500, 8999)]            # "graded windows": the second starts 500 frames before a kick-off
            late = [(1, 0, 4199), (2, 5000, 8999)]               # play blocks that start at that kick-off
            g = run29g.run(data, root / 'g', game='SYN', halves=windows, release=None, base_release=None)
            a = run29.run(data, root / 'a', game='SYN', halves=windows, release=None)
            b = run29.run(data, root / 'b2', game='SYN', halves=late, release=None)
            self.assertEqual(g['submission_sha256'], a['submission_sha256'])
            rep = json.loads((root / 'g' / 'run.json').read_text())
            self.assertIn('v2.9g', rep['system'])
            self.assertEqual(rep['dead_leadin_frames'], [])
            self.assertIn('graded windows', rep['period_source'])
            lg, lb = labels(root / 'g' / 'submission.csv'), labels(root / 'b2' / 'submission.csv')
            self.assertTrue((lb[4200:5000] == 'D').all())        # with the late block the lead-in is written D
            self.assertTrue((lg[4200:4500] == 'D').all())        # outside the graded windows both write D
            self.assertTrue((lg[4500:5000] != 'D').any())        # here the models decide (the synthetic ball is in play)


if __name__ == '__main__':
    unittest.main()
