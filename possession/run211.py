"""Generate the competition submission with possession v2.11.

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run211 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <clock observations dir> --broadcast-clock <clock observations dir>]

v2.11 = v2.9 with one safeguard. An automatic tracker decides the team of a track from the kit, and a
goalkeeper wears another kit than his team-mates. Before the features are computed, goalkeeper track
pieces that sit in a slot of the team that does not defend their goal are moved to the defending team
(possession/keeper2.py; positions and track continuity only). When nothing is moved the output is the
output of possession.run29. The noise gate, the broadcast alignment, the registration and the 0.50 m
gate use the tracking as given, exactly as in v2.9; only the models see the corrected ids. Selected on
external matches with simulated goalkeeper errors and a simulated camera that does not always show the
far goalkeeper (possession-v211-plan.json); whether the provided tracking has such errors was not
looked at. run.json records what was moved (aggregates only).
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
from .features import play_blocks
from .smooth import smooth_positions
from .noise import estimate_noise, choose_path, THRESHOLD_M
from .fusion import align_auto, fuse_gated, GATE_MEDIAN_M
from .clocksync import read_observations, half_lags
from . import broadcast as bc
from .run import sha256, detect_periods, home_index, ORGANISER_HALVES, ORGANISER_HOME, SOURCES as V21_SOURCES
from .register import register_ball
from .keeper2 import correct_goalkeepers
from .run24 import V21_MODEL, V23_MODEL, V21_SHA256, SOURCES as V24_SOURCES, _check_sources
from .run29 import ORGANISER_PLAY_HALVES, ORGANISER_DEAD_LEADIN, USE_CLOCK, _clock_file, SOURCES as V29_SOURCES

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'possession-v211-release.json'
SOURCES = V29_SOURCES + ('keeper2.py', 'run211.py')


def check_release(path=RELEASE):
    """Every source and both bundles must match the frozen release manifest."""
    rel = json.loads(Path(path).read_text(encoding='utf-8'))
    for name in SOURCES:
        if rel['source_sha256'].get(name) != sha256(HERE / name):
            raise ValueError(f'frozen source changed: {name}')
    for key, model in (('v2.1', V21_MODEL), ('v2.3', V23_MODEL)):
        if rel['bundle_sha256'][key] != sha256(model):
            raise ValueError(f'frozen bundle changed: {key}')
    return rel


def run(data_dir, out, game='BAR-ATH', halves=None, tactical_clock=None, broadcast_clock=None,
        v21_model=V21_MODEL, v23_model=V23_MODEL, release=RELEASE):
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
    halves = halves or ORGANISER_PLAY_HALVES.get((game, n)) or ORGANISER_HALVES.get((game, n))
    if halves:
        for h, a, b in halves:
            period[a:b + 1] = h
        period_source = 'organiser graded windows; second-half play starts at the kick-off frame published in FAQ.md'
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
        labels, _, _ = predict_labels(smooth_positions(model_input, half), b23)
    else:
        bundle = b21
        labels, _, _ = predict_labels(model_input, b21)
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
    report = {'rows': n, 'system': 'possession-v2.11 (v2.9 + goalkeeper team correction)',
              'goalkeeper_correction': keeper,
              'dead_leadin_frames': [list(x) for x in ORGANISER_DEAD_LEADIN.get((game, n), [])],
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
                              'broadcast homography validity flags (if present)', 'automatic clock readings (if given)'],
              'not_used': ['tactical video pixels beyond the clock readings', 'smart tagging', 'ground truth', 'public window'],
              'output': str(csv_path)}
    (target / 'run.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
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
