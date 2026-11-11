"""Synthetic tests for the broadcast alignment/fusion module (possession v4 candidate).
No match data; these check mechanics, not football accuracy."""
import unittest
import numpy as np
try:
    from possession import broadcast as bc
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
FPS = 25.0
PITCH = np.array([105.0, 68.0])


def tactical(n=30000, seed=0):
    """Ten players per team and a ball that moves between them (random walk, metres)."""
    rng = np.random.default_rng(seed)
    # smooth running (AR(1) velocity, ~3 m/s), so 16 s old content is far from the live positions
    v = np.zeros((n, 20, 2))
    e = rng.normal(0, 0.03, (n, 20, 2))
    for t in range(1, n):
        v[t] = 0.98 * v[t - 1] + e[t]
    p = rng.uniform([10, 5], [95, 63], (20, 2)) + np.cumsum(v, 0)
    p = np.abs(p) % (2 * PITCH)
    p = np.where(p > PITCH, 2 * PITCH - p, p)          # reflect into the pitch
    team = np.r_[np.zeros(10), np.ones(10)].astype(np.int8)
    owner = np.repeat(rng.integers(0, 20, n // 100 + 1), 100)[:n]
    ball = p[np.arange(n), owner] + rng.normal(0, 0.3, (n, 2))
    return {'ball': ball, 'players': p, 'team': team}


def broadcast_of(tac, lag, rng, garbage=False):
    """Broadcast frame b shows tactical frame b + lag; a window of players around the ball;
    every 3000 frames a 250-frame replay of older content; 20% close-up frames."""
    n = len(tac['ball'])
    B = n - abs(lag)
    b = np.arange(B)
    content = b + lag if lag >= 0 else b
    content = np.clip(content, 0, n - 1)
    live = np.ones(B, bool)
    for s in range(1000, B - 300, 3000):
        content[s:s + 250] = np.clip(content[s:s + 250] - 400, 0, n - 1)
        live[s:s + 250] = False
    valid = rng.random(B) > 0.2
    P = tac['players'][content].copy()
    c = tac['ball'][content]
    vis = (np.abs(P[..., 0] - c[:, None, 0]) < 25) & (np.abs(P[..., 1] - c[:, None, 1]) < 15)
    P = P + rng.normal(0, 0.3, P.shape)
    P[~vis | ~valid[:, None]] = np.nan
    ball = c + rng.normal(0, 0.4, (B, 2))
    if garbage:
        ball = ball + rng.normal(0, 8.0, (B, 2))
    ball[~valid | (rng.random(B) < 0.3)] = np.nan
    true_t = np.where(live & valid, content, -1)
    return {'ball': ball, 'players': P, 'team': tac['team'].copy()}, valid, true_t


@NEEDS
class AlignmentTests(unittest.TestCase):
    def test_coarse_offset_recovers_lag(self):
        tac = tactical()
        rng = np.random.default_rng(1)
        bro, valid, _ = broadcast_of(tac, 1234, rng)
        d, sc, sc2 = bc.coarse_offset(np.where(valid[:, None], bro['ball'], np.nan), tac['ball'],
                                      np.ones(len(tac['ball']), bool), FPS)
        self.assertEqual(d, 1234)
        self.assertGreater(sc, sc2)

    def test_align_rejects_replays_and_fuse_fills_gaps(self):
        tac = tactical()
        rng = np.random.default_rng(2)
        bro, valid, true_t = broadcast_of(tac, 700, rng)
        tac_missing = dict(tac, ball=np.where((rng.random(len(tac['ball'])) < 0.4)[:, None], np.nan, tac['ball']))
        bro2, orep = bc.orient(tac_missing, bro, valid, FPS, PITCH)
        self.assertFalse(orep['flip_x'] or orep['flip_y'] or orep['team_swapped'])
        t_of_b, rep = bc.align(tac_missing, bro2, valid, FPS, [(1, 0, len(tac['ball']) - 1)])
        acc = t_of_b >= 0
        good = acc & (true_t >= 0) & (np.abs(t_of_b - true_t) <= 2)
        self.assertGreater(acc.sum(), 1000)
        self.assertGreater(good.sum() / acc.sum(), 0.98)
        fused, frep = bc.fuse(tac_missing['ball'], bro2['ball'], t_of_b, FPS)
        self.assertTrue(frep['used'])
        self.assertGreater(frep['filled'], 1000)
        known = np.isfinite(tac_missing['ball']).all(1)
        np.testing.assert_array_equal(fused[known], tac_missing['ball'][known])
        filled = ~known & np.isfinite(fused).all(1)
        err = np.linalg.norm(fused[filled] - tac['ball'][filled], axis=1)
        self.assertLess(np.median(err), 1.0)

    def test_gate_refuses_disagreeing_broadcast_ball(self):
        tac = tactical()
        rng = np.random.default_rng(3)
        bro, valid, _ = broadcast_of(tac, 300, rng, garbage=True)
        t_of_b = np.where(valid, np.arange(len(valid)) + 300, -1)
        fused, frep = bc.fuse(tac['ball'].copy(), bro['ball'], t_of_b, FPS)
        self.assertFalse(frep['used'])
        self.assertEqual(frep['filled'], 0)

    def test_orient_detects_flipped_axes(self):
        tac = tactical()
        rng = np.random.default_rng(4)
        bro, valid, _ = broadcast_of(tac, 500, rng)
        flipped = dict(bro, ball=PITCH - bro['ball'], players=PITCH - bro['players'])
        bro2, orep = bc.orient(tac, flipped, valid, FPS, PITCH)
        self.assertTrue(orep['flip_x'] and orep['flip_y'])
        self.assertEqual(orep['global_lag'], 500)


if __name__ == '__main__':
    unittest.main()
