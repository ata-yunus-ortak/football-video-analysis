"""Quick functional check of the staged run217 on synthetic bundles (no match data): against run216 with the second model
switched off, on the v2.3 path, and with the eight members on."""
import sys, tempfile, json, contextlib, io, time, platform
from pathlib import Path
import numpy as np
sys.path.insert(0, '.')
from possession import run216, run217
from tests.test_possession_crossplatform import bundle, HALVES
def q(entry, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return entry.run(*a, **kw)
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    lost = bundle(root / 'lost', lost=True)
    kw = dict(game='SYN', halves=HALVES, release=None)
    a = q(run216, lost, root / 'a', pooled=False, **kw); b = q(run217, lost, root / 'b', pooled=False, **kw)
    print('second model off: same bytes', a['submission_sha256'] == b['submission_sha256'])
    t = time.time(); c = q(run216, lost, root / 'c', **kw); t216 = time.time() - t
    t = time.time(); e = q(run217, lost, root / 'e', **kw); t217 = time.time() - t
    print('on: path', e['path'], 'second', {k: v for k, v in e['second_model'].items() if k != 'weights_sha256'}, 'differs from v2.16', c['submission_sha256'] != e['submission_sha256'],
          'added', e['added_players'].get('player_positions_added'), 'seconds', round(t216, 1), round(t217, 1))
    la = np.array([r.split(',')[1] for r in (root / 'c' / 'submission.csv').read_text().splitlines()[1:]])
    lb = np.array([r.split(',')[1] for r in (root / 'e' / 'submission.csv').read_text().splitlines()[1:]])
    print('frames changed', int((la != lb).sum()), 'of', len(la), 'labels', sorted(set(lb)))
    f = q(run217, lost, root / 'f', **kw); print('again: same bytes', f['submission_sha256'] == e['submission_sha256'], e['submission_sha256'][:16])
    noisy = bundle(root / 'noisy', player_noise=0.45, lost=True)
    g = q(run216, noisy, root / 'g', **kw); h = q(run217, noisy, root / 'h', **kw)
    print('v2.3 path:', h['path'], 'second used', h['second_model']['used'], 'same bytes as v2.16', g['submission_sha256'] == h['submission_sha256'])
    print(platform.python_version(), np.__version__)
