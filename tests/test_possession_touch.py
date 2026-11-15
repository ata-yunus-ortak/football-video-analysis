"""Synthetic checks of the touch / control-change features (possession v2.12 candidate, development only).

These tests show that the code does what its docstring says on hand-made tracking; they are not a measure of
football accuracy. numpy only (the comparison with possession.features.play_blocks skips without scipy).
"""
import ast
import unittest
from pathlib import Path
import numpy as np
from possession.touch import touch_features, touch_events, play_blocks, PERSP, COMMON, STATE_CAP_S

FPS = 25.0
PASS_T, RECV_T = 100, 149        # home slot 0 passes at frame 100, away slot 2 receives at frame 149


def _pass_match(noise=0.05, seed=0, lead=20, n=400):
    """Home player (slot 0) at x=40 plays the ball at 10 m/s to an away player (slot 2) at x=60.

    Frames [0, lead) are outside play (period 0); the ball rests at the home player's feet before the pass and
    at the away player's feet after the reception. Slots 1 and 3 are far from the ball.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    players = np.zeros((n, 4, 2))
    players[:, 0] = (40.0, 30.0)
    players[:, 1] = (20.0, 10.0)
    players[:, 2] = (60.0, 30.0)
    players[:, 3] = (85.0, 60.0)
    players += rng.normal(0, 0.03, players.shape)
    bx = np.where(t < PASS_T, 40.4, np.minimum(40.4 + (t - PASS_T) * 10.0 / FPS, 59.6))
    ball = np.stack([bx, np.full(n, 30.0)], 1) + rng.normal(0, noise, (n, 2))
    period = np.r_[np.zeros(lead), np.ones(n - lead)].astype(np.int8)
    return dict(fps=FPS, pitch=np.array([105.0, 68.0]), ball=ball.astype(np.float32),
                players=players.astype(np.float32), team=np.array([0, 0, 1, 1], np.int8), period=period)


def _col(names):
    return {k: i for i, k in enumerate(names)}


class TouchFeatureTests(unittest.TestCase):
    def test_shapes_names_and_outside_blocks(self):
        m = _pass_match()
        X, names = touch_features(m)
        self.assertEqual(X.shape, (len(m['ball']), len(names)))
        self.assertEqual(X.dtype, np.float32)
        self.assertEqual(len(names), len(COMMON) + 3 * len(PERSP))
        self.assertEqual(len(set(names)), len(names))
        self.assertTrue(np.isnan(X[:20]).all())                    # period 0: outside every play block
        i = _col(names)
        for c in ('tc_since_any', 'h_tc_since', 'k_tc_since', 'h_tc_last', 'tc_since_change'):
            self.assertTrue(np.isfinite(X[20:, i[c]]).all(), c)     # event-state columns defined everywhere
            self.assertTrue((X[20:, i[c]] <= STATE_CAP_S).all(), c)

    def test_team_swap_symmetry(self):
        m = _pass_match()
        X, names = touch_features(m)
        Xs, names_s = touch_features(m, swap=True)
        self.assertEqual(names, names_s)
        i = _col(names)
        for c in COMMON:
            self.assertTrue(np.array_equal(X[:, i[f'tc_{c}']], Xs[:, i[f'tc_{c}']], equal_nan=True), c)
        for c in PERSP:
            self.assertTrue(np.array_equal(X[:, i[f'h_tc_{c}']], Xs[:, i[f'k_tc_{c}']], equal_nan=True), c)
            self.assertTrue(np.array_equal(X[:, i[f'k_tc_{c}']], Xs[:, i[f'h_tc_{c}']], equal_nan=True), c)
            self.assertTrue(np.array_equal(X[:, i[f'diff_tc_{c}']], -Xs[:, i[f'diff_tc_{c}']], equal_nan=True), c)
        e, es = touch_events(m), touch_events(m, swap=True)
        self.assertTrue(np.array_equal(e['frame'], es['frame']))
        self.assertTrue(np.array_equal(np.where(e['team'] >= 0, 1 - e['team'], -1), es['team']))

    def test_deterministic_and_input_untouched(self):
        m = _pass_match(noise=0.2, seed=3)
        ball, players = m['ball'].copy(), m['players'].copy()
        X1, _ = touch_features(m)
        X2, _ = touch_features(m)
        self.assertTrue(np.array_equal(X1, X2, equal_nan=True))
        self.assertTrue(np.array_equal(m['ball'], ball, equal_nan=True))
        self.assertTrue(np.array_equal(m['players'], players, equal_nan=True))

    def test_pass_gives_touches_and_team_change_at_the_right_time(self):
        m = _pass_match()
        e = touch_events(m)
        att = e['frame'][e['team'] >= 0]
        home = e['frame'][e['team'] == 0]
        away = e['frame'][e['team'] == 1]
        self.assertTrue(np.any(np.abs(home - PASS_T) <= 2), e)
        self.assertTrue(np.any(np.abs(away - RECV_T) <= 2), e)
        self.assertFalse(np.any((att > PASS_T + 7) & (att < RECV_T - 7)), e)   # nothing in mid-flight
        X, names = touch_features(m)
        i = _col(names)
        r = 130                                                     # ball in flight after the home pass
        self.assertEqual(X[r, i['h_tc_last']], 1.0); self.assertEqual(X[r, i['k_tc_last']], 0.0)
        self.assertEqual(X[r, i['diff_tc_last']], 1.0)
        self.assertAlmostEqual(float(X[r, i['h_tc_since']]), (r - home[np.argmin(np.abs(home - PASS_T))]) / FPS, 5)
        self.assertEqual(float(X[r, i['k_tc_since']]), STATE_CAP_S)
        r = 180                                                     # after the away reception
        self.assertEqual(X[r, i['h_tc_last']], 0.0); self.assertEqual(X[r, i['k_tc_last']], 1.0)
        self.assertEqual(X[r, i['diff_tc_last']], -1.0)
        t_recv = away[np.argmin(np.abs(away - RECV_T))]
        self.assertAlmostEqual(float(X[r, i['tc_since_change']]), (r - t_recv) / FPS, 5)
        self.assertEqual(X[t_recv, i['tc_nchange_p1']], 1.0)
        self.assertGreaterEqual(X[t_recv, i['k_tc_zt_c1']], 3.0)
        self.assertTrue(np.isnan(X[t_recv, i['h_tc_zt_c1']]) or X[t_recv, i['h_tc_zt_c1']] < X[t_recv, i['k_tc_zt_c1']])
        # co-movement: before the pass the ball stays with the home player, during the flight it does not
        self.assertLess(X[80, i['h_tc_cm_p']], 1.0)
        self.assertGreater(X[130, i['h_tc_cm_p']], 5.0)
        self.assertGreater(X[130, i['k_tc_cm_p']], 5.0)
        self.assertLess(X[200, i['k_tc_cm_f']], 1.0)
        # pressure: no opponent within 2 m of the player nearest to the ball
        self.assertEqual(X[80, i['h_tc_press']], 0.0)
        self.assertAlmostEqual(float(X[80, i['h_tc_opp_gap']]), 20.0, delta=0.5)

    def test_reception_inside_a_ball_gap_is_inferred(self):
        m = _pass_match()
        m['ball'][RECV_T - 5:RECV_T + 5] = np.nan                 # 10 missing frames around the reception
        e = touch_events(m)
        k = np.flatnonzero((e['team'] == 1) & (np.abs(e['frame'] - RECV_T) <= 3))
        self.assertEqual(len(k), 1, e)
        self.assertEqual(e['kind'][k[0]], 1.0)                      # inferred across the gap, not seen
        X, names = touch_features(m)
        i = _col(names)
        self.assertEqual(X[RECV_T + 20, i['k_tc_last']], 1.0)
        self.assertTrue(np.isfinite(X[RECV_T, i['tc_z']]))          # the gap carries its own score
        self.assertTrue(np.isfinite(X[RECV_T, i['h_tc_press']]))    # last ball seen 6 frames ago (< 0.5 s)
        self.assertTrue(np.isnan(X[RECV_T + 30, i['tc_z']]) or np.isfinite(X[RECV_T + 30, i['tc_z']]))

    def test_missing_ball_is_not_invented(self):
        m = _pass_match()
        m['ball'][200:320] = np.nan                                 # long gap: nothing can be measured inside
        X, names = touch_features(m)
        i = _col(names)
        mid = slice(240, 290)
        for c in ('tc_z', 'tc_dv', 'tc_zmax_c1', 'h_tc_cm_p', 'k_tc_cm_f', 'h_tc_press', 'k_tc_opp_gap',
                  'h_tc_zt_c1'):
            self.assertTrue(np.isnan(X[mid, i[c]]).all(), c)
        self.assertTrue(np.isfinite(X[mid, i['k_tc_since']]).all())   # the last event is carried, not the ball
        self.assertTrue((X[mid, i['k_tc_last']] == 1.0).all())
        e = touch_events(m)
        self.assertFalse(np.any((e['frame'] > 210) & (e['frame'] < 310)))
        m2 = _pass_match()
        m2['ball'][:] = np.nan                                      # no ball at all
        X2, _ = touch_features(m2)
        self.assertTrue(np.isnan(X2[20:, i['tc_z']]).all())
        self.assertTrue((X2[20:, i['tc_since_any']] == STATE_CAP_S).all())
        self.assertTrue((X2[20:, i['h_tc_last']] == 0).all() and (X2[20:, i['k_tc_last']] == 0).all())
        self.assertTrue(np.isnan(X2[20:, i['h_tc_d_last']]).all())

    def test_false_detection_jump_is_not_a_touch(self):
        m = _pass_match()
        m['ball'][250:256] = (85.0, 60.0)                            # 6-frame false ball at the far away player
        e = touch_events(m)
        self.assertFalse(np.any((e['frame'] >= 243) & (e['frame'] <= 262) & (e['team'] >= 0)), e)

    def test_blocks_do_not_mix_and_short_blocks_work(self):
        m = _pass_match()
        m['period'][RECV_T:] = 2                                     # half change exactly at the reception
        X, names = touch_features(m)
        i = _col(names)
        self.assertEqual(float(X[RECV_T, i['tc_since_any']]), STATE_CAP_S)   # nothing carried over
        m3 = _pass_match(n=30, lead=27)                              # a 3-frame block
        X3, _ = touch_features(m3)
        self.assertEqual(X3.shape[0], 30)

    def test_play_blocks_match_features(self):
        try:
            from possession.features import play_blocks as fpb
        except ImportError:
            self.skipTest('scipy not installed')
        p = np.r_[np.zeros(5), np.ones(10), np.full(3, 2), np.zeros(4), np.full(7, 2), np.ones(2)].astype(np.int8)
        self.assertEqual(play_blocks(p), fpb(p))

    def test_numpy_only(self):
        src = Path(__file__).resolve().parents[1] / 'possession' / 'touch.py'
        mods = set()
        for node in ast.walk(ast.parse(src.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Import):
                mods |= {a.name.split('.')[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                mods.add((node.module or '').split('.')[0] if node.level == 0 else '.')
        self.assertEqual(mods, {'numpy'})


if __name__ == '__main__':
    unittest.main()
