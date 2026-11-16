"""Make clean external tracking look like automatic, uncorrected tracking.

The external training matches are corrected optical tracking: the ball is present on every frame
and every player has one continuous track. The competition ATD is automatic: the ball is missing on
about four frames in ten, players drop out, and positions jitter. A model trained on the clean
version would lean on a ball signal it will not have, so every training replica is degraded with
randomly drawn noise parameters (domain randomisation). Nothing here is fitted to the competition
match: the only anchors are the figures published in the challenge documentation (ball missing on
~41% of graded frames, ~20.5 tracked players of 22).

Missingness is driven by physical causes only -- ball height, ball speed, crowding around the ball
and the ball leaving the pitch -- never by the possession label itself.
"""
import numpy as np

HALF_LENGTH, HALF_WIDTH = 52.5, 34.0


def _markov_mask(rng, p_off, p_on):
    """Boolean visibility from a two-state chain with per-frame switch-off / switch-on hazards."""
    n = len(p_off)
    draws = rng.random(n)
    visible = np.empty(n, bool)
    state = True
    for i in range(n):
        if state:
            if draws[i] < p_off[i]:
                state = False
        elif draws[i] < p_on[i]:
            state = True
        visible[i] = state
    return visible


def _smooth_noise(rng, shape, sigma, span=5):
    """Temporally correlated jitter: white noise averaged over `span` frames, rescaled to sigma."""
    noise = rng.normal(0.0, 1.0, shape)
    kernel = np.ones(span) / span
    noise = np.apply_along_axis(lambda col: np.convolve(col, kernel, mode="same"), 0, noise)
    return (noise * sigma * np.sqrt(span)).astype(np.float32)


def degrade(ball, team0, team1, rng, level=None):
    """Return degraded copies (ball (T,2), team0 (T,N,2), team1 (T,N,2)).

    ball may be (T,2) or (T,3); a third column is height in metres and is only used to decide
    when the ball is likely to be lost. `level` in [0,1] overrides the random severity draw.
    """
    n = len(ball)
    xy = ball[:, :2].astype(np.float32).copy()
    height = ball[:, 2] if ball.shape[1] > 2 else np.zeros(n, np.float32)
    present = ~np.isnan(xy[:, 0])
    filled = np.where(present[:, None], xy, 0.0)

    severity = rng.uniform(0.0, 1.0) if level is None else level
    step = np.zeros(n, np.float32)
    step[1:] = np.hypot(*(filled[1:] - filled[:-1]).T) * 25.0
    both = np.concatenate([team0, team1], axis=1)
    dist = np.hypot(both[:, :, 0] - filled[:, None, 0], both[:, :, 1] - filled[:, None, 1])
    crowd = np.nansum(dist < 2.5, axis=1)

    base_off = rng.uniform(0.004, 0.012) * (0.5 + severity)
    p_off = base_off * (1.0
                        + rng.uniform(2.0, 10.0) * (height > rng.uniform(1.2, 2.5))
                        + rng.uniform(0.5, 3.0) * np.clip(crowd - 1, 0, 4)
                        + rng.uniform(0.0, 4.0) * (step > rng.uniform(12.0, 22.0)))
    mean_gap = rng.uniform(12.0, 45.0) * (0.6 + 0.8 * severity)
    p_on = np.full(n, 1.0 / mean_gap)
    margin = rng.uniform(0.0, 2.5)
    outside = (np.abs(filled[:, 0]) > HALF_LENGTH + margin) | (np.abs(filled[:, 1]) > HALF_WIDTH + margin)
    p_off = np.where(outside, rng.uniform(0.15, 0.6), p_off)
    p_on = np.where(outside, rng.uniform(0.0, 0.03), p_on)
    visible = _markov_mask(rng, np.clip(p_off, 0, 1), p_on) & present

    xy += _smooth_noise(rng, xy.shape, rng.uniform(0.03, 0.30))
    # False ball detections: a short burst sitting on a random player.
    for _ in range(rng.poisson(rng.uniform(0.0, 1.5) * n / 1500.0)):
        start = rng.integers(0, n)
        length = rng.integers(2, 20)
        player = both[start, rng.integers(0, both.shape[1])]
        if not np.isnan(player[0]):
            xy[start:start + length] = player + rng.normal(0, 0.5, 2)
            visible[start:start + length] = True
    xy[~visible] = np.nan

    teams = []
    for team in (team0, team1):
        team = team.astype(np.float32).copy()
        team += _smooth_noise(rng, team.shape, rng.uniform(0.03, 0.25))
        off = rng.uniform(0.0002, 0.0015) * (0.5 + severity)
        on = 1.0 / rng.uniform(15.0, 75.0)
        for j in range(team.shape[1]):
            keep = _markov_mask(rng, np.full(n, off), np.full(n, on))
            team[~keep, j] = np.nan
        teams.append(team)
    return xy, teams[0], teams[1]
