"""Generate the competition submission with possession v2.15.

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run215 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <clock observations dir> --broadcast-clock <clock observations dir>]

v2.15 is possession.run211 with three changes; every other line of run() below is the v2.11 flow.
1. Play blocks: the organisers' graded windows only, as in possession.run211g. The kick-off frame
   published in FAQ.md is not used; the models run on the whole graded second half.
2. A second model family. On the v2.1 path (measured noise at most 0.30 m) the second-stage
   probabilities of the v2 models are pooled (possession/pooling.py) with the probabilities of a temporal
   convolution network (possession/tcn/, models/possession-tcn-v215.npz), and the pooled P(dead) and
   P(home | alive) go through the unchanged v2 decoder with the constants of the bundle. The network
   reads the tracking the v2 models see (after the goalkeeper team check, with the filled ball when the
   0.50 m gate opened), in metres from the pitch centre. On the v2.3 path (noisier tracking) nothing is
   pooled: the pooling was not measured there, and the output is that of possession.run211k.
   The network's architecture, features and NumPy inference were written by a team member (branch
   mtah-possession, commit 167dc7b); its three weight sets were trained for this release on the six open
   DFL matches the v2 models are trained on (CC BY 4.0), corrupted by both simulators of the team.
   Selected on external matches against gates registered beforehand (possession-v215-plan.json,
   possession-v215-results.json); two earlier ways of adding this model failed their gates and are
   not used (possession-v213-*, possession-v214-*).
3. After that: the Smart Tagging kick-off rule of possession/kickoff.py, as in possession.run211k (frames
   of a graded block before its first automatic "Kick Off (Start)" tag are written D).
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from .data import read_epts
from .bundle import load as load_bundle
from .pipeline import predict_labels
from .decode import emissions, decode_blocks
from .features import play_blocks
from .smooth import smooth_positions
from .noise import estimate_noise, choose_path, THRESHOLD_M
from .fusion import align_auto, fuse_gated, GATE_MEDIAN_M
from .clocksync import read_observations, half_lags
from . import broadcast as bc
from .run import sha256, detect_periods, home_index, ORGANISER_HALVES, ORGANISER_HOME, SOURCES as V21_SOURCES
from . import run211, run211k, kickoff, pooling
from .tcn import infer as tcn_infer, decode as tcn_decode
from .register import register_ball
from .keeper2 import correct_goalkeepers
from .run24 import V21_MODEL, V23_MODEL, V21_SHA256, SOURCES as V24_SOURCES, _check_sources
from .run29 import USE_CLOCK, _clock_file

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'possession-v215-release.json'
TCN_MODEL = HERE.parent / 'models' / 'possession-tcn-v215.npz'
TCN_SOURCES = ('tcn/__init__.py', 'tcn/infer.py', 'tcn/features.py', 'tcn/decode.py')
SOURCES = run211.SOURCES + TCN_SOURCES + ('pooling.py', 'kickoff.py', 'run211g.py', 'run211k.py', 'run215.py')
FUSED_PATH = 'v2.1'            # the only path on which the pooling was measured


def check_release(path=RELEASE):
    """Every source and both bundles must match the frozen release manifest."""
    rel = json.loads(Path(path).read_text(encoding='utf-8'))
    for name in SOURCES:
        if rel['source_sha256'].get(name) != sha256(HERE / name):
            raise ValueError(f'frozen source changed: {name}')
    for key, model in (('v2.1', V21_MODEL), ('v2.3', V23_MODEL), ('tcn', TCN_MODEL)):
        if rel['bundle_sha256'][key] != sha256(model):
            raise ValueError(f'frozen bundle changed: {key}')
    return rel


def tcn_arrays(m, a, b):
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
        v21_model=V21_MODEL, v23_model=V23_MODEL, tcn_model=TCN_MODEL, release=RELEASE, pooled=True):
    rel = check_release(release) if release else None
    b21, b23 = load_bundle(v21_model), load_bundle(v23_model)
    if release and b21['sha256'] != V21_SHA256:
        raise ValueError('the v2.1 bundle is not the frozen possession-v2.npz')
    _check_sources(b21, V21_SOURCES)
    _check_sources(b23, V24_SOURCES)
    half = int(b23['card'].get('smooth_half', 0))
    if half <= 0:
        raise ValueError('the v2.3 bundle card has no smooth_half')
    root = Path(data_dir)
    meta, raw = root / 'tactical' / f'{game}_tactical_atd.xml', root / 'tactical' / f'{game}_tactical_atd.txt'
    match, info = read_epts(meta, raw)
    n = len(match['ball'])
    if match['first_frame_id'] != 1:
        raise ValueError('ATD frame ids must start at 1 (video_frame = frame_id - 1)')
    home, home_rule = home_index(info['team_names'], ORGANISER_HOME.get(game))
    if home == 1:
        match['team'] = (1 - match['team']).astype(np.int8)
    period = np.zeros(n, np.int8)
    halves = halves or ORGANISER_HALVES.get((game, n))                      # change 1: graded windows only
    if halves:
        for h, a, b in halves:
            period[a:b + 1] = h
        period_source = ('organiser graded windows (games.half_video_blocks); the models run on the whole graded second half; '
                         'frames before a usable Smart Tagging kick-off tag are then written D')
    else:
        period = detect_periods(match)
        period_source = 'automatic tracking-density detection'
        if not period.any():
            period[:] = 1
            period_source = 'whole recording (no play blocks detected)'
    match['period'] = period
    graded = period > 0
    blocks = [(k + 1, a, b - 1) for k, (a, b) in enumerate(play_blocks(period))]
    noise = estimate_noise(match)                    # on the raw tactical tracking, before any fill
    path, trigger = choose_path(noise)
    model_input, keeper = correct_goalkeepers(match)  # team ids as the models see them; everything below up to the fill uses the ids as given
    # --- broadcast fill
    fusion = {'used': False}
    bdir = root / 'broadcast'
    bmeta, braw = bdir / f'{game}_broadcast_atd.xml', bdir / f'{game}_broadcast_atd.txt'
    bhom = bdir / f'{game}_broadcast_homography.csv'
    if bmeta.exists() and braw.exists() and bhom.exists():
        bro, binfo = read_epts(bmeta, braw)
        if bro['first_frame_id'] != 1:
            raise ValueError('broadcast ATD frame ids must start at 1')
        valid, _ = bc.read_homography(bhom, len(bro['ball']))
        lags, crep = ({}, {'status': 'no clock observations given'})
        if (tactical_clock or broadcast_clock) and not USE_CLOCK:
            crep = {'status': 'clock observations ignored: the clock anchor is not part of this release'}
        elif tactical_clock and broadcast_clock:
            lags, crep = half_lags(read_observations(_clock_file(tactical_clock)),
                                   read_observations(_clock_file(broadcast_clock)), match['fps'], blocks)
        bro2, t_of_b, arep = align_auto(match, bro, valid, match['fps'], match['pitch'], blocks, clock_lags=lags)
        reg_ball, rrep = register_ball(bro2, match, t_of_b, match['fps'])
        filled_ball, frep = fuse_gated(match['ball'], reg_ball, t_of_b, match['fps'], graded)
        frep['registration'] = rrep
        fusion = dict(frep, alignment_mode=arep['mode'], alignment=arep['align'], orientation=arep['orient'],
                      clock=crep, threshold_median_m=GATE_MEDIAN_M,
                      broadcast_input_sha256={'atd_meta': sha256(bmeta), 'atd_raw': sha256(braw), 'homography': sha256(bhom)})
        if frep['used']:
            model_input = dict(model_input, ball=filled_ball)
    else:
        fusion['reason'] = 'broadcast ATD/homography not found'
    if path == 'v2.3':
        bundle = b23
        labels, p_dead, p_home = predict_labels(smooth_positions(model_input, half), b23)
    else:
        bundle = b21
        labels, p_dead, p_home = predict_labels(model_input, b21)
    second = {'used': False, 'reason': 'switched off (test only)' if not pooled else f'the pooling is used on the {FUSED_PATH} path only'}
    if pooled and path == FUSED_PATH:                                          # change 2: the second model family
        tcn = tcn_probabilities(tcn_infer.load_weights(tcn_model), model_input, period)
        p_dead, p_home = pooling.pool(tcn, p_dead, p_home)
        labels = decode_blocks(emissions(p_dead, p_home), period, bundle['decoder'])
        second = {'used': True, 'weights_sha256': sha256(tcn_model), 'pool': pooling.POOL, 'weight': pooling.WEIGHT}
    target = Path(out)
    target.mkdir(parents=True, exist_ok=False)
    csv_path = target / 'submission.csv'
    with open(csv_path, 'x', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['frame', 'label'])
        w.writerows(zip(range(n), labels.tolist()))
    spells = 0
    for a, b in play_blocks(period):
        seg = labels[a:b]
        brk = np.r_[True, seg[1:] != seg[:-1]]
        spells += int(np.sum(brk & np.isin(seg, ('H', 'A'))))
    report = {'rows': n, 'system': ('possession-v2.15 (v2.11 on the graded windows; on the v2.1 path its probabilities are pooled with a '
                                    'temporal convolution network before the v2 decoder; Smart Tagging kick-off rule)'),
              'second_model': second,
              'goalkeeper_correction': keeper,
              'dead_leadin_frames': [],
              'path': path, 'broadcast_fill_used': bool(fusion.get('used')),
              'gate': {'measured_noise': {k: (v if not isinstance(v, float) or np.isfinite(v) else None) for k, v in noise.items()},
                       'threshold_m': THRESHOLD_M, 'triggered_by': trigger},
              'fusion': fusion, 'model_sha256': bundle['sha256'], 'model_version': bundle['card'].get('version'),
              'release_manifest_sha256': hashlib.sha256(Path(release).read_bytes()).hexdigest() if release else None,
              'input_sha256': {'atd_meta': sha256(meta), 'atd_raw': sha256(raw)},
              'source_sha256': {name: sha256(HERE / name) for name in SOURCES},
              'period_source': period_source,
              'teams': {'home': info['team_names'][home], 'away': info['team_names'][1 - home], 'home_rule': home_rule,
                        'track_slots': info['slots'], 'slots_without_team': info['slots_without_team'],
                        'slot_layout': info['layout'], 'format_specifications': info['format_specifications']},
              'label_counts_in_play_blocks': {k: int(np.sum(labels[graded] == k)) for k in 'HADX'},
              'possession_spells_in_play_blocks': spells, 'submission_sha256': sha256(csv_path),
              'inputs_used': ['tactical ATD metadata', 'tactical ATD raw positions', 'broadcast ATD (if present)',
                              'broadcast homography validity flags (if present)', 'automatic clock readings (if given)',
                              'smart tagging: kick-off tags only (if present)'],
              'not_used': ['tactical video pixels beyond the clock readings', 'smart tagging other than kick-off tags', 'ground truth',
                           'public window'],
              'output': str(csv_path)}
    (target / 'run.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    if halves:                                                                 # change 3: Smart Tagging kick-off rule
        kickoff.apply_to_submission(target, root / 'tactical' / f'{game}_tactical_smart_tagging.xml',
                                    [(a, b) for _, a, b in halves], run211k.frame_rate(meta))
        report = json.loads((target / 'run.json').read_text(encoding='utf-8'))
    print(json.dumps({k: report[k] for k in ('rows', 'system', 'path', 'broadcast_fill_used', 'model_version',
                                             'label_counts_in_play_blocks', 'submission_sha256')}, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--data-dir', required=True, help='bundle root containing tactical/ and broadcast/')
    p.add_argument('--out', required=True, help='new output folder (must not exist)')
    p.add_argument('--tactical-clock', default=None, help='clock observations of the tactical video (tools/possession_clock.py)')
    p.add_argument('--broadcast-clock', default=None, help='clock observations of the broadcast video')
    a = p.parse_args()
    run(a.data_dir, a.out, tactical_clock=a.tactical_clock, broadcast_clock=a.broadcast_clock)
