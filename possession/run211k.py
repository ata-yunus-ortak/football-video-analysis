"""Possession v2.11k: v2.11g plus the Smart Tagging kick-off rule.

    python -m possession.run211k --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <dir> --broadcast-clock <dir>]

possession.run211g runs the models on the whole graded second half, which starts before the kick-off, and
lets them decide what happens there. This entry point adds one rule after it (possession/kickoff.py): in
every graded block, the frames before the first automatic Smart Tagging "Kick Off (Start)" tag are written
D, if that tag starts less than ten minutes after the block's first frame. The tag is read from
tactical/<game>_tactical_smart_tagging.xml, an automatic asset of the provided bundle. No frame number is
stored in the code; the kick-off frame published in FAQ.md is not used.

If the file is missing or unreadable, or holds no usable tag, the output is the output of
possession.run211g. Everything else is possession.run211g: its manifest and, through it, every frozen
v2.11 source and both bundles are verified, and kickoff.py and this file are verified against
possession-v211k-release.json. The rule cannot be measured on external matches (their tracking starts at
the kick-off and they have no Smart Tagging); its tests are synthetic.
"""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from . import run211, run211g, kickoff
from .run import sha256, ORGANISER_HALVES

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent / 'possession-v211k-release.json'
SOURCES = ('kickoff.py', 'run211k.py')


def check_release(path=RELEASE):
    rel = json.loads(Path(path).read_text(encoding='utf-8'))
    for name in SOURCES:
        if rel['source_sha256'].get(name) != sha256(HERE / name):
            raise ValueError(f'frozen source changed: {name}')
    if rel['base_release_sha256'] != sha256(run211g.RELEASE):
        raise ValueError('the v2.11g release manifest changed')
    run211g.check_release()
    return rel


def frame_rate(meta_path):
    """Frames per second of the tracking, from the EPTS metadata (the Smart Tagging times are seconds of the same video)."""
    fps = float(ET.parse(meta_path).getroot().findtext('.//FrameRate'))
    if not fps > 0:
        raise ValueError('no frame rate in the tracking metadata')
    return fps


def run(data_dir, out, game='BAR-ATH', halves=None, release=RELEASE, base_release=run211g.RELEASE,
        v211_release=run211.RELEASE, **kw):
    check_release(release) if release else None
    halves = halves or ORGANISER_HALVES.get((game, run211g.N_FRAMES.get(game)))
    if not halves:
        raise ValueError('no graded windows are known for this game')
    run211g.run(data_dir, out, game=game, halves=halves, release=base_release, base_release=v211_release, **kw)
    root = Path(data_dir)
    fps = frame_rate(root / 'tactical' / f'{game}_tactical_atd.xml')
    kickoff.apply_to_submission(out, root / 'tactical' / f'{game}_tactical_smart_tagging.xml',
                                [(a, b) for _, a, b in halves], fps)
    p = Path(out) / 'run.json'
    report = json.loads(p.read_text(encoding='utf-8'))
    report['system'] = 'possession-v2.11k (v2.11g + dead ball before the Smart Tagging kick-off tag of a graded block)'
    report['period_source'] = ('organiser graded windows (games.half_video_blocks); the models run on the whole graded second half; '
                               'frames before a usable Smart Tagging kick-off tag are then written D')
    report['inputs_used'] = list(report.get('inputs_used', [])) + ['smart tagging: kick-off tags only (if present)']
    report['not_used'] = [x for x in report.get('not_used', []) if x != 'smart tagging'] + ['smart tagging other than kick-off tags']
    report['v211k_release_manifest_sha256'] = hashlib.sha256(Path(release).read_bytes()).hexdigest() if release else None
    report['v211k_source_sha256'] = {name: sha256(HERE / name) for name in SOURCES}
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
