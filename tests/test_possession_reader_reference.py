"""The tracking reader against the organisers' description of the file (synthetic file; no match data).

DATA.md and starter/baseline.py of the organisers' repository describe the provided Automatic Tracking
Data: Metrica's FIFA/EPTS export, 46 track slots named "Track 1".."Track 46" with ids "1".."46", one
record per video frame numbered from 1, every group "x,y,speed" normalised to 0-1, NaN for a missing
observation, the first Team of the metadata is the home side, a slot belongs to the team named by its
teamId. The organisers load the pair with kloppy 3.18.0 (requirements-starter.txt).

This module writes a synthetic pair in that shape (the XML structure is the one of the public Metrica
sample game 3 export) and checks possession.data.read_epts against
  (1) an independent line-by-line parser that follows the organisers' baseline (always), and
  (2) kloppy.metrica.load_tracking_epts, when kloppy is installed (not a dependency of this repository).
It says nothing about accuracy; it guards the conventions: slot order, team of a slot, x/y columns,
metres, missing values, frame numbering.
"""
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession.data import read_epts
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
try:
    from kloppy import metrica
    HAVE_KLOPPY = True
except Exception:
    HAVE_KLOPPY = False

PITCH = (105.0, 68.0)


def write_like_provided(folder, n=600, slots=46, seed=5, missing='NaN,NaN,NaN', extra_team=0, names=('FC Barcelona', 'Athletic Club')):
    """Synthetic EPTS pair shaped like the provided ATD. Returns (meta path, raw path, truth dict)."""
    rng = np.random.default_rng(seed)
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    team = np.r_[np.zeros(slots // 2 + 1), np.ones(slots - slots // 2 - 1)].astype(int)       # unequal on purpose
    rng.shuffle(team)
    ids = [str(k + 1) for k in range(slots)]
    xy = rng.uniform(0.02, 0.98, (n, slots, 2)).round(5)
    seen = rng.random((n, slots)) < 0.45                       # about 21 of 46 slots carry a player
    seen[n // 3:n // 3 + 40] = False                           # a break: nobody is tracked
    ball = rng.uniform(0.02, 0.98, (n, 2)).round(5)
    ball_seen = rng.random(n) < 0.57
    ball_seen[n // 3:n // 3 + 40] = False
    speed = rng.uniform(0, 9, (n, slots)).round(3)
    lines = []
    for i in range(n):
        groups = [f'{xy[i, j, 0]:.5f},{xy[i, j, 1]:.5f},{speed[i, j]:.3f}' if seen[i, j] else missing for j in range(slots)]
        b = f'{ball[i, 0]:.5f},{ball[i, 1]:.5f},{rng.uniform(0, 30):.3f}' if ball_seen[i] else 'NaN,NaN,NaN'
        lines.append(f'{i + 1}:' + ';'.join(groups) + ':' + b)
    raw = folder / 'SYN_tactical_atd.txt'
    raw.write_bytes(('\n'.join(lines) + '\n').encode('ascii'))
    players = ''.join(f'<Player id="{ids[j]}" teamId="{"TA" if team[j] == 0 else "TB"}"><Name>Track {j + 1}</Name>'
                      f'<ShirtNumber>{j + 1}</ShirtNumber></Player>' for j in range(slots))
    players += ''.join(f'<Player id="R{k}" teamId="REF"><Name>Official {k}</Name><ShirtNumber>0</ShirtNumber></Player>'
                       for k in range(extra_team))
    channels = ''.join(f'<PlayerChannel channelId="{c}" id="player{ids[j]}_{c}" playerId="{ids[j]}"/>' for j in range(slots) for c in 'xys')
    refs = ''.join('<SplitRegister separator=",">' + ''.join(f'<PlayerChannelRef playerChannelId="player{ids[j]}_{c}"/>' for c in 'xys')
                   + '</SplitRegister>' for j in range(slots))
    meta = folder / 'SYN_tactical_atd.xml'
    meta.write_text(
        '<?xml version="1.0" encoding="utf-8"?><main><Metadata><GlobalConfig><ProviderName>Metrica Sports</ProviderName>'
        '<FrameRate>25</FrameRate><ProviderGlobalParameters>'
        + ''.join(f'<ProviderParameter><Name>{k}</Name><Value>{v}</Value></ProviderParameter>' for k, v in
                  (('first_half_start', 1), ('first_half_end', n // 2), ('second_half_start', n // 2 + 1), ('second_half_end', n)))
        + '</ProviderGlobalParameters></GlobalConfig><Sessions><Session id="session1"><SessionType>Match</SessionType>'
        f'<FieldSize><Width>{PITCH[0]:g}</Width><Height>{PITCH[1]:g}</Height></FieldSize></Session></Sessions>'
        f'<Teams><Team id="TA"><Name>{names[0]}</Name></Team><Team id="TB"><Name>{names[1]}</Name></Team></Teams>'
        f'<Players>{players}</Players><Devices><Device id="device1"><Name>Device 1</Name><Sensors>'
        '<Sensor id="position"><Name>Position</Name><Channels><Channel id="x"><Name>position_x</Name><Unit>normalized</Unit></Channel>'
        '<Channel id="y"><Name>position_y</Name><Unit>normalized</Unit></Channel></Channels></Sensor>'
        '<Sensor id="speed"><Name>Speed</Name><Channels><Channel id="s"><Name>speed</Name><Unit>m/s</Unit></Channel></Channels></Sensor>'
        f'</Sensors></Device></Devices><PlayerChannels>{channels}</PlayerChannels></Metadata>'
        f'<DataFormatSpecifications><DataFormatSpecification endFrame="{n}" separator=":" startFrame="1">'
        f'<StringRegister name="frameCount"/><SplitRegister separator=";">{refs}</SplitRegister>'
        '<SplitRegister separator=","><BallChannelRef channelId="x"/><BallChannelRef channelId="y"/><BallChannelRef channelId="s"/>'
        '</SplitRegister></DataFormatSpecification></DataFormatSpecifications></main>', encoding='utf-8')
    return meta, raw, {'team': team, 'xy': np.where(seen[..., None], xy, np.nan), 'ball': np.where(ball_seen[:, None], ball, np.nan)}


def nearest_team_like_baseline(meta, raw, n, pitch=PITCH):
    """Team (0 home, 1 away, -1 nobody) of the tracked player nearest to the ball, read the way the organisers'
    starter/baseline.py reads the file: i-th group = i-th Player entry, first Team = home, frame_id - 1 = row."""
    import xml.etree.ElementTree as ET
    root = ET.parse(meta).getroot()
    home = [t.get('id') for t in root.iter('Team')][0]
    side = [0 if p.get('teamId') == home else 1 for p in root.iter('Player')]
    out = np.full(n, -1)
    for line in Path(raw).read_text().splitlines():
        fid, groups, ball = line.split(':')
        if ball.startswith('N'):
            continue
        bx, by = (float(v) for v in ball.split(',')[:2])
        best = None
        for slot, g in enumerate(groups.split(';')):
            if g.startswith('N'):
                continue
            x, y = (float(v) for v in g.split(',')[:2])
            d = ((x - bx) * pitch[0]) ** 2 + ((y - by) * pitch[1]) ** 2
            if best is None or d < best[0]:
                best = (d, side[slot])
        if best is not None:
            out[int(fid) - 1] = best[1]
    return out


def nearest_team_from_match(match):
    d = np.linalg.norm(match['players'].astype(np.float64) - match['ball'][:, None].astype(np.float64), axis=2)
    ok = np.isfinite(d).any(1)
    out = np.full(len(d), -1)
    out[ok] = match['team'][np.nanargmin(np.where(np.isfinite(d[ok]), d[ok], np.inf), axis=1)]
    return out


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class ReaderReferenceTests(unittest.TestCase):
    def test_reader_follows_the_documented_layout_of_the_provided_file(self):
        with tempfile.TemporaryDirectory() as d:
            meta, raw, truth = write_like_provided(d)
            match, info = read_epts(meta, raw)
            self.assertEqual((info['slots'], info['slots_without_team'], match['first_frame_id']), (46, 0, 1))
            self.assertEqual(info['team_names'], ['FC Barcelona', 'Athletic Club'])
            np.testing.assert_array_equal(match['team'], truth['team'])
            np.testing.assert_allclose(match['players'], truth['xy'] * np.array(PITCH), atol=1e-4)      # metres, NaN where missing
            np.testing.assert_allclose(match['ball'], truth['ball'] * np.array(PITCH), atol=1e-4)
            np.testing.assert_array_equal(nearest_team_from_match(match), nearest_team_like_baseline(meta, raw, len(match['ball'])))

    def test_other_ways_of_writing_a_missing_slot_and_slots_of_no_team(self):
        with tempfile.TemporaryDirectory() as d:
            for k, missing in enumerate(('NaN,NaN,0', 'NaN,NaN,0.000', 'nan,nan,nan')):
                meta, raw, truth = write_like_provided(Path(d) / str(k), n=200, missing=missing, extra_team=3 * (k == 0))
                match, info = read_epts(meta, raw) if k else self._with_officials(meta, raw)
                self.assertEqual(match['players'].shape[1], 46)                          # slots of no team are dropped
                np.testing.assert_array_equal(match['team'], truth['team'])
                np.testing.assert_array_equal(np.isnan(match['players']).all(2), np.isnan(truth['xy']).all(2))
                if missing.startswith('N'):       # the organisers' baseline recognises a missing group by its first letter
                    np.testing.assert_array_equal(nearest_team_from_match(match), nearest_team_like_baseline(meta, raw, 200))

    def _with_officials(self, meta, raw):
        """Three extra Player entries of a third team id, listed after the 46 tracks and absent from the raw groups:
        the reader must still take the 46 groups as the 46 tracks (the specification names them)."""
        match, info = read_epts(meta, raw)
        self.assertEqual((info['slots'], info['slots_without_team']), (49, 3))
        return match, info

    @unittest.skipUnless(HAVE_KLOPPY, 'kloppy (the organisers\' loader, optional) not installed')
    def test_reader_agrees_with_kloppy(self):
        with tempfile.TemporaryDirectory() as d:
            meta, raw, _ = write_like_provided(d, n=300)
            match, _ = read_epts(meta, raw)
            ds = metrica.load_tracking_epts(meta_data=str(meta), raw_data=str(raw))
            teams = ds.metadata.teams
            players = {p.player_id: p for t in teams for p in t.players}
            self.assertEqual(len(ds.records), len(match['ball']))
            self.assertEqual(teams[0].name, 'FC Barcelona')                              # kloppy's home side = ours
            for r in (0, 57, 120, 299):
                fr = ds.records[r]
                self.assertEqual(fr.frame_id, r + 1)
                for j in range(46):
                    c = fr.players_coordinates.get(players[str(j + 1)])
                    got = match['players'][r, j] / np.array(PITCH)
                    if c is None or c.x is None or np.isnan(c.x):
                        self.assertTrue(np.isnan(got).all())
                    else:
                        np.testing.assert_allclose(got, (c.x, c.y), atol=1e-6)
                    self.assertEqual(match['team'][j], 0 if players[str(j + 1)].team is teams[0] else 1)
                b = fr.ball_coordinates
                if b is None or b.x is None or np.isnan(b.x):
                    self.assertTrue(np.isnan(match['ball'][r]).all())
                else:
                    np.testing.assert_allclose(match['ball'][r] / np.array(PITCH), (b.x, b.y), atol=1e-6)


if __name__ == '__main__':
    unittest.main()
