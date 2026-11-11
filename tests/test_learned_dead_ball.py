import tempfile
import unittest
from pathlib import Path

import numpy as np

from development.learned_dead_ball import corrupt, features, predict_mask, smooth
from development.motion_possession import predict
from test_motion_possession import CONFIG, sample
from tools.idsse_data import convert

PITCH = (105.0, 68.0)


def moving(n, fps, speed=2.0, slots=4):
    """Players moving along x at constant speed, corner-origin metres."""
    t = np.arange(n) / fps
    base = np.array([[20.0, 10.0], [40.0, 30.0], [60.0, 50.0], [80.0, 20.0]])[:slots]
    p = np.repeat(base[None], n, 0)
    p[..., 0] += speed * t[:, None]
    return p


class FeatureTests(unittest.TestCase):
    def test_speed_feature_measures_metres_per_second(self):
        x, names = features(moving(250, 25.0), np.array([0, 0, 1, 1]), np.ones(250, int), 25.0, PITCH)
        col = x[:, names.index("spd1s_mean_all")]
        self.assertAlmostEqual(float(np.nanmedian(col)), 2.0, places=3)

    def test_frame_rate_independent(self):
        a, names = features(moving(100, 10.0), np.array([0, 0, 1, 1]), np.ones(100, int), 10.0, PITCH)
        b, _ = features(moving(250, 25.0), np.array([0, 0, 1, 1]), np.ones(250, int), 25.0, PITCH)
        i = names.index("spd3s_mean_all_c1")
        self.assertAlmostEqual(float(a[50, i]), float(b[125, i]), places=3)

    def test_corner_and_centre_origins_agree(self):
        p = moving(80, 10.0)
        teams, period = np.array([0, 0, 1, 1]), np.ones(80, int)
        a, _ = features(p, teams, period, 10.0, PITCH)
        b, _ = features(p - np.array(PITCH) / 2, teams, period, 10.0, PITCH, origin="centre")
        np.testing.assert_allclose(a, b, equal_nan=True)

    def test_windows_do_not_cross_periods(self):
        n, fps = 200, 10.0
        p = moving(n, fps)
        p[:100] = p[0]                                  # period 1 frozen, period 2 moving
        x, names = features(p, np.array([0, 0, 1, 1]), np.r_[np.ones(100), np.full(100, 2)].astype(int), fps, PITCH)
        i = names.index("spd1s_mean_all_c8")
        self.assertAlmostEqual(float(x[110, i]), 2.0, places=3)
        self.assertAlmostEqual(float(x[90, i]), 0.0, places=3)

    def test_missing_players_give_finite_or_nan_not_errors(self):
        p = moving(60, 10.0)
        p[10:30] = np.nan                                # nobody tracked, e.g. a break
        x, _ = features(p, np.array([0, 0, 1, 1]), np.ones(60, int), 10.0, PITCH)
        self.assertEqual(x.shape[0], 60)
        self.assertFalse(np.isinf(x).any())

    def test_rejects_misaligned_inputs(self):
        with self.assertRaises(ValueError):
            features(moving(20, 10.0), np.array([0, 1]), np.ones(20, int), 10.0, PITCH)
        with self.assertRaises(ValueError):
            features(moving(20, 10.0), np.array([0, 0, 1, 1]), np.ones(20, int), 10.0, PITCH, origin="top")


class SmoothingTests(unittest.TestCase):
    def test_short_runs_removed_and_edges_kept(self):
        fps = 10.0
        prob = np.zeros(100)
        prob[:5] = 1                                     # edge run, kept
        prob[30:33] = 1                                  # 0.3 s blip, removed
        prob[60:90] = 1                                  # 3 s stoppage, kept
        lab = smooth(prob, np.ones(100, int), fps, 0.1, 0.5, 1.0)
        self.assertTrue(lab[:5].all())
        self.assertFalse(lab[30:33].any())
        self.assertTrue(lab[60:90].all())

    def test_corrupt_is_seeded_and_removes_data(self):
        p = moving(500, 25.0)
        a = corrupt(p, np.random.default_rng(3), 0.3, 0.5, 25.0)
        b = corrupt(p, np.random.default_rng(3), 0.3, 0.5, 25.0)
        np.testing.assert_array_equal(a, b)
        self.assertGreater(np.isnan(a).mean(), 0.05)
        self.assertEqual(a.shape, p.shape)


class StubModel:
    """Predicts dead when players are slow: a stand-in, not a trained model."""
    def __init__(self, names):
        self.i = names.index("spd1s_mean_all")

    def predict_proba(self, x):
        p = (np.nan_to_num(x[:, self.i], nan=0.0) < 0.5).astype(float)
        return np.column_stack([1 - p, p])


class IntegrationTests(unittest.TestCase):
    def test_predict_mask_uses_repository_inputs(self):
        n, fps = 200, 10.0
        p = moving(n, fps)
        p[100:] = p[100]                                 # players stop
        inputs = {"players": p, "teams": np.array([0, 0, 1, 1]), "period": np.ones(n, int),
                  "fps": np.array(fps), "pitch": np.array(PITCH)}
        _, names = features(p, inputs["teams"], inputs["period"], fps, PITCH)
        mask = predict_mask(StubModel(names), inputs, (0.5, 0.5, 1.0))
        self.assertFalse(mask[20:90].any())
        self.assertTrue(mask[120:190].all())

    def test_learned_mask_sets_D_with_its_own_reason(self):
        x = sample()
        n = len(x["frame"])
        mask = np.zeros(n, bool)
        mask[12:16] = True
        r = predict(x, np.full(n, "X"), CONFIG, learned_dead_mask=mask)
        self.assertTrue(np.all(r["labels"][12:16] == "D"))
        self.assertTrue(np.all(r["reasons"][12:16] == "learned_player_motion_dead_ball"))
        self.assertFalse(np.any(r["labels"][~mask] == "D"))

    def test_learned_mask_must_be_aligned_boolean(self):
        x = sample()
        n = len(x["frame"])
        with self.assertRaises(ValueError):
            predict(x, np.full(n, "X"), CONFIG, learned_dead_mask=np.zeros(n - 1, bool))
        with self.assertRaises(ValueError):
            predict(x, np.full(n, "X"), CONFIG, learned_dead_mask=np.zeros(n, int))


MI = """<?xml version="1.0"?><PutDataRequest><MatchInformation><Teams>
<Team TeamId="H" Role="home"/><Team TeamId="G" Role="guest"/></Teams></MatchInformation></PutDataRequest>"""


def frame(n, x, y, extra=""):
    return f'<Frame N="{n}" T="t" X="{x}" Y="{y}" D="0" S="0" A="0" M="1"{extra}/>\n'


def pos_xml():
    out = ['<?xml version="1.0"?>\n<PutDataRequest><Positions>\n']
    for section, start in (("firstHalf", 10000), ("secondHalf", 100000)):
        out.append(f'<FrameSet GameSection="{section}" MatchId="M" TeamId="BALL" PersonId="B">\n')
        for k in range(4):
            out.append(frame(start + k, 0, 0, f' BallPossession="1" BallStatus="{1 if k < 2 else 0}"'))
        out.append("</FrameSet>\n")
        for team, person, x in (("H", "P1", -10), ("G", "P2", 10), ("referee", "R1", 0)):
            out.append(f'<FrameSet GameSection="{section}" MatchId="M" TeamId="{team}" PersonId="{person}">\n')
            out += [frame(start + k, x, 1.5) for k in range(4)]
            out.append("</FrameSet>\n")
    out.append("</Positions></PutDataRequest>\n")
    return "".join(out)


class IdsseConvertTests(unittest.TestCase):
    def test_convert_drops_referees_and_reads_ball_status(self):
        with tempfile.TemporaryDirectory() as d:
            pos, mi = Path(d) / "pos.xml", Path(d) / "mi.xml"
            pos.write_text(pos_xml())
            mi.write_text(MI)
            r = convert(pos, mi)
        self.assertEqual(r["players"].shape, (8, 2, 2))
        np.testing.assert_array_equal(r["teams"], [0, 1])
        np.testing.assert_array_equal(r["period"], [1, 1, 1, 1, 2, 2, 2, 2])
        np.testing.assert_array_equal(r["dead"], [False, False, True, True] * 2)
        self.assertNotIn("ball", r)
        self.assertEqual(float(r["players"][0, 0, 0]), -10.0)


if __name__ == "__main__":
    unittest.main()
