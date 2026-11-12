"""Turn per-frame class probabilities into a label sequence with realistic possessions.

Per-frame argmax flickers, and the ranking metric counts possessions, not frames: every spurious
flip splits one real possession into two unmatched ones. Decoding is a Viterbi pass over the three
states (team 0, team 1, dead) with a fixed cost for every state change, i.e. the most likely
sequence under a sticky hidden Markov model.
"""
import numpy as np


def viterbi(log_prob, switch_cost):
    """log_prob (T, K); switch_cost scalar or (K, K) matrix of penalties with a zero diagonal."""
    n, k = log_prob.shape
    cost = np.asarray(switch_cost, dtype=np.float64)
    if cost.ndim == 0:
        cost = cost * (1.0 - np.eye(k))
    score = log_prob[0].astype(np.float64).copy()
    back = np.zeros((n, k), dtype=np.int8)
    for t in range(1, n):
        candidate = score[:, None] - cost
        back[t] = np.argmax(candidate, axis=0)
        score = candidate[back[t], np.arange(k)] + log_prob[t]
    path = np.empty(n, dtype=np.int8)
    path[-1] = int(np.argmax(score))
    for t in range(n - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return path


def upsample(prob, stride, n):
    """Model outputs at every `stride`-th frame -> one row per frame, linearly interpolated."""
    if stride == 1:
        return prob[:n]
    grid = np.arange(len(prob)) * stride
    full = np.arange(n)
    return np.stack([np.interp(full, grid, prob[:, k]) for k in range(prob.shape[1])], axis=1)


def decode(prob, switch_cost, stride=1, n=None):
    n = n or len(prob) * stride
    full = upsample(prob, stride, n)
    return viterbi(np.log(np.clip(full, 1e-6, 1.0)), switch_cost)
