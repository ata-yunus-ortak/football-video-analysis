"""Separate external Sportec coordinate inputs from H/A/D target attributes.

Schema references: Bassek et al. (2025), doi:10.1038/s41597-025-04505-y;
PySport/kloppy Sportec loader documentation. This is an independent streaming
adapter; no Kloppy source copied. Dataset attribution: DFL / Sportec, CC BY 4.0.
Finite provider coordinates are NOT an independent image visibility verdict.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from tools.metrica_data import external_output, sha256, verify_file


PERIODS = {'firstHalf': 1, 'secondHalf': 2}


def rows(path, match_id):
    with Path(path).open('rb') as stream:
        yield from _rows(stream, match_id)


def _rows(stream, match_id):
    context = None
    frameset = None
    for event, element in ET.iterparse(stream, events=('start', 'end')):
        if event == 'start' and element.tag == 'FrameSet':
            if element.get('MatchId') != match_id:
                raise ValueError('Wrong match in tracking frameset')
            period = PERIODS.get(element.get('GameSection'))
            obj = 'ball' if element.get('TeamId') == 'BALL' else element.get('PersonId')
            context = (period, obj)
            frameset = element
        elif event == 'end' and element.tag == 'Frame':
            if context and context[0] is not None and context[1] is not None:
                yield context[0], context[1], dict(element.attrib)
            element.clear()
            if frameset is not None:
                frameset.remove(element)
        elif event == 'end' and element.tag == 'FrameSet':
            context, frameset = None, None
            element.clear()


def convert(meta_path, tracking_path, out, expected_match):
    meta = ET.parse(meta_path).getroot().find('MatchInformation')
    if meta is None or meta.find('General').get('MatchId') != expected_match:
        raise ValueError('Wrong or missing match metadata')
    env = meta.find('Environment')
    pitch = np.array([float(env.get('PitchX')), float(env.get('PitchY'))])
    if not np.isfinite(pitch).all() or (pitch <= 0).any():
        raise ValueError('Positive pitch dimensions required')
    roster, teams = [], []
    for team in meta.findall('./Teams/Team'):
        role = team.get('Role')
        if role not in ('home', 'guest', 'away'):
            raise ValueError('Unknown team role')
        for player in team.findall('./Players/Player'):
            roster.append(player.get('PersonId'))
            teams.append(0 if role == 'home' else 1)
    if len(set(roster)) != len(roster) or None in roster or set(teams) != {0, 1}:
        raise ValueError('Unique players and two teams required')
    slots = {v: i for i, v in enumerate(roster)}
    keys = sorted({(period, int(row['N'])) for period, obj, row in rows(tracking_path, expected_match)
                   if obj == 'ball' or obj in slots})
    if not keys:
        raise ValueError('No external frames')
    index = {key: i for i, key in enumerate(keys)}
    n = len(keys)
    x = {'ball': np.full((n, 2), np.nan), 'players': np.full((n, len(roster), 2), np.nan),
         'teams': np.array(teams, np.int8), 'period': np.array([p for p, _ in keys], np.int8),
         'frame': np.arange(n), 'fps': np.array(25.), 'pitch': pitch,
         'ball_observed': np.zeros(n, bool), 'player_detected': np.zeros((n, len(roster)), bool)}
    labels = np.full(n, 'X', dtype='<U1')
    native = np.array([f for _, f in keys])
    seen_ball, seen_player = np.zeros(n, bool), np.zeros((n, len(roster)), bool)
    statuses, ownership = Counter(), Counter()
    for period, obj, row in rows(tracking_path, expected_match):
        if obj != 'ball' and obj not in slots:
            continue  # officials are not players
        i = index[period, int(row['N'])]
        point = np.array([float(row.get('X', 'nan')), float(row.get('Y', 'nan'))]) + pitch/2
        finite = np.isfinite(point).all()
        if obj == 'ball':
            if seen_ball[i]: raise ValueError('Duplicate ball frame')
            seen_ball[i] = True
            x['ball'][i] = point
            x['ball_observed'][i] = finite
            state, owner = row.get('BallStatus'), row.get('BallPossession')
            statuses[str(state)] += 1; ownership[str(owner)] += 1
            if state == '0': labels[i] = 'D'
            elif state == '1': labels[i] = {'1': 'H', '2': 'A'}.get(owner, 'X')
        else:
            j = slots[obj]
            if seen_player[i, j]: raise ValueError('Duplicate player frame')
            seen_player[i, j] = True
            x['players'][i, j] = point
            x['player_detected'][i, j] = finite
    adjacent = np.r_[False, (np.diff(native) == 1) & (np.diff(x['period']) == 0)]
    x['ball_pair_valid'] = adjacent
    x['player_pair_valid'] = np.broadcast_to(adjacent[:, None], seen_player.shape).copy()
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(out/'inputs.npz', **x)
    np.savez_compressed(out/'targets.npz', labels=labels)
    np.savez_compressed(out/'source-clock.npz', source_frame=native, period=x['period'])
    dead, live = labels == 'D', np.isin(labels, ('H', 'A'))
    report = {'fixture_id': expected_match, 'frames': n, 'fps': 25.,
              'labels': dict(zip(*[a.tolist() for a in np.unique(labels, return_counts=True)])),
              'ball_status_values': dict(statuses), 'ball_possession_values': dict(ownership),
              'dead_frames_with_finite_ball': int(np.sum(dead & x['ball_observed'])),
              'live_frames_with_finite_ball': int(np.sum(live & x['ball_observed'])),
              'missing_ball_records': int(np.sum(~seen_ball)),
              'native_discontinuities': int(np.sum(~adjacent[1:] & (np.diff(x['period']) == 0))),
              'coordinate_visibility_semantics': 'finite provider positions; no independent image detection mask supplied',
              'target_attributes_excluded_from_features': ['BallStatus', 'BallPossession'],
              'events_used_as_inputs': False, 'provided_fixture_used': False,
              'inputs_sha256': sha256(out/'inputs.npz'), 'targets_sha256': sha256(out/'targets.npz'),
              'source_clock_sha256': sha256(out/'source-clock.npz'),
              'raw_sha256': {'metadata': sha256(meta_path), 'tracking': sha256(tracking_path)},
              'adapter_sha256': sha256(__file__)}
    (out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def run(plan_path, raw_dir, fixture, out):
    plan = json.loads(Path(plan_path).read_text())
    if plan['provided_fixture_used'] is not False or plan['repository'] != 'https://huggingface.co/datasets/pysport/idsse-data':
        raise ValueError('Registered external data only')
    files = [v for v in plan['files'] if v['fixture_id'] == fixture]
    if len(files) != 2 or any(v['split'] == 'reserved_test' for v in files):
        raise ValueError('Registered development fixture required; reserved test not accessible')
    paths = {}
    for entry in files:
        path = Path(raw_dir)/entry['path']
        if path.stat().st_size != entry['bytes']:
            raise ValueError('Wrong raw source size')
        if entry['sha256']:
            if sha256(path) != entry['sha256']: raise ValueError('Wrong raw source SHA256')
        else: verify_file(path, entry)
        paths['tracking' if 'positions_raw' in path.name else 'meta'] = path
    out = external_output(out)
    result = convert(paths['meta'], paths['tracking'], out, 'DFL-MAT-'+fixture)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--plan', default='sportec-data-plan.json')
    p.add_argument('--raw-dir', required=True); p.add_argument('--fixture', required=True)
    p.add_argument('--out', required=True); a = p.parse_args()
    run(a.plan, a.raw_dir, a.fixture, a.out)
