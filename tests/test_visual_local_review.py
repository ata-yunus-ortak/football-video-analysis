import copy
from pathlib import Path
import tempfile
import unittest

from tools.visual_local_review import assumption_context, player_window, run


class LocalIntegratedReviewTests(unittest.TestCase):
    def test_explicit_local_review_required_before_any_source_access(self):
        with self.assertRaises(ValueError): run('unused','unused','unused','unused','unused')

    def test_assumptions_are_separate_and_never_mutate_strict_evidence(self):
        context={'alignment_validated':False,'clock_error_bound_s':.4,
                 'calibration_validated':False,'frame_kind':'unknown',
                 'normalized_pitch_to_image':[[1,0,0],[0,1,0],[0,0,1]]}
        original=copy.deepcopy(context)
        preview=assumption_context(context)
        self.assertEqual(context,original)
        self.assertTrue(preview['alignment_validated'])
        self.assertFalse(context['alignment_validated'])
        self.assertEqual(context['clock_error_bound_s'],.4)

    def test_player_window_ignores_ball_and_uses_metadata_team(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);meta=root/'meta.xml';raw=root/'tracking.txt'
            meta.write_text('<Root><FieldSize><Width>105</Width><Height>68</Height></FieldSize><Teams><Team id="home"/><Team id="away"/></Teams><Players><Player id="1" teamId="home"><Name>One</Name><ShirtNumber>10</ShirtNumber></Player><Player id="2" teamId="away"><Name>Two</Name><ShirtNumber>9</ShirtNumber></Player></Players></Root>')
            raw.write_text('1:0.1,0.2,0;0.4,0.5,0:NOT_A_NUMERIC_BALL\n2:0.2,0.2,0;NaN,NaN,0:DO_NOT_PARSE\n')
            rows,display,pitch=player_window({'meta':str(meta),'tracking':str(raw),'video':'local-video'}, {0,1})
            self.assertEqual(len(rows[0]),2);self.assertEqual(len(rows[1]),1)
            self.assertEqual([r['team'] for r in rows[0]],['H','A'])
            self.assertEqual(pitch,[105,68]);self.assertIn('H #10',display.values())
