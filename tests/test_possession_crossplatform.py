"""Does this computer reproduce the recorded bytes of the release pipeline? (synthetic bundle; no match data)

SUBMISSION.md asks that the public repository regenerates the submitted file, and the organisers may
run it on their own machine. Floating-point libraries differ between operating systems and numpy
builds, so this module runs the entry points of the first two steps of the technical ladder on
deterministic synthetic bundles and compares the SHA-256 of every produced file with the values
recorded on Linux x86-64 under Python 3.10 / numpy 1.26.4 (requirements-possession.txt) and under
Python 3.13 / numpy 2.5.3:
  possession.run29.run   five variants: both model paths, with and without the broadcast camera, with
                         and without the clock anchor (the code that possession.run211 shares);
  possession.run211.run  two variants on a bundle whose goalkeeper tracks carry the other team's id,
                         so that the goalkeeper team correction (possession/keeper2.py) moves tracks:
                         v2.1 path with broadcast and clock, v2.3 path with the tactical camera only.

A difference is not an accuracy statement. It says that this platform does not reproduce the recorded
bytes; the platform, Python and numpy versions that produced the submitted file must then be written
into the technical document. When the synthetic input itself differs (random generator), nothing can
be concluded and the test is skipped.

    python -m tests.test_possession_crossplatform --status     # prints SAME, DIFFERENT or INPUT_DIFFERS
"""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
try:
    from possession import run29, run211
    from tests.test_possession_v25 import _write_epts, _write_homography, clock_rows
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

N, LAG, HALVES = 9000, 400, [(1, 0, 4499), (2, 4500, 8999)]
KEEPER_N, KEEPER_HALVES = 15000, [(1, 0, 7499), (2, 7500, 14999)]      # long enough for the whole-half rule of the correction
# Recorded 2026-11-11 on Linux x86-64; identical under Python 3.10.20 and 3.12.3 with numpy 1.26.4 and under Python 3.13.18 / numpy 2.5.3.
# 'input' and the five possession.run29 values are unchanged since their first recording; 'input_keepers' covers the two goalkeeper bundles.
EXPECTED = {
    'input': '91996a46b7ec006bf956b53276788e0a8e00e4dc0e15b6e47f20a279976a5ec9',
    'input_keepers': '802cb77f5a79c7eab32406acf7b4c323ea53aba06641c0b980f00a6edf63f449',
    'runs': {
        'clean_clock': {'sha256': '4076554ee2db1ddeb51336a10820b266fbb6a1c60681d096eddf984a5bb3f8b6',
                        'path': 'v2.1', 'fill': True, 'mode': 'clock'},
        'clean_tracking': {'sha256': '4d2d56291d685c3070756db6df0036d6f5960d9d959d8939351074378c24a6e7',
                           'path': 'v2.1', 'fill': True, 'mode': 'tracking'},
        'noisy_clock': {'sha256': 'fe87161998b76804cc6d743acfa95e338581aba9a927d7fb39f981d0ff38f5bc',
                        'path': 'v2.3', 'fill': True, 'mode': 'clock'},
        'clean_tactical_only': {'sha256': 'f4b3dbd789c022b3478dc4db0d53eeb37ce6b11e742461c2f3dbc0e804c801f1',
                                'path': 'v2.1', 'fill': False, 'mode': None},
        'noisy_tactical_only': {'sha256': '9b39402e191465bdc9cedc16aba754f0e5284641cfba8cea847eae58a38de07e',
                                'path': 'v2.3', 'fill': False, 'mode': None},
        'keepers_clock': {'sha256': '8172eade06d275576231d462b64fca35992642c78a561c379efe12f2a72c7f34',
                          'path': 'v2.1', 'fill': True, 'mode': 'clock', 'moved_pieces': 4},
        'keepers_noisy_tactical_only': {'sha256': 'cc6305dd20944414cc8350930a69d0cefdc57fc860410d011d7209b634d18dfd',
                                        'path': 'v2.3', 'fill': False, 'mode': None, 'moved_pieces': 11},
    },
}


def bundle(root, player_noise=0.0, seed=29):
    """Tactical tracking with ball gaps and optional player jitter; broadcast = the same match from frame LAG on,
    shifted by a slowly changing calibration error; clock readings of both videos."""
    rng = np.random.default_rng(seed)
    s, T = 10, N + LAG
    v = np.zeros((T, s, 2)); e = rng.normal(0, 0.02, (T, s, 2))
    for t in range(1, T):
        v[t] = 0.98 * v[t - 1] + e[t]
    P = np.clip(np.array([52.0, 34.0]) + rng.uniform(-25, 25, (1, s, 2)) + np.cumsum(v, 0), 1, 104)
    owner = np.repeat(rng.integers(0, s, T // 200 + 1), 200)[:T]
    ball = P[np.arange(T), owner] + 0.4
    team = np.r_[np.zeros(s // 2), np.ones(s - s // 2)].astype(np.int8)
    tb = ball[:N].copy()
    tb[np.repeat(rng.random(N // 100 + 1) < 0.4, 100)[:N]] = np.nan
    tp = P[:N] + rng.normal(0, player_noise, (N, s, 2)) if player_noise else P[:N]
    _write_epts(root / 'tactical', 'SYN_tactical', tp, tb, team)
    B = N - LAG
    drift = 0.3 * np.cumsum(rng.normal(0, 0.01, (B, 1, 2)), 0) + np.array([0.35, -0.25])   # calibration error
    _write_epts(root / 'broadcast', 'SYN_broadcast', P[LAG:LAG + B] + drift, ball[LAG:LAG + B] + drift[:, 0], team)
    _write_homography(root / 'broadcast' / 'SYN_broadcast_homography.csv', B, np.ones(B, bool))
    kick = [(0, 4500), (4500, 9000)]
    for name, rows in (('clock-tactical', clock_rows(N, kick, phase=5)),
                       ('clock-broadcast', clock_rows(B, [(a - LAG, b - LAG) for a, b in kick], phase=70))):
        (root / name).mkdir()
        (root / name / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    return root


def keeper_bundle(root, player_noise=0.0, seed=31):
    """22 tracks: outfield players around a centre of play that wanders between the two ends and one goalkeeper per
    goal whose track carries the other team's id; the teams change ends at half-time. Ball, broadcast stream and
    clock readings as in bundle()."""
    rng = np.random.default_rng(seed)
    N, half = KEEPER_N, KEEPER_HALVES[1][1]
    T, L, W = N + LAG, 105.0, 68.0
    e = rng.normal(0, 0.02, (T, 23, 2))
    e[:, 22] *= 0.5                                     # the centre of play moves more slowly than a player
    keep = np.r_[np.full(22, 0.99), 0.998][:, None]
    v = np.zeros((T, 23, 2)); x = np.zeros((T, 23, 2))
    for t in range(1, T):
        v[t] = 0.98 * v[t - 1] + e[t]                   # smooth speeds
        x[t] = keep * x[t - 1] + v[t]                   # positions that return to their place
    play = np.clip(52.5 + 2.5 * x[:, 22, 0], 22.0, 83.0)
    first = np.arange(T) < half                         # tactical frames of the first half
    P = np.zeros((T, 22, 2))
    spot = rng.uniform(-14, 14, (22, 2))
    for k in (0, 1):
        left = first if k == 0 else ~first              # frames in which this team defends the left goal
        for i in range(1, 11):
            c = 11 * k + i
            P[:, c, 0] = np.clip(play + spot[c, 0] + np.where(left, -6.0, 6.0) + x[:, c, 0], 16.0, L - 16.0)
            P[:, c, 1] = np.clip(34.0 + 1.6 * spot[c, 1] + x[:, c, 1], 1.0, W - 1.0)
        depth = 6.0 + 0.12 * np.where(left, play, L - play)                  # the goalkeeper comes out when play is far away
        P[:, 11 * k, 0] = np.where(left, depth, L - depth) + 0.2 * x[:, 11 * k, 0]
        P[:, 11 * k, 1] = 34.0 + 0.4 * x[:, 11 * k, 1]
    owner = np.repeat(rng.integers(0, 22, T // 200 + 1), 200)[:T]
    ball = P[np.arange(T), owner] + 0.4
    team = np.r_[np.zeros(11), np.ones(11)].astype(np.int8)
    team[0], team[11] = 1, 0                                                 # both goalkeepers under the other id
    tb = ball[:N].copy()
    tb[np.repeat(rng.random(N // 100 + 1) < 0.4, 100)[:N]] = np.nan
    tp = P[:N] + rng.normal(0, player_noise, (N, 22, 2)) if player_noise else P[:N]
    _write_epts(root / 'tactical', 'SYN_tactical', tp, tb, team)
    B = N - LAG
    drift = 0.3 * np.cumsum(rng.normal(0, 0.01, (B, 1, 2)), 0) + np.array([0.35, -0.25])
    _write_epts(root / 'broadcast', 'SYN_broadcast', P[LAG:LAG + B] + drift, ball[LAG:LAG + B] + drift[:, 0], team)
    _write_homography(root / 'broadcast' / 'SYN_broadcast_homography.csv', B, np.ones(B, bool))
    kick = [(0, half), (half, N)]
    for name, rows in (('clock-tactical', clock_rows(N, kick, phase=5)),
                       ('clock-broadcast', clock_rows(B, [(a - LAG, b - LAG) for a, b in kick], phase=70))):
        (root / name).mkdir()
        (root / name / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    return root


def digest(root):
    """SHA-256 of every file below root (names and text content; line endings normalised)."""
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob('*')):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode() + b'\0')
            h.update(p.read_text(encoding='utf-8').replace('\r\n', '\n').encode() + b'\0')
    return h.hexdigest()


def produce(work):
    """{'input': digest, 'input_keepers': digest, 'runs': {variant: {'sha256', 'path', 'fill', 'mode'[, 'moved_pieces']}}}
    for this computer."""
    work = Path(work)
    out = {'runs': {}}
    clean, noisy = bundle(work / 'clean'), bundle(work / 'noisy', player_noise=0.45)
    keepers, keepers_noisy = keeper_bundle(work / 'keepers'), keeper_bundle(work / 'keepers-noisy', player_noise=0.45)
    out['input'] = hashlib.sha256((digest(clean) + digest(noisy)).encode()).hexdigest()
    out['input_keepers'] = hashlib.sha256((digest(keepers) + digest(keepers_noisy)).encode()).hexdigest()

    def one(name, data, clock, entry=run29, halves=HALVES):
        kw = dict(tactical_clock=data / 'clock-tactical', broadcast_clock=data / 'clock-broadcast') if clock else {}
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            r = entry.run(data, work / ('out-' + name), game='SYN', halves=halves, release=None, **kw)
        out['runs'][name] = {'sha256': r['submission_sha256'], 'path': r['path'], 'fill': bool(r['broadcast_fill_used']),
                             'mode': r['fusion'].get('alignment_mode')}
        if entry is run211:
            out['runs'][name]['moved_pieces'] = int(r['goalkeeper_correction']['moved_pieces'])
    one('clean_clock', clean, True)
    one('clean_tracking', clean, False)
    one('noisy_clock', noisy, True)
    shutil.rmtree(clean / 'broadcast'); shutil.rmtree(noisy / 'broadcast')
    one('clean_tactical_only', clean, False)
    one('noisy_tactical_only', noisy, False)
    one('keepers_clock', keepers, True, run211, KEEPER_HALVES)
    shutil.rmtree(keepers_noisy / 'broadcast')
    one('keepers_noisy_tactical_only', keepers_noisy, False, run211, KEEPER_HALVES)
    return out


def status(got=None):
    """('SAME' | 'DIFFERENT' | 'INPUT_DIFFERS', names): the variants that differ, or for INPUT_DIFFERS ['keepers'] when
    only the goalkeeper bundles differ as input and the other variants give the recorded bytes."""
    if got is None:
        with tempfile.TemporaryDirectory() as d:
            got = produce(d)
    if got['input'] != EXPECTED['input']:
        return 'INPUT_DIFFERS', []
    names = comparable(got)
    bad = sorted(k for k in names if got['runs'].get(k) != EXPECTED['runs'][k])
    if bad:
        return 'DIFFERENT', bad
    return ('SAME', []) if len(names) == len(EXPECTED['runs']) else ('INPUT_DIFFERS', ['keepers'])


def comparable(got):
    """Variants whose synthetic input equals the recorded one on this computer."""
    same = got.get('input_keepers') == EXPECTED['input_keepers']
    return [k for k in EXPECTED['runs'] if same or not k.startswith('keepers')]


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class CrossPlatformTests(unittest.TestCase):
    def test_release_pipeline_reproduces_the_recorded_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            got = produce(d)
        if got['input'] != EXPECTED['input']:
            self.skipTest('the synthetic input differs on this platform; no conclusion')
        names = comparable(got)
        self.assertEqual({k: got['runs'][k]['path'] for k in names},
                         {k: EXPECTED['runs'][k]['path'] for k in names})              # both model paths are exercised
        self.assertTrue(all(v['moved_pieces'] > 0 for v in EXPECTED['runs'].values() if 'moved_pieces' in v))   # the correction is exercised
        self.assertEqual({k: got['runs'][k] for k in names}, {k: EXPECTED['runs'][k] for k in names})
        if len(names) < len(EXPECTED['runs']):
            self.skipTest('the synthetic goalkeeper bundles differ on this platform; the other variants give the recorded bytes')


if __name__ == '__main__':
    if '--status' in sys.argv:
        word, bad = status()
        print(word + (' ' + ' '.join(bad) if bad else ''))
        sys.exit(0 if word == 'SAME' else 2 if word == 'DIFFERENT' else 3)
    if '--record' in sys.argv:
        with tempfile.TemporaryDirectory() as d:
            print(json.dumps(produce(d), indent=1))
        sys.exit(0)
    unittest.main()
