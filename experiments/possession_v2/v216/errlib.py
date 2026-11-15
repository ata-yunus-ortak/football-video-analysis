"""Shared code of the error-pattern work of 15 Nov (development only, on copies already scored in earlier validations):
loads the stored probabilities of both model families for a development copy, forms the v2.15 decision (pool 0.2, v2
decoder) and extracts possessions and their matching exactly as the organisers' metric does. Nothing opens the provided match."""
import sys, glob, os, json, numpy as np, warnings
warnings.filterwarnings('ignore')
for p in ('/home/claude/work/v213', '/home/claude/sc', '/home/claude/work/v214', '/home/claude/work/v215'):
    sys.path.insert(0, p)
from possession.decode import emissions, decode_blocks, LETTERS
from possession.features import play_blocks
from possession.evaluate import score
from possession import official_metrics as pm
import lib214 as L
import pooling

DEC = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}       # v2.1 path, the release constants
DEV = '/home/claude/work/v216/dev/'
IOUS = (0.3, 0.4, 0.5, 0.6, 0.7)
FPS = 25


def copies():
    return sorted(f for f in glob.glob(L.PROBS + '*.npz') if not f.endswith('.feat.npz') and '.m_' not in f)


def load(f):
    """dict of one development copy with the v2.15 decision ('pred'); cached."""
    key = os.path.basename(f)[:-4]
    c = DEV + key + '.npz'
    d = dict(np.load(f, allow_pickle=False))
    d['key'] = key; d['match'] = key.split('_')[0]; d['sim2'] = key.endswith('sim2'); d['path'] = str(d['path'])
    if os.path.exists(c):
        z = np.load(c)
        d.update(tcn=z['tcn'], pd2=z['pd2'], ph2=z['ph2'], pred=z['pred'])
        return d
    tags = ['d4s0', 'd4s1', 'd4s2'] if key.startswith('J03') else ['d6s0', 'd6s1', 'd6s2']
    tcn = L.ensemble_tcn([f[:-4] + '.m_' + t + '.npz' for t in tags], d['per'])
    if d['path'] == 'v2.1':
        pd2, ph2 = pooling.pool(tcn, d['p_dead'], d['p_home'])
        pred = decode_blocks(emissions(pd2, ph2), d['per'], DEC)
    else:
        pd2, ph2, pred = d['p_dead'], d['p_home'], d['v2_labels']
    np.savez_compressed(c, tcn=tcn.astype(np.float32), pd2=pd2, ph2=ph2, pred=pred)
    d.update(tcn=tcn, pd2=pd2, ph2=ph2, pred=pred)
    return d


def spells(labels, per):
    """[(start, stop, team)] maximal H or A runs inside each play block (team 0 = H, 1 = A); original frame indices."""
    out = []
    lab = np.asarray(labels)
    for a, b in play_blocks(per):
        w = lab[a:b]
        br = np.flatnonzero(w[1:] != w[:-1]) + 1
        bo = np.concatenate(([0], br, [len(w)]))
        for i in range(len(bo) - 1):
            if w[bo[i]] in ('H', 'A'):
                out.append((a + int(bo[i]), a + int(bo[i + 1]), 0 if w[bo[i]] == 'H' else 1))
    return out


def overlaps(gs, ps):
    """[(iou, i, j)] same-team overlapping pairs, sorted as the organisers sort them (two-pointer sweep)."""
    out = []
    j0 = 0
    for i, (a, b, k) in enumerate(gs):
        while j0 < len(ps) and ps[j0][1] <= a:
            j0 += 1
        j = j0
        while j < len(ps) and ps[j][0] < b:
            c, d, kk = ps[j]
            if kk == k and d > a and c < b:
                inter = min(b, d) - max(a, c); union = max(b, d) - min(a, c)
                out.append((inter / float(union), i, j))
            j += 1
    out.sort(key=lambda t: (-t[0], t[1], t[2]))
    return out


def match(gs, ps):
    """credit per GT spell and per predicted spell (share of the five IoU thresholds at which it is matched), the
    partner at 0.3, and spellF1."""
    ov = overlaps(gs, ps)
    cg, cp = np.zeros(len(gs)), np.zeros(len(ps))
    pg = np.full(len(gs), -1); pp = np.full(len(ps), -1); ig = np.zeros(len(gs))
    f1 = []
    for th in IOUS:
        mg, mp = set(), set()
        for iou, i, j in ov:
            if iou < th:
                break
            if i in mg or j in mp:
                continue
            mg.add(i); mp.add(j)
            cg[i] += 0.2; cp[j] += 0.2
            if th == IOUS[0]:
                pg[i], pp[j], ig[i] = j, i, iou
        tp = len(mg)
        f1.append(2.0 * tp / (len(gs) + len(ps)) if gs or ps else 0.0)
    return cg, cp, pg, pp, ig, float(np.mean(f1))


def f1_of(lab, pred, per):
    return match(spells(lab, per), spells(pred, per))[5]


def controlled(labels, per, tau):
    """Labels in which a possession shorter than tau frames that follows a possession of the other team (no stoppage in
    between) does not count: the previous team keeps the ball ("a simple touch without control" of CHALLENGE.md).
    The first possession after a stoppage or at the start of a block always counts."""
    lab = np.asarray(labels).copy()
    if tau <= 0:
        return lab
    for a, b in play_blocks(per):
        w = lab[a:b]
        br = np.flatnonzero(w[1:] != w[:-1]) + 1
        bo = np.concatenate(([0], br, [len(w)]))
        cur = None
        for i in range(len(bo) - 1):
            s, e = bo[i], bo[i + 1]
            x = w[s]
            if x not in ('H', 'A'):
                cur = None
            elif cur is None or x == cur:
                cur = x
            elif e - s >= tau:
                cur = x
            else:
                w[s:e] = cur
        lab[a:b] = w
    return lab
