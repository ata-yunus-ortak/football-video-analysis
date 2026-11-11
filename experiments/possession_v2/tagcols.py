import sys, numpy as np
sys.path.insert(0, '/home/claude/sc')
from possession.tags import simulate_tags, tag_features
from possession.features import play_blocks

def tag_columns(m, lab, seed, swap, p=None):
    rng = np.random.default_rng(10_000 + seed)
    tags = simulate_tags(lab, m['ball'], m['period'], m['pitch'], m['fps'], rng, p)
    n = len(lab)
    out = np.full((n, 12), np.nan, np.float32)
    for a, b in play_blocks(m['period']):
        local = [dict(t, start=t['start'] - a, end=t['end'] - a,
                      team=(None if t['team'] is None else (1 - t['team'] if swap else t['team'])))
                 for t in tags if t['end'] > a and t['start'] < b]
        C, P = tag_features(local, b - a, None, m['fps'])
        cols = list(C.values()) + list(P[0].values()) + list(P[1].values()) + [P[0][k] - P[1][k] for k in P[0]]
        out[a:b] = np.stack(cols, 1)
    return out
