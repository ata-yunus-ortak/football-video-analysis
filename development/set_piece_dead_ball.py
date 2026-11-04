"""Experimental automatic-tag prior plus measured waiting/restart evidence.

Tag spans are search windows, not D truth. Missing ball is never assigned D.
All thresholds must be selected on independently evaluable external fixtures.
"""
from dataclasses import dataclass
import re
import numpy as np
from .dead_ball_features import extract


@dataclass(frozen=True)
class DeadBallConfig:
    lookback_s: float
    lookahead_s: float
    stationary_s: float
    still_speed_mps: float
    stationary_radius_m: float
    restart_speed_mps: float
    restart_confirmation_s: float
    launch_gap_s: float
    max_ball_speed_mps: float
    contact_radius_m: float
    restart_region_m: float

    def __post_init__(self):
        if any(not np.isfinite(v) or v <= 0 for v in vars(self).values()):
            raise ValueError('Positive finite external dead-ball configuration required')
        if not self.still_speed_mps < self.restart_speed_mps < self.max_ball_speed_mps:
            raise ValueError('Ordered still/restart/maximum speed thresholds required')


def normalized(value):
    return ' '.join(re.sub(r'[-_()]', ' ', str(value)).casefold().split())


def restart_kind(event):
    if normalized(event.get('code', '')) != 'set pieces':
        return None
    values = []
    for key, items in event.get('tags', {}).items():
        if normalized(key) == 'type':
            values.extend(items if isinstance(items, list) else [items])
    kinds = set()
    for value in values:
        value = normalized(value)
        if 'retaken' in value:
            return None
        if value.startswith('kick off'):
            value = 'kick off'
        if value in ('throw in', 'goal kick', 'free kick', 'corner kick', 'kick off'):
            kinds.add(value)
    return next(iter(kinds)) if len(kinds) == 1 else None


def in_restart_region(point, pitch, kind, radius):
    x, y = point
    length, width = pitch
    if kind == 'throw in':
        return min(abs(y), abs(width - y)) <= radius
    if kind == 'corner kick':
        return min(np.linalg.norm(point - corner) for corner in
                   ([0, 0], [0, width], [length, 0], [length, width])) <= radius
    if kind == 'goal kick':
        return min(abs(x), abs(length - x)) <= radius and 0 <= y <= width
    if kind == 'kick off':
        return np.linalg.norm(point - np.asarray(pitch) / 2) <= radius
    return 0 <= x <= length and 0 <= y <= width


def apply(inputs, labels, events, cfg):
    features = extract(inputs)  # automatic tags remain a separate argument
    ball, players = np.asarray(inputs['ball'], float), np.asarray(inputs['players'], float)
    period, pitch, fps = np.asarray(inputs['period']), np.asarray(inputs['pitch']), float(inputs['fps'])
    n = len(ball)
    base = np.asarray(labels)
    if base.shape != (n,) or not np.isin(base, ('H', 'A', 'X')).all():
        raise ValueError('Aligned pre-D H/A/X labels required')
    observed = features['ball_present']
    speed = features['ball_speed_mps']
    jumps = np.isfinite(speed) & (speed > cfg.max_ball_speed_mps)
    reliable = observed & ~jumps
    reliable[:-1] &= ~jumps[1:]
    detected = np.asarray(inputs.get('player_detected', np.isfinite(players).all(2)))
    if detected.shape != players.shape[:2] or detected.dtype.kind != 'b':
        raise ValueError('Aligned boolean player observations required')
    still = reliable & np.isfinite(speed) & (speed <= cfg.still_speed_mps)
    waiting = max(1, int(np.ceil(cfg.stationary_s * fps)))
    confirmation = max(1, int(np.ceil(cfg.restart_confirmation_s * fps)))
    launch_gap = max(1, int(np.ceil(cfg.launch_gap_s * fps)))
    dead = np.zeros(n, bool)
    records = []
    for event in events:
        if normalized(event.get('code', '')) != 'set pieces':
            continue
        kind = restart_kind(event)
        record = {'tag_id': event.get('id'), 'restart_type': kind,
                  'status': 'unresolved', 'reason': 'no_supported_wait_and_restart'}
        if kind is None:
            record['reason'] = 'unsupported_ambiguous_or_retaken_type'
            records.append(record)
            continue
        a, b = float(event['start_s']), float(event['end_s'])
        if not np.isfinite(a) or not np.isfinite(b) or b < a:
            raise ValueError('Invalid automatic tag time')
        left = max(0, int(np.floor((a - cfg.lookback_s) * fps)))
        right = min(n, int(np.ceil((b + cfg.lookahead_s) * fps)))
        # Restart motion must occur near the supplied restart tag, not anywhere
        # in a long look-back region. Search can extend after its end.
        first_launch = max(1, int(round(a * fps)), left)
        found = []
        for restart in range(first_launch, right - confirmation + 1):
            end = restart + confirmation
            if (not reliable[restart:end].all() or not np.all(speed[restart:end] >= cfg.restart_speed_mps)
                    or not np.all(period[restart:end] == period[restart])):
                continue
            slow = np.flatnonzero(still[max(left, restart - launch_gap):restart])
            if not len(slow):
                continue
            last_wait = max(left, restart - launch_gap) + int(slow[-1])
            begin = last_wait
            while begin > left and still[begin - 1] and period[begin - 1] == period[restart]:
                begin -= 1
            if (last_wait - begin + 1 < waiting or not reliable[begin:end].all()
                    or not np.all(period[begin:end] == period[restart])):
                continue
            if np.max(np.linalg.norm(ball[begin:last_wait + 1] - ball[last_wait], axis=1)) > cfg.stationary_radius_m:
                continue
            # The entire preparation gap must stay near the waiting point;
            # do not pair a prior stop with an unrelated later fast pass.
            if np.max(np.linalg.norm(ball[last_wait:restart] - ball[last_wait], axis=1)) > cfg.stationary_radius_m:
                continue
            if not in_restart_region(ball[last_wait], pitch, kind, cfg.restart_region_m):
                continue
            distance = np.linalg.norm(players[last_wait] - ball[last_wait], axis=1)
            supported = detected[last_wait] & np.isfinite(distance)
            if not np.any(supported & (distance <= cfg.contact_radius_m)):
                continue
            # Include an earlier observed pitch exit only with a continuous
            # measured path and no previous restart-speed step in between.
            start = begin
            if kind in ('throw in', 'goal kick', 'corner kick'):
                for frame in range(begin - 1, left - 1, -1):
                    if (not reliable[frame] or period[frame] != period[restart]
                            or not np.isfinite(speed[frame]) or speed[frame] >= cfg.restart_speed_mps):
                        break
                    if features['observed_exit_step'][frame]:
                        start = frame
                        break
            # Deduplicate alternative motion frames for the same waiting run.
            if not found or found[-1][0] != start:
                found.append((start, restart))
        if len(found) == 1:
            start, restart = found[0]
            dead[start:restart] = True
            record.update(status='supported_dead_ball_candidate', reason='automatic_tag_plus_measured_wait_and_launch',
                          start_frame=start, restart_frame=restart,
                          boundary_kind='observed_exit_or_measured_wait_onset', exact_whistle_time_verified=False)
        elif len(found) > 1:
            record['reason'] = 'multiple_possible_restarts'
        records.append(record)
    result = base.astype('<U1', copy=True)
    result[dead] = 'D'
    return {'labels': result, 'dead_ball_mask': dead, 'dead_ball_events': records,
            'dead_ball_selected_release': False, 'dead_ball_ground_truth_verified': False}
