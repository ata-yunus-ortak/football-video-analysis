"""Generate the competition submission with possession v2.4 (noise-gated v2.1 / v2.3).

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run24 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir

Reads only data/tactical/BAR-ATH_tactical_atd.xml and _atd.txt. The high-frequency position noise of the
tracking is measured inside the graded halves (possession/noise.py). If neither the player nor the ball
noise exceeds 0.30 m (the largest noise the v2.1 models saw in training), the frozen v2.1 system runs
unchanged (same output as python -m possession.run). Otherwise positions are smoothed over +-2 frames and the v2.3
models (trained with wider noise) are used. The gate uses no label, video or ground truth; run.json
records the measured noise and the path taken.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .data import read_epts
from .bundle import load as load_bundle
from .pipeline import predict_labels
from .features import play_blocks
from .smooth import smooth_positions
from .noise import estimate_noise, choose_path, THRESHOLD_M
from .run import sha256, detect_periods, home_index, ORGANISER_HALVES, ORGANISER_HOME, SOURCES as V21_SOURCES

HERE = Path(__file__).resolve().parent
V21_MODEL = HERE.parent / 'models' / 'possession-v2.npz'
V23_MODEL = HERE.parent / 'models' / 'possession-v23.npz'
V21_SHA256 = '1cd59ba5c21a5abc2be24f8294b3af3d61d84997b61edfc08c028384a9d550d1'
SOURCES = V21_SOURCES + ('smooth.py', 'noise.py', 'run24.py')


def _check_sources(bundle, names):
    frozen = bundle['card'].get('source_sha256', {})
    for name in names:
        if frozen and frozen.get(name) != sha256(HERE / name):
            raise ValueError(f'frozen source changed: {name}')


def run(data_dir, out, v21_model=V21_MODEL, v23_model=V23_MODEL, game='BAR-ATH', halves=None,
        expected_v21_sha256=V21_SHA256):
    b21, b23 = load_bundle(v21_model), load_bundle(v23_model)
    if expected_v21_sha256 and b21['sha256'] != expected_v21_sha256:
        raise ValueError('the v2.1 bundle is not the frozen possession-v2.npz')
    _check_sources(b21, V21_SOURCES)
    _check_sources(b23, SOURCES)
    half = int(b23['card'].get('smooth_half', 0))
    if half <= 0:
        raise ValueError('the v2.3 bundle card has no smooth_half')
    tactical = Path(data_dir) / 'tactical'
    meta, raw = tactical / f'{game}_tactical_atd.xml', tactical / f'{game}_tactical_atd.txt'
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
    noise = estimate_noise(match)
    path, trigger = choose_path(noise)
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
    graded = period > 0
    spells = 0
    for a, b in play_blocks(period):
        seg = labels[a:b]
        brk = np.r_[True, seg[1:] != seg[:-1]]
        spells += int(np.sum(brk & np.isin(seg, ('H', 'A'))))
    report = {'rows': n, 'system': 'possession-v2.4 (noise-gated)', 'path': path,
              'gate': {'measured_noise': {k: (v if np.isfinite(v) else None) for k, v in noise.items()},
                       'threshold_m': THRESHOLD_M, 'triggered_by': trigger,
                       'rule': 'v2.3 path if players_m or ball_m > threshold, else v2.1'},
              'model_sha256': bundle['sha256'], 'model_version': bundle['card'].get('version'),
              'bundles_sha256': {'v2.1': b21['sha256'], 'v2.3': b23['sha256']},
              'input_sha256': {'atd_meta': sha256(meta), 'atd_raw': sha256(raw)},
              'source_sha256': {name: sha256(HERE / name) for name in SOURCES},
              'period_source': period_source,
              'teams': {'home': info['team_names'][home], 'away': info['team_names'][1 - home],
                        'home_rule': home_rule, 'track_slots': info['slots'],
                        'slots_without_team': info['slots_without_team'], 'slot_layout': info['layout'],
                        'format_specifications': info['format_specifications']},
              'label_counts_in_play_blocks': {k: int(np.sum(labels[graded] == k)) for k in 'HADX'},
              'possession_spells_in_play_blocks': spells, 'submission_sha256': sha256(csv_path),
              'inputs_used': ['tactical ATD metadata', 'tactical ATD raw positions'],
              'not_used': ['video', 'broadcast', 'homography', 'smart tagging', 'ground truth', 'public window'],
              'output': str(csv_path)}
    (target / 'run.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('rows', 'system', 'path', 'model_version', 'teams',
                                             'label_counts_in_play_blocks', 'possession_spells_in_play_blocks',
                                             'submission_sha256')}, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--data-dir', required=True, help='folder containing tactical/BAR-ATH_tactical_atd.*')
    p.add_argument('--out', required=True, help='new output folder (must not exist)')
    a = p.parse_args()
    run(a.data_dir, a.out)
