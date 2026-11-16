"""Per-frame features from team-level tracking. No player identities are used anywhere.

Input (one half): ball (T,2) and two teams (T,N,2), metres with the pitch centre at the origin,
NaN where an object is not observed. Team 0 is rotated so that it always attacks towards +x, which
makes every feature symmetric under "swap the teams"; the classes are then team 0 / team 1 / dead.

Everything is scaled by fixed constants so no statistic is ever fitted to a particular match.
"""
import warnings

import numpy as np

HALF_LENGTH, HALF_WIDTH = 52.5, 34.0
FPS = 25
N_FEATURES = 37


def orientation(team0, team1):
    """+1 if team 0 already attacks towards +x (its players sit at lower x), else -1."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return 1.0 if np.nanmean(team0[:, :, 0]) <= np.nanmean(team1[:, :, 0]) else -1.0


def _interp(xy):
    """Linear interpolation through gaps, plus frames since last / until next observation."""
    n = len(xy)
    seen = ~np.isnan(xy[:, 0])
    index = np.arange(n)
    if not seen.any():
        return np.zeros_like(xy), np.full(n, n), np.full(n, n)
    filled = np.stack([np.interp(index, index[seen], xy[seen, k]) for k in (0, 1)], axis=1)
    last = np.maximum.accumulate(np.where(seen, index, -1))
    since = np.where(last >= 0, index - last, n)
    nxt = np.minimum.accumulate(np.where(seen, index, 2 * n)[::-1])[::-1]
    until = np.where(nxt < 2 * n, nxt - index, n)
    return filled.astype(np.float32), since, until


def _velocity(track, lag=2):
    """Central-difference velocity (m/s) per track; NaN where either end is missing or absurd."""
    vel = np.full_like(track, np.nan)
    vel[lag:-lag] = (track[2 * lag:] - track[:-2 * lag]) * (FPS / (2.0 * lag))
    speed = np.hypot(vel[..., 0], vel[..., 1])
    vel[speed > 12.0] = np.nan
    return vel


def _nan(func, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return np.nan_to_num(func(*args, **kwargs), nan=0.0)


def build(ball, team0, team1):
    """(T, N_FEATURES) float32 feature matrix for one half."""
    sign = orientation(team0, team1)
    ball = ball[:, :2] * sign
    team0 = team0 * sign
    team1 = team1 * sign
    n = len(ball)

    seen = ~np.isnan(ball[:, 0])
    pos, since, until = _interp(ball)
    gap = np.where(seen, 0, since + until)
    bvel = np.zeros_like(pos)
    bvel[2:-2] = (pos[4:] - pos[:-4]) * (FPS / 4.0)
    bspeed = np.hypot(bvel[:, 0], bvel[:, 1])
    margin = np.minimum(HALF_LENGTH - np.abs(pos[:, 0]), HALF_WIDTH - np.abs(pos[:, 1]))

    cols = [seen.astype(np.float32), pos[:, 0] / HALF_LENGTH, pos[:, 1] / HALF_WIDTH,
            np.clip(margin / 10.0, -1, 3), np.clip(bspeed / 20.0, 0, 2),
            np.clip(bvel[:, 0] / 20.0, -2, 2),
            np.log1p(np.minimum(since, 750)) / 5.0, np.log1p(np.minimum(until, 750)) / 5.0,
            np.log1p(np.minimum(gap, 750)) / 5.0]

    dists = []
    for team in (team0, team1):
        d = np.hypot(team[:, :, 0] - pos[:, None, 0], team[:, :, 1] - pos[:, None, 1])
        nearest = _nan(np.nanmin, d, axis=1)
        nearest[np.isnan(d).all(axis=1)] = 50.0
        dists.append(nearest)
        cols.append(np.log1p(nearest) / 3.0)
        cols.append(np.clip(np.nansum(d < 3.0, axis=1) / 3.0, 0, 2))
    cols.append(np.tanh((dists[1] - dists[0]) / 3.0))

    speeds = []
    for team in (team0, team1):
        vel = _velocity(team)
        speed = np.hypot(vel[..., 0], vel[..., 1])
        speeds.append(speed)
        x, y = team[:, :, 0], team[:, :, 1]
        count = (~np.isnan(x)).sum(axis=1)
        ordered = np.sort(np.where(np.isnan(x), np.inf, x), axis=1)
        low2 = np.where(count >= 2, ordered[:, 1], 0.0)
        ordered_desc = -np.sort(np.where(np.isnan(x), np.inf, -x), axis=1)
        high2 = np.where(count >= 2, ordered_desc[:, 1], 0.0)
        centroid = _nan(np.nanmean, x, axis=1)
        cols += [_nan(np.nanmean, vel[..., 0], axis=1) / 5.0,
                 _nan(np.nanmean, speed, axis=1) / 5.0,
                 centroid / HALF_LENGTH, _nan(np.nanmean, y, axis=1) / HALF_WIDTH,
                 _nan(np.nanstd, x, axis=1) / 20.0, _nan(np.nanstd, y, axis=1) / 20.0,
                 count / 11.0, (pos[:, 0] - centroid) / 30.0,
                 np.nan_to_num(low2, posinf=0.0) / HALF_LENGTH,
                 np.nan_to_num(high2, neginf=0.0) / HALF_LENGTH]
    all_speed = np.concatenate(speeds, axis=1)
    cols.append(_nan(np.nanmean, all_speed < 1.0, axis=1))
    cols.append(_nan(np.nanmax, all_speed, axis=1) / 10.0)
    # Speed of whoever is closest to the ball, either team: a carrier moves, a ball boy does not.
    both = np.concatenate([team0, team1], axis=1)
    d = np.hypot(both[:, :, 0] - pos[:, None, 0], both[:, :, 1] - pos[:, None, 1])
    nearest = np.argmin(np.where(np.isnan(d), np.inf, d), axis=1)
    cols.append(np.nan_to_num(all_speed[np.arange(n), nearest], nan=0.0) / 8.0)

    feats = np.stack(cols, axis=1).astype(np.float32)
    assert feats.shape[1] == N_FEATURES, feats.shape
    return feats, sign


def swap_labels(label):
    """Labels after exchanging the two teams: 0 <-> 1, dead stays dead."""
    return np.where(label == 2, 2, 1 - label).astype(np.int8)
