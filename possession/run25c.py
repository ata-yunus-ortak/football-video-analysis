"""Possession v2.5c: v2.5b with the organisers' published second-half kick-off frame.

    python -m possession.run25c --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <dir> --broadcast-clock <dir>]

The organisers' FAQ states: "the second half is graded from frame 110,808 but does not kick off
until 113,742. Those 2,934 frames are graded and all of them are D." The first half "is graded from
the kickoff itself". possession.run25 treats 110,808 as the start of second-half play, so the models
(trained on halves that begin at the kick-off) see two minutes of players walking out as play.
This entry point passes play blocks that start at the published kick-off; the frames before it are
outside the play blocks and are written as D like every other frame outside play. Nothing else
changes: every frozen v2.5b source and both bundles are verified by run25.check_release, and this
file is verified against possession-v25c-release.json.

The kick-off frame is a fixture constant published by the organisers, like the graded windows; it is
not measured by us and its effect cannot be measured on external matches (their tracking starts at
the kick-off). It is not derived from the video, the ground truth file or the public window.
"""
import argparse
import hashlib
import json
from pathlib import Path
from . import run25
from .run import sha256

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'possession-v25c-release.json'
# (half, first play frame, last graded frame); half 2 starts at the kick-off published in FAQ.md.
ORGANISER_PLAY_HALVES = {('BAR-ATH', 199319): [(1, 11185, 90651), (2, 113742, 190197)]}
ORGANISER_DEAD_LEADIN = {('BAR-ATH', 199319): [(110808, 113741)]}
N_FRAMES = {'BAR-ATH': 199319}


def check_release(path=RELEASE):
    rel = json.loads(Path(path).read_text(encoding='utf-8'))
    if rel['source_sha256'].get('run25c.py') != sha256(HERE / 'run25c.py'):
        raise ValueError('frozen source changed: run25c.py')
    if rel['base_release_sha256'] != sha256(run25.RELEASE):
        raise ValueError('the v2.5b release manifest changed')
    return rel


def run(data_dir, out, game='BAR-ATH', halves=None, leadin=None, release=RELEASE, base_release=run25.RELEASE, **kw):
    rel = check_release(release) if release else None
    key = (game, N_FRAMES.get(game))
    halves = halves or ORGANISER_PLAY_HALVES.get(key)
    leadin = leadin if leadin is not None else ORGANISER_DEAD_LEADIN.get(key, [])
    report = run25.run(data_dir, out, game=game, halves=halves, release=base_release, **kw)
    if halves and report['rows'] != (N_FRAMES.get(game) or report['rows']):
        raise ValueError('unexpected number of frames for the published play blocks')
    p = Path(out) / 'run.json'
    report = json.loads(p.read_text(encoding='utf-8'))
    report['system'] = 'possession-v2.5c (v2.5b + published second-half kick-off)'
    report['period_source'] = 'organiser graded windows; second-half play starts at the kick-off frame published in FAQ.md'
    report['dead_leadin_frames'] = [list(x) for x in leadin]
    report['v25c_release_manifest_sha256'] = hashlib.sha256(Path(release).read_bytes()).hexdigest() if release else None
    report['v25c_source_sha256'] = sha256(HERE / 'run25c.py')
    p.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--data-dir', required=True, help='bundle root containing tactical/ and broadcast/')
    p.add_argument('--out', required=True, help='new output folder (must not exist)')
    p.add_argument('--tactical-clock', default=None)
    p.add_argument('--broadcast-clock', default=None)
    a = p.parse_args()
    run(a.data_dir, a.out, tactical_clock=a.tactical_clock, broadcast_clock=a.broadcast_clock)
