"""H/A/D Viterbi with a frame-dependent team-switch cost (possession v2.6 candidate, experimental).

Same chain as possession/decode.py, but the cost of switching H<->A into frame t is
    switch_t = max(0, s0 - beta * logit(h_t)),
where h_t is a learned probability that a team change happens within +-0.5 s of t (possession/hazard.py).
beta = 0 gives the constant-cost decoder of decode.py. Costs are selected on external fixtures only.
"""
import numpy as np
from .decode import LETTERS, D


def switch_costs(hazard, s0, beta, eps=1e-4):
    h = np.clip(np.asarray(hazard, float), eps, 1 - eps)
    return np.maximum(0.0, s0 - beta * np.log(h / (1 - h)))


def viterbi_tv(logp, switch, out_cost, in_cost, bias_dead=0.0):
    """Exact Viterbi; switch is an array (cost of an H<->A change into frame t)."""
    n = len(logp)
    if n == 0:
        return np.zeros(0, np.int8)
    e = logp.astype(float).copy()
    e[:, D] += bias_dead
    eh, ea, ed = e[:, 0].tolist(), e[:, 1].tolist(), e[:, 2].tolist()
    sw = np.asarray(switch, float).tolist()
    sh, sa, sd = eh[0], ea[0], ed[0]
    BH = [0] * n; BA = [1] * n; BD = [2] * n
    for t in range(1, n):
        c = sw[t]
        c0, c1, c2 = sh, sa - c, sd - in_cost
        if c0 >= c1 and c0 >= c2: nh, BH[t] = c0, 0
        elif c1 >= c2: nh, BH[t] = c1, 1
        else: nh, BH[t] = c2, 2
        c0, c1, c2 = sh - c, sa, sd - in_cost
        if c1 >= c0 and c1 >= c2: na, BA[t] = c1, 1
        elif c0 >= c2: na, BA[t] = c0, 0
        else: na, BA[t] = c2, 2
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


def decode_blocks_tv(logp, hazard, period, params, outside='D'):
    """params: switch_s0, switch_beta, out_cost, in_cost, bias_dead."""
    from .features import play_blocks
    n = len(logp)
    out = np.full(n, outside, dtype='<U1')
    sw = switch_costs(hazard, params['switch_s0'], params['switch_beta'])
    for a, b in play_blocks(period):
        st = viterbi_tv(logp[a:b], sw[a:b], params['out_cost'], params['in_cost'], params.get('bias_dead', 0.0))
        out[a:b] = LETTERS[st]
    return out
