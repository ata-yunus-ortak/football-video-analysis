import unittest

import numpy as np

from development.learned_possession import corrupt_ball, decode, features

PITCH = (105.0, 68.0)
TEAMS = np.array([0, 0, 1, 1])


def scene(n, fps):
    t = np.arange(n) / fps
    p = np.repeat(np.array([[30.0, 20.0], [40.0, 40.0], [70.0, 30.0], [80.0, 50.0]])[None], n, 0)
    p[..., 0] += t[:, None]
    ball = p[:, 0].copy()                      # home player 0 carries the ball
    return p, ball


class PossessionFeatureTests(unittest.TestCase):
    def test_nearest_player_distance_and_missing_ball(self):
        p, ball = scene(100, 10.0)
        ball[40:60] = np.nan
        x, names = features(p, TEAMS, ball, np.ones(100, int), 10.0, PITCH)
        self.assertAlmostEqual(float(x[10, names.index("t0_ball_d1")]), 0.0, places=5)
        self.assertTrue(np.isnan(x[50, names.index("t0_ball_d1")]))
        self.assertEqual(float(x[50, names.index("ball_seen")]), 0.0)
        self.assertTrue(np.isfinite(x[50, names.index("advance_diff")]))   # player shape survives

    def test_frame_rate_independent(self):
        a, names = features(*scene(100, 10.0)[:1], TEAMS, scene(100, 10.0)[1], np.ones(100, int), 10.0, PITCH)
        p, b = scene(250, 25.0)
        c, _ = features(p, TEAMS, b, np.ones(250, int), 25.0, PITCH)
        i = names.index("t0_forward_speed_c1")
        self.assertAlmostEqual(float(a[50, i]), float(c[125, i]), places=3)

    def test_rejects_misaligned_ball(self):
        p, ball = scene(20, 10.0)
        with self.assertRaises(ValueError):
            features(p, TEAMS, ball[:-1], np.ones(20, int), 10.0, PITCH)


class DecodeTests(unittest.TestCase):
    def test_hysteresis_short_spells_and_dead_ball(self):
        prob = np.r_[np.full(50, .9), np.full(3, .1), np.full(47, .9), np.full(50, .1)]
        dead = np.zeros(150, bool)
        dead[140:] = True
        lab = decode(prob, dead, np.ones(150, int), 10.0, 0.1, 0.1, 1.0)
        self.assertTrue(np.all(lab[:100] == "H"))      # 0.3 s flicker absorbed
        self.assertTrue(np.all(lab[105:140] == "A"))
        self.assertTrue(np.all(lab[140:] == "D"))

    def test_corrupt_ball_seeded(self):
        b = np.zeros((300, 2))
        x = corrupt_ball(b, np.random.default_rng(0), 0.3, 0.5, 25.0)
        y = corrupt_ball(b, np.random.default_rng(0), 0.3, 0.5, 25.0)
        np.testing.assert_array_equal(x, y)
        self.assertGreater(np.isnan(x[:, 0]).mean(), 0.05)


if __name__ == "__main__":
    unittest.main()


class SubmissionTests(unittest.TestCase):
    def test_predict_labels_combines_dead_and_possession(self):
        from tools.predict_submission import predict_labels

        class Dead:
            def predict_proba(self, x):
                p = np.zeros(len(x)); p[150:] = 1
                return np.column_stack([1 - p, p])

        class Home:
            def predict_proba(self, x):
                p = np.r_[np.ones(100), np.zeros(len(x) - 100)]
                return np.column_stack([1 - p, p])

        p, ball = scene(200, 10.0)
        x = {"players": p, "ball": ball, "teams": TEAMS, "period": np.ones(200, int),
             "fps": np.array(10.0), "pitch": np.array(PITCH)}
        dmeta = {"smoothing": {"window_s": 0.1, "threshold": 0.5, "min_run_s": 0.1}}
        pmeta = {"decoding": {"window_s": 0.1, "margin": 0.0, "min_spell_s": 0.1}}
        labels, dead = predict_labels(x, Dead(), dmeta, Home(), pmeta)
        self.assertTrue(np.all(labels[:100] == "H"))
        self.assertTrue(np.all(labels[100:150] == "A"))
        self.assertTrue(np.all(labels[150:] == "D"))

    def test_atd_normalisation_round_trip(self):
        from tools.idsse_to_atd import normalised
        p = np.array([[-52.5, 34.0], [0.0, 0.0], [52.5, -34.0]])
        np.testing.assert_allclose(normalised(p), [[0, 0], [0.5, 0.5], [1, 1]])
