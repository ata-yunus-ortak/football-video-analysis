"""Fusion of the TCN with a second model that outputs P(dead) and P(home | alive) per frame.

This is the exact rule of the development head-to-head, with nothing left to choose:

1. The second model's two outputs become three classes [home, away, dead]:
       P(home) = (1 - P(dead)) * P(home | alive)
       P(away) = (1 - P(dead)) * (1 - P(home | alive))
       P(dead) = P(dead)
2. The TCN's probabilities (12.5 Hz) are linearly interpolated to the 25 fps frame grid.
3. Arithmetic mean on the 25 fps grid: weight * TCN + (1 - weight) * other.
4. One Viterbi pass at 25 fps over log(clip(p, 1e-6, 1)) with the same cost for every state
   change. The switch cost is therefore in units of nats per 25 fps frame transition.
   No dead-ball bias, no in/out costs, no other decoder.

Each half (or graded block) is fused and decoded on its own.
"""
import numpy as np

from .decode import upsample, viterbi
from .infer import STRIDE

WEIGHT = 0.5
SWITCH_COST = 6.0


def three_class(p_dead, p_home_given_alive):
    p_dead = np.asarray(p_dead, np.float64)
    p_home = np.asarray(p_home_given_alive, np.float64)
    return np.stack([(1 - p_dead) * p_home, (1 - p_dead) * (1 - p_home), p_dead], axis=1)


def fuse(tcn_prob, p_dead, p_home_given_alive, weight=WEIGHT, switch_cost=SWITCH_COST):
    """tcn_prob: (ceil(T / 2), 3) from infer.probabilities; p_dead, p_home_given_alive: (T,).

    Returns (T,) int8 labels: 0 home (team 0), 1 away (team 1), 2 dead.
    """
    other = three_class(p_dead, p_home_given_alive)
    tcn = upsample(np.asarray(tcn_prob, np.float64), STRIDE, len(other))
    mixed = weight * tcn + (1.0 - weight) * other
    return viterbi(np.log(np.clip(mixed, 1e-6, 1.0)), switch_cost)
