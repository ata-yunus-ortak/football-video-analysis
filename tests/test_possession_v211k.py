"""Synthetic checks for possession/run211k.py (v2.11g + Smart Tagging kick-off rule); no accuracy claims."""
import ast
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import run211g, run211k, kickoff
    from tests.test_possession_v25 import bundle_with_broadcast
    from tests.test_possession_kickoff import tagging, kick
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

WINDOWS = [(1, 0, 4199), (2, 4500, 8999)]            # "graded windows": the second starts before a kick-off


def labels(path):
    return np.array([r.split(',')[1] for r in Path(path).read_text().splitlines()[1:]])


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class Run211kTests(unittest.TestCase):
    def test_manifest_and_no_frame_constant(self):
        self.assertEqual(run211k.check_release()['version'], 'possession-v2.11k')
        for mod in (run211k, kickoff):
            tree = ast.parse(Path(mod.__file__).read_text(encoding='utf-8'))
            numbers = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                       and not isinstance(n.value, bool)]
            self.assertTrue(all(abs(v) < 1000 for v in numbers), numbers)        # no frame number of any match in the code

    def test_tag_rule_on_a_synthetic_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle_with_broadcast(root / 'b', n=9000, lag=0)
            shutil.rmtree(data / 'broadcast')
            fps = run211k.frame_rate(data / 'tactical' / 'SYN_tactical_atd.xml')
            kw = dict(game='SYN', halves=WINDOWS, release=None, base_release=None)
            g = run211g.run(data, root / 'g', **kw)
            lg = labels(root / 'g' / 'submission.csv')
            self.assertTrue((lg[4500:5000] != 'D').any())                       # the models label play before the "kick-off"
            # 1. no Smart Tagging file: the bytes of v2.11g
            k0 = run211k.run(data, root / 'k0', v211_release=None, **kw)
            self.assertEqual((root / 'k0' / 'submission.csv').read_bytes(), (root / 'g' / 'submission.csv').read_bytes())
            self.assertEqual(k0['submission_sha256'], g['submission_sha256'])
            self.assertIn('no smart tagging file', k0['kickoff_rule']['status'])
            self.assertIn('v2.11k', k0['system'])
            # 2. a kick-off tag 500 frames into the second window, one before the first window and other tags
            tag_file = data / 'tactical' / 'SYN_tactical_smart_tagging.xml'
            tag_file.write_text(tagging([kick(5000 / fps), kick(0.0), kick(6000 / fps, text='Free Kick'),
                                         (7000 / fps, 7100 / fps, 'BUILD UP', [('Team', 'Home')])]), encoding='utf-8')
            k1 = run211k.run(data, root / 'k1', v211_release=None, **kw)
            lk = labels(root / 'k1' / 'submission.csv')
            self.assertTrue((lk[4500:5000] == 'D').all())
            keep = np.r_[0:4500, 5000:9000]
            self.assertTrue(np.array_equal(lk[keep], lg[keep]))                  # nothing else changes
            rep = json.loads((root / 'k1' / 'run.json').read_text())
            self.assertEqual(rep['kickoff_rule']['used_in_block'], [True, True])  # first window: tag at its first frame, nothing to change
            self.assertEqual(rep['kickoff_rule']['frames_changed_in_block'], [0, int(np.sum(lg[4500:5000] != 'D'))])
            self.assertEqual(rep['submission_sha256'], k1['submission_sha256'])
            self.assertNotEqual(k1['submission_sha256'], g['submission_sha256'])
            self.assertEqual(rep['label_counts_in_play_blocks'],
                             {c: int(np.sum(np.r_[lk[0:4200], lk[4500:9000]] == c)) for c in 'HADX'})
            self.assertNotIn('smart tagging', rep['not_used'])
            self.assertEqual(len(lk), 9000)
            # 3. an unreadable file: the bytes of v2.11g again
            tag_file.write_text('<file><instance>', encoding='utf-8')
            k2 = run211k.run(data, root / 'k2', v211_release=None, **kw)
            self.assertEqual((root / 'k2' / 'submission.csv').read_bytes(), (root / 'g' / 'submission.csv').read_bytes())
            self.assertIn('unreadable', k2['kickoff_rule']['status'])


if __name__ == '__main__':
    unittest.main()
