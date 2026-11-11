"""Build the full-size v2.5 reproducibility fixture once: Metrica sample game 3 tracking (labels NOT read) and a
synthetic 'good' broadcast EPTS stream + homography validity + clock observations for both recordings."""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from possession.data import read_epts
from possession.features import play_blocks
import synth_broadcast2 as sb2
import synth_clock as sc
from exp_v25 import quality

FIX = Path('/home/claude/work/repro25_fixture')
src = Path('/home/claude/ext/sd/data/Sample_Game_3')
m, info = read_epts(src / 'Sample_Game_3_metadata.xml', src / 'Sample_Game_3_tracking.txt')
p = info['provider_parameters']
n = len(m['ball'])
per = np.zeros(n, np.int8)
halves = [(1, int(p['first_half_start']) - 1, int(p['first_half_end']) - 1),
          (2, int(p['second_half_start']) - 1, int(p['second_half_end']) - 1)]
for h, a, b in halves:
    per[a:b + 1] = h
m['period'] = per
lab = np.full(n, 'H')                      # no labels read: no dead-ball replays in this fixture
rng = np.random.default_rng(424242)
q = quality(rng, 'good')
bro, valid, true_t, clock_t = sb2.simulate_with_clock(m, lab, rng, q)
B = len(bro['ball'])
FIX.mkdir(parents=True, exist_ok=False)
(FIX / 'broadcast').mkdir()
pitch = np.array(m['pitch'], float)
team = bro['team']
(FIX / 'broadcast' / 'MET3_broadcast_atd.xml').write_text(
    f'<main><FrameRate>25</FrameRate><FieldSize><Width>{pitch[0]:g}</Width><Height>{pitch[1]:g}</Height></FieldSize>'
    '<Team id="h"/><Team id="a"/>' + ''.join(f'<Player teamId="{"ha"[int(t)]}"/>' for t in team) + '</main>')
P, Bb = bro['players'] / pitch, bro['ball'] / pitch
with open(FIX / 'broadcast' / 'MET3_broadcast_atd.txt', 'w') as fh:
    for i in range(B):
        g = ';'.join('NaN,NaN,0' if not np.isfinite(P[i, j]).all() else f'{P[i, j, 0]:.5f},{P[i, j, 1]:.5f},1.0'
                     for j in range(P.shape[1]))
        b = 'NaN,NaN,NaN' if not np.isfinite(Bb[i]).all() else f'{Bb[i, 0]:.5f},{Bb[i, 1]:.5f},2.0'
        fh.write(f'{i + 1}:{g}:{b}\n')
with open(FIX / 'broadcast' / 'MET3_broadcast_homography.csv', 'w') as fh:
    fh.write('frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid\n')
    for i in range(B):
        fh.write(f'{i},1,0,0,0,1,0,0,0,1,0.5,{int(valid[i])}\n')
blocks = [(a, b + 1) for _, a, b in halves]
rc = np.random.default_rng(434343)
for name, live in (('clock_tac', np.arange(n)), ('clock_bro', clock_t)):
    (FIX / name).mkdir()
    rows = sc.observations(live, blocks, 25.0, rc, 0.8, 0.02)
    (FIX / name / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
(FIX / 'halves.json').write_text(json.dumps(halves))
print('fixture', n, B, q)
