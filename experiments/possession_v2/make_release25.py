"""Freeze the v2.5 release: SHA-256 of every inference source and both bundles -> possession-v25-release.json."""
import json, hashlib, subprocess, sys
from pathlib import Path
S = Path('/home/claude/sc')
sys.path.insert(0, str(S))
from possession import run25
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
use_clock = run25.USE_CLOCK
rel = {'version': 'possession-v2.5' + ('b' if use_clock else ''),
       'frozen_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
       'entry_point': 'python -m possession.run25',
       'components': {'core': 'possession-v2.1 (models/possession-v2.npz)',
                      'noise_gate_and_v2_3_path': 'possession-v2.4 (possession/noise.py, smooth.py, models/possession-v23.npz)',
                      'broadcast_fill': 'possession-v2.5 (possession/fusion.py, broadcast.py; accuracy gate median <= 0.50 m)',
                      'clock_anchor': 'possession-v2.5b (possession/clocksync.py)' if use_clock else 'not used'},
       'source_sha256': {name: sha(S / 'possession' / name) for name in run25.SOURCES},
       'bundle_sha256': {'v2.1': sha(S / 'models' / 'possession-v2.npz'), 'v2.3': sha(S / 'models' / 'possession-v23.npz')},
       'plans': ['possession-v2-plan.json', 'possession-v23-plan.json', 'possession-v24-plan.json', 'possession-v25-plan.json']
                + (['possession-v25b-plan.json'] if use_clock else []),
       'provided_fixture_used': False}
(S / 'possession-v25-release.json').write_text(json.dumps(rel, indent=2) + '\n')
print(json.dumps(rel, indent=1))
