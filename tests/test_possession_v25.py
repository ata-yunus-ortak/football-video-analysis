"""Synthetic checks for the gated broadcast ball fill (possession/fusion.py); no accuracy claims."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession.fusion import fuse_gated, accuracy_gate, project, fill, GATE_MEDIAN_M
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False
NEEDS = unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')


def streams(n=8000, err=0.1, miss=0.4, seed=0):
    """Tactical ball with gaps, broadcast ball = truth + err noise, identity mapping (t_of_b = b)."""
    rng = np.random.default_rng(seed)
    truth = np.cumsum(rng.normal(0, 0.2, (n, 2)), 0) + 50.0
    tac = truth + rng.normal(0, 0.1, (n, 2))
    gaps = np.repeat(rng.random(n // 50 + 1) < miss, 50)[:n]
    tac[gaps] = np.nan
    bro = truth + rng.normal(0, err, (n, 2))
    return tac, bro, np.arange(n), gaps


@NEEDS
class FusionTests(unittest.TestCase):
    def test_accurate_broadcast_opens_the_gate_and_fills_only_missing_frames(self):
        tac, bro, t_of_b, gaps = streams(err=0.1)
        out, rep = fuse_gated(tac, bro, t_of_b, 25.0, graded_mask=np.ones(len(tac), bool))
        self.assertTrue(rep['used'])
        np.testing.assert_array_equal(out[~gaps], tac[~gaps])          # tactical balls never replaced
        self.assertTrue(np.isfinite(out[gaps]).all())
        self.assertGreater(rep['ball_visible_graded_after'], rep['ball_visible_graded_before'])

    def test_inaccurate_broadcast_keeps_the_tactical_ball(self):
        tac, bro, t_of_b, _ = streams(err=1.0)
        out, rep = fuse_gated(tac, bro, t_of_b, 25.0)
        self.assertFalse(rep['used'])
        self.assertFalse(rep['median_ok'])
        np.testing.assert_array_equal(np.isnan(out), np.isnan(tac))

    def test_too_little_overlap_or_too_few_accepted_frames_close_the_gate(self):
        tac, bro, t_of_b, _ = streams(n=2000, err=0.05)
        self.assertFalse(fuse_gated(tac, bro, t_of_b, 25.0)[1]['used'])     # < 120 s of overlap
        tac, bro, t_of_b, _ = streams(err=0.05)
        t_sparse = np.where(np.arange(len(t_of_b)) % 40 == 0, t_of_b, -1)  # 2.5% accepted
        self.assertFalse(fuse_gated(tac, bro, t_sparse, 25.0)[1]['accepted_ok'])

    def test_implausible_jump_is_not_filled_and_unaccepted_frames_are_ignored(self):
        tac = np.full((100, 2), np.nan); tac[:50] = 10.0; tac[60:] = 10.0
        bb = np.full((100, 2), np.nan); bb[50:60] = 10.0; bb[52] = 60.0      # 50 m away 2 frames later
        out, ok = fill(tac, bb, 25.0)
        self.assertFalse(ok[52]); self.assertTrue(ok[51])
        self.assertTrue(np.isnan(project(np.ones((5, 2)), np.array([-1, -1, 2, -1, -1]), 5)[[0, 1, 3, 4]]).all())


def clock_rows(n_frames, kickoffs, fps=25.0, every=125, phase=0, offset=0, unread=(), misread=()):
    """Readings of a match clock that starts at 0 (half 1) / 2700 (half 2) at the given video frames."""
    rows = []
    for k, f in enumerate(range(phase, n_frames, every)):
        clock = None
        for h, (a, e) in enumerate(kickoffs):
            if a <= f + offset < e:
                clock = float((f + offset - a) // int(fps) + 2700 * h)
        if k in unread:
            clock = None
        if k in misread:
            clock = 1234.0
        rows.append({'video_time_s': f / fps, 'clock_s': clock, 'confidence': 0.95 if clock is not None else None,
                     'period': None})
    return rows


try:
    from possession.clocksync import clock_runs, clock_anchors, half_lags
    HAVE_CLOCK = True
except ImportError:
    HAVE_CLOCK = False


@unittest.skipUnless(HAVE_CLOCK, 'possession dependencies not installed')
class ClockSyncTests(unittest.TestCase):
    def test_runs_break_at_jumps_and_ignore_misreads(self):
        rows = clock_rows(30000, [(0, 15000), (17000, 30000)], misread={40})
        runs = clock_runs(rows)
        self.assertGreaterEqual(len(runs), 2)
        for run in runs:                                   # a run never spans the half-time jump
            clocks = [r['clock_s'] for r in run['rows']]
            self.assertTrue(all(c < 2700 for c in clocks) or all(c >= 2700 for c in clocks))
            self.assertTrue(all(b > a for a, b in zip(clocks, clocks[1:])))
        self.assertFalse(any(r['clock_s'] == 1234.0 for run in runs for r in run['rows']))

    def test_half_lags_recover_a_known_offset_per_half(self):
        T = 60000
        halves_tac = [(0, 25000), (30000, 55000)]
        tac = clock_rows(T, halves_tac, phase=7, unread={3, 4, 5, 90})
        # broadcast: content of tactical frame b + 1000 in half 1 and b + 3500 in half 2
        bro = [dict(r) for r in clock_rows(T, [(-1000, 24000), (26500, 51500)], phase=60, misread={11})]
        lags, rep = half_lags(tac, bro, 25.0, [(1, 0, 24999), (2, 30000, 54999)])
        self.assertLessEqual(abs(lags[1] - 1000), 25)
        self.assertLessEqual(abs(lags[2] - 3500), 25)

    def test_ambiguous_added_time_is_not_anchored(self):
        # first half lasts 47 min (clock up to 46:59), second half starts again at 45:00: 45:00-46:59 occurs twice
        halves = [(0, 70500), (75000, 145000)]
        tac = clock_rows(150000, halves, phase=3)
        bro = clock_rows(150000, [(a - 500, e - 500) for a, e in halves], phase=50)
        frames = np.array([round(tt * 25) for tt, _ in clock_anchors(tac, bro)])
        self.assertGreater(len(frames), 500)
        ambiguous = ((frames >= 67500) & (frames < 70500)) | ((frames >= 75000) & (frames < 78000))
        self.assertFalse(ambiguous.any())
        lags = np.array([round(25 * (tt - bt)) for tt, bt in clock_anchors(tac, bro)])
        self.assertLessEqual(np.max(np.abs(lags - 500)), 25)


def _write_epts(folder, stem, players, ball, team, pitch=(105.0, 68.0)):
    folder.mkdir(parents=True, exist_ok=True)
    P, B = players / np.array(pitch), ball / np.array(pitch)
    (folder / f'{stem}_atd.xml').write_text(
        '<main><FrameRate>25</FrameRate><FieldSize><Width>105</Width><Height>68</Height></FieldSize>'
        '<Team id="h"/><Team id="a"/>' + ''.join(f'<Player teamId="{"ha"[t]}"/>' for t in team) + '</main>')
    lines = []
    for i in range(len(B)):
        groups = ';'.join('NaN,NaN,0' if not np.isfinite(P[i, j]).all() else f'{P[i, j, 0]:.5f},{P[i, j, 1]:.5f},1.0'
                          for j in range(P.shape[1]))
        b = 'NaN,NaN,NaN' if not np.isfinite(B[i]).all() else f'{B[i, 0]:.5f},{B[i, 1]:.5f},2.0'
        lines.append(f'{i + 1}:{groups}:{b}')
    (folder / f'{stem}_atd.txt').write_text('\n'.join(lines) + '\n')


def _write_homography(path, n, valid):
    rows = ['frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid']
    rows += [f'{i},1,0,0,0,1,0,0,0,1,0.5,{int(valid[i])}' for i in range(n)]
    path.write_text('\n'.join(rows) + '\n')


def bundle_with_broadcast(root, n=9000, lag=400, gap_frac=0.4, seed=11):
    """Tactical tracking with ball gaps; broadcast = the same match seen from frame `lag` on, ball complete."""
    rng = np.random.default_rng(seed)
    s = 10
    v = np.zeros((n + lag, s, 2)); e = rng.normal(0, 0.02, (n + lag, s, 2))
    for t in range(1, n + lag):
        v[t] = 0.98 * v[t - 1] + e[t]
    P = np.array([52.0, 34.0]) + rng.uniform(-25, 25, (1, s, 2)) + np.cumsum(v, 0)
    P = np.clip(P, 1, 104)
    owner = np.repeat(rng.integers(0, s, (n + lag) // 200 + 1), 200)[:n + lag]
    ball = P[np.arange(n + lag), owner] + 0.4
    team = np.r_[np.zeros(s // 2), np.ones(s - s // 2)].astype(np.int8)
    tb = ball[:n].copy()
    tb[np.repeat(rng.random(n // 100 + 1) < gap_frac, 100)[:n]] = np.nan
    _write_epts(root / 'tactical', 'SYN_tactical', P[:n], tb, team)
    B = n - lag
    _write_epts(root / 'broadcast', 'SYN_broadcast', P[lag:lag + B], ball[lag:lag + B], team)
    _write_homography(root / 'broadcast' / 'SYN_broadcast_homography.csv', B, np.ones(B, bool))
    return root


try:  # the entry points need scipy and pandas (requirements-possession.txt)
    from possession import run24 as _run24, run25 as _run25      # noqa: F401
    HAVE_RUN = True
except ImportError:
    HAVE_RUN = False


@unittest.skipUnless(HAVE_RUN, 'possession dependencies not installed')
class Run25Tests(unittest.TestCase):
    def test_run25_without_broadcast_equals_run24_and_with_an_accurate_broadcast_fills_gaps(self):
        from possession import run24, run25, validate
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = bundle_with_broadcast(root / 'b', n=9000, lag=0)
            halves = [(1, 0, 4499), (2, 4500, 8999)]
            r25 = run25.run(data, root / 'o25', game='SYN', halves=halves, release=None)
            self.assertTrue(r25['broadcast_fill_used'])
            self.assertGreater(r25['fusion']['ball_visible_graded_after'], r25['fusion']['ball_visible_graded_before'])
            ok, info = validate.check(root / 'o25' / 'submission.csv', rows=9000)
            self.assertTrue(ok, info)
            import shutil
            shutil.rmtree(data / 'broadcast')
            r25b = run25.run(data, root / 'o25b', game='SYN', halves=halves, release=None)
            r24 = run24.run(data, root / 'o24', game='SYN', halves=halves)
            self.assertFalse(r25b['broadcast_fill_used'])
            self.assertEqual(r25b['submission_sha256'], r24['submission_sha256'])


    def test_run25_uses_the_clock_anchor_only_when_the_release_enables_it(self):
        import json
        from possession import run25
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            n, lag = 9000, 400
            data = bundle_with_broadcast(root / 'b', n=n, lag=lag)
            halves = [(1, 0, 4499), (2, 4500, 8999)]
            kick = [(0, 4500), (4500, 9000)]
            for name, rows in (('tac', clock_rows(n, kick, phase=5)),
                               ('bro', clock_rows(n - lag, [(a - lag, e - lag) for a, e in kick], phase=70))):
                (root / name).mkdir()
                (root / name / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
            saved = run25.USE_CLOCK
            try:
                run25.USE_CLOCK = False
                off = run25.run(data, root / 'o1', game='SYN', halves=halves, release=None,
                                tactical_clock=root / 'tac', broadcast_clock=root / 'bro')
                self.assertNotEqual(off['fusion'].get('alignment_mode'), 'clock')
                run25.USE_CLOCK = True
                on = run25.run(data, root / 'o2', game='SYN', halves=halves, release=None,
                               tactical_clock=root / 'tac', broadcast_clock=root / 'bro')
                self.assertEqual(on['fusion']['alignment_mode'], 'clock')
                self.assertTrue(on['broadcast_fill_used'])
            finally:
                run25.USE_CLOCK = saved


if __name__ == '__main__':
    unittest.main()
