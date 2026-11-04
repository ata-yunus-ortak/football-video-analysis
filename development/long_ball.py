"""Tag-guided measured long-ball runs, without interpolating missing flight."""
from dataclasses import dataclass
import numpy as np
from .dead_ball_features import extract
from .set_piece_dead_ball import normalized


@dataclass(frozen=True)
class LongBallConfig:
    min_speed_mps: float
    max_speed_mps: float
    min_distance_m: float
    min_duration_s: float
    min_straightness: float
    max_turn_degrees: float

    def __post_init__(self):
        if any(not np.isfinite(v) or v <= 0 for v in vars(self).values()):
            raise ValueError('Positive finite external long-ball settings required')
        if (self.max_speed_mps <= self.min_speed_mps or self.min_straightness > 1
                or self.max_turn_degrees > 180):
            raise ValueError('Invalid speed, straightness or turn bound')


def detect(inputs, events, cfg, blocked=None):
    features = extract(inputs)
    ball = np.asarray(inputs['ball'], float)
    period = np.asarray(inputs['period'])
    fps = float(inputs['fps'])
    n = len(ball)
    excluded = np.zeros(n, bool) if blocked is None else np.asarray(blocked, bool)
    if excluded.shape != (n,):
        raise ValueError('Aligned blocked-frame mask required')
    observed = features['ball_present'] & (features['ball_edge_margin_m'] >= 0)
    velocity = np.full((n, 2), np.nan)
    valid = observed[1:] & observed[:-1] & (period[1:] == period[:-1])
    velocity[1:] = np.where(valid[:, None], np.diff(ball, axis=0) * fps, np.nan)
    speed = np.linalg.norm(velocity, axis=1)
    bad_jump = np.isfinite(speed) & (speed > cfg.max_speed_mps)
    reliable = observed & ~bad_jump & ~excluded
    reliable[:-1] &= ~bad_jump[1:]
    step = np.zeros(n, bool)
    step[1:] = (reliable[1:] & reliable[:-1] & (period[1:] == period[:-1])
                & (speed[1:] >= cfg.min_speed_mps) & (speed[1:] <= cfg.max_speed_mps))
    turn = np.zeros(n, bool)
    for frame in np.flatnonzero(step):
        if frame > 1 and step[frame - 1]:
            cosine = np.dot(velocity[frame], velocity[frame - 1]) / (speed[frame] * speed[frame - 1])
            turn[frame] = np.clip(cosine, -1., 1.) < np.cos(np.deg2rad(cfg.max_turn_degrees))
    flight = np.zeros(n, bool)
    candidates, unresolved, by_bounds = [], [], {}
    for event in events:
        if normalized(event.get('code', '')) != 'long ball':
            continue
        a, b = float(event['start_s']), float(event['end_s'])
        if not np.isfinite(a) or not np.isfinite(b) or b < a:
            raise ValueError('Invalid automatic long-ball interval')
        left, right = max(0, round(a * fps)), min(n, round(b * fps))
        run = None
        runs = []
        # Both endpoints must lie inside the half-open tag interval. A run
        # terminates at missing data, a period change, a turn or a slow step.
        for frame in range(max(1, left + 1), right):
            if not step[frame] or turn[frame]:
                if run is not None:
                    runs.append((run - 1, frame - 1))
                    run = None
            if step[frame] and run is None:
                run = frame
        if run is not None:
            runs.append((run - 1, right - 1))
        supported = 0
        for first, last in runs:
            duration = (last - first) / fps
            if duration < cfg.min_duration_s:
                continue
            displacement = float(np.linalg.norm(ball[last] - ball[first]))
            path = float(np.linalg.norm(np.diff(ball[first:last + 1], axis=0), axis=1).sum())
            straightness = displacement / path if path else 0.
            if displacement < cfg.min_distance_m or straightness < cfg.min_straightness:
                continue
            supported += 1
            key = (first, last)
            if key in by_bounds:
                by_bounds[key]['tag_ids'].append(event.get('id'))
                continue
            candidate = {'tag_ids': [event.get('id')], 'start_frame': first, 'end_frame': last,
                         'end_frame_exclusive': last + 1, 'duration_s': duration,
                         'displacement_m': displacement, 'path_length_m': path,
                         'mean_speed_mps': path / duration, 'straightness': straightness,
                         'status': 'supported_long_ball_candidate', 'height_verified': False}
            candidates.append(candidate)
            by_bounds[key] = candidate
            # Endpoint contacts remain available. Never identify a recipient
            # merely because the travelling ball passes near that player.
            flight[first + 1:last] = True
        if not supported:
            unresolved.append({'tag_id': event.get('id'), 'reason': 'no_continuous_fast_long_run'})
    candidates.sort(key=lambda e: (e['start_frame'], e['end_frame']))
    return {'long_ball_flight_mask': flight, 'long_ball_events': candidates,
            'long_ball_unresolved_tags': unresolved, 'long_ball_selected_release': False}
