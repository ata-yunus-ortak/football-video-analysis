"""Synthetic checks of the final-test tool and of the tracking-file writer; no match data, no network, no accuracy claims.

The final test itself (tools/possession_final_test.py on the reserved external match) is run once by the team and
is not part of this suite. These tests check the process around it: the plan names the frozen release and the
reserved match, the tool refuses anything else and refuses a second run, the evaluation runs end to end on a
synthetic prepared match, and files written by possession/epts_export.py are read back correctly.
"""
import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import numpy as np
try:
    from possession import inputs_check as ic
    from possession.data import read_epts
    from possession.epts_export import write_packed
    from tools import possession_final_test as ft
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

REPO = Path(__file__).resolve().parents[1]


def prepared_match(folder, n=9000, seed=3):
    """A small synthetic match in the layout tools/sportec_prepare.convert writes (inputs.npz, targets.npz)."""
    rng = np.random.default_rng(seed)
    s = 10
    v = np.zeros((n, s, 2)); e = rng.normal(0, 0.02, (n, s, 2))
    for t in range(1, n):
        v[t] = 0.98 * v[t - 1] + e[t]
    players = np.clip(np.array([52.0, 34.0]) + rng.uniform(-25, 25, (1, s, 2)) + np.cumsum(v, 0), 1, 104)
    team = np.r_[np.zeros(s // 2), np.ones(s - s // 2)].astype(np.int8)
    seg = rng.integers(0, s, n // 200 + 1)
    owner = np.repeat(seg, 200)[:n]
    dead = np.repeat(rng.random(n // 200 + 1) < 0.2, 200)[:n]
    ball = players[np.arange(n), owner] + 0.4
    labels = np.where(dead, 'D', np.where(team[owner] == 0, 'H', 'A'))
    folder = Path(folder); folder.mkdir(parents=True)
    np.savez_compressed(folder / 'inputs.npz', ball=ball, players=players, teams=team, period=np.r_[np.ones(n // 2), np.full(n - n // 2, 2)].astype(np.int8),
                        fps=np.array(25.0), pitch=np.array([105.0, 68.0]), ball_observed=~dead, player_detected=np.ones((n, s), bool))
    np.savez_compressed(folder / 'targets.npz', labels=labels)
    return folder


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class FinalTestToolTests(unittest.TestCase):
    def test_plan_names_the_frozen_release_the_reserved_match_and_the_registered_tool(self):
        plan = json.loads(ft.PLAN.read_text(encoding='utf-8'))
        entry = importlib.import_module(plan['release']['module'])
        self.assertEqual(plan['release']['name'], entry.check_release()['version'])
        self.assertEqual(plan['release']['manifest_sha256'], ft.sha256(entry.RELEASE))
        delivered = json.loads((REPO / 'possession-release.json').read_text(encoding='utf-8'))
        self.assertEqual((plan['release']['name'], plan['release']['module']),
                         (delivered['release'], delivered['steps'][0]['module']))              # the test is of the release that is delivered
        data = json.loads(ft.DATA_PLAN.read_text(encoding='utf-8'))
        files = [e for e in data['files'] if e['fixture_id'] == plan['fixture']['id']]
        self.assertEqual({e['split'] for e in files}, {'reserved_test'})
        self.assertEqual(sorted(e['path'] for e in files), sorted(f['path'] for f in plan['fixture']['files']))
        self.assertEqual(plan['simulator_sha256'], {n: ft.sha256(ft.ARCHIVE / n) for n in ft.SIMULATORS})
        self.assertEqual(plan['tool']['sha256'], ft.sha256(ft.__file__))                      # the tool is the registered one
        self.assertEqual(plan['tool']['writer_sha256'], ft.sha256(REPO / 'possession' / 'epts_export.py'))
        seeds = [c['seed'] for c in plan['design']['tactical_copies']]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(plan['design']['broadcast_regimes'], list(ft.REGIMES))
        self.assertIn('none', plan['decision_rule'])
        self.assertIs(plan['provided_fixture_used'], False)

    def test_only_the_registered_reserved_match_is_acquired_and_never_twice(self):
        data = json.loads(ft.DATA_PLAN.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as d, mock.patch('urllib.request.urlopen', side_effect=AssertionError('network')):
            for bad in ('J03WN1', 'NOPE'):                                                    # a development match, an unknown match
                with self.assertRaises(ValueError):
                    ft.acquire(Path(d), data, bad)
            moved = json.loads(json.dumps(data))
            for e in moved['files']:
                if e['fixture_id'] == 'J03WMX':
                    e['url'] = e['url'].replace('huggingface.co', 'example.invalid')
            with self.assertRaises(ValueError):
                ft.acquire(Path(d), moved, 'J03WMX')                                          # not the pinned source
            done = Path(d) / 'results.json'
            done.write_text('{}')
            out = io.StringIO()
            with mock.patch.object(ft, 'RESULTS', done), contextlib.redirect_stdout(out):
                code = ft.main(['--out', str(Path(d) / 'out')])
            self.assertEqual(code, 1)
            self.assertIn('already been run', out.getvalue())
            self.assertFalse((Path(d) / 'out' / 'raw').exists())

    def test_rehearsal_runs_the_design_on_a_prepared_match_and_writes_nothing_into_the_repository(self):
        with tempfile.TemporaryDirectory() as d:
            prepared = prepared_match(Path(d) / 'prepared')
            args = ['--out', str(Path(d) / 'out'), '--rehearsal', 'SYN', '--prepared', str(prepared), '--limit', '1', '--regimes', 'good']
            existed = ft.RESULTS.exists()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ft.main(args), 0)
            res = json.loads((Path(d) / 'out' / 'rehearsal-SYN-results.json').read_text(encoding='utf-8'))
            self.assertEqual([r['system'] for r in res['rows']], ['baseline logic', 'tactical only', 'broadcast good'])
            self.assertTrue(all(0.0 <= r['spell_f1'] <= 1.0 and 0.0 <= r['macro_f1'] <= 1.0 for r in res['rows']))
            self.assertIn('REHEARSAL', res['record'])
            self.assertIs(res['provided_fixture_used'], False)
            self.assertEqual(ft.RESULTS.exists(), existed)                                    # only the real run writes the repository file
            self.assertFalse(list((Path(d) / 'out' / 'work-rehearsal-SYN').glob('copy*')))    # working files removed
            again = mock.patch.object(ft, 'run_release', side_effect=AssertionError('finished rows are not run again'))
            with again, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ft.main(args), 0)

    def test_written_files_are_read_back_by_the_release_reader(self):
        rng = np.random.default_rng(8)
        n, s = 400, 14
        players = rng.uniform(1, 100, (n, s, 2)).astype(np.float32)
        players[rng.random((n, s)) < 0.2] = np.nan
        ball = rng.uniform(1, 100, (n, 2)).astype(np.float32)
        ball[rng.random(n) < 0.3] = np.nan
        team = np.r_[np.zeros(7), np.ones(7)].astype(np.int8)
        with tempfile.TemporaryDirectory() as d:
            peak = write_packed(Path(d), 'SYN_tactical', players, ball, team, 46, (105.0, 68.0))
            self.assertLessEqual(max(peak), 23)
            meta, raw = Path(d) / 'SYN_tactical_atd.xml', Path(d) / 'SYN_tactical_atd.txt'
            match, info = read_epts(meta, raw)
            self.assertEqual((info['slots'], info['slots_without_team'], match['first_frame_id'], len(match['ball'])), (46, 0, 1, n))
            np.testing.assert_allclose(match['ball'], ball, atol=2e-3)                        # 5 decimals of a normalised coordinate
            for k in (0, 1):                                                                  # the same players per team in every frame, in any slot
                want = np.sort(np.nan_to_num(players[:, team == k, 0], nan=1e9), 1)
                got = np.sort(np.nan_to_num(match['players'][:, match['team'] == k, 0], nan=1e9), 1)[:, :want.shape[1]]
                np.testing.assert_allclose(got, want, atol=2e-3)
            self.assertEqual(ic.starter_difference(match, ic.second_reading(meta, raw)), '')


if __name__ == '__main__':
    unittest.main()
