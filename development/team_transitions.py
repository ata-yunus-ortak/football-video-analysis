"""Offline team-motion change context, corroborated by local ball evidence.

Compare the SAME measured slots before/after each candidate. A change in the
visible roster must not be interpreted as a change of team behaviour.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class TransitionConfig:
    window_s: float
    vector_change_mps: float
    speed_change_mps: float
    refractory_s: float
    evidence_window_s: float
    min_team_players: int

    def __post_init__(self):
        if any(not np.isfinite(v) or v <= 0 for v in (
                self.window_s, self.vector_change_mps, self.speed_change_mps,
                self.refractory_s, self.evidence_window_s)):
            raise ValueError('Positive finite transition scales required')
        if type(self.min_team_players) is not int or self.min_team_players < 1:
            raise ValueError('Positive team coverage required')


def detect(player_velocity, teams, period, fps, direct_team, cfg):
    v = np.asarray(player_velocity, float)
    teams, period, direct = np.asarray(teams), np.asarray(period), np.asarray(direct_team)
    n = len(period)
    if (v.ndim != 3 or v.shape[0] != n or v.shape[2] != 2
            or teams.shape != (v.shape[1],) or not np.isin(teams, (0, 1)).all()
            or direct.shape != (n,) or not np.isin(direct, (-1, 0, 1)).all()
            or not np.isfinite(fps) or fps <= 0):
        raise ValueError('Aligned team motion and direct evidence required')
    width = max(1, int(np.ceil(cfg.window_s * fps)))
    vector_change = np.full((n, 2), np.nan)
    speed_change = np.full((n, 2), np.nan)
    cohort_count = np.zeros((n, 2), int)
    score = np.full(n, np.nan)
    for frame in range(width, n - width + 1):
        region = slice(frame - width, frame + width)
        if period[frame] not in (1, 2) or not np.all(period[region] == period[frame]):
            continue
        common = np.isfinite(v[region]).all(axis=(0, 2))
        for team in (0, 1):
            cohort = common & (teams == team)
            count = int(cohort.sum())
            cohort_count[frame, team] = count
            if count < cfg.min_team_players:
                continue
            before = v[frame - width:frame, cohort]
            after = v[frame:frame + width, cohort]
            vector_change[frame, team] = np.linalg.norm(after.mean(axis=(0, 1)) - before.mean(axis=(0, 1)))
            speed_change[frame, team] = abs(np.linalg.norm(after, axis=2).mean()
                                            - np.linalg.norm(before, axis=2).mean())
        if np.isfinite(vector_change[frame]).all():
            # Both teams must exhibit a change, rather than only one runner.
            strength = np.maximum(vector_change[frame] / cfg.vector_change_mps,
                                  speed_change[frame] / cfg.speed_change_mps)
            score[frame] = float(np.min(strength))
    refractory = max(1, int(np.ceil(cfg.refractory_s * fps)))
    selected = []
    candidates = np.flatnonzero(score >= 1)
    for frame in sorted(candidates.tolist(), key=lambda f: (-score[f], f)):
        if all(period[frame] != period[other] or abs(frame - other) > refractory for other in selected):
            selected.append(frame)
    horizon = max(1, int(np.ceil(cfg.evidence_window_s * fps)))
    events = []
    for frame in sorted(selected):
        left, right = max(0, frame - horizon), min(n, frame + horizon + 1)
        before = np.flatnonzero((direct[left:frame] >= 0) & (period[left:frame] == period[frame])) + left
        after = np.flatnonzero((direct[frame:right] >= 0) & (period[frame:right] == period[frame])) + frame
        a = int(before[-1]) if len(before) else None
        b = int(after[0]) if len(after) else None
        supported = a is not None and b is not None and direct[a] != direct[b]
        events.append({'frame': frame, 'status': 'supported_turnover_candidate' if supported else 'team_motion_change_only',
                       'from_team': int(direct[a]) if supported else None,
                       'to_team': int(direct[b]) if supported else None,
                       'before_evidence_frame': a, 'after_evidence_frame': b,
                       'vector_change_mps': vector_change[frame].tolist(),
                       'speed_change_mps': speed_change[frame].tolist(),
                       'cohort_counts': cohort_count[frame].tolist()})
    return {'team_vector_change_mps': vector_change, 'team_speed_change_mps': speed_change,
            'team_change_cohort_counts': cohort_count, 'team_transition_events': events}
