"""In-memory reference for the rehearsal: the same corrupted content before duplicated tracks and slot packing
(one column per source track), tactical camera only, frozen release logic. Writes a CSV for score_prova.py."""
import sys, csv, json, time
import numpy as np
sys.path.insert(0, '/home/claude/sc')
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.noise import estimate_noise, choose_path
t0 = time.time()
z = np.load(sys.argv[1])
m = {'fps': 25.0, 'pitch': np.array([105.0, 68.0]), 'ball': z['ball'], 'players': z['players'], 'team': z['team'], 'period': z['period_play']}
b21 = load_bundle('/home/claude/sc/models/possession-v2.npz'); b23 = load_bundle('/home/claude/sc/models/possession-v23.npz')
noise = estimate_noise(m); path, _ = choose_path(noise)
labels = predict_labels(smooth_positions(m, int(b23['card']['smooth_half'])), b23)[0] if path == 'v2.3' else predict_labels(m, b21)[0]
with open(sys.argv[2], 'w', newline='') as fh:
    w = csv.writer(fh, lineterminator='\n'); w.writerow(['frame', 'label']); w.writerows(zip(range(len(labels)), labels.tolist()))
print('R1', path, json.dumps(noise), round(time.time() - t0), 's', flush=True)
