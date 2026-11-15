"""Exploration 1 (development copies only): true restarts of the five development matches with a type guessed from the
clean ball position (possession.tags._restart_type), and how the v2.15 decision treats the dead-ball stretch before each.
Nothing opens the provided match."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/work/v216')
import errlib as E
import harness as H
from possession.tags import _restart_type
from possession.features import play_blocks

def restarts(name):
    m, lab = H.load(name)
    per, fps = m['period'], float(m['fps'])
    L, W = float(m['pitch'][0]), float(m['pitch'][1])
    ball = np.asarray(m['ball'])[:, :2]
    out = []
    for a, b in play_blocks(per):
        seg = lab[a:b]
        br = np.flatnonzero(seg[1:] != seg[:-1]) + 1
        bo = np.concatenate(([0], br, [len(seg)]))
        for i in range(len(bo) - 1):
            if seg[bo[i]] != 'D' or bo[i + 1] >= len(seg) or seg[bo[i + 1]] not in ('H', 'A'):
                continue
            s, t = a + int(bo[i]), a + int(bo[i + 1])
            back = ball[max(a, t - 2 * int(fps)):t + 1]
            ok = np.isfinite(back).all(1)
            typ = _restart_type(back[ok][-1] if ok.any() else np.array([np.nan, np.nan]), L, W)
            prev = seg[bo[i - 1]] if i > 0 else '-'
            out.append((s, t, typ, prev, seg[bo[i + 1]], i == 0))
    return out, fps, sum(b - a for a, b in play_blocks(per)) / fps / 60.0

if __name__ == '__main__':
    R = {}
    for name in ('J03WN1', 'J03WR9', 'MET1', 'MET2', 'MET3'):
        r, fps, minutes = restarts(name)
        R[name] = {'minutes': minutes, 'restarts': [(int(s), int(t), typ, p, n, bool(f)) for s, t, typ, p, n, f in r]}
        c = {}
        for s, t, typ, p, n, f in r:
            c.setdefault(typ, []).append((t - s) / fps)
        print(name, f'{minutes:.1f} min', len(r), 'restarts', {k: (len(v), round(float(np.median(v)), 1)) for k, v in c.items()},
              'same team after', round(np.mean([p == n for s, t, typ, p, n, f in r if p in 'HA']), 2))
    json.dump(R, open('restarts.json', 'w'))
