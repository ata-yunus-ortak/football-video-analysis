"""Synthetic checks of the PASS/FAIL-only public-window check (possession/public_check.py); no match data."""
import io
import contextlib
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import public_check as pc
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def truth(n=4000, a=500, b=3500, seed=3):
    """X outside [a, b); inside, runs of H / A / D of 2-12 s."""
    rng = np.random.default_rng(seed)
    lab = np.full(n, 'X', dtype='<U1')
    t = a
    while t < b:
        k = int(rng.integers(50, 300))
        lab[t:min(b, t + k)] = 'HAD'[int(rng.integers(0, 3))]
        t += k
    return lab


def write(path, labels):
    Path(path).write_text('frame,label\n' + ''.join(f'{i},{v}\n' for i, v in enumerate(labels)), encoding='utf-8')
    return path


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class PublicCheckTests(unittest.TestCase):
    def test_correct_file_passes_and_the_verdict_is_stored_without_scores(self):
        with tempfile.TemporaryDirectory() as d:
            gt = write(Path(d) / 'gt.csv', truth())
            pred = truth(); pred[pred == 'X'] = 'D'
            sub = write(Path(d) / 'sub.csv', pred)
            res, stored = pc.check(sub, gt)
            self.assertEqual(res, {k: True for k in pc.CHECKS})
            self.assertFalse(stored)
            marker = Path(str(sub) + '.public_check.json').read_text()
            self.assertNotIn('f1', marker.replace('spell_f1_mean', '').replace('macro_f1', ''))   # thresholds only
            res2, stored2 = pc.check(sub, gt)
            self.assertTrue(stored2); self.assertEqual(res2, res)

    def test_exchanged_teams_fail_the_floor_and_the_exchange_check(self):
        with tempfile.TemporaryDirectory() as d:
            lab = truth()
            gt = write(Path(d) / 'gt.csv', lab)
            pred = lab.copy(); pred[lab == 'H'] = 'A'; pred[lab == 'A'] = 'H'; pred[lab == 'X'] = 'D'
            res, _ = pc.check(write(Path(d) / 'sub.csv', pred), gt)
            self.assertTrue(res['valid_submission'])
            self.assertFalse(res['above_broken_floor'])
            self.assertFalse(res['teams_not_exchanged'])

    def test_shifted_frames_fail_the_floor_but_not_the_exchange_check(self):
        with tempfile.TemporaryDirectory() as d:
            lab = truth()
            gt = write(Path(d) / 'gt.csv', lab)
            pred = np.roll(np.where(lab == 'X', 'D', lab), 400)      # 16 s late
            res, _ = pc.check(write(Path(d) / 'sub.csv', pred), gt)
            self.assertTrue(res['valid_submission'])
            self.assertFalse(res['above_broken_floor'])

    def test_invalid_file_fails_everything_and_changed_bytes_are_checked_again(self):
        with tempfile.TemporaryDirectory() as d:
            lab = truth()
            gt = write(Path(d) / 'gt.csv', lab)
            sub = write(Path(d) / 'sub.csv', np.where(lab == 'X', 'D', lab)[:-5])   # wrong row count
            res, _ = pc.check(sub, gt)
            self.assertEqual(res, {k: False for k in pc.CHECKS})
            write(sub, np.where(lab == 'X', 'D', lab))
            res, stored = pc.check(sub, gt)
            self.assertFalse(stored)
            self.assertTrue(all(res.values()))

    def test_command_line_prints_words_only(self):
        with tempfile.TemporaryDirectory() as d:
            lab = truth()
            gt = write(Path(d) / 'gt.csv', lab)
            sub = write(Path(d) / 'sub.csv', np.where(lab == 'X', 'D', lab))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = pc.main([str(sub), str(gt)])
            self.assertEqual(code, 0)
            text = out.getvalue()
            self.assertIn('PUBLIC CHECK OK', text)
            self.assertFalse(any(ch.isdigit() for ch in text))


if __name__ == '__main__':
    unittest.main()
