"""Generate the competition submission from the provided bundle with the frozen v2 model.

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir

Reads only data/tactical/BAR-ATH_tactical_atd.xml and _atd.txt. Writes submission.csv
(frame,label; 199319 rows) and run.json (input/model/source hashes and aggregate counts).
No video, ground truth, public window, Smart Tagging or manual file is read.
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

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE.parent / 'models' / 'possession-v2.npz'
# Graded halves published by the organisers in games.py (half_video_blocks("BAR-ATH")).
# Used only to know where play blocks are; every label inside them comes from the model.
ORGANISER_HALVES = {('BAR-ATH', 199319): [(1, 11185, 90651), (2, 110808, 190197)]}
# DATA.md: "Home is Barcelona (H), away is Athletic (A)". The EPTS convention already puts the
# home team first; the name check only guards against a reordered export.
ORGANISER_HOME = {'BAR-ATH': 'barcelona'}
SOURCES = ('data.py', 'features.py', 'trees.py', 'decode.py', 'pipeline.py', 'bundle.py', 'run.py',
           'stack.py', 'tags.py')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def detect_periods(match, min_players=16, smooth_s=10):
    """Fallback for other matches: the two longest runs with >= min_players tracked players."""
    n = len(match['ball'])
    count = np.isfinite(match['players']).all(2).sum(1).astype(float)
    k = int(smooth_s * match['fps'])
    c = np.convolve(count, np.ones(2 * k + 1) / (2 * k + 1), mode='same')
    ok = c >= min_players
    edges = np.flatnonzero(np.diff(np.r_[0, ok.astype(np.int8), 0]))
    runs = sorted(zip(edges[::2], edges[1::2]), key=lambda r: r[1] - r[0], reverse=True)[:2]
    period = np.zeros(n, np.int8)
    for i, (a, b) in enumerate(sorted(runs)):
        period[a:b] = i + 1
    return period


def home_index(names, key):
    """Index of the home team: the unique team whose name contains key, else the first Team."""
    hits = [i for i, nm in enumerate(names) if key and key in nm.lower()]
    if len(hits) == 1:
        return hits[0], f'team name contains "{key}"'
    return 0, 'metadata order (first Team = home, FIFA/EPTS convention)'


def run(data_dir, out, model=DEFAULT_MODEL, game='BAR-ATH', halves=None):
    bundle = load_bundle(model)
    frozen = bundle['card'].get('source_sha256', {})
    for name in SOURCES:
        if frozen and frozen.get(name) != sha256(HERE / name):
            raise ValueError(f'frozen source changed: {name}')
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
        for half, a, b in halves:
            period[a:b + 1] = half
        period_source = 'organiser games.half_video_blocks'
    else:
        period = detect_periods(match)
        period_source = 'automatic tracking-density detection'
        if not period.any():
            period[:] = 1
            period_source = 'whole recording (no play blocks detected)'
    match['period'] = period
    labels, p_dead, p_home = predict_labels(match, bundle)
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
    report = {'rows': n, 'model_sha256': bundle['sha256'], 'model_version': bundle['card'].get('version'),
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
    print(json.dumps({k: report[k] for k in ('rows', 'model_version', 'teams', 'label_counts_in_play_blocks',
                                             'possession_spells_in_play_blocks', 'submission_sha256')}, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--data-dir', required=True, help='folder containing tactical/BAR-ATH_tactical_atd.*')
    p.add_argument('--out', required=True, help='new output folder (must not exist)')
    p.add_argument('--model', default=str(DEFAULT_MODEL))
    a = p.parse_args()
    run(a.data_dir, a.out, a.model)
