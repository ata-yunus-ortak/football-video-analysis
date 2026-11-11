"""Reporting only (after the validation rows exist): what the goalkeeper correction moves on the validation copies
when the goalkeeper ids are correct (condition 'none' of exp_v210.py). For every moved piece: is its true team the
team it was moved to, and is it a goalkeeper? No model is run and nothing is selected.
Usage: gk_none.py OUT_JSON"""
import json
import sys
import warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession import keeper as K
from possession.features import play_blocks
from possession.epts_export import tracklets, pack
from exp_v210 import NAMES, SEED, SLOT46, true_goalkeepers

if __name__ == '__main__':
    out = {'copies': []}
    for i, name in enumerate(NAMES):
        m, lab = load(name)
        gk = true_goalkeepers(m)
        S = m['players'].shape[1]
        clean = np.asarray(m['players'])
        for j in (0, 1):
            seed = SEED + 10 * i + j
            rng = np.random.default_rng(seed)
            dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
            wide = np.asarray(dm['players'])
            true = np.r_[m['team'], 1 - dm['team'][S:]]            # degrade's extra columns carry the wrong id by design
            n = len(wide)
            P, _ = pack(n, tracklets(wide, dm['team']), SLOT46)
            L, W = m['pitch']
            kinds = {'goalkeeper under the wrong id (flipped by the corruption), moved to his team': [0, 0],
                     'outfield player under the wrong id (flipped by the corruption), moved to his team': [0, 0],
                     'goalkeeper with the right id, moved to the other team': [0, 0],
                     'outfield player with the right id, moved to the other team': [0, 0]}
            for a, b in play_blocks(m['period']):
                found, facts = K._block(P[a:b].astype(np.float64), SLOT46, L, W)
                for slot, s, e, t in found:
                    fin = np.flatnonzero(np.isfinite(P[a + s:a + e, slot]).all(1))
                    r = a + s + int(fin[len(fin) // 2])                                   # a frame in the middle of the piece
                    c = int(np.flatnonzero((wide[r, :, 0] == P[r, slot, 0]) & (wide[r, :, 1] == P[r, slot, 1]))[0])
                    d = [np.linalg.norm(clean[r, g] - P[r, slot]) for k in (0, 1) for g in gk[k]]
                    is_gk = bool(np.nanmin(d) < 2.5)                                      # the corrupted position of a goalkeeper
                    key = ('goalkeeper' if is_gk else 'outfield player') + (
                        ' under the wrong id (flipped by the corruption), moved to his team' if true[c] == t else ' with the right id, moved to the other team')
                    kinds[key][0] += 1
                    kinds[key][1] += len(fin)
            row = {'copy': f'{name}|{seed}', 'moved_pieces_and_frames': kinds,
                   'goalkeeper_frames': int(sum(np.isfinite(clean[:, g]).all(1).sum() for k in (0, 1) for g in gk[k]))}
            out['copies'].append(row)
            print(json.dumps(row), flush=True)
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
    print('NONEDONE', flush=True)
