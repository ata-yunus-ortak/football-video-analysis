"""Reproducibility of the frozen v2.4 release across interpreters (run under Python 3.13/numpy 2.5 and
Python 3.10/numpy 1.26 and compare). No labels are read.
 - synthetic ATD (tests/test_possession_v24.match), quiet and with 0.5 m player noise, through run24.run
 - full-size external EPTS (Metrica sample game 3 tracking) through run24.run (clean -> expected v2.1 path)
 - the same tracking with 0.5 m player noise (noise array saved once to disk, so both interpreters add the
   identical values) through the v2.3 path functions"""
import sys, os, time, json, resource, tempfile, hashlib, io
from pathlib import Path
sys.path.insert(0, '/home/claude/sc')
import numpy as np
from possession import run24
from possession.data import read_epts
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.noise import estimate_noise, choose_path
from tests.test_possession_v24 import match, write_atd, HALVES

out = {'python': sys.version.split()[0], 'numpy': np.__version__}
with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    for tag, sd in (('quiet', 0.0), ('noisy', 0.5)):
        data = write_atd(root / tag, match(seed=8, player_sd=sd))
        rep = run24.run(data, root / f'out_{tag}', game='SYN', halves=HALVES)
        out[f'synthetic_{tag}'] = {'path': rep['path'], 'sha256': rep['submission_sha256']}

src = Path('/home/claude/ext/sd/data/Sample_Game_3')
with tempfile.TemporaryDirectory() as d:
    tac = Path(d) / 'bundle' / 'tactical'; tac.mkdir(parents=True)
    os.symlink(src / 'Sample_Game_3_metadata.xml', tac / 'MET3_tactical_atd.xml')
    os.symlink(src / 'Sample_Game_3_tracking.txt', tac / 'MET3_tactical_atd.txt')
    m, info = read_epts(tac / 'MET3_tactical_atd.xml', tac / 'MET3_tactical_atd.txt')
    p = info['provider_parameters']
    halves = [(1, int(p['first_half_start']) - 1, int(p['first_half_end']) - 1),
              (2, int(p['second_half_start']) - 1, int(p['second_half_end']) - 1)]
    t = time.time()
    rep = run24.run(Path(d) / 'bundle', Path(d) / 'out', game='MET3', halves=halves)
    out['met3_full_size'] = {'path': rep['path'], 'sha256': rep['submission_sha256'], 'seconds': round(time.time() - t, 1),
                             'measured_noise': rep['gate']['measured_noise']}
# v2.3 path on full size: identical added noise from disk
period = np.zeros(len(m['ball']), np.int8)
for h, a, b in halves:
    period[a:b + 1] = h
m['period'] = period
noise_file = '/home/claude/work/met3_player_noise_0p5.npy'
if not os.path.exists(noise_file):
    np.save(noise_file, np.random.default_rng(2024).normal(0, 0.5, m['players'].shape).astype(np.float32))
m['players'] = (m['players'] + np.load(noise_file)).astype(np.float32)
nz = estimate_noise(m)
path, why = choose_path(nz)
b23 = load_bundle(run24.V23_MODEL)
t = time.time()
labels, _, _ = predict_labels(smooth_positions(m, int(b23['card']['smooth_half'])), b23)
buf = 'frame,label\n' + ''.join(f'{i},{l}\n' for i, l in enumerate(labels.tolist()))
out['met3_with_0p5m_player_noise_v23_path'] = {'gate_path': path, 'measured_players_m': round(nz['players_m'], 4),
                                               'labels_sha256': hashlib.sha256(buf.encode()).hexdigest(),
                                               'seconds': round(time.time() - t, 1)}
out['peak_rss_gb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)
print('REPRO', json.dumps(out))
