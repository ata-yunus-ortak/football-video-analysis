import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from tools.sportec_prepare import convert, run


META = '''<Root><MatchInformation><General MatchId="DFL-MAT-SYNTHETIC"/>
<Environment PitchX="100" PitchY="60"/><Teams>
<Team Role="home"><Players><Player PersonId="h"/></Players></Team>
<Team Role="guest"><Players><Player PersonId="a"/></Players></Team>
</Teams></MatchInformation></Root>'''


def tracking(status='0', duplicate=False):
    frames = '<Frame N="10" X="0" Y="0" BallStatus="'+status+'" BallPossession="1"/>'
    if duplicate: frames += frames
    return '''<Root><FrameSet GameSection="firstHalf" MatchId="DFL-MAT-SYNTHETIC" TeamId="BALL">'''+frames+'''
<Frame N="12" X="1" Y="2" BallStatus="1" BallPossession="2"/>
<Frame N="13" X="2" Y="2"/>
</FrameSet><FrameSet GameSection="firstHalf" MatchId="DFL-MAT-SYNTHETIC" TeamId="HOME" PersonId="h">
<Frame N="10" X="1" Y="0"/><Frame N="12" X="2" Y="0"/>
</FrameSet><FrameSet GameSection="firstHalf" MatchId="DFL-MAT-SYNTHETIC" TeamId="REF" PersonId="referee">
<Frame N="10" X="1" Y="1"/>
</FrameSet></Root>'''


class SportecPrepareTests(unittest.TestCase):
    def prepare(self, root, text, name):
        (root/'meta.xml').write_text(META)
        (root/'tracking.xml').write_text(text)
        report = convert(root/'meta.xml', root/'tracking.xml', root/name, 'DFL-MAT-SYNTHETIC')
        with np.load(root/name/'inputs.npz', allow_pickle=False) as z: x = {k:z[k] for k in z.files}
        with np.load(root/name/'targets.npz', allow_pickle=False) as z: y = z['labels']
        return report, x, y

    def test_targets_separate_and_missing_state_not_dead(self):
        with tempfile.TemporaryDirectory() as tmp:
            r, x, y = self.prepare(Path(tmp), tracking(), 'out')
            self.assertEqual(y.tolist(), ['D', 'A', 'X'])
            self.assertEqual(x['ball'][0].tolist(), [50., 30.])
            self.assertEqual(x['players'].shape, (3, 2, 2))
            self.assertEqual(r['dead_frames_with_finite_ball'], 1)
            self.assertEqual(r['native_discontinuities'], 1)
            self.assertEqual(x['ball_pair_valid'].tolist(), [False, False, True])
            self.assertFalse({'BallStatus','BallPossession','labels'} & set(x))

    def test_changing_target_never_changes_feature_arrays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, a, ya = self.prepare(root, tracking('0'), 'a')
            _, b, yb = self.prepare(root, tracking('1'), 'b')
            self.assertNotEqual(ya[0], yb[0])
            for key in a:
                np.testing.assert_array_equal(a[key], b[key])

    def test_duplicate_and_wrong_match_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                self.prepare(Path(tmp), tracking(duplicate=True), 'out')
            with self.assertRaisesRegex(ValueError, 'Wrong match'):
                self.prepare(Path(tmp), tracking().replace('DFL-MAT-SYNTHETIC', 'DIFFERENT'), 'out2')

    def test_reserved_test_refused_before_file_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = {'provided_fixture_used':False, 'repository':'https://huggingface.co/datasets/pysport/idsse-data',
                 'files':[{'fixture_id':'reserved','split':'reserved_test'}]*2}
            (root/'plan.json').write_text(json.dumps(p))
            with self.assertRaisesRegex(ValueError, 'reserved test'):
                run(root/'plan.json', root/'absent', 'reserved', root/'out')


if __name__ == '__main__': unittest.main()
