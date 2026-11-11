"""Synthetic tests for possession v3 (Smart Tagging evidence). No match data, no accuracy claims."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import smarttags as st
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')


def match(n=3000, seed=0):
    """Six players; possession alternates every 300 frames; a dead stretch; two halves."""
    rng = np.random.default_rng(seed)
    base = np.array([[20, 20], [35, 40], [50, 30], [60, 25], [75, 45], [85, 50]], float)
    players = base[None] + np.cumsum(rng.normal(0, 0.05, (n, 6, 2)), 0)
    team = np.array([0, 0, 0, 1, 1, 1], np.int8)
    owner = np.where((np.arange(n) // 300) % 2 == 0, 1, 4)
    ball = players[np.arange(n), owner] + 0.3
    lab = np.where(owner < 3, 'H', 'A').astype('<U1')
    ball[1400:1500] = (52.5, -1.0)
    lab[1400:1500] = 'D'
    period = np.r_[np.ones(n // 2), np.full(n - n // 2, 2)].astype(np.int8)
    return ball, players, team, period, lab


XML = """<?xml version="1.0" encoding="utf-8"?><file><ALL_INSTANCES>
<instance><ID>1</ID><start>10.0</start><end>15.0</end><code>SET PIECES</code>
 <label><group>Team</group><text>N/A</text></label><label><group>Type</group><text>Throw-in</text></label></instance>
<instance><ID>2</ID><start>20.0</start><end>30.0</end><code>PROGRESSION</code>
 <label><group>Team</group><text>Barcelona</text></label></instance>
<instance><ID>3</ID><start>20.0</start><end>30.0</end><code>DEFENDING IN MIDDLE THIRD</code>
 <label><group>Team</group><text>Atletic Club</text></label></instance>
<instance><ID>4</ID><start>40.0</start><end>44.0</end><code>SET PIECES</code>
 <label><group>Team</group><text>Atletic Club</text></label><label><group>Type</group><text>Kick Off (After Goal)</text></label></instance>
<instance><ID>5</ID><end>50.0</end><code>BUILD UP</code></instance>
</ALL_INSTANCES></file>"""


@NEEDS
class ReaderTests(unittest.TestCase):
    def write(self, d):
        p = Path(d) / 'tags.xml'
        p.write_text(XML)
        return p

    def test_reads_codes_frames_types_and_teams(self):
        with tempfile.TemporaryDirectory() as d:
            tags = st.read(self.write(d), 25.0, ['FC Barcelona', 'Athletic Club'])
        self.assertEqual(len(tags), 4)  # instance without <start> skipped
        self.assertEqual(tags[0], {'code': 'set pieces', 'start': 250, 'end': 375, 'team': None, 'type': 'throw-in'})
        self.assertEqual((tags[1]['code'], tags[1]['team']), ('progression', 0))
        self.assertEqual((tags[2]['code'], tags[2]['team']), ('defending in middle third', 1))
        self.assertEqual((tags[3]['type'], tags[3]['team']), ('kick off', 1))

    def test_documented_aliases_when_names_do_not_match(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.write(d)
            self.assertIsNone(st.read(p, 25.0, ['Team A', 'Team B'])[1]['team'])
            tags = st.read(p, 25.0, ['Team A', 'Team B'], game='BAR-ATH')
        self.assertEqual([t['team'] for t in tags], [None, 0, 1, 1])


@NEEDS
class FeatureTests(unittest.TestCase):
    def test_signs_coverage_and_outside_blocks(self):
        n = 3000
        period = np.r_[np.zeros(100), np.ones(n - 100)].astype(np.int8)
        tags = [{'code': 'progression', 'start': 500, 'end': 750, 'team': 0, 'type': ''},
                {'code': 'defending in middle third', 'start': 500, 'end': 750, 'team': 1, 'type': ''},
                {'code': 'ball in the box', 'start': 1000, 'end': 1100, 'team': 1, 'type': ''},
                {'code': 'set pieces', 'start': 2000, 'end': 2125, 'team': None, 'type': 'throw-in'}]
        F, names = st.features(tags, n, period, 25.0)
        c = {nm: F[:, j] for j, nm in enumerate(names)}
        self.assertTrue(np.isnan(F[:100]).all())
        self.assertFalse(np.isnan(F[100:]).any())
        self.assertEqual(c['tg_e'][600], 2.0)
        self.assertEqual(c['tg_e'][1050], -1.0)
        self.assertEqual(c['tg_e'][1500], 0.0)
        self.assertEqual(c['sp_in'][2050], 1.0)
        self.assertEqual(c['sp_throw-in'][2050], 1.0)
        self.assertEqual(c['sp_team'][2050], 0.0)
        self.assertAlmostEqual(c['sp_since_start'][2050], 50 / 25.0)
        F2, _ = st.features(tags, n, period, 25.0, use=('setpiece',))
        self.assertEqual(F2[600, names.index('tg_e')], 0.0)

    def test_swap_mirrors_signed_columns_only(self):
        ball, players, team, period, lab = match()
        rng = np.random.default_rng(3)
        tags = st.simulate(lab, ball, players, team, period, np.array([105., 68.]), 25.0, rng,
                           st.sample_params(np.random.default_rng(1), 'clean'))
        self.assertGreater(len(tags), 0)
        F, names = st.features(tags, len(lab), period, 25.0)
        G, _ = st.features(tags, len(lab), period, 25.0, swap=True)
        for j, nm in enumerate(names):
            np.testing.assert_array_equal(G[:, j], -F[:, j] if nm in st.SIGNED else F[:, j])


@NEEDS
class GateAndSimulationTests(unittest.TestCase):
    def test_gate_keeps_agreeing_and_drops_inverted_group(self):
        ball, players, team, period, lab = match(6000)
        n = len(lab)
        ph = np.where(lab == 'H', 0.9, np.where(lab == 'A', 0.1, 0.5))
        pd_ = np.where(lab == 'D', 0.9, 0.05)
        runs = np.flatnonzero(np.r_[True, lab[1:] != lab[:-1]])
        tags = []
        for s, e in zip(runs, np.r_[runs[1:], n]):
            if lab[s] in ('H', 'A'):
                k = 0 if lab[s] == 'H' else 1
                tags.append({'code': 'progression', 'start': s, 'end': e, 'team': k, 'type': ''})
                tags.append({'code': 'defending in middle third', 'start': s, 'end': e, 'team': k, 'type': ''})
        use, rep = st.gate(tags, pd_, ph, period)
        self.assertEqual(use, ('attack',))
        self.assertGreater(rep['attack']['agreement'], 0.99)
        self.assertLess(rep['defend']['agreement'], 0.01)
        self.assertFalse(rep['setpiece']['used'])

    def test_simulation_is_deterministic_and_respects_regimes(self):
        ball, players, team, period, lab = match(6000)
        pitch = np.array([105., 68.])
        def run(regime, seed=4):
            rng = np.random.default_rng(seed)
            return st.simulate(lab, ball, players, team, period, pitch, 25.0, rng, st.sample_params(rng, regime))
        self.assertEqual(run('clean'), run('clean'))
        self.assertEqual(run('none'), [])
        own = {}
        for t in run('inverted_defending'):
            if t['code'] in st.DEFEND and t['team'] is not None:
                mid = min(len(lab) - 1, max(0, (t['start'] + t['end']) // 2))
                own.setdefault(lab[mid] == ('H', 'A')[t['team']], 0)
                own[lab[mid] == ('H', 'A')[t['team']]] += 1
        self.assertGreater(own.get(True, 0), own.get(False, 0))


if __name__ == '__main__':
    unittest.main()
