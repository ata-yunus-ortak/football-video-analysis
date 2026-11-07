"""Read-only association of image ball tracks with automatic tracking projections.

Agreement is supporting evidence, never ground truth or an ownership decision.
Unknown airborne geometry cannot select a candidate. No coordinates are filled.
"""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class SupportConfig:
    radius_diagonal: float
    separation_diagonal: float
    max_clock_error_s: float

    def __post_init__(self):
        if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
               for v in vars(self).values()):
            raise ValueError('Explicit positive finite support parameters required')
        if not self.separation_diagonal < self.radius_diagonal <= 1:
            raise ValueError('Separation must be smaller than image-diagonal radius')


def project_ground_ball(xy_m, pitch_m, normalized_pitch_to_image):
    """Ground-only pitch metres -> native pixels; no centering convention guessed."""
    xy, pitch, matrix = (np.asarray(v, dtype=float) for v in
                         (xy_m, pitch_m, normalized_pitch_to_image))
    if (xy.shape != (2,) or pitch.shape != (2,) or matrix.shape != (3, 3)
            or not all(np.isfinite(v).all() for v in (xy, pitch, matrix))
            or (pitch <= 0).any()):
        raise ValueError('Finite native homography, metre point and pitch dimensions required')
    try:
        if not np.isfinite(np.linalg.inv(matrix)).all(): return None
    except np.linalg.LinAlgError:
        return None
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        p = matrix @ np.r_[xy / pitch, 1.]
        if not np.isfinite(p).all() or p[2] == 0: return None
        result = p[:2] / p[2]
    return result.tolist() if np.isfinite(result).all() else None


HINT_FIELDS = {'source_id', 'source_frame', 'video_time_s', 'camera_epoch',
               'tracking_source_id', 'tracking_sample_id', 'tracking_sha256',
               'origin', 'measurement', 'alignment_validated', 'clock_error_bound_s',
               'calibration_validated', 'ground_validated', 'frame_kind', 'projected_xy_px'}


def assess(packet, hint, config):
    """Return an added evidence record; never mutate detector or temporal tracks."""
    result = {'schema': 'tracking-supported-ball-v1', 'status': 'unavailable',
              'reason': 'no_automatic_tracking', 'candidate_detection_id': None,
              'candidate_track_id': None, 'tracking_sample_id': None,
              'tracking_source_id': None, 'tracking_sha256': None,
              'projected_xy_px': None, 'candidate_distances': [],
              'source_id': packet['source_id'], 'source_frame': packet['source_frame'],
              'video_time_s': packet['video_time_s'], 'camera_epoch': packet['camera_epoch'],
              'measurement': False, 'independent_accuracy_verified': False,
              'selected_in_play_ball': False, 'fusion_eligible': False, 'possession': None}
    if hint is None: return result
    if set(hint) != HINT_FIELDS or hint['origin'] != 'automatic_tracking':
        raise ValueError('Automatic tracking projection contract only; references/events forbidden')
    for key in ('measurement', 'alignment_validated', 'calibration_validated', 'ground_validated'):
        if type(hint[key]) is not bool: raise ValueError('Explicit boolean evidence required')
    if (type(hint['source_frame']) is not int or type(hint['camera_epoch']) is not int
            or hint['source_frame'] < 0 or hint['camera_epoch'] < 0):
        raise ValueError('Native integer frame/epoch required')
    for key in ('tracking_source_id', 'tracking_sample_id', 'source_id'):
        if not isinstance(hint[key], str) or not hint[key]: raise ValueError('Source-bound IDs required')
    digest = hint['tracking_sha256']
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Tracking input SHA-256 required')
    bound, time = hint['clock_error_bound_s'], hint['video_time_s']
    if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0 for x in (bound, time)):
        raise ValueError('Finite native time and alignment error bound required')
    result.update({k: hint[k] for k in ('tracking_source_id', 'tracking_sample_id', 'tracking_sha256')})
    def reject(reason):
        result.update(status='rejected', reason=reason)
        return result
    if any(hint[k] != packet[k] for k in ('source_id', 'source_frame', 'camera_epoch')):
        return reject('source_frame_or_camera_mismatch')
    if (not hint['alignment_validated'] or bound > config.max_clock_error_s
            or abs(time - packet['video_time_s']) > bound + 1e-9):
        return reject('unverified_or_inaccurate_alignment')
    if not hint['measurement']: return reject('tracking_is_not_observed')
    if hint['frame_kind'] != 'live': return reject('not_verified_live')
    if not hint['calibration_validated']: return reject('calibration_unvalidated')
    if not hint['ground_validated']: return reject('airborne_or_ground_unknown')
    point = hint['projected_xy_px']
    if (not isinstance(point, list) or len(point) != 2
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in point)):
        return reject('projection_missing_or_invalid')
    width, height = packet['image_size_px']
    if not 0 <= point[0] < width or not 0 <= point[1] < height:
        return reject('projection_outside_image')
    result['projected_xy_px'] = list(point)
    raw = {r['detection_id']: r for r in packet['objects'] if r['kind'] == 'ball_candidate'}
    candidates, used = [], set()
    for track in packet.get('ball_tracking', {}).get('tracks', []):
        # Forecasts, tentative tracks and unrelated object IDs never become observations.
        if track['state'] != 'observed' or track['measurement'] is not True: continue
        key = track['detection_id']
        if key not in raw or key in used or track['measured_position_px'] != raw[key]['image_xy_px']:
            raise ValueError('Observed track must reference exactly one current raw detection')
        used.add(key)
        distance = math.dist(point, raw[key]['image_xy_px']) / math.hypot(width, height)
        candidates.append({'detection_id': key, 'track_id': track['track_id'],
                           'distance_diagonal': distance})
    candidates.sort(key=lambda row: (row['distance_diagonal'], row['detection_id']))
    result['candidate_distances'] = candidates
    if not candidates: return reject('no_confirmed_measured_ball')
    if candidates[0]['distance_diagonal'] > config.radius_diagonal:
        return reject('tracking_image_disagreement')
    if len(candidates) > 1 and candidates[1]['distance_diagonal'] - candidates[0]['distance_diagonal'] < config.separation_diagonal:
        result.update(status='ambiguous', reason='multiple_nearby_candidates')
        return result
    best = candidates[0]
    result.update(status='supported_candidate', reason='observed_track_agrees_with_tracking',
                  candidate_detection_id=best['detection_id'], candidate_track_id=best['track_id'],
                  measurement=True)
    return result


def cross_check(primary, secondary, alignment, config):
    """Two independently observed camera candidates, not two independent truths.

    Secondary already passed its own native camera/geometry gates. Pair mapping
    must bind both exact frames; replays cannot inherit a previous match.
    """
    result = {'status': 'unavailable', 'reason': 'no_secondary',
              'independent_truth': False, 'fusion_eligible': False}
    if secondary is None or alignment is None: return result
    required = {'primary_source_id', 'primary_frame', 'primary_epoch',
                'secondary_source_id', 'secondary_frame', 'secondary_epoch',
                'verified', 'error_bound_s'}
    if set(alignment) != required: raise ValueError('Exact camera-pair alignment contract required')
    bound = alignment['error_bound_s']
    if (type(alignment['verified']) is not bool or type(bound) not in (int, float)
            or not math.isfinite(bound) or bound < 0): raise ValueError('Valid pair evidence required')
    matched = all(alignment[f'{prefix}_{field}'] == packet[key]
                  for prefix, packet in (('primary', primary), ('secondary', secondary))
                  for field, key in (('source_id', 'source_id'), ('frame', 'source_frame'), ('epoch', 'camera_epoch')))
    if (not matched or primary['source_id'] == secondary['source_id']
            or not alignment['verified'] or bound > config.max_clock_error_s):
        return dict(result, status='rejected', reason='pair_alignment_unverified_or_mismatched')
    if any(p['status'] != 'supported_candidate' for p in (primary, secondary)):
        return dict(result, status='rejected', reason='camera_candidate_not_supported')
    if any(primary[k] != secondary[k] for k in ('tracking_source_id', 'tracking_sample_id', 'tracking_sha256')):
        return dict(result, status='rejected', reason='different_tracking_observations')
    return dict(result, status='corroborated_candidate', reason='two_camera_observations_agree_with_same_tracking_sample')
