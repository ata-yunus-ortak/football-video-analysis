"""Generate the competition submission with possession v2.5 (v2.4 + gated broadcast ball fill).

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run25 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <clock observations dir> --broadcast-clock <clock observations dir>]

Steps: (1) read the tactical ATD; (2) measure its position noise and choose the v2.1 or v2.3 path exactly
as possession.run24 (on the raw tactical tracking); (3) read the broadcast ATD and homography validity,
align the broadcast frames to the tactical timeline (anchored on the on-screen clock when automatic clock
observations of both videos are given, tools/possession_clock.py; otherwise from the tracking alone);
(4) only if the two cameras agree closely where both see the ball (median distance <= 0.50 m), fill the
missing tactical ball positions with the aligned broadcast ball; (5) run the chosen path. Without
broadcast files, or when the gate is closed, the output equals possession.run24. run.json records
every decision (aggregates only).
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
from .run24 import V21_MODEL, V23_MODEL, V21_SHA256, SOURCES as V24_SOURCES, _check_sources

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'possession-v25-release.json'
SOURCES = V24_SOURCES + ('broadcast.py', 'fusion.py', 'clocksync.py', 'run25.py')
USE_CLOCK = True   # frozen: the clock-anchored alignment (v2.5b) was selected


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


def _clock_file(p):
    p = Path(p)
    return p / 'observations.jsonl' if p.is_dir() else p


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
    halves = halves or ORGANISER_HALVES.get((game, n))
    if halves:
        for h, a, b in halves:
            period[a:b + 1] = h
        period_source = 'organiser games.half_video_blocks'
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
        filled_ball, frep = fuse_gated(match['ball'], bro2['ball'], t_of_b, match['fps'], graded)
        fusion = dict(frep, alignment_mode=arep['mode'], alignment=arep['align'], orientation=arep['orient'],
                      clock=crep, threshold_median_m=GATE_MEDIAN_M,
                      broadcast_input_sha256={'atd_meta': sha256(bmeta), 'atd_raw': sha256(braw), 'homography': sha256(bhom)})
        if frep['used']:
            match = dict(match, ball=filled_ball)
    else:
        fusion['reason'] = 'broadcast ATD/homography not found'
    if path == 'v2.3':
        bundle = b23
        labels, _, _ = predict_labels(smooth_positions(match, half), b23)
    else:
        bundle = b21
        labels, _, _ = predict_labels(match, b21)
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
    report = {'rows': n, 'system': 'possession-v2.5 (noise-gated v2.1 / v2.3 + gated broadcast ball fill)',
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
