"""Synthetic checks for possession v2.16 (possession/playerfill.py, possession/run216.py); no accuracy claims."""
import ast
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import run215, run216, playerfill
    from tests.test_possession_crossplatform import bundle, HALVES
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def scene(T=600, seed=3):
    """Eight players (four per team) that drift slowly, far apart; the ball next to player 1."""
    rng = np.random.default_rng(seed)
    start = np.array([[15, 12], [35, 20], [55, 30], [75, 44], [20, 50], [42, 58], [62, 10], [88, 26]], float)
    truth = start + np.cumsum(rng.normal(0, 0.02, (T, 8, 2)), 0)
    team = np.array([0, 0, 0, 0, 1, 1, 1, 1], np.int8)
    return truth, team, truth[:, 1] + 0.5


class FillTests(unittest.TestCase):
    """possession/playerfill.py needs numpy only."""

    def setUp(self):
        from possession import playerfill as f
        self.f = f
        self.truth, self.team, self.ball = scene()
        self.T = len(self.truth)
        self.offset = np.array([0.4, -0.3])                        # calibration error of the second camera

    def tracks(self, lost=(0, 100, 200)):
        tac = self.truth.astype(np.float32).copy()
        j, a, b = lost
        tac[a:b, j] = np.nan
        return ({'players': tac, 'team': self.team, 'ball': self.ball.copy()},
                {'players': self.truth + self.offset, 'team': self.team.copy(), 'ball': self.ball + self.offset})

    def test_constant_is_fixed(self):
        self.assertEqual(self.f.EMPTY_R_M, 1.5)

    def test_a_lost_player_is_added_and_tactical_positions_stay(self):
        tac, bro = self.tracks()
        p, t, rep = self.f.fill_players(tac, bro, np.arange(self.T), 25.0)
        self.assertEqual(p.shape, (self.T, 16, 2))
        self.assertTrue(np.array_equal(p[:, :8], tac['players'], equal_nan=True))          # nothing tactical is moved or removed
        self.assertEqual(p.dtype, tac['players'].dtype)
        self.assertTrue(np.array_equal(t, np.r_[self.team, self.team]))
        extra = np.isfinite(p[:, 8:]).all(2)
        self.assertTrue(extra[100:200, 0].all())                                           # the lost player, in the slot of its broadcast track
        self.assertFalse(extra[:100].any() or extra[200:].any() or extra[:, 1:].any())     # and nothing else
        self.assertLess(float(np.abs(p[100:200, 8] - self.truth[100:200, 0]).max()), 0.05) # at its place: the calibration error is removed
        self.assertEqual((rep['player_positions_added'], rep['frames_with_an_added_player'], rep['extra_slots'], rep['extra_slots_used']), (100, 100, 8, 1))

    def test_nothing_is_added_next_to_a_tactical_player_of_either_team(self):
        tac, bro = self.tracks(lost=(0, 0, 0))                     # the tactical tracking has every player
        bro['team'][2] = 1                                         # the second camera has one of them under the other team
        p, t, rep = self.f.fill_players(tac, bro, np.arange(self.T), 25.0)
        self.assertEqual(rep['player_positions_added'], 0)
        self.assertFalse(np.isfinite(p[:, 8:]).any())

    def test_frames_without_an_accepted_broadcast_frame_get_nothing(self):
        tac, bro = self.tracks()
        t_of_b = np.arange(self.T)
        t_of_b[120:160] = -1
        p, t, rep = self.f.fill_players(tac, bro, t_of_b, 25.0)
        extra = np.isfinite(p[:, 8:]).all(2)
        self.assertFalse(extra[120:160].any())
        self.assertTrue(extra[100:120, 0].all() and extra[160:200, 0].all())

    def test_the_broadcast_frame_is_written_to_its_tactical_frame(self):
        tac, bro = self.tracks()
        lag = 40                                                   # broadcast frame b shows tactical frame b + lag
        bro = {'players': bro['players'][lag:], 'team': bro['team'], 'ball': bro['ball'][lag:]}
        p, t, rep = self.f.fill_players(tac, bro, np.arange(self.T - lag) + lag, 25.0)
        extra = np.isfinite(p[:, 8:]).all(2)
        self.assertTrue(extra[100:200, 0].all() and not extra[:100].any() and not extra[200:].any())
        self.assertLess(float(np.abs(p[100:200, 8] - self.truth[100:200, 0]).max()), 0.05)

    def test_without_three_common_players_there_is_no_offset_and_nothing_is_added(self):
        tac, bro = self.tracks()
        bro['players'][:, 3:] = np.nan                             # the second camera sees players 0, 1, 2; player 0 is lost: two in common
        p, t, rep = self.f.fill_players(tac, bro, np.arange(self.T), 25.0)
        self.assertFalse(np.isfinite(p[113:187, 8:]).any())        # the offset of a frame is a median over half a second on either side
        self.assertTrue(np.isfinite(p[100:105, 8]).all())          # so only the first and last half second of the stretch have one


def labels(path):
    return np.array([r.split(',')[1] for r in Path(path).read_text().splitlines()[1:]])


def quiet(entry, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return entry.run(*a, **kw)


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class Run216Tests(unittest.TestCase):
    def test_manifest_and_no_frame_constant(self):
        rel = run216.check_release()
        self.assertEqual(rel['version'], 'possession-v2.16')
        self.assertEqual(run216.SOURCES, run215.SOURCES + ('playerfill.py', 'run216.py'))
        v215 = json.loads(run215.RELEASE.read_text(encoding='utf-8'))
        self.assertEqual({k: rel['source_sha256'][k] for k in v215['source_sha256']}, v215['source_sha256'])      # no v2.15 file changed
        self.assertEqual(rel['bundle_sha256'], v215['bundle_sha256'])
        for mod in (run216, playerfill):
            tree = ast.parse(Path(mod.__file__).read_text(encoding='utf-8'))
            numbers = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                       and not isinstance(n.value, bool)]
            self.assertTrue(all(abs(v) <= 2000 for v in numbers), numbers)       # no frame number of any match in the code

    def test_players_are_added_behind_the_open_gate_and_everything_else_is_v215(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle(root / 'lost', lost=True)
            kw = dict(game='SYN', halves=HALVES, release=None)
            old = quiet(run215, data, root / 'v215', **kw)
            # 1. the step switched off: the bytes of v2.15 (every other line of run216 is the v2.15 flow)
            off = quiet(run216, data, root / 'off', add_players=False, **kw)
            self.assertEqual((root / 'off' / 'submission.csv').read_bytes(), (root / 'v215' / 'submission.csv').read_bytes())
            self.assertFalse(off['added_players']['used'])
            # 2. the step on: players are added, the labels are H/A/D, the report holds counts only
            on = quiet(run216, data, root / 'on', **kw)
            rep = json.loads((root / 'on' / 'run.json').read_text())
            self.assertTrue(old['broadcast_fill_used'] and rep['broadcast_fill_used'])
            self.assertIn('v2.16', rep['system'])
            self.assertTrue(rep['added_players']['used'])
            self.assertGreater(rep['added_players']['player_positions_added'], 1000)
            self.assertEqual(set(rep['added_players']), {'used', 'frames_with_a_usable_offset', 'player_positions_added', 'frames_with_an_added_player',
                                                         'extra_slots', 'extra_slots_used', 'empty_radius_m'})
            lo = labels(root / 'on' / 'submission.csv')
            self.assertEqual(len(lo), 9000)
            self.assertTrue(set(np.unique(lo)) <= {'H', 'A', 'D'})
            self.assertTrue((lo != labels(root / 'v215' / 'submission.csv')).any())           # the added players have a say
            self.assertEqual(rep['second_model']['used'], old['second_model']['used'])
            self.assertEqual(rep['submission_sha256'], on['submission_sha256'])
            # 3. the same run again: the same bytes
            quiet(run216, data, root / 'again', **kw)
            self.assertEqual((root / 'again' / 'submission.csv').read_bytes(), (root / 'on' / 'submission.csv').read_bytes())
            # 4. the two cameras disagree on the ball (gate closed): nothing is added, the bytes of v2.15
            raw = data / 'broadcast' / 'SYN_broadcast_atd.txt'
            rows = []
            for line in raw.read_text().splitlines():
                head, ball = line.rsplit(':', 1)
                x, y, z = ball.split(',')
                rows.append(f'{head}:{ball}' if x == 'NaN' else f'{head}:{float(x) + 3.0 / 105.0:.5f},{y},{z}')      # the ball 3 m off its players
            raw.write_text('\n'.join(rows) + '\n')
            shut = quiet(run216, data, root / 'shut', **kw)
            self.assertFalse(shut['broadcast_fill_used'] or shut['added_players']['used'])
            quiet(run215, data, root / 'shut215', **kw)
            self.assertEqual((root / 'shut' / 'submission.csv').read_bytes(), (root / 'shut215' / 'submission.csv').read_bytes())
            # 5. no broadcast files: the bytes of v2.15
            shutil.rmtree(data / 'broadcast')
            none = quiet(run216, data, root / 'none', **kw)
            self.assertFalse(none['added_players']['used'])
            quiet(run215, data, root / 'none215', **kw)
            self.assertEqual((root / 'none' / 'submission.csv').read_bytes(), (root / 'none215' / 'submission.csv').read_bytes())

    def test_noisy_path_adds_players_too(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle(root / 'noisy', player_noise=0.45, lost=True)
            v = quiet(run216, data, root / 'v', game='SYN', halves=HALVES, release=None)
            self.assertEqual(v['path'], 'v2.3')
            self.assertTrue(v['added_players']['used'])
            self.assertFalse(v['second_model']['used'])
            self.assertTrue(set(np.unique(labels(root / 'v' / 'submission.csv'))) <= {'H', 'A', 'D'})


if __name__ == '__main__':
    unittest.main()
