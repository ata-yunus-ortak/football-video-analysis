"""Possession v2.9g: v2.9 without the published second-half kick-off frame (reserve entry point).

    python -m possession.run29g --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <dir> --broadcast-clock <dir>]

possession.run29 starts second-half play at frame 113,742, the kick-off frame the organisers publish
in FAQ.md, and writes the graded frames before it (110,808-113,741) as D without running the models
on them. Whether a constant taken from the organisers' own documentation may be hard-coded was asked
on 11 November 2026. This entry point is the answer "no" prepared in advance: the play blocks are the
graded windows of games.half_video_blocks("BAR-ATH") only, so the models and the decoder run on the
whole graded second half and decide by themselves what happens before the kick-off.

Everything else is possession.run29: every frozen v2.9 source and both bundles are verified by
run29.check_release, and this file is verified against possession-v29g-release.json. It is made of
parts that were each selected on external matches (v2.5b and the registration of v2.9); what the
models do on a period before a kick-off could not be measured externally, because external tracking
starts at the kick-off.
"""
import argparse
import hashlib
import json
from pathlib import Path
from . import run29
from .run import sha256, ORGANISER_HALVES

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'possession-v29g-release.json'
N_FRAMES = {'BAR-ATH': 199319}


def check_release(path=RELEASE):
    rel = json.loads(Path(path).read_text(encoding='utf-8'))
    if rel['source_sha256'].get('run29g.py') != sha256(HERE / 'run29g.py'):
        raise ValueError('frozen source changed: run29g.py')
    if rel['base_release_sha256'] != sha256(run29.RELEASE):
        raise ValueError('the v2.9 release manifest changed')
    return rel


def run(data_dir, out, game='BAR-ATH', halves=None, release=RELEASE, base_release=run29.RELEASE, **kw):
    check_release(release) if release else None
    halves = halves or ORGANISER_HALVES.get((game, N_FRAMES.get(game)))
    if not halves:
        raise ValueError('no graded windows are known for this game')
    report = run29.run(data_dir, out, game=game, halves=halves, release=base_release, **kw)
    if report['rows'] != (N_FRAMES.get(game) or report['rows']):
        raise ValueError('unexpected number of frames for the graded windows')
    p = Path(out) / 'run.json'
    report = json.loads(p.read_text(encoding='utf-8'))
    report['system'] = 'possession-v2.9g (v2.9 without the published second-half kick-off frame; play blocks = graded windows)'
    report['period_source'] = 'organiser graded windows (games.half_video_blocks); the models run on the whole graded second half'
    report['dead_leadin_frames'] = []
    report['v29g_release_manifest_sha256'] = hashlib.sha256(Path(release).read_bytes()).hexdigest() if release else None
    report['v29g_source_sha256'] = sha256(HERE / 'run29g.py')
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
