"""Measured adjacency masks, including native-source continuity after fusion."""
import numpy as np


def pair_masks(inputs):
    ball, players = np.asarray(inputs['ball']), np.asarray(inputs['players'])
    period, frame = np.asarray(inputs['period']), np.asarray(inputs['frame'])
    n = len(ball)
    if (ball.shape != (n, 2) or players.ndim != 3 or players.shape[0] != n or players.shape[2] != 2
            or period.shape != (n,) or frame.shape != (n,)):
        raise ValueError('Aligned source arrays required for continuity')
    observed = np.asarray(inputs['ball_observed'])
    detected = np.asarray(inputs.get('player_detected', np.isfinite(players).all(2)))
    if observed.shape != (n,) or detected.shape != players.shape[:2] or observed.dtype.kind != 'b' or detected.dtype.kind != 'b':
        raise ValueError('Boolean observation masks required')
    adjacent = np.zeros(n, bool)
    adjacent[1:] = ((np.diff(frame) == 1) & (period[1:] == period[:-1])
                    & np.isin(period[1:], (1, 2)))
    bp = observed & np.isfinite(ball).all(1)
    pp = detected & np.isfinite(players).all(2)
    ball_pair = adjacent.copy()
    player_pair = np.broadcast_to(adjacent[:, None], players.shape[:2]).copy()
    ball_pair[1:] &= bp[1:] & bp[:-1]
    player_pair[1:] &= pp[1:] & pp[:-1]
    names = ('ball_pair_valid', 'player_pair_valid')
    if 'hybrid_tracking_version' in inputs and any(name not in inputs for name in names):
        raise ValueError('Hybrid measurements must retain both source-continuity masks')
    for name, target in zip(names, (ball_pair, player_pair)):
        if name in inputs:
            value = np.asarray(inputs[name])
            if value.shape != target.shape or value.dtype.kind != 'b':
                raise ValueError('Source continuity masks must be aligned booleans')
            target &= value
    return ball_pair, player_pair
