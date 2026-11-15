"""Derive possession/run214.py from the frozen possession/run211.py by exact text replacements (each must match once),
so that everything not listed here is the v2.11 flow verbatim. Usage: python3 make_run214.py <out file>"""
import sys
from pathlib import Path

src = Path('/home/claude/sc/possession/run211.py').read_text(encoding='utf-8')
a = src.index('import argparse')
body = src[a:]


def rep(old, new, count=1):
    global body
    assert body.count(old) == count, (body.count(old), old[:80])
    body = body.replace(old, new)


DOC = '''"""Generate the competition submission with possession v2.14.

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run214 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <clock observations dir> --broadcast-clock <clock observations dir>]

v2.14 is possession.run211 with three changes; every other line of run() below is the v2.11 flow.
1. Play blocks: the organisers' graded windows only, as in possession.run211g. The kick-off frame
   published in FAQ.md is not used; the models run on the whole graded second half.
2. A second model family. On the v2.1 path (measured noise at most 0.30 m) the second-stage
   probabilities of the v2 models are pooled (possession/fuse2.py) with the probabilities of a temporal
   convolution network (possession/tcn/, models/possession-tcn-v214.npz), and the pooled P(dead) and
   P(home | alive) go through the unchanged v2 decoder with the constants of the bundle. The network
   reads the tracking the v2 models see (after the goalkeeper team check, with the filled ball when the
   0.50 m gate opened), in metres from the pitch centre. On the v2.3 path (noisier tracking) nothing is
   pooled: the pooling was not measured there, and the output is the v2.11g output.
   The network's architecture, features and NumPy inference were written by a team member (branch
   mtah-possession, commit 167dc7b); its three weight sets were trained for this release on the six open
   DFL matches the v2 models are trained on (CC BY 4.0), corrupted by both simulators of the team.
   Selected on external matches against gates registered beforehand (possession-v214-plan.json,
   possession-v214-results.json).
3. After that: the Smart Tagging kick-off rule of possession/kickoff.py, as in possession.run211k (frames
   of a graded block before its first automatic "Kick Off (Start)" tag are written D).
"""
'''

rep("from .pipeline import predict_labels\n",
    "from .pipeline import predict_labels\nfrom .decode import emissions, decode_blocks\n")
rep("from .run import sha256, detect_periods, home_index, ORGANISER_HALVES, ORGANISER_HOME, SOURCES as V21_SOURCES",
    "from .run import sha256, detect_periods, home_index, ORGANISER_HALVES, ORGANISER_HOME, SOURCES as V21_SOURCES\n"
    "from . import run211, run211k, kickoff, fuse2\nfrom .tcn import infer as tcn_infer, decode as tcn_decode")
rep("from .run29 import ORGANISER_PLAY_HALVES, ORGANISER_DEAD_LEADIN, USE_CLOCK, _clock_file, SOURCES as V29_SOURCES",
    "from .run29 import USE_CLOCK, _clock_file")
rep("RELEASE = HERE.parent / 'possession-v211-release.json'\nSOURCES = V29_SOURCES + ('keeper2.py', 'run211.py')",
    "RELEASE = HERE.parent / 'possession-v214-release.json'\n"
    "TCN_MODEL = HERE.parent / 'models' / 'possession-tcn-v214.npz'\n"
    "TCN_SOURCES = ('tcn/__init__.py', 'tcn/infer.py', 'tcn/features.py', 'tcn/decode.py')\n"
    "SOURCES = run211.SOURCES + TCN_SOURCES + ('fuse2.py', 'kickoff.py', 'run211g.py', 'run211k.py', 'run214.py')\n"
    "FUSED_PATH = 'v2.1'            # the only path on which the pooling was measured")
rep("    for key, model in (('v2.1', V21_MODEL), ('v2.3', V23_MODEL)):",
    "    for key, model in (('v2.1', V21_MODEL), ('v2.3', V23_MODEL), ('tcn', TCN_MODEL)):")
rep("""def run(data_dir, out, game='BAR-ATH', halves=None, tactical_clock=None, broadcast_clock=None,
        v21_model=V21_MODEL, v23_model=V23_MODEL, release=RELEASE):""",
    '''def tcn_arrays(m, a, b):
    """Frames a..b-1 as the network expects them: metres from the pitch centre, float32, NaN where missing; team 0 = home."""
    c = np.asarray(m['pitch'], np.float64) / 2.0
    team = np.asarray(m['team'])
    P = np.asarray(m['players'][a:b], np.float64)
    ball = (np.asarray(m['ball'][a:b], np.float64)[:, :2] - c).astype(np.float32)
    return ball, (P[:, team == 0] - c).astype(np.float32), (P[:, team == 1] - c).astype(np.float32)


def tcn_probabilities(members, m, period):
    """(n, 3) probabilities [home, away, dead] on the frame grid; the network runs on every play block on its own."""
    tcn = np.full((len(period), 3), 1.0 / 3.0)
    for a, b in play_blocks(period):
        prob = tcn_infer.probabilities(members, *tcn_arrays(m, a, b))
        tcn[a:b] = tcn_decode.upsample(np.asarray(prob, np.float64), tcn_infer.STRIDE, b - a)
    return tcn


def run(data_dir, out, game='BAR-ATH', halves=None, tactical_clock=None, broadcast_clock=None,
        v21_model=V21_MODEL, v23_model=V23_MODEL, tcn_model=TCN_MODEL, release=RELEASE, pooled=True):''')
rep("    halves = halves or ORGANISER_PLAY_HALVES.get((game, n)) or ORGANISER_HALVES.get((game, n))",
    "    halves = halves or ORGANISER_HALVES.get((game, n))                      # change 1: graded windows only")
rep("        period_source = 'organiser graded windows; second-half play starts at the kick-off frame published in FAQ.md'",
    "        period_source = ('organiser graded windows (games.half_video_blocks); the models run on the whole graded second half; '\n"
    "                         'frames before a usable Smart Tagging kick-off tag are then written D')")
rep("""    if path == 'v2.3':
        bundle = b23
        labels, _, _ = predict_labels(smooth_positions(model_input, half), b23)
    else:
        bundle = b21
        labels, _, _ = predict_labels(model_input, b21)
""", """    if path == 'v2.3':
        bundle = b23
        labels, p_dead, p_home = predict_labels(smooth_positions(model_input, half), b23)
    else:
        bundle = b21
        labels, p_dead, p_home = predict_labels(model_input, b21)
    second = {'used': False, 'reason': 'switched off (test only)' if not pooled else f'the pooling is used on the {FUSED_PATH} path only'}
    if pooled and path == FUSED_PATH:                                          # change 2: the second model family
        tcn = tcn_probabilities(tcn_infer.load_weights(tcn_model), model_input, period)
        p_dead, p_home = fuse2.pool(tcn, p_dead, p_home)
        labels = decode_blocks(emissions(p_dead, p_home), period, bundle['decoder'])
        second = {'used': True, 'weights_sha256': sha256(tcn_model), 'pool': fuse2.POOL, 'weight': fuse2.WEIGHT}
""")
rep("    report = {'rows': n, 'system': 'possession-v2.11 (v2.9 + goalkeeper team correction)',",
    "    report = {'rows': n, 'system': ('possession-v2.14 (v2.11 on the graded windows; on the v2.1 path its probabilities are pooled with a '\n"
    "                                    'temporal convolution network before the v2 decoder; Smart Tagging kick-off rule)'),\n"
    "              'second_model': second,")
rep("              'dead_leadin_frames': [list(x) for x in ORGANISER_DEAD_LEADIN.get((game, n), [])],",
    "              'dead_leadin_frames': [],")
rep("                              'broadcast homography validity flags (if present)', 'automatic clock readings (if given)'],",
    "                              'broadcast homography validity flags (if present)', 'automatic clock readings (if given)',\n"
    "                              'smart tagging: kick-off tags only (if present)'],")
rep("              'not_used': ['tactical video pixels beyond the clock readings', 'smart tagging', 'ground truth', 'public window'],",
    "              'not_used': ['tactical video pixels beyond the clock readings', 'smart tagging other than kick-off tags', 'ground truth',\n"
    "                           'public window'],")
rep("""    (target / 'run.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('rows', 'system', 'path', 'broadcast_fill_used', 'model_version',
                                             'label_counts_in_play_blocks', 'submission_sha256')}, indent=2))
    return report
""", """    (target / 'run.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    if halves:                                                                 # change 3: Smart Tagging kick-off rule
        kickoff.apply_to_submission(target, root / 'tactical' / f'{game}_tactical_smart_tagging.xml',
                                    [(a, b) for _, a, b in halves], run211k.frame_rate(meta))
        report = json.loads((target / 'run.json').read_text(encoding='utf-8'))
    print(json.dumps({k: report[k] for k in ('rows', 'system', 'path', 'broadcast_fill_used', 'model_version',
                                             'label_counts_in_play_blocks', 'submission_sha256')}, indent=2))
    return report
""")
Path(sys.argv[1]).write_text(DOC + body, encoding='utf-8')
print('written', sys.argv[1], len((DOC + body).splitlines()), 'lines')
