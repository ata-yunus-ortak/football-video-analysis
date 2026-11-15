"""Development code for the tag-rescue idea (15 Nov): a set-piece tag says a restart happened inside its window, so a dead-ball
stretch ends there. If the decision has no D around the window, force one where the decoder objects least.
Simulated tags only (external matches have no Smart Tagging). Nothing opens the provided match."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/work/v216')
import errlib as E
from possession.decode import emissions, viterbi, LETTERS
from possession.features import play_blocks

FPS = 25
PUB = {'throw-in': 26, 'corner kick': 12, 'goal kick': 10, 'free kick': 5, 'kick off': 4}     # DATA.md (kick-offs after goals)
MIN = 158857 / 25.0 / 60.0
R = json.load(open('/home/claude/work/v217/restarts.json'))
REG = {'clean': dict(scale=(1, 1), lag=(0, 0), sigma=(0.3, 0.3), false=(0, 0)),
       'default': dict(scale=(0.5, 1.5), lag=(-1.5, 1.5), sigma=(0.3, 3.0), false=(0, 0.15)),
       'noisy': dict(scale=(0.5, 0.5), lag=(1.5, 1.5), sigma=(3.0, 3.0), false=(0.15, 0.15)),
       'false30': dict(scale=(0.5, 1.5), lag=(-1.5, 1.5), sigma=(0.3, 3.0), false=(0.30, 0.30)),
       'second': dict(scale=(1, 1), lag=(0, 0), sigma=(1.0, 1.0), false=(0.05, 0.05))}       # "accurate to about a second"


def sim_tags(match, lab, per, rng, regime):
    """[(start, end, type, true restart frame or -1)] set-piece windows in frames."""
    q = REG[regime]
    rr = R[match]['restarts']; minutes = R[match]['minutes']
    cnt = {}
    for s, t, typ, p, n, first in rr:
        cnt[typ] = cnt.get(typ, 0) + 1
    scale = {k: rng.uniform(*q['scale']) for k in PUB}
    lag, sigma, fr = rng.uniform(*q['lag']), rng.uniform(*q['sigma']), rng.uniform(*q['false'])
    out = []
    for s, t, typ, p, n, first in rr:
        if rng.random() >= min(1.0, PUB[typ] / MIN * minutes * scale[typ] / cnt[typ]):
            continue
        a = t - rng.uniform(0.5, 4) * FPS + (lag + rng.normal(0, sigma)) * FPS
        b = t + rng.uniform(1, 5) * FPS + (lag + rng.normal(0, sigma)) * FPS
        b = max(b, a + 0.2 * FPS)
        out.append((int(round(a)), int(round(b)), typ, t))
    alive = np.flatnonzero(np.isin(lab, ('H', 'A')) & (per > 0))
    for _ in range(rng.poisson(fr * len(out))):
        f = int(alive[rng.integers(len(alive))])
        out.append((f, f + int(rng.uniform(3, 7) * FPS), 'false', -1))
    return out


def fwd_bwd(e, sw, oc, ic):
    """alpha[t, s]: best score of a path ending in s at t; beta[t, s]: best score of the rest after t given s at t."""
    n = len(e)
    al = np.empty((n, 3)); be = np.zeros((n, 3))
    eh, ea, ed = e[:, 0].tolist(), e[:, 1].tolist(), e[:, 2].tolist()
    h, a, d = eh[0], ea[0], ed[0]
    AL = [(h, a, d)]
    for t in range(1, n):
        h, a, d = max(h, a - sw, d - ic) + eh[t], max(h - sw, a, d - ic) + ea[t], max(h - oc, a - oc, d) + ed[t]
        AL.append((h, a, d))
    al[:] = AL
    h = a = d = 0.0
    BE = [(0.0, 0.0, 0.0)] * n
    for t in range(n - 2, -1, -1):
        xh, xa, xd = eh[t + 1] + h, ea[t + 1] + a, ed[t + 1] + d
        h, a, d = max(xh, xa - sw, xd - oc), max(xh - sw, xa, xd - oc), max(xh - ic, xa - ic, xd)
        BE[t] = (h, a, d)
    be[:] = BE
    return al, be


def rescue(pd2, ph2, pred, per, tags, dec, pre=5.0, post=0.0, cmax=1e9, bridge=0.0, minlen=0):
    """Returns (labels, report). For every tag window without a D of the decision in [start - pre, end + post): force the
    decoder through D at the frame of that region where it costs least, if the cost (in the decoder's log units) is <= cmax.
    bridge > 0: a possession piece shorter than bridge seconds between the forced D and the next team change is written D.
    minlen: forced runs shorter than minlen frames are widened symmetrically."""
    out = pred.copy(); rep = []
    logp = emissions(pd2, ph2)
    for a0, b0 in play_blocks(per):
        e = logp[a0:b0].astype(float).copy(); e[:, 2] += dec.get('bias_dead', 0.0)
        cur = out[a0:b0]
        todo = []
        isd = cur == 'D'
        cs = np.concatenate(([0], np.cumsum(isd)))
        al = be = None
        for (ta, tb, typ, truth) in tags:
            r0, r1 = max(a0, ta - int(pre * FPS)), min(b0, tb + int(post * FPS))
            if r1 <= r0 or ta >= b0 or tb <= a0:
                continue
            r0 -= a0; r1 -= a0
            if cs[r1] - cs[r0] > 0:
                rep.append((ta, tb, typ, truth, 'has_d', 0.0, -1)); continue
            if al is None:
                al, be = fwd_bwd(e, dec['switch'], dec['out_cost'], dec['in_cost'])
                best = al[-1].max()
            thr = al[r0:r1, 2] + be[r0:r1, 2]
            k = int(np.argmax(thr)); cost = float(best - thr[k])
            if cost > cmax:
                rep.append((ta, tb, typ, truth, 'too_costly', cost, -1)); continue
            todo.append(r0 + k)
            rep.append((ta, tb, typ, truth, 'forced', cost, a0 + r0 + k))
        if not todo:
            continue
        e2 = e.copy()
        for k in todo:
            e2[k, 0] = e2[k, 1] = -1e9
        st = viterbi(e2, dec['switch'], dec['out_cost'], dec['in_cost'], 0.0)
        new = LETTERS[st]
        if minlen or bridge:
            for k in todo:
                i, j = k, k + 1
                while i > 0 and new[i - 1] == 'D':
                    i -= 1
                while j < len(new) and new[j] == 'D':
                    j += 1
                if j - i < minlen:
                    ext = (minlen - (j - i) + 1) // 2
                    i, j = max(0, i - ext), min(len(new), j + ext)
                    new[i:j] = 'D'
                if bridge:
                    lim = int(bridge * FPS)
                    # piece after the run up to the next change
                    u = j
                    while u < len(new) and new[u] == new[j] and u - j <= lim:
                        u += 1
                    if u < len(new) and new[u] != new[j] and new[u] != 'D' and u - j <= lim and j < len(new):
                        new[j:u] = 'D'
                    v = i
                    while v > 0 and new[v - 1] == new[i - 1] and i - v <= lim:
                        v -= 1
                    if v > 0 and i > 0 and new[v - 1] != new[i - 1] and new[v - 1] != 'D' and i - v <= lim:
                        new[v:i] = 'D'
        out[a0:b0] = new
    return out, rep


def macro_f1(lab, pred, per):
    g = per > 0
    f = []
    for c in 'HAD':
        tp = np.sum((lab == c) & (pred == c) & g); fp = np.sum((lab != c) & (pred == c) & g); fn = np.sum((lab == c) & (pred != c) & g)
        f.append(2 * tp / max(2 * tp + fp + fn, 1))
    return float(np.mean(f))
