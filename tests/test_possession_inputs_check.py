"""Synthetic checks of the input self-check (possession/inputs_check.py); no match data."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import inputs_check as ic
    from tests.test_possession_reader_reference import write_like_provided
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def bundle(root, n=900, valid='1', invalid='0', missing='NaN,NaN,NaN'):
    """Synthetic bundle (stem SYN) and the facts a DATA.md for it would publish."""
    root = Path(root)
    _, _, t = write_like_provided(root / 'tactical', n=n, slots=46, seed=5, missing=missing)
    meta, raw, b = write_like_provided(root / 'broadcast', n=n - 100, slots=51, seed=6)
    for f in (meta, raw):
        f.rename(f.with_name(f.name.replace('SYN_tactical', 'SYN_broadcast')))
    rng = np.random.default_rng(1)
    ok = rng.random(n - 100) < 0.66
    rows = ['frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid']
    rows += [f'{i},1822.663,-511.2005,44.48168,1.698323,169.2971,255.7303,-0.01907188,-0.5269586,1,0.2910854,{valid}' if ok[i]
             else f'{i},NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,{invalid}' for i in range(n - 100)]
    (root / 'broadcast' / 'SYN_broadcast_homography.csv').write_text('\n'.join(rows) + '\n')
    windows = ((100, 399), (500, 849))
    graded = np.zeros(n, bool)
    for a, e in windows:
        graded[a:e + 1] = True
    seen = np.isfinite(t['ball']).all(1)
    pub = {'tactical_records': n, 'tactical_slots': 46, 'tactical_ball_frames': int(seen.sum()),
           'graded_ball_frames': int(seen[graded].sum()), 'graded_windows': windows,
           'mean_tracked_on_graded': round(float(np.isfinite(t['xy']).all(2).sum(1)[graded].mean()), 1),
           'broadcast_records': n - 100, 'broadcast_slots': 51,
           'broadcast_ball_share': round(float(np.isfinite(b['ball']).all(1).mean()), 3),
           'broadcast_homography_valid_share': round(float(ok.mean()), 3), 'home_name_contains': 'barcelona'}
    return root, pub


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class InputsCheckTests(unittest.TestCase):
    def test_files_that_match_their_description_pass_every_check(self):
        with tempfile.TemporaryDirectory() as d:
            root, pub = bundle(d)
            res = ic.check(root, game='SYN', pub=pub)
            self.assertEqual(res, {k: True for k in ic.CHECKS})

    def test_a_flag_the_reader_does_not_understand_is_reported_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            root, pub = bundle(d, valid='1.0', invalid='0.0')          # the frozen reader accepts 1 / True / true only
            res = ic.check(root, game='SYN', pub=pub)
            self.assertFalse(res['broadcast_homography_valid_share'])
            self.assertTrue(all(v for k, v in res.items() if k != 'broadcast_homography_valid_share'))

    def test_a_wrong_description_fails_only_the_fact_that_is_wrong_and_missing_broadcast_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root, pub = bundle(d)
            wrong = dict(pub, tactical_ball_frames=pub['tactical_ball_frames'] + 40, mean_tracked_on_graded=pub['mean_tracked_on_graded'] + 3,
                         home_name_contains='athletic')
            res = ic.check(root, game='SYN', pub=wrong)
            self.assertEqual(sorted(k for k, v in res.items() if v is False),
                             ['first_team_is_named_barcelona', 'tactical_ball_frames', 'tactical_tracked_objects'])
            for f in (root / 'broadcast').iterdir():
                f.unlink()
            res = ic.check(root, game='SYN', pub=pub)
            self.assertTrue(all(res[k] is None for k in ic.CHECKS if k.startswith('broadcast')))
            self.assertTrue(all(res[k] for k in ic.CHECKS if not k.startswith('broadcast')))

    def test_a_file_whose_groups_do_not_follow_the_player_list_is_reported(self):
        """The release's reader follows the DataFormatSpecification (as kloppy does); the organisers' starter code takes
        the i-th group as the i-th Player entry. If the two ever differ on the provided file, the check must say so."""
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as d:
            root, pub = bundle(d, missing='nan,nan,nan')                # lower-case missing values are read alike by both
            self.assertTrue(ic.check(root, game='SYN', pub=pub)['tactical_agrees_with_starter_reading'])
            meta = root / 'tactical' / 'SYN_tactical_atd.xml'
            tree = ET.parse(meta)
            players = tree.getroot().find('.//Players')
            entries = list(players)
            for e in entries:
                players.remove(e)
            for e in reversed(entries):                                 # same specification, Player list in another order
                players.append(e)
            tree.write(meta, encoding='utf-8', xml_declaration=True)
            details = {}
            res = ic.check(root, game='SYN', pub=pub, details=details)
            self.assertEqual([k for k, v in res.items() if v is False], ['tactical_agrees_with_starter_reading'])
            self.assertEqual(details, {'tactical_agrees_with_starter_reading': 'team_counts'})      # the aspect is named, no value

    def test_a_file_the_reader_cannot_read_is_described_by_syntax_facts_and_the_error_class(self):
        with tempfile.TemporaryDirectory() as d:
            root, pub = bundle(d)
            raw = root / 'tactical' / 'SYN_tactical_atd.txt'
            lines = raw.read_text().splitlines()
            lines[400] = lines[400].rsplit(':', 1)[0] + ':abc,0.5,1.0'           # a value that is not a number
            raw.write_text('\n'.join(lines) + '\n')
            details = {}
            res = ic.check(root, game='SYN', pub=pub, details=details)
            self.assertFalse(res['tactical_raw_values_are_numbers_or_nan'])
            self.assertTrue(res['tactical_raw_lines_have_three_parts'] and res['tactical_raw_groups_equal_player_entries'])
            self.assertFalse(res['tactical_raw_frame_ids_count_from_one'])       # the malformed line is not counted
            self.assertFalse(res['tactical_reader_runs'])
            self.assertEqual(details, {'tactical_reader_runs': 'ValueError'})
            self.assertIsNone(res['tactical_records'])                           # nothing after the reader was checked
            self.assertTrue(all(res[k] for k in ic.CHECKS if k.startswith('broadcast')))
            lines[400] = 'not a tracking line'
            lines.insert(0, 'frame:players:ball')                                # a header line and a line without parts
            raw.write_text('\n'.join(lines) + '\n')
            res = ic.check(root, game='SYN', pub=pub)
            self.assertFalse(res['tactical_raw_lines_have_three_parts'])
            self.assertFalse(res['tactical_raw_groups_equal_player_entries'])    # the header has one group
            self.assertFalse(res['tactical_reader_runs'])

    def test_command_line_prints_names_and_words_only(self):
        with tempfile.TemporaryDirectory() as d:
            root, _ = bundle(d)
            for f in list((root / 'tactical').iterdir()) + list((root / 'broadcast').iterdir()):
                f.rename(f.with_name(f.name.replace('SYN_', 'BAR-ATH_')))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = ic.main(['--data-dir', str(root)])
            text = out.getvalue()
            self.assertEqual(code, 2)                                   # a 900-frame file is not the provided match
            self.assertIn('FAIL tactical_records', text)
            self.assertIn('PASS tactical_slots', text)
            self.assertIn('INPUTS DIFFER FROM DATA.md', text)
            self.assertFalse(any(ch.isdigit() for ch in text.replace('DATA.md', '')))


if __name__ == '__main__':
    unittest.main()
