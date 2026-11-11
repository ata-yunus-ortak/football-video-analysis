"""Do the release's readers see what DATA.md says the provided files contain? PASS/FAIL only.

    python -m possession.inputs_check --data-dir <bundle root with tactical/ and broadcast/>

DATA.md of the organisers' repository publishes aggregate facts about the provided files: record
counts, track slots, on how many frames the ball is present, the mean number of tracked objects on
graded frames, the share of usable broadcast homography rows, and that the first team of the
metadata is the home side, Barcelona. This tool reads the files with the very functions the release
uses (possession.data.read_epts, possession.broadcast.read_homography) and compares what they
return with those published facts.

Each tracking file is also read a second time without the release's reader, line by line, the way
the organisers' own starter/baseline.py reads it: the i-th group of a line is the i-th Player entry
of the metadata, the first Team is the home side, a group that starts with N is missing,
row = frame_id - 1. That pass checks the syntax DATA.md describes (three ':' parts per line, one
';' group per Player entry, numbers or NaN, frame ids counting from 1), and its result is compared
with the release's reader on every frame: where the ball is, how many tracks of each team are
present, and which team's tracked player is nearest to the ball.

It prints PASS, FAIL or SKIP per fact and never a value, so the lines can be shared. After a FAIL
of a comparison the differing aspect is named (for example ..._starter_reading__team_counts), after
a reader error the error class. A FAIL means that a reader and the documentation disagree about the
file; the place to look is the reader (a format detail), never a model, a threshold or the release.
Nothing here is compared with the video, with a ground truth or with an output of the system.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from .data import read_epts
from . import broadcast as bc

GAME = 'BAR-ATH'
# DATA.md (table "tactical / broadcast", sections "Automatic Tracking Data" and "Homography") and the graded
# windows table; counts are exact where DATA.md gives a count and rounded where it gives a percentage.
PUBLISHED = {
    'tactical_records': 199319, 'tactical_slots': 46,
    'tactical_ball_frames': 113488, 'graded_ball_frames': 94214, 'graded_windows': ((11185, 90651), (110808, 190197)),
    'mean_tracked_on_graded': 20.5,
    'broadcast_records': 164488, 'broadcast_slots': 51, 'broadcast_ball_share': 0.505,
    'broadcast_homography_valid_share': 0.658, 'home_name_contains': 'barcelona',
}
COUNT_TOL = 0.002        # of the number of frames a count refers to
SHARE_TOL = 0.001        # DATA.md rounds shares to 0.1 percent
MEAN_TOL = 0.1           # DATA.md rounds the mean to 0.1
NEAR_TIE_M = 1e-3        # two players this close to being equally near the ball may be ordered either way
RAW = ('raw_lines_have_three_parts', 'raw_groups_equal_player_entries', 'raw_values_are_numbers_or_nan', 'raw_frame_ids_count_from_one',
       'reader_runs')
CHECKS = tuple(f'tactical_{k}' for k in RAW) + (
    'tactical_records', 'tactical_frame_ids', 'tactical_slots', 'tactical_slots_belong_to_a_team', 'first_team_is_named_barcelona',
    'tactical_ball_frames', 'tactical_ball_on_graded_frames', 'tactical_tracked_objects', 'tactical_agrees_with_starter_reading',
) + tuple(f'broadcast_{k}' for k in RAW) + (
    'broadcast_records', 'broadcast_slots', 'broadcast_slots_belong_to_a_team', 'broadcast_ball_share',
    'broadcast_agrees_with_starter_reading', 'broadcast_homography_rows', 'broadcast_homography_valid_share')
_NUM = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[Nn][Aa][Nn]'
_GROUP = rf'(?:{_NUM})(?:,(?:{_NUM}))*'
_LINE = re.compile(rf'\d+:{_GROUP}(?:;{_GROUP})*:{_GROUP}')


def second_reading(meta, raw):
    """One pass over a tracking pair without possession.data, the way the organisers' starter/baseline.py reads it.

    Malformed lines are counted, never raised. Returns the syntax facts and, for every well-formed line, the frame
    id, whether there is a ball, its position in metres, the number of present tracks of the first and of the
    second team, and the team (0/1, -1 = nobody) of the present track nearest to the ball."""
    root = ET.parse(meta).getroot()
    ids = [t.get('id') for t in root.iter('Team')][:2]
    side = [ids.index(p.get('teamId')) if p.get('teamId') in ids else -1 for p in root.iter('Player')]
    fs = root.find('.//FieldSize')
    length, width = float(fs.findtext('Width')), float(fs.findtext('Height'))
    three = groups = numbers = True
    fid, seen, ball, count, near = [], [], [], [], []
    nan = float('nan')
    with open(raw, encoding='utf-8-sig') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split(':')
            if len(parts) != 3:
                three = False
                continue
            gs = parts[1].split(';')
            if len(gs) != len(side):
                groups = False
                continue
            if not _LINE.fullmatch(line):
                numbers = False
                continue
            b = parts[2]
            has_ball = b[:1] not in ('N', 'n')
            bx = by = nan
            if has_ball:
                f = b.split(',')
                bx, by = float(f[0]) * length, float(f[1]) * width
            best, best_team, c = None, -1, [0, 0]
            for slot, g in enumerate(gs):
                if g[:1] in ('N', 'n') or side[slot] < 0:
                    continue
                c[side[slot]] += 1
                if has_ball:
                    f = g.split(',')
                    dx, dy = float(f[0]) * length - bx, float(f[1]) * width - by
                    d = dx * dx + dy * dy
                    if best is None or d < best:
                        best, best_team = d, side[slot]
            fid.append(int(parts[0])); seen.append(has_ball); ball.append((bx, by)); count.append(c); near.append(best_team)
    fid = np.array(fid, np.int64)
    return {'syntax': {'raw_lines_have_three_parts': three, 'raw_groups_equal_player_entries': groups,
                       'raw_values_are_numbers_or_nan': numbers,
                       'raw_frame_ids_count_from_one': bool(len(fid)) and bool(np.array_equal(fid, np.arange(1, len(fid) + 1)))},
            'rows': len(fid), 'seen': np.array(seen, bool), 'ball': np.array(ball, np.float64).reshape(-1, 2),
            'count': np.array(count, np.int64).reshape(-1, 2), 'near': np.array(near, np.int64)}


def starter_difference(match, ref):
    """'' when the release's reader and the second reading describe every frame alike; otherwise the first aspect in
    which they differ: syntax, rows, ball_presence, ball_position, team_counts or nearest_team."""
    n = len(match['ball'])
    if not all(ref['syntax'].values()):
        return 'syntax'
    if ref['rows'] != n:
        return 'rows'
    ball = np.asarray(match['ball'], np.float64)
    seen = np.isfinite(ball).all(1)
    if not np.array_equal(seen, ref['seen']):
        return 'ball_presence'
    if seen.any() and float(np.abs(ball[seen] - ref['ball'][seen]).max()) > NEAR_TIE_M:
        return 'ball_position'
    players = np.asarray(match['players'], np.float64)
    team = np.asarray(match['team'])
    present = np.isfinite(players).all(2)
    if not np.array_equal(np.stack([present[:, team == k].sum(1) for k in (0, 1)], 1), ref['count']):
        return 'team_counts'
    d = np.linalg.norm(players - ball[:, None], axis=2)
    d[~np.isfinite(d)] = np.inf
    dk = [d[:, team == k].min(1) if (team == k).any() else np.full(n, np.inf) for k in (0, 1)]
    ours = np.where(np.isfinite(np.minimum(dk[0], dk[1])), np.where(dk[0] <= dk[1], 0, 1), -1)
    with np.errstate(invalid='ignore'):
        tie = np.abs(dk[0] - dk[1]) <= NEAR_TIE_M
    return 'nearest_team' if ((ours != ref['near']) & ~tie).any() else ''


def _read(cam, meta, raw, details):
    """Syntax facts of one tracking pair, then the release's reader. Returns (results, match, info)."""
    ref = second_reading(meta, raw)
    res = {f'{cam}_{k}': v for k, v in ref['syntax'].items()}
    try:
        match, info = read_epts(meta, raw)
    except Exception as e:                      # the class is reported, never the message
        res[f'{cam}_reader_runs'] = False
        if details is not None:
            details[f'{cam}_reader_runs'] = type(e).__name__
        return res, None, None
    res[f'{cam}_reader_runs'] = True
    diff = starter_difference(match, ref)
    res[f'{cam}_agrees_with_starter_reading'] = not diff
    if diff and details is not None:
        details[f'{cam}_agrees_with_starter_reading'] = diff
    return res, match, info


def tactical_checks(meta, raw, pub=PUBLISHED, details=None):
    res, match, info = _read('tactical', meta, raw, details)
    if match is None:
        return res
    n = len(match['ball'])
    ball = np.isfinite(match['ball']).all(1)
    graded = np.zeros(n, bool)
    for a, b in pub['graded_windows']:
        graded[a:b + 1] = True
    g = int(graded.sum())
    tracked = float(np.isfinite(match['players']).all(2).sum(1)[graded].mean()) if g else float('nan')
    with_ball = tracked + (float(ball[graded].mean()) if g else float('nan'))     # DATA.md does not say whether the ball counts
    res.update({
        'tactical_records': n == pub['tactical_records'],
        'tactical_frame_ids': match['first_frame_id'] == 1,                       # read_epts itself requires consecutive ids
        'tactical_slots': info['slots'] == pub['tactical_slots'],
        'tactical_slots_belong_to_a_team': info['slots_without_team'] == 0,
        'first_team_is_named_barcelona': pub['home_name_contains'] in (info['team_names'][0] or '').lower(),
        'tactical_ball_frames': abs(int(ball.sum()) - pub['tactical_ball_frames']) <= COUNT_TOL * pub['tactical_records'],
        'tactical_ball_on_graded_frames': g > 0 and abs(int(ball[graded].sum()) - pub['graded_ball_frames']) <= COUNT_TOL * g,
        'tactical_tracked_objects': g > 0 and min(abs(tracked - pub['mean_tracked_on_graded']),
                                                  abs(with_ball - pub['mean_tracked_on_graded'])) <= MEAN_TOL,
    })
    return res


def broadcast_checks(meta, raw, homography, pub=PUBLISHED, details=None):
    res, match, info = _read('broadcast', meta, raw, details)
    if match is None:
        return res
    n = len(match['ball'])
    valid, _ = bc.read_homography(homography, n)
    with open(homography, newline='', encoding='utf-8-sig') as fh:
        rows = sum(1 for line in fh if line.strip()) - 1
    res.update({
        'broadcast_records': n == pub['broadcast_records'],
        'broadcast_slots': info['slots'] == pub['broadcast_slots'],
        'broadcast_slots_belong_to_a_team': info['slots_without_team'] == 0,
        'broadcast_ball_share': abs(float(np.isfinite(match['ball']).all(1).mean()) - pub['broadcast_ball_share']) <= SHARE_TOL,
        'broadcast_homography_rows': rows == n,
        'broadcast_homography_valid_share': abs(float(valid.mean()) - pub['broadcast_homography_valid_share']) <= SHARE_TOL,
    })
    return res


def check(data_dir, game=GAME, pub=PUBLISHED, details=None):
    """{check name: True | False | None}; None = not checked (the files of that camera are not there, or the reader
    stopped with an error). details (a dict, optional) receives, for a failed comparison with the second reading, the
    aspect that differs, and for a reader error the error class."""
    root = Path(data_dir)
    t, b = root / 'tactical', root / 'broadcast'
    res = {k: None for k in CHECKS}
    res.update(tactical_checks(t / f'{game}_tactical_atd.xml', t / f'{game}_tactical_atd.txt', pub, details))
    files = (b / f'{game}_broadcast_atd.xml', b / f'{game}_broadcast_atd.txt', b / f'{game}_broadcast_homography.csv')
    if all(p.exists() for p in files):
        res.update(broadcast_checks(*files, pub, details))
    return res


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--data-dir', required=True)
    a = p.parse_args(argv)
    details = {}
    res = check(a.data_dir, details=details)
    for k in CHECKS:
        print(('SKIP ' if res[k] is None else 'PASS ' if res[k] else 'FAIL ') + k + ('__' + details[k] if k in details else ''))
    bad = [k for k in CHECKS if res[k] is False]
    print('INPUTS ' + ('OK' if not bad else 'DIFFER FROM DATA.md'))
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
