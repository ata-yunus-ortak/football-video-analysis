"""Synthetic checks of the goalkeeper team correction (possession/keeper2.py) and of the v2.11 entry point.

No match data and no accuracy claims: the scenes are drawn by formula. The checks are about the rule: correct
team ids are left alone; goalkeeper tracks under the other team's id are moved to the team that defends their
goal, for a whole half (most of the goal's evidence is under the other id) or for a while (the piece continues
a goalkeeper piece); pieces without direct evidence follow the goalkeeper they continue; attackers are not
moved, also when the goalkeeper is not tracked while play is far away; and the entry point equals
possession.run29 whenever nothing is moved.
"""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import numpy as np
try:
    from possession import run29, run211, keeper as first_version
    from possession.keeper2 import correct_goalkeepers, FAR_M, DOM_FRAMES
    from tests.test_possession_crossplatform import bundle, HALVES
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

L, W, T = 105.0, 68.0, 6000          # two halves of four minutes


def scene(seed=4):
    """22 tracks in two halves: play drifts between the two ends, outfield players around it, a goalkeeper per goal.
    Columns 0-10 are team 0 (column 0 its goalkeeper), 11-21 team 1 (column 11 its goalkeeper). Team 0 defends the
    left goal in the first half and the right goal in the second."""
    rng = np.random.default_rng(seed)
    n = 2 * T
    t = np.arange(n)
    play = 52.5 + 30 * np.sin(2 * np.pi * t / 1000.0)                    # x of the centre of play
    P = np.zeros((n, 22, 2), np.float32)
    off = rng.uniform(-14, 14, (22, 2))
    for k in (0, 1):
        for i in range(1, 11):
            c = 11 * k + i
            push = -6 if k == 0 else 6                                   # each team a little towards its own goal in half one
            P[:, c, 0] = np.clip(play + off[c, 0] + np.where(t < T, push, -push), 16, L - 16)    # outfield players stay in front of the goalkeepers
            P[:, c, 1] = 34 + 1.6 * off[c, 1] + 3 * np.sin(t / 97.0 + c)
        left = (t < T) if k == 0 else (t >= T)                           # frames in which this team defends the left goal
        depth = 6 + 0.12 * np.where(left, play, L - play)                # the goalkeeper comes out when play is far away
        P[:, 11 * k, 0] = np.where(left, depth, L - depth)
        P[:, 11 * k, 1] = 34 + 2 * np.sin(t / 61.0 + k)
    P[..., 0] = np.clip(P[..., 0], 0.5, L - 0.5)
    P[..., 1] = np.clip(P[..., 1], 0.5, W - 0.5)
    P += rng.normal(0, 0.05, P.shape).astype(np.float32)
    team = np.r_[np.zeros(11), np.ones(11)].astype(np.int8)
    period = np.r_[np.ones(T), np.full(T, 2)].astype(np.int8)
    return {'fps': 25.0, 'pitch': np.array([L, W]), 'players': P, 'team': team, 'period': period,
            'ball': np.full((n, 2), np.nan, np.float32)}


def team_of(match, xy):
    """Team id under which each position xy (n, 2) is found in match (-1 = not found)."""
    P, team = np.asarray(match['players']), np.asarray(match['team'])
    eq = (P[..., 0] == xy[:, None, 0]) & (P[..., 1] == xy[:, None, 1])
    return np.where(eq.any(1), team[np.argmax(eq, 1)], -1)


def far_from_left(m):
    """Frames of the first half in which play is in the other half (the left goalkeeper's goal is far away)."""
    return (np.arange(2 * T) < T) & (np.nanmedian(m['players'][..., 0], 1) >= FAR_M)


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class KeeperTests(unittest.TestCase):
    def test_correct_ids_are_left_alone(self):
        m = scene()
        fixed, rep = correct_goalkeepers(m)
        self.assertIs(fixed, m)
        self.assertEqual((rep['moved_pieces'], rep['moved_frames'], rep['new_columns']), (0, 0, 0))
        self.assertEqual([h['left_team'] for h in rep['halves']], [0, 1])
        self.assertTrue(all(h['left_goalkeeper_pieces'] >= 1 and h['right_goalkeeper_pieces'] >= 1 for h in rep['halves']))
        self.assertTrue(all(h[f'{s}_evidence_frames']['defending_id'] >= DOM_FRAMES and h[f'{s}_evidence_frames']['other_id'] == 0
                            for h in rep['halves'] for s in ('left', 'right')))

    def test_goalkeepers_under_the_other_id_for_the_whole_match_are_moved(self):
        for wrong in ((0,), (0, 11)):
            m = scene()
            m['team'] = m['team'].copy()
            for c in wrong:
                m['team'][c] = 1 - m['team'][c]
            fixed, rep = correct_goalkeepers(m)
            self.assertEqual(rep['moved_pieces'], 2 * len(wrong))                        # one piece per goalkeeper and half
            for c, true in ((0, 0), (11, 1)):
                np.testing.assert_array_equal(team_of(fixed, m['players'][:, c]), true)
            for c in (3, 7, 14, 20):                                                       # nobody else is touched
                np.testing.assert_array_equal(fixed['players'][:, c], m['players'][:, c])
            self.assertEqual(len(fixed['team']), fixed['players'].shape[1])
            self.assertEqual(int(np.isfinite(fixed['players']).all(2).sum()), int(np.isfinite(m['players']).all(2).sum()))
            dominant = [h[f'{s}_evidence_frames']['other_id_dominant'] for h in rep['halves'] for s in ('left', 'right')]
            self.assertEqual(sum(dominant), 2 * len(wrong))                                # decided per goal and half

    def test_a_goalkeeper_under_the_other_id_for_a_minute_is_moved_because_the_piece_continues_him(self):
        m = scene()
        far = np.flatnonzero(far_from_left(m))
        a = int(far[len(far) // 2]) - 700
        b = a + 1500                                                                       # 60 s that include play at both ends
        extra = np.full((2 * T, 2), np.nan, np.float32)
        extra[a:b] = m['players'][a:b, 0]
        P = np.concatenate([m['players'], extra[:, None]], 1)
        P[a:b, 0] = np.nan
        m2 = dict(m, players=P, team=np.r_[m['team'], np.int8(1)])
        fixed, rep = correct_goalkeepers(m2)
        self.assertEqual(rep['moved_pieces'], 1)
        self.assertFalse(rep['halves'][0]['left_evidence_frames']['other_id_dominant'])    # not the whole-half rule
        np.testing.assert_array_equal(team_of(fixed, m['players'][:, 0]), 0)

    def test_a_piece_without_far_frames_follows_the_goalkeeper_it_continues(self):
        m = scene()
        near = np.flatnonzero((np.arange(2 * T) < T) & (np.nanmedian(m['players'][..., 0], 1) < 40))    # play at team 0's goal
        a, b = int(near[0]), int(near[0]) + 200
        self.assertTrue(np.all(np.diff(near[:200]) == 1))
        extra = np.full((2 * T, 2), np.nan, np.float32)
        extra[a:b] = m['players'][a:b, 0]
        P = np.concatenate([m['players'], extra[:, None]], 1)
        P[a:b, 0] = np.nan                                                                 # the tracker re-labels the goalkeeper for 8 s
        m2 = dict(m, players=P, team=np.r_[m['team'], np.int8(1)])
        fixed, rep = correct_goalkeepers(m2)
        self.assertEqual(rep['moved_pieces'], 1)
        np.testing.assert_array_equal(team_of(fixed, m['players'][:, 0]), 0)

    def test_attackers_are_not_moved(self):
        m = scene()
        P = m['players'].copy()
        near = np.flatnonzero((np.arange(2 * T) < T) & (np.nanmedian(P[..., 0], 1) < 40))
        a = int(near[0])
        P[a:a + 150, 15] = P[a:a + 150, 0] + np.array([3.0, 2.0], np.float32)             # an attacker 3.6 m from the goalkeeper for 6 s
        extra = np.full((2 * T, 2), np.nan, np.float32)                                    # and a short attacker track right beside him
        extra[a + 20:a + 80] = P[a + 20:a + 80, 0] + np.array([2.5, -1.0], np.float32)
        m2 = dict(m, players=np.concatenate([P, extra[:, None]], 1), team=np.r_[m['team'], np.int8(1)])
        fixed, rep = correct_goalkeepers(m2)
        self.assertIs(fixed, m2)

    def test_a_forward_waiting_up_the_pitch_is_not_moved_when_the_far_goalkeeper_is_not_tracked(self):
        """The camera follows play: the left goalkeeper is not tracked while play is in the other half, and a forward
        of the other team waits 24 m from that goal during three of those spells. He is then the tracked player nearest
        to the goal by far. The first version of the rule (possession/keeper.py) moved him to the defending team."""
        m = scene()
        P = m['players'].copy()
        far = far_from_left(m)
        P[far, 0] = np.nan                                                                 # goalkeeper out of view
        d = np.diff(np.r_[0, far.astype(np.int8), 0])
        starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        self.assertGreaterEqual(len(starts), 3)
        for s, e in list(zip(starts, ends))[:3]:
            s, e = int(s) + 20, min(int(e) - 20, int(s) + 320)                             # at most 12 s per spell
            P[s:e, 15] = np.array([24.0, 30.0], np.float32) + np.random.default_rng(s).normal(0, 0.05, (e - s, 2)).astype(np.float32)
            P[s - 1, 15] = P[e, 15] = np.nan                                               # each wait is a track piece of its own
        m2 = dict(m, players=P)
        old, old_rep = first_version.correct_goalkeepers(m2)
        self.assertGreater(old_rep['moved_pieces'], 0)                                     # what the first version did
        waits = np.abs(P[:, 15, 0] - 24.0) < 1.0
        self.assertTrue((team_of(old, P[:, 15])[waits] == 0).any())                       # the waiting forward under the defenders' id
        fixed, rep = correct_goalkeepers(m2)
        self.assertIs(fixed, m2)
        ev = rep['halves'][0]['left_evidence_frames']
        self.assertGreater(ev['other_id'], 0)                                              # he does look like a goalkeeper in those frames
        self.assertFalse(ev['other_id_dominant'])                                          # but not for most of the half, and he continues nobody

    def test_slots_that_change_identity(self):
        m = scene()
        team = m['team'].copy()
        team[0], team[11] = 1, 0                                                           # both goalkeepers under the other id
        rng = np.random.default_rng(1)
        n = 2 * T
        P = np.full((n, 30, 2), np.nan, np.float32)                                        # 15 anonymous slots per team
        slot_team = np.r_[np.zeros(15), np.ones(15)].astype(np.int8)
        cut = np.sort(rng.choice(np.arange(200, n - 200), 12, replace=False))              # every track changes slot 12 times
        bounds = np.r_[0, cut, n]
        for a, b in zip(bounds[:-1], bounds[1:]):
            for k in (0, 1):
                cols = np.flatnonzero(team == k)
                P[a:b - 3, 15 * k + rng.permutation(15)[:len(cols)]] = m['players'][a:b - 3][:, cols]     # three frames lost at every change
        fixed, rep = correct_goalkeepers(dict(m, players=P, team=slot_team))
        for c, true in ((0, 0), (11, 1)):
            got = team_of(fixed, m['players'][:, c])
            self.assertGreater(float((got[got >= 0] == true).mean()), 0.97)
        for c in (5, 16):                                                                  # an outfield player keeps his team
            got = team_of(fixed, m['players'][:, c])
            self.assertTrue((got[got >= 0] == m['team'][c]).all())


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class EntryPointTests(unittest.TestCase):
    def test_without_a_moved_piece_the_file_is_the_v29_file_and_the_report_says_what_was_moved(self):
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            data = bundle(Path(d) / 'syn')
            ref = run29.run(data, Path(d) / 'out29', game='SYN', halves=HALVES, release=None)
            with mock.patch.object(run211, 'correct_goalkeepers', side_effect=lambda m: (m, {'halves': [], 'moved_pieces': 0, 'moved_frames': 0, 'new_columns': 0})):
                same = run211.run(data, Path(d) / 'out211a', game='SYN', halves=HALVES, release=None)
            self.assertEqual(same['submission_sha256'], ref['submission_sha256'])
            rep = run211.run(data, Path(d) / 'out211b', game='SYN', halves=HALVES, release=None)
            self.assertEqual(rep['rows'], ref['rows'])
            self.assertIn('v2.11', rep['system'])
            self.assertEqual(sorted(rep['goalkeeper_correction']), ['halves', 'moved_frames', 'moved_pieces', 'new_columns'])
            self.assertEqual(rep['fusion']['alignment'], ref['fusion']['alignment'])       # the broadcast path sees the ids as given
            self.assertEqual(rep['gate'], ref['gate'])


if __name__ == '__main__':
    unittest.main()
