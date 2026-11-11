"""Reproducibility of the v2.5 entry point across interpreters (Python 3.13/numpy 2.5 vs 3.10/numpy 1.26):
full-size external EPTS (Metrica sample game 3 tracking corrupted with degrade(), labels not read) plus a synthetic broadcast EPTS
stream built from the same game (written once to disk, then read by both interpreters), with and without
clock observation files. Usage: repro_v25.py OUT_JSON"""
import sys, os, json, time, resource, tempfile
from pathlib import Path
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
import numpy as np
from possession import run29

FIX = Path('/home/claude/work/repro25_fixture')
src = Path('/home/claude/ext/sd/data/Sample_Game_3')
out = {'python': sys.version.split()[0], 'numpy': np.__version__, 'release': 'v2.9'}
with tempfile.TemporaryDirectory() as d:
    root = Path(d) / 'bundle'
    (root / 'tactical').mkdir(parents=True)
    os.symlink(FIX / 'tactical' / 'MET3_tactical_atd.xml', root / 'tactical' / 'MET3_tactical_atd.xml')
    os.symlink(FIX / 'tactical' / 'MET3_tactical_atd.txt', root / 'tactical' / 'MET3_tactical_atd.txt')
    os.symlink(FIX / 'broadcast', root / 'broadcast')
    halves = json.loads((FIX / 'halves.json').read_text())
    for tag, clocks in (('no_clock', {}), ('clock', {'tactical_clock': FIX / 'clock_tac', 'broadcast_clock': FIX / 'clock_bro'})):
        t = time.time()
        rep = run29.run(root, Path(d) / f'out_{tag}', game='MET3', halves=[tuple(h) for h in halves], **clocks)
        out[tag] = {'sha256': rep['submission_sha256'], 'path': rep['path'], 'fill_used': rep['broadcast_fill_used'],
                    'alignment_mode': rep['fusion'].get('alignment_mode'), 'registered_frames': (rep['fusion'].get('registration') or {}).get('registered_ball_frames'), 'seconds': round(time.time() - t, 1)}
out['peak_rss_gb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
print('REPRO29', json.dumps(out))
