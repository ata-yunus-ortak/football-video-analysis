"""Synthetic checks for the player-based registration of the broadcast ball (possession/register.py); no accuracy claims."""
import unittest
import numpy as np
from possession.register import frame_offsets, register_ball, MIN_MATCHES


def scene(n=400, s=12, seed=0):
    rng = np.random.default_rng(seed)
    P = np.array([52.0, 34.0]) + rng.uniform(-20, 20, (1, s, 2)) + np.cumsum(rng.normal(0, 0.05, (n, s, 2)), 0)
    team = np.r_[np.zeros(s // 2), np.ones(s - s // 2)].astype(np.int8)
    ball = P[:, 0] + 0.5
    return P, team, ball


class RegisterTests(unittest.TestCase):
    def test_constant_shift_is_measured_and_removed(self):
        P, team, ball = scene()
        shift = np.array([0.8, -0.5])
        bro = {'players': P + shift, 'team': team, 'ball': ball + shift}
        tac = {'players': P, 'team': team}
        t = np.arange(len(P))
        off = frame_offsets(bro['players'], team, bro['ball'], P, team, t)
        self.assertTrue(np.allclose(off, shift, atol=1e-9))
        out, rep = register_ball(bro, tac, t, 25.0)
        self.assertLess(np.nanmax(np.abs(out - ball)), 0.2)    # only the +-2 frame smoothing of a jittery ball remains
        self.assertAlmostEqual(rep['median_offset_m'], float(np.linalg.norm(shift)), places=3)

    def test_unaccepted_frames_and_frames_without_enough_players_get_no_ball(self):
        P, team, ball = scene()
        bp = P + 0.3
        bp[100:200, MIN_MATCHES - 1:] = np.nan            # too few players visible
        t = np.arange(len(P)); t[300:] = -1
        out, _ = register_ball({'players': bp, 'team': team, 'ball': ball + 0.3}, {'players': P, 'team': team}, t, 25.0)
        self.assertTrue(np.isnan(out[320:]).all())
        self.assertTrue(np.isnan(out[120:180]).all())
        self.assertTrue(np.isfinite(out[:80]).all())

    def test_a_wrong_match_is_trimmed(self):
        P, team, ball = scene()
        bp = P + 0.4
        bp[:, 3] += 2.5                                    # one player badly placed by the broadcast tracking
        off = frame_offsets(bp, team, ball + 0.4, P, team, np.arange(len(P)))
        self.assertLess(np.nanmax(np.abs(off - 0.4)), 1e-6)

    def test_missing_broadcast_ball_stays_missing(self):
        P, team, ball = scene()
        b = ball + 0.2; b[50:60] = np.nan
        out, _ = register_ball({'players': P + 0.2, 'team': team, 'ball': b}, {'players': P, 'team': team}, np.arange(len(P)), 25.0)
        self.assertTrue(np.isnan(out[50:60]).all())


try:
    from possession import run25, run29
    from tests.test_possession_v25 import bundle_with_broadcast
    HAVE_RUN = True
except ImportError:
    HAVE_RUN = False


@unittest.skipUnless(HAVE_RUN, 'possession dependencies not installed')
class Run29Tests(unittest.TestCase):
    def test_published_kickoff_constants(self):
        self.assertEqual(run29.ORGANISER_PLAY_HALVES[('BAR-ATH', 199319)], [(1, 11185, 90651), (2, 113742, 190197)])
        self.assertEqual(run29.ORGANISER_DEAD_LEADIN[('BAR-ATH', 199319)], [(110808, 113741)])

    def test_run29_without_broadcast_equals_run25_and_with_broadcast_reports_the_registration(self):
        import shutil, tempfile
        from pathlib import Path
        from possession import validate
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle_with_broadcast(root / 'b', n=9000, lag=0)
            halves = [(1, 0, 4499), (2, 4500, 8999)]
            r = run29.run(data, root / 'o29', game='SYN', halves=halves, release=None)
            self.assertTrue(r['broadcast_fill_used'])
            self.assertIn('registration', r['fusion'])
            self.assertLess(r['fusion']['registration']['median_offset_m'], 0.05)   # identical cameras: nothing to correct
            ok, info = validate.check(root / 'o29' / 'submission.csv', rows=9000)
            self.assertTrue(ok, info)
            shutil.rmtree(data / 'broadcast')
            a = run29.run(data, root / 'a', game='SYN', halves=halves, release=None)
            b = run25.run(data, root / 'b2', game='SYN', halves=halves, release=None)
            self.assertEqual(a['submission_sha256'], b['submission_sha256'])


if __name__ == '__main__':
    unittest.main()
