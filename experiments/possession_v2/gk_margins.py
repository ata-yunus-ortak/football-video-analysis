"""Development (training matches only): direct-evidence frames per goal and half under each team id, for correct
ids and camera windows: how far is the 'other id' evidence from the dominance thresholds of possession.keeper2?"""
import sys, json, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import keeper2 as K
from possession.epts_export import tracklets, pack
from exp_v210 import true_goalkeepers, with_error, SLOT46
from camera_view import apply_view
for name in sys.argv[1:]:
    m, lab = load(name); gk = true_goalkeepers(m); gk['clean_team'] = m['team'].copy()
    seed = 6000 + sum(map(ord, name)) % 1000
    rng = np.random.default_rng(seed); dm0 = degrade(m, lab, rng, sample_params(rng, ranges=RANGES)); n = len(dm0['ball'])
    for hw in (None, 50.0, 42.0, 35.0, 28.0):
        dm = dm0 if hw is None else apply_view(dm0, m, hw)[0]
        for k, cond in enumerate(('none', 'gk_both')):
            wide, team, true, isgk = with_error(cond, dm, gk, np.random.default_rng(seed + 50 + 2 * k))
            P, _ = pack(n, tracklets(wide, team), SLOT46)
            fixed, rep = K.correct_goalkeepers(dict(dm, players=P, team=SLOT46))
            ev = [(h[f'{s}_evidence_frames']['defending_id'], h[f'{s}_evidence_frames']['other_id'], h[f'{s}_evidence_frames']['other_id_dominant']) for h in rep['halves'] for s in ('left', 'right')]
            print(name, hw, cond, 'evidence (defending id, other id, dominant) per half and goal:', ev, 'moved', rep['moved_pieces'], flush=True)
