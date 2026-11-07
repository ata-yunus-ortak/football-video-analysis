"""Measured player motion and persistent ball/player co-motion evidence.

Team means are descriptive context only. Coordinates share one pitch axis;
neither a team mean vector nor a speed magnitude identifies possession.
"""
from dataclasses import dataclass
import numpy as np
from .dead_ball_features import extract
from .continuity import pair_masks


@dataclass(frozen=True)
class DribbleConfig:
    radius_m: float
    velocity_error_mps: float
    min_speed_mps: float
    max_player_speed_mps: float
    confirmation_s: float
    player_margin_m: float
    min_team_players: int

    def __post_init__(self):
        scales = (self.radius_m, self.velocity_error_mps, self.min_speed_mps,
                  self.max_player_speed_mps, self.confirmation_s, self.player_margin_m)
        if any(not np.isfinite(v) or v <= 0 for v in scales):
            raise ValueError('Positive finite dribble scales required')
        if (self.max_player_speed_mps <= self.min_speed_mps
                or type(self.min_team_players) is not int or self.min_team_players < 1):
            raise ValueError('Valid player speed guard and team coverage required')


def measured_motion(inputs, max_player_speed_mps):
    """Velocity from adjacent measured slots, quarantining both jump endpoints."""
    extract(inputs)
    players = np.asarray(inputs['players'], float)
    period = np.asarray(inputs['period'])
    n, p, _ = players.shape
    detected = np.asarray(inputs.get('player_detected', np.isfinite(players).all(2)))
    if detected.shape != (n, p) or detected.dtype.kind != 'b':
        raise ValueError('Boolean player observation flags required')
    measured = detected & np.isfinite(players).all(2) & np.isin(period, (1, 2))[:, None]
    pair = pair_masks(inputs)[1][1:] & measured[1:] & measured[:-1]
    player_velocity = np.full_like(players, np.nan)
    player_velocity[1:] = np.where(pair[..., None], np.diff(players, axis=0) * float(inputs['fps']), np.nan)
    speeds = np.linalg.norm(player_velocity, axis=2)
    jumps = np.isfinite(speeds) & (speeds > max_player_speed_mps)
    measured &= ~jumps
    measured[:-1] &= ~jumps[1:]
    valid_velocity = np.isfinite(speeds) & measured
    valid_velocity[1:] &= measured[:-1]
    player_velocity[~valid_velocity] = np.nan
    return player_velocity, measured, valid_velocity


def evidence(inputs, ball_velocity, reliable_ball, cfg):
    player_velocity, measured, valid_velocity = measured_motion(inputs, cfg.max_player_speed_mps)
    players = np.asarray(inputs['players'], float)
    ball = np.asarray(inputs['ball'], float)
    teams = np.asarray(inputs['teams'])
    period = np.asarray(inputs['period'])
    n, p, _ = players.shape
    velocity = np.asarray(ball_velocity, float)
    reliable = np.asarray(reliable_ball, bool)
    if velocity.shape != (n, 2) or reliable.shape != (n,) or teams.shape != (p,) or not np.isin(teams, (0, 1)).all():
        raise ValueError('Aligned velocities, reliability and team slots required')
    speeds = np.linalg.norm(player_velocity, axis=2)
    means = np.full((n, 2, 2), np.nan)
    mean_speed = np.full((n, 2), np.nan)
    counts = np.zeros((n, 2), int)
    for team in (0, 1):
        eligible = valid_velocity & (teams == team)[None, :]
        counts[:, team] = eligible.sum(axis=1)
        supported = counts[:, team] >= cfg.min_team_players
        total = np.where(eligible[..., None], player_velocity, 0).sum(axis=1)
        means[supported, team] = total[supported] / counts[supported, team, None]
        total_speed = np.where(eligible, speeds, 0).sum(axis=1)
        mean_speed[supported, team] = total_speed[supported] / counts[supported, team]

    distance = np.linalg.norm(players - ball[:, None, :], axis=2)
    distance[~measured | ~np.isfinite(distance)] = np.inf
    slots = np.full(n, -1, int)
    errors = np.full(n, np.nan)
    ball_speed = np.linalg.norm(velocity, axis=1)
    if p:
        order = np.argsort(distance, axis=1)
        nearest = order[:, 0]
        closest = distance[np.arange(n), nearest]
        second = distance[np.arange(n), order[:, 1]] if p > 1 else np.full(n, np.inf)
        error = np.linalg.norm(player_velocity[np.arange(n), nearest] - velocity, axis=1)
        margin = np.zeros(n)
        np.subtract(second, closest, out=margin, where=np.isfinite(closest))
        eligible = (reliable & np.isfinite(error) & (closest <= cfg.radius_m)
                    & (margin >= cfg.player_margin_m)
                    & (error <= cfg.velocity_error_mps)
                    & (ball_speed >= cfg.min_speed_mps)
                    & (speeds[np.arange(n), nearest] >= cfg.min_speed_mps))
        slots[eligible] = nearest[eligible]
        errors[eligible] = error[eligible]
    # Require the same observed slot over a duration measured in seconds.
    # Backdate confirmed runs only to their first supported velocity sample.
    owner_slot = np.full(n, -1, int)
    required = max(1, int(np.ceil(cfg.confirmation_s * float(inputs['fps']))))
    start, pending = 0, -1
    for frame, slot in enumerate(slots):
        if slot < 0:
            pending = -1
            continue
        if slot != pending or frame == 0 or period[frame] != period[frame - 1]:
            start, pending = frame, int(slot)
        if frame - start + 1 >= required:
            owner_slot[start:frame + 1] = slot
    return {'dribble_slot': owner_slot, 'dribble_velocity_error_mps': errors,
            'player_velocity_mps': player_velocity, 'team_mean_velocity_mps': means,
            'team_mean_speed_mps': mean_speed, 'team_velocity_counts': counts}
