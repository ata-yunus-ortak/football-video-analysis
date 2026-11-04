"""Offline experimental motion/contact evidence; not a selected release.

All distances are metres, velocities m/s. Signed vx/vy are derived from x/y;
the export's scalar speed is not a signed velocity or height. A motion change
is only a contact candidate, and a same-team chain only a pass candidate.
"""
from dataclasses import dataclass
import numpy as np
from .dead_ball_features import extract
from .player_motion import evidence


@dataclass(frozen=True)
class MotionConfig:
    window_s: float
    fast_speed_mps: float
    max_speed_mps: float
    min_delta_velocity_mps: float
    contact_radius_m: float
    player_margin_m: float
    refractory_s: float
    max_pass_s: float

    def __post_init__(self):
        if any(not np.isfinite(v) or v <= 0 for v in vars(self).values()):
            raise ValueError("Positive finite external configuration required")
        if self.max_speed_mps <= self.fast_speed_mps:
            raise ValueError("Physical guard must exceed the fast-flight threshold")


def predict(inputs, baseline_labels, config, dribble_config=None):
    features = extract(inputs)  # rejects label/event-bearing feature inputs
    ball = np.asarray(inputs['ball'], float)
    players = np.asarray(inputs['players'], float)
    period = np.asarray(inputs['period'])
    teams = np.asarray(inputs['teams'])
    n = len(ball)
    fps = float(inputs['fps'])
    baseline = np.asarray(baseline_labels)
    if (baseline.shape != (n,) or not np.isin(baseline, ('H', 'A', 'X')).all()
            or teams.shape != (players.shape[1],) or not np.isin(teams, (0, 1)).all()):
        raise ValueError("Aligned H/A/X baseline and player team slots required")
    observed = features['ball_present'] & (features['ball_edge_margin_m'] >= 0)
    if 'player_detected' in inputs:
        detected = np.asarray(inputs['player_detected'])
        if detected.shape != players.shape[:2] or detected.dtype.kind != 'b':
            raise ValueError("Aligned boolean player observation mask required")
    else:
        detected = np.isfinite(players).all(2)
    velocity = np.full((n, 2), np.nan)
    pairs = observed[1:] & observed[:-1] & (period[1:] == period[:-1])
    velocity[1:] = np.where(pairs[:, None], np.diff(ball, axis=0) * fps, np.nan)
    speed = np.linalg.norm(velocity, axis=1)
    # Quarantine both endpoints of impossible steps; never bridge a missing
    # point, period boundary, pitch exit or quarantined jump into a pass.
    jumps = np.isfinite(speed) & (speed > config.max_speed_mps)
    reliable = observed & ~jumps
    reliable[:-1] &= ~jumps[1:]
    flight = np.isfinite(speed) & (speed >= config.fast_speed_mps)
    flight[:-1] |= flight[1:].copy() & pairs
    labels = baseline.astype('<U1', copy=True)
    reasons = np.full(n, 'baseline_slow_or_unresolved', dtype='<U48')
    labels[flight | ~reliable] = 'X'
    reasons[flight] = 'fast_ball_no_proximity_ownership'
    reasons[~reliable] = 'missing_outside_or_implausible_ball'
    player_motion = {}
    dribble_team = np.full(n, -1, int)
    if dribble_config is not None:
        player_motion = evidence(inputs, velocity, reliable, dribble_config)
        dribble_slot = player_motion['dribble_slot']
        supported = dribble_slot >= 0
        dribble_team[supported] = teams[dribble_slot[supported]]
        labels[supported] = np.where(dribble_team[supported] == 0, 'H', 'A')
        reasons[supported] = 'persistent_ball_player_comotion'
    width = max(1, int(np.ceil(config.window_s * fps)))
    refractory = max(1, int(np.ceil(config.refractory_s * fps)))
    delta = np.full(n, np.nan)
    incoming = np.full((n, 2), np.nan)
    outgoing = np.full((n, 2), np.nan)
    candidates = []
    for frame in range(width, n - width):
        region = slice(frame - width, frame + width + 1)
        if not reliable[region].all() or not np.all(period[region] == period[frame]):
            continue
        incoming[frame] = np.median(velocity[frame - width + 1:frame + 1], axis=0)
        outgoing[frame] = np.median(velocity[frame + 1:frame + width + 1], axis=0)
        delta[frame] = np.linalg.norm(outgoing[frame] - incoming[frame])
        if delta[frame] >= config.min_delta_velocity_mps:
            candidates.append(frame)
    # Select peaks without using player proximity to choose the time of a turn.
    selected = []
    for frame in sorted(candidates, key=lambda f: (-delta[f], f)):
        if all(abs(frame - other) > refractory or period[frame] != period[other]
               for other in selected):
            selected.append(frame)
    contacts = []
    for frame in sorted(selected):
        d = np.linalg.norm(players[frame] - ball[frame], axis=1)
        # Require the same slot to be measured immediately before/at/after
        # contact; tracking slots still do not prove persistent person identity.
        support = (detected[frame - 1:frame + 2].all(axis=0)
                   & np.isfinite(players[frame - 1:frame + 2]).all(axis=(0, 2)))
        d[~support | ~np.isfinite(d)] = np.inf
        order = np.argsort(d)
        slot = int(order[0]) if len(order) else -1
        closest = float(d[slot]) if slot >= 0 else np.inf
        second = float(d[order[1]]) if len(order) > 1 else np.inf
        assigned = closest <= config.contact_radius_m and second - closest >= config.player_margin_m
        team = int(teams[slot]) if assigned else None
        contacts.append({'frame': frame, 'slot': slot if assigned else None,
                         'team': team, 'delta_velocity_mps': float(delta[frame]),
                         'distance_m': closest if np.isfinite(closest) else None,
                         'status': 'candidate_contact' if assigned else 'ambiguous_motion_change'})
        if assigned:
            labels[frame] = 'H' if team == 0 else 'A'
            reasons[frame] = 'candidate_motion_contact'
        else:
            labels[frame] = 'X'
            reasons[frame] = 'ambiguous_motion_change'
    passes = []
    for sender, receiver in zip(contacts, contacts[1:]):
        start, stop = sender['frame'], receiver['frame']
        if (sender['slot'] is None or receiver['slot'] is None
                or sender['team'] != receiver['team'] or sender['slot'] == receiver['slot']
                or (stop - start) / fps > config.max_pass_s
                or np.any((dribble_team[start:stop + 1] >= 0)
                          & (dribble_team[start:stop + 1] != sender['team']))
                or not reliable[start:stop + 1].all()
                or not np.all(period[start:stop + 1] == period[start])):
            continue
        slots = [sender['slot'], receiver['slot']]
        if not (detected[start:stop + 1, slots].all()
                and np.isfinite(players[start:stop + 1, slots]).all()):
            continue
        passes.append({'start_frame': start, 'end_frame': stop,
                       'sender_slot': sender['slot'], 'receiver_slot': receiver['slot'],
                       'team': sender['team'], 'status': 'candidate_same_team_pass'})
        labels[start:stop + 1] = 'H' if sender['team'] == 0 else 'A'
        reasons[start:stop + 1] = 'candidate_same_team_pass_span'
    return {**player_motion, 'labels': labels, 'reasons': reasons, 'velocity_mps': velocity,
            'delta_velocity_mps': delta, 'fast_flight': flight,
            'contacts': contacts, 'passes': passes,
            'contact_verified': False, 'selected_release': False}
