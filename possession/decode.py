"""H/A/D Viterbi decoding of per-frame probabilities with transition costs.

States: 0=H, 1=A, 2=D. Score = sum_t log P(state_t) + bias_D*[state_t==D] - transition costs.
Costs are in log-probability units; they are selected on external fixtures only.
"""
import numpy as np

H, A, D = 0, 1, 2


def emissions(p_dead, p_home, eps=1e-4):
    p_dead = np.clip(np.asarray(p_dead, float), eps, 1 - eps)
    p_home = np.clip(np.asarray(p_home, float), eps, 1 - eps)
    return np.stack([np.log1p(-p_dead) + np.log(p_home), np.log1p(-p_dead) + np.log1p(-p_home),
                     np.log(p_dead)], 1)


def viterbi(logp, switch, out_cost, in_cost, bias_dead=0.0):
    """Exact Viterbi for the 3-state chain; logp is (n,3). Returns int8 states."""
    n = len(logp)
    if n == 0:
        return np.zeros(0, np.int8)
    e = logp.astype(float).copy()
    e[:, D] += bias_dead
    back = np.zeros((n, 3), np.int8)
    eh, ea, ed = e[:, 0].tolist(), e[:, 1].tolist(), e[:, 2].tolist()
    sh, sa, sd = eh[0], ea[0], ed[0]
    bh, ba, bd = back[:, 0], back[:, 1], back[:, 2]
    BH = [0] * n; BA = [1] * n; BD = [2] * n
    for t in range(1, n):
        # into H
        c0, c1, c2 = sh, sa - switch, sd - in_cost
        if c0 >= c1 and c0 >= c2: nh, BH[t] = c0, 0
        elif c1 >= c2: nh, BH[t] = c1, 1
        else: nh, BH[t] = c2, 2
        # into A
        c0, c1, c2 = sh - switch, sa, sd - in_cost
        if c1 >= c0 and c1 >= c2: na, BA[t] = c1, 1
        elif c0 >= c2: na, BA[t] = c0, 0
        else: na, BA[t] = c2, 2
        # into D
        c0, c1, c2 = sh - out_cost, sa - out_cost, sd
        if c2 >= c0 and c2 >= c1: nd, BD[t] = c2, 2
        elif c0 >= c1: nd, BD[t] = c0, 0
        else: nd, BD[t] = c1, 1
        sh, sa, sd = nh + eh[t], na + ea[t], nd + ed[t]
    states = np.zeros(n, np.int8)
    s = int(np.argmax([sh, sa, sd]))
    tables = (BH, BA, BD)
    for t in range(n - 1, -1, -1):
        states[t] = s
        s = tables[s][t]
    return states


LETTERS = np.array(['H', 'A', 'D'])


def decode_blocks(logp, period, params, outside='D'):
    from .features import play_blocks
    n = len(logp)
    out = np.full(n, outside, dtype='<U1')
    for a, b in play_blocks(period):
        st = viterbi(logp[a:b], params['switch'], params['out_cost'], params['in_cost'],
                     params.get('bias_dead', 0.0))
        out[a:b] = LETTERS[st]
    return out
