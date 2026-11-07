"""Tactical-first measured overlays with explicit alignment/visibility evidence.

Unselected development component. No images, labels, event inputs, interpolation,
or persistent cross-camera identity claim. Review-only clock maps are ineligible.
"""
from dataclasses import dataclass
import re
import numpy as np
from .continuity import pair_masks
from .dead_ball_features import extract


OBJECT_REASONS = {0: 'tactical_frame_fallback', 1: 'no_confirmed_visible_broadcast_track',
    2: 'association_unconfirmed', 3: 'visible_broadcast_measurement', 4: 'fresh_visible_track_link',
    5: 'ball_not_visible', 6: 'ball_ground_projection_unknown', 7: 'ball_confidence_low_or_unknown',
    8: 'ball_missing_or_implausible', 9: 'ball_not_stable', 10: 'ball_source_conflict',
    11: 'broadcast_fills_missing_tactical_ball'}


@dataclass(frozen=True)
class HybridConfig:
    min_visible_players: int
    min_visible_per_team: int
    min_match_fraction: float
    max_alignment_error_s: float
    position_radius_m: float
    assignment_margin_m: float
    velocity_error_mps: float
    max_player_speed_mps: float
    min_bulk_fast_players: int
    bulk_fast_fraction: float
    confirmation_s: float
    recovery_s: float
    min_measurement_confidence: float
    ball_agreement_m: float
    max_ball_speed_mps: float
    max_identity_gap_s: float

    def __post_init__(self):
        for name in ('min_visible_players', 'min_visible_per_team', 'min_bulk_fast_players'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError('Positive integer coverage settings required')
        if self.min_visible_players < 2 * self.min_visible_per_team:
            raise ValueError('Total coverage must allow the required coverage of both teams')
        for name in ('min_match_fraction', 'bulk_fast_fraction', 'min_measurement_confidence'):
            if not np.isfinite(getattr(self, name)) or not 0 < getattr(self, name) <= 1:
                raise ValueError('Finite fractions/confidence in (0,1] required')
        integer_names = ('min_visible_players', 'min_visible_per_team', 'min_bulk_fast_players')
        fraction_names = ('min_match_fraction', 'bulk_fast_fraction', 'min_measurement_confidence')
        for name, value in vars(self).items():
            if name not in integer_names + fraction_names and (not np.isfinite(value) or value <= 0):
                raise ValueError('Explicit positive hybrid geometry/timing settings required')


def _inside(points, pitch):
    return np.isfinite(points).all(-1) & (points >= 0).all(-1) & (points <= pitch).all(-1)


def _bool(data, name, shape):
    value = np.asarray(data[name])
    if value.shape != shape or value.dtype.kind != 'b':
        raise ValueError('Aligned boolean field required: ' + name)
    return value


def _confidence(data, name, shape):
    value = np.asarray(data[name], float)
    if value.shape != shape or np.isinf(value).any() or np.any(np.isfinite(value) & ((value < 0) | (value > 1))):
        raise ValueError('Aligned confidence in [0,1] or missing required: ' + name)
    return value


def _motion(inputs, measured, ball=False, epoch=None):
    positions = np.asarray(inputs['ball' if ball else 'players'], float)
    pairs = pair_masks(inputs)[0 if ball else 1].copy()
    pairs[1:] &= measured[1:] & measured[:-1]
    if epoch is not None:
        same = epoch[1:] == epoch[:-1]
        pairs[1:] &= same if ball else same[:, None]
    velocity = np.full_like(positions, np.nan)
    velocity[1:] = np.diff(positions, axis=0) * float(inputs['fps'])
    velocity[~pairs] = np.nan
    return velocity, pairs


def _quarantine(speed, limit):
    bad = np.isfinite(speed) & (speed > limit)
    endpoints = bad.copy()
    endpoints[:-1] |= bad[1:]
    return endpoints


def _pairs(tpos, bpos, tv, bv, tvalid, bvalid, teams, bteams, cfg):
    result = []
    for team in (0, 1):
        ti = np.flatnonzero(tvalid & (teams == team))
        bi = np.flatnonzero(bvalid & (bteams == team))
        if len(ti) < 2 or len(bi) < 2:
            continue
        distance = np.linalg.norm(tpos[ti, None] - bpos[None, bi], axis=2)
        b_for_t, t_for_b = distance.argmin(1), distance.argmin(0)
        tmargin = np.partition(distance, 1, axis=1)[:, 1] - distance.min(1)
        bmargin = np.partition(distance, 1, axis=0)[1] - distance.min(0)
        for local_t, local_b in enumerate(b_for_t):
            t, b = int(ti[local_t]), int(bi[local_b])
            if (t_for_b[local_b] == local_t and distance[local_t, local_b] <= cfg.position_radius_m
                    and tmargin[local_t] >= cfg.assignment_margin_m and bmargin[local_b] >= cfg.assignment_margin_m
                    and np.isfinite(tv[t]).all() and np.isfinite(bv[b]).all()
                    and np.linalg.norm(tv[t] - bv[b]) <= cfg.velocity_error_mps):
                result.append((t, b, float(distance[local_t, local_b])))
    return result


def fuse(tactical, broadcast, alignment, view, cfg):
    """Prefer measured visible broadcast objects only after all gates succeed.

    ``view`` comes from automatic image observations, never ATD finiteness.
    ``alignment`` must come from a validated automatic release or a generated
    synthetic mapping. Known review candidates always retain tactical input.
    Short missing tactical tracks can use a fresh established geometric link;
    no position is predicted or filled without a measured broadcast point.
    """
    extract(tactical)
    extract(broadcast)
    if 'hybrid_tracking_version' in tactical or 'hybrid_tracking_version' in broadcast:
        raise ValueError('Nested fusion is not supported')
    n, p, _ = np.asarray(tactical['players']).shape
    m, q, _ = np.asarray(broadcast['players']).shape
    teams, bteams = np.asarray(tactical['teams']), np.asarray(broadcast['teams'])
    pitch = np.asarray(tactical['pitch'], float)
    if (teams.shape != (p,) or bteams.shape != (q,) or not np.isin(teams, (0, 1)).all()
            or not np.isin(bteams, (0, 1)).all() or not np.array_equal(pitch, broadcast['pitch'])):
        raise ValueError('Common pitch axes and metadata-mapped binary teams required')
    out = {key: np.array(value, copy=True) for key, value in tactical.items()}
    out['players'], out['ball'] = np.array(tactical['players'], float, copy=True), np.array(tactical['ball'], float, copy=True)
    out['player_detected'] = np.array(tactical.get('player_detected', np.isfinite(tactical['players']).all(2)), bool, copy=True)
    out['ball_observed'] = np.array(tactical['ball_observed'], bool, copy=True)
    player_source, ball_source = np.zeros((n, p), np.int8), np.zeros(n, np.int8)
    player_reason, ball_reason = np.zeros((n, p), np.uint8), np.zeros(n, np.uint8)
    slots = np.full((n, p), -1, int)
    indices = np.full(n, -1, int)
    reasons = np.full(n, 'missing_visual_evidence', dtype='<U48')
    allowed = np.zeros(n, bool)
    matched_fraction, residual = np.full(n, np.nan), np.full(n, np.nan)

    def finish(epoch=None, native_player_pair=None, native_ball_pair=None):
        bp, pp = pair_masks(tactical)
        for f in range(1, n):
            for t in range(p):
                if player_source[f, t] != player_source[f - 1, t]:
                    pp[f, t] = False
                elif player_source[f, t]:
                    pp[f, t] = bool(indices[f] == indices[f - 1] + 1
                        and slots[f, t] == slots[f - 1, t] and epoch[indices[f]] == epoch[indices[f - 1]]
                        and native_player_pair[indices[f], slots[f, t]]
                        and tactical['period'][f] == tactical['period'][f - 1])
            if ball_source[f] != ball_source[f - 1]:
                bp[f] = False
            elif ball_source[f]:
                bp[f] = bool(indices[f] == indices[f - 1] + 1
                    and epoch[indices[f]] == epoch[indices[f - 1]] and native_ball_pair[indices[f]]
                    and tactical['period'][f] == tactical['period'][f - 1])
        out['player_pair_valid'], out['ball_pair_valid'] = pp, bp
        out['hybrid_tracking_version'] = np.asarray('tactical-first-experimental-v1')
        return {'inputs': out, 'player_source': player_source, 'ball_source': ball_source,
                'broadcast_slot': slots, 'broadcast_frame': indices,
                'frame_allowed': allowed, 'frame_reason': reasons,
                'match_fraction': matched_fraction, 'geometry_residual_m': residual,
                'player_reason_code': player_reason, 'ball_reason_code': ball_reason,
                'object_reason_legend': OBJECT_REASONS,
                'selected_release': False, 'visual_accuracy_evaluated': False}

    if alignment is None:
        reasons[:] = 'no_alignment'
        return finish()
    if (alignment.get('source_kind') == 'automatic_review_candidates'
            or alignment.get('usable_for_possession') is False or alignment.get('review_only') is True):
        reasons[:] = 'alignment_not_validated'
        return finish()
    if (alignment.get('source_kind') not in ('synthetic_known_alignment', 'externally_validated_automatic_alignment')
            or alignment.get('human_anchors_used') is not False):
        raise ValueError('Automatic validated alignment provenance required; no manual anchors')
    if alignment['source_kind'] == 'externally_validated_automatic_alignment':
        if (alignment.get('validation_source_kind') != 'permitted_external_dual_camera'
                or not isinstance(alignment.get('validation_report_sha256'), str)
                or not re.fullmatch(r'[0-9a-f]{64}', alignment['validation_report_sha256'])):
            raise ValueError('Independent external dual-camera validation provenance required')
    indices[:] = np.asarray(alignment['broadcast_frame'])
    raw_indices = np.asarray(alignment['broadcast_frame'])
    if raw_indices.shape != (n,) or raw_indices.dtype.kind not in 'iu' or np.any((indices < -1) | (indices >= m)):
        raise ValueError('Native integer broadcast frame indices or -1 required')
    verified = _bool(alignment, 'verified', (n,))
    timing_error = np.asarray(alignment['error_bound_s'], float)
    if timing_error.shape != (n,) or np.any(np.isfinite(timing_error) & (timing_error < 0)):
        raise ValueError('Aligned nonnegative timing error bounds required')
    if view is None:
        return finish()
    if view.get('source_kind') not in ('automatic_image_observations', 'synthetic_image_observations'):
        reasons[:] = 'visibility_not_independently_observed'
        return finish()
    visible = _bool(view, 'player_visible', (m, q))
    ball_visible = _bool(view, 'ball_visible', (m,))
    calibration = _bool(view, 'calibration_valid', (m,))
    ball_ground = _bool(view, 'ball_ground_valid', (m,))
    confidence = _confidence(view, 'player_confidence', (m, q))
    ball_confidence = _confidence(view, 'ball_confidence', (m,))
    epoch, kind = np.asarray(view['camera_epoch']), np.asarray(view['frame_kind'])
    if (epoch.shape != (m,) or epoch.dtype.kind not in 'iu' or kind.shape != (m,)
            or not np.isin(kind, ('live', 'replay', 'close_up', 'no_picture', 'unknown')).all()):
        raise ValueError('Aligned automatic camera epoch and frame kind required')
    if float(tactical['fps']) != float(broadcast['fps']):
        reasons[:] = 'native_frame_rates_differ'
        return finish()
    fps = float(tactical['fps'])
    tpos, bpos = np.asarray(tactical['players']), np.asarray(broadcast['players'])
    tvalid = out['player_detected'] & _inside(tpos, pitch)
    bmeasured = (np.asarray(broadcast.get('player_detected', np.isfinite(bpos).all(2)))
                 & visible & np.isfinite(bpos).all(2) & (confidence >= cfg.min_measurement_confidence))
    bvalid = bmeasured & _inside(bpos, pitch)
    tvelocity, _ = _motion(tactical, tvalid)
    bvelocity, bpair = _motion(broadcast, bmeasured, epoch=epoch)
    tspeed, bspeed = np.linalg.norm(tvelocity, axis=2), np.linalg.norm(bvelocity, axis=2)
    tvalid &= ~_quarantine(tspeed, cfg.max_player_speed_mps)
    bad_players = _quarantine(bspeed, cfg.max_player_speed_mps)
    bvalid &= ~bad_players
    fast = np.isfinite(bspeed) & (bspeed > cfg.max_player_speed_mps)
    count, total = fast.sum(1), np.isfinite(bspeed).sum(1)
    bulk = (count >= cfg.min_bulk_fast_players) & (count / np.maximum(total, 1) >= cfg.bulk_fast_fraction)
    bulk[:-1] |= bulk[1:].copy()
    bball = np.asarray(broadcast['ball'])
    ball_valid = (np.asarray(broadcast['ball_observed']) & ball_visible & ball_ground
                  & _inside(bball, pitch) & (ball_confidence >= cfg.min_measurement_confidence))
    ball_velocity, ball_pair = _motion(broadcast, ball_valid, ball=True, epoch=epoch)
    ball_valid &= ~_quarantine(np.linalg.norm(ball_velocity, axis=1), cfg.max_ball_speed_mps)
    confirmation, recovery = max(1, int(np.ceil(cfg.confirmation_s * fps))), max(1, int(np.ceil(cfg.recovery_s * fps)))
    native_ball_age = np.zeros(m, int)
    for j in range(m):
        if ball_valid[j]:
            native_ball_age[j] = (native_ball_age[j - 1] + 1 if j and ball_pair[j] else 1)
    previous_pair, pair_age = np.full(p, -1, int), np.zeros(p, int)
    cached, cached_at = np.full(p, -1, int), np.full(p, -10**9, int)
    cached_pos, cached_vel = np.full((p, 2), np.nan), np.full((p, 2), np.nan)
    stable, healthy = 0, 0
    for f, j in enumerate(indices):
        reason = None
        consecutive = (f > 0 and j >= 0 and indices[f - 1] >= 0 and j == indices[f - 1] + 1
                       and epoch[j] == epoch[indices[f - 1]] and tactical['period'][f] == tactical['period'][f - 1])
        if not consecutive:
            stable, healthy = 0, 0
            pair_age[:] = 0;previous_pair[:] = -1;cached[:] = -1
        if j < 0:
            reason = 'no_time_match'
        elif not verified[f] or not np.isfinite(timing_error[f]) or timing_error[f] > cfg.max_alignment_error_s:
            reason = 'alignment_uncertain'
        elif tactical['period'][f] not in (1, 2) or tactical['period'][f] != broadcast['period'][j]:
            reason = 'period_mismatch'
        elif kind[j] != 'live':
            reason = 'camera_' + str(kind[j])
        elif not calibration[j]:
            reason = 'invalid_calibration'
        elif bulk[j]:
            reason = 'collective_extreme_motion'
        elif not consecutive:
            reason = 'native_alignment_break'
        elif visible[j].sum() < cfg.min_visible_players:
            reason = 'too_few_visible_players'
        elif any((visible[j] & bvalid[j] & (bteams == team)).sum() < cfg.min_visible_per_team for team in (0, 1)):
            reason = 'insufficient_team_coverage'
        pairs = []
        if reason is None:
            pairs = _pairs(tpos[f], bpos[j], tvelocity[f], bvelocity[j], tvalid[f], bvalid[j], teams, bteams, cfg)
            matched_fraction[f] = len(pairs) / max(1, int((visible[j] & _inside(bpos[j], pitch)).sum()))
            residual[f] = float(np.median([d for _, _, d in pairs])) if pairs else np.nan
            if (matched_fraction[f] < cfg.min_match_fraction
                    or any(sum(teams[t] == team for t, _, _ in pairs) < cfg.min_visible_per_team for team in (0, 1))):
                reason = 'source_geometry_or_motion_disagrees'
        if reason is not None:
            reasons[f] = reason
            stable, healthy = 0, 0;pair_age[:] = 0;previous_pair[:] = -1;cached[:] = -1
            continue
        healthy += 1;stable += 1
        now = np.full(p, -1, int)
        for t, b, _ in pairs:
            now[t] = b
        pair_age = np.where((now >= 0) & (now == previous_pair) & consecutive, pair_age + 1, np.where(now >= 0, 1, 0))
        previous_pair = now
        if stable < confirmation or healthy < recovery:
            reasons[f] = 'awaiting_stable_confirmation'
            continue
        allowed[f] = True;reasons[f] = 'broadcast_visible_objects_preferred'
        player_reason[f] = 1
        used = set()
        for t, b, _ in pairs:
            if pair_age[t] < confirmation:
                player_reason[f, t] = 2
                continue
            # A broadcast slot cannot simultaneously supply two canonical players.
            cached[(cached == b) & (np.arange(p) != t)] = -1
            cached[t], cached_at[t] = b, f
            cached_pos[t], cached_vel[t] = tpos[f, t], tvelocity[f, t]
            out['players'][f, t], out['player_detected'][f, t] = bpos[j, b], True
            player_source[f, t], slots[f, t] = 1, b;used.add(b)
            player_reason[f, t] = 3
        for t in np.flatnonzero(~tvalid[f] & (cached >= 0)):
            b, age = cached[t], (f - cached_at[t]) / fps
            if (b in used or age > cfg.max_identity_gap_s or not bvalid[j, b]
                    or not np.isfinite(bvelocity[j, b]).all()
                    or np.linalg.norm(bvelocity[j, b] - cached_vel[t]) > cfg.velocity_error_mps
                    or np.linalg.norm(bpos[j, b] - cached_pos[t]) > cfg.position_radius_m + cfg.max_player_speed_mps * age):
                continue
            out['players'][f, t], out['player_detected'][f, t] = bpos[j, b], True
            player_source[f, t], slots[f, t] = 1, b;used.add(b)
            player_reason[f, t] = 4
        if not ball_visible[j]:
            ball_reason[f] = 5
        elif not ball_ground[j]:
            ball_reason[f] = 6
        elif not np.isfinite(ball_confidence[j]) or ball_confidence[j] < cfg.min_measurement_confidence:
            ball_reason[f] = 7
        elif not ball_valid[j]:
            ball_reason[f] = 8
        elif native_ball_age[j] < confirmation:
            ball_reason[f] = 9
        else:
            tactical_ball_good = bool(out['ball_observed'][f] and _inside(out['ball'][f], pitch))
            if not tactical_ball_good or np.linalg.norm(out['ball'][f] - bball[j]) <= cfg.ball_agreement_m:
                out['ball'][f], out['ball_observed'][f], ball_source[f] = bball[j], True, 1
                ball_reason[f] = 3 if tactical_ball_good else 11
            else:
                ball_reason[f] = 10
    return finish(epoch, bpair, ball_pair)
