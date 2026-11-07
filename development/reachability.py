"""Symmetric local arrival-time evidence, never standalone possession.

After a reaction interval at observed velocity, estimate travel to the current
ball position at a configured running speed. This is a modelled time, not an
observed touch or a calibrated control probability. No event/team-in-possession
input, role bonus, missing-velocity substitution or selected defaults.
"""
from dataclasses import dataclass
import numpy as np
from .player_motion import measured_motion


@dataclass(frozen=True)
class ReachabilityConfig:
    reaction_time_s: float
    running_speed_mps: float
    max_observed_speed_mps: float
    max_contact_time_s: float
    time_margin_s: float
    min_team_players: int

    def __post_init__(self):
        if any(not np.isfinite(v) or v <= 0 for v in (
                self.reaction_time_s, self.running_speed_mps,
                self.max_observed_speed_mps, self.max_contact_time_s, self.time_margin_s)):
            raise ValueError('Positive finite externally supplied reachability settings required')
        if (self.max_observed_speed_mps < self.running_speed_mps
                or self.max_contact_time_s <= self.reaction_time_s
                or type(self.min_team_players) is not int or self.min_team_players < 1):
            raise ValueError('Consistent running speed, time horizon and team coverage required')


def estimate(inputs, reliable_ball, cfg):
    velocity, measured, valid = measured_motion(inputs, cfg.max_observed_speed_mps)
    players = np.asarray(inputs['players'], float)
    teams = np.asarray(inputs['teams'])
    ball = np.asarray(inputs['ball'], float)
    reliable = np.asarray(reliable_ball)
    n, p, _ = players.shape
    if (reliable.shape != (n,) or reliable.dtype.kind != 'b'
            or teams.shape != (p,) or not np.isin(teams, (0, 1)).all()):
        raise ValueError('Aligned boolean reliability and team slots required')
    projected = players + velocity * cfg.reaction_time_s
    times = cfg.reaction_time_s + np.linalg.norm(projected - ball[:, None], axis=2) / cfg.running_speed_mps
    observed = (np.asarray(inputs['ball_observed']) & np.isfinite(ball).all(1)
                & (ball >= 0).all(1) & (ball <= np.asarray(inputs['pitch'])).all(1))
    times[~valid | ~(reliable & observed)[:, None]] = np.nan
    counts = np.column_stack([(valid & (teams == team)[None]).sum(1) for team in (0, 1)])
    team_times = np.full((n, 2), np.nan)
    for team in (0, 1):
        slots = teams == team
        if slots.any():
            best = np.min(np.where(np.isfinite(times[:, slots]), times[:, slots], np.inf), axis=1)
            keep = np.isfinite(best) & (counts[:, team] >= cfg.min_team_players)
            team_times[keep, team] = best[keep]
    return {'arrival_time_s': times, 'team_arrival_time_s': team_times,
            'arrival_team_counts': counts, 'arrival_player_velocity_mps': velocity}


def resolve_contact(frame, distances, support, arrival, cfg, radius_m):
    """Resolve only a motion-change contact with two locally plausible players.

    Retain ambiguity if any nearby candidate has unknown velocity/visibility.
    A runner elsewhere on the pitch cannot be assigned a contact at this point.
    """
    times = arrival['arrival_time_s'][frame]
    nearby = np.isfinite(distances) & (distances <= radius_m)
    if (nearby.sum() < 2 or not support[nearby].all()
            or not np.isfinite(times[nearby]).all()
            or np.any(arrival['arrival_team_counts'][frame] < cfg.min_team_players)):
        return None
    slots = np.flatnonzero(nearby)
    order = slots[np.argsort(times[slots], kind='stable')]
    best, runner_up = int(order[0]), int(order[1])
    margin = float(times[runner_up] - times[best])
    if times[best] > cfg.max_contact_time_s or margin < cfg.time_margin_s:
        return None
    return {'slot': best, 'arrival_time_s': float(times[best]), 'arrival_margin_s': margin}
