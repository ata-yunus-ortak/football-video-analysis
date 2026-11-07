"""Experimental video-led possession. Tracking supplies player identity only.

No tracking ball, provider possession, baseline owner or dataset reference is
accepted. All positions used for control come from current image detections.
"""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class VisualPossessionConfig:
    identity_radius_heights: float
    identity_margin_heights: float
    identity_confirmation_s: float
    control_radius_heights: float
    control_margin_heights: float
    max_relative_motion_heights_s: float
    control_confirmation_s: float
    min_confidence: float
    min_players_per_team: int
    min_identity_fraction: float
    max_alignment_error_s: float
    cross_camera_radius_m: float
    min_common_players: int
    max_player_speed_mps: float
    bulk_jump_fraction: float

    def __post_init__(self):
        for key, value in vars(self).items():
            if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
                raise ValueError('Explicit positive finite video-led settings required')
        for key in ('min_players_per_team', 'min_common_players'):
            if type(getattr(self, key)) is not int: raise ValueError('Integer coverage required')
        if any(getattr(self, k) > 1 for k in ('min_confidence', 'min_identity_fraction', 'bulk_jump_fraction')):
            raise ValueError('Fractions must be in (0,1]')


CONTEXT_FIELDS = {'source_id', 'source_frame', 'camera_epoch', 'video_time_s',
                  'origin', 'tracking_sha256', 'metadata_sha256', 'homography_sha256',
                  'alignment_validated', 'clock_error_bound_s', 'calibration_validated',
                  'frame_kind', 'pitch_m', 'normalized_pitch_to_image', 'players'}


def transform(points, matrix):
    points = np.asarray(points, float).reshape(-1, 2)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        p = np.column_stack((points, np.ones(len(points)))) @ matrix.T
        p = p[:, :2] / p[:, 2:3]
    return p


class VisualCamera:
    def __init__(self, config):
        self.cfg, self.previous, self.links, self.control = config, None, {}, None
        self.previous_positions = {}
        self.identity_teams = {}

    def consume(self, packet, context):
        cfg = self.cfg
        result = {'source_id': packet['source_id'], 'source_frame': packet['source_frame'],
                  'video_time_s': packet['video_time_s'], 'camera_epoch': packet['camera_epoch'],
                  'label': 'X', 'owner_id': None, 'reason': 'identity_context_missing',
                  'players': [], 'ball': None, 'view_eligible': False, 'identity_fraction': 0.,
                  'bulk_jump': False, 'possession_is_experimental': True,
                  'tracking_ball_used': False, 'baseline_owner_used': False}
        current = (packet['source_id'], packet['source_frame'], packet['camera_epoch'], packet['video_time_s'])
        continuous = (self.previous is not None and current[0] == self.previous[0]
                      and current[1] == self.previous[1] + 1 and current[2] == self.previous[2]
                      and 0 < current[3] - self.previous[3] <= 1.5 / packet['fps'])
        if not continuous: self.links, self.control, self.previous_positions = {}, None, {}
        self.previous = current

        def unknown(reason):
            result['reason'] = reason
            self.control = None
            return result

        if context is None:
            self.links, self.previous_positions = {}, {}
            return unknown('identity_context_missing')
        if set(context) != CONTEXT_FIELDS or context['origin'] != 'automatic_player_tracking':
            raise ValueError('Player-only automatic identity context required; no ball/owner/reference fields')
        for key in ('tracking_sha256', 'metadata_sha256', 'homography_sha256'):
            v = context[key]
            if not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v):
                raise ValueError('Source content hashes required')
        for key in ('alignment_validated', 'calibration_validated'):
            if type(context[key]) is not bool: raise ValueError('Explicit geometry/time evidence required')
        error, time = context['clock_error_bound_s'], context['video_time_s']
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in (error, time)):
            raise ValueError('Finite clock and error bound required')
        if any(context[k] != packet[k] for k in ('source_id', 'source_frame', 'camera_epoch')):
            self.links, self.previous_positions = {}, {}
            return unknown('identity_source_mismatch')
        if (not context['alignment_validated'] or error > cfg.max_alignment_error_s
                or abs(time - packet['video_time_s']) > error + 1e-9):
            self.links, self.previous_positions = {}, {}
            return unknown('identity_alignment_unvalidated')
        if context['frame_kind'] != 'live' or not context['calibration_validated']:
            self.links, self.previous_positions = {}, {}
            return unknown('view_or_calibration_unvalidated')
        matrix, pitch = np.asarray(context['normalized_pitch_to_image'], float), np.asarray(context['pitch_m'], float)
        if (matrix.shape != (3, 3) or pitch.shape != (2,) or not np.isfinite(matrix).all()
                or not np.isfinite(pitch).all() or (pitch <= 0).any()):
            self.links, self.previous_positions = {}, {}
            return unknown('invalid_geometry')
        try: inverse = np.linalg.inv(matrix)
        except np.linalg.LinAlgError:
            self.links, self.previous_positions = {}, {}
            return unknown('singular_geometry')
        roster = context['players']
        ids = set()
        for row in roster:
            if (set(row) != {'player_id', 'team', 'normalized_xy'} or row['team'] not in ('H', 'A')
                    or not isinstance(row['player_id'], str) or not row['player_id'] or row['player_id'] in ids):
                raise ValueError('Unique canonical player IDs and metadata H/A teams required')
            ids.add(row['player_id'])
            if self.identity_teams.get(row['player_id'], row['team']) != row['team']:
                raise ValueError('Canonical player cannot change metadata team within this run')
            self.identity_teams[row['player_id']] = row['team']
            xy = np.asarray(row['normalized_xy'], float)
            if xy.shape != (2,) or not np.isfinite(xy).all(): raise ValueError('Measured player coordinates required')
        people = [r for r in packet['objects'] if r['kind'] == 'person_candidate'
                  and r['confidence'] >= cfg.min_confidence]
        height = np.array([r['box_xyxy_px'][3] - r['box_xyxy_px'][1] for r in people])
        if any(h <= 0 for h in height): raise ValueError('Positive image person height required')
        width, image_height = packet['image_size_px']
        # Truncated feet cannot reliably label a person or establish control.
        usable = [i for i, r in enumerate(people) if r['box_xyxy_px'][0] > 0
                  and r['box_xyxy_px'][1] > 0 and r['box_xyxy_px'][2] < width
                  and r['box_xyxy_px'][3] < image_height]
        projected = transform([r['normalized_xy'] for r in roster], matrix)
        next_links, labelled = {}, {}
        if people and roster:
            feet = np.array([r['image_xy_px'] for r in people])
            distance = np.linalg.norm(feet[:, None] - projected[None], axis=2) / height[:, None]
            distance[~np.isfinite(distance)] = np.inf
            for i in usable:
                key = people[i].get('image_track_id')
                if not key or sum(r.get('image_track_id') == key for r in people) != 1: continue
                j = int(distance[i].argmin())
                column = distance[:, j]
                # Reciprocal best assignment; ambiguity on either side is rejected.
                others = np.delete(distance[i], j); competitors = np.delete(column, i)
                if (column.argmin() != i or distance[i, j] > cfg.identity_radius_heights
                        or (len(others) and others.min() - distance[i, j] < cfg.identity_margin_heights)
                        or (len(competitors) and competitors.min() - distance[i, j] < cfg.identity_margin_heights)):
                    continue
                identity = roster[j]['player_id']
                old = self.links.get(key)
                start = old[1] if old and old[0] == identity else current[3]
                next_links[key] = identity, start
                if current[3] - start + 1 / packet['fps'] + 1e-9 < cfg.identity_confirmation_s: continue
                pitch_point = transform([people[i]['image_xy_px']], inverse)[0] * pitch
                if not np.isfinite(pitch_point).all() or (pitch_point < 0).any() or (pitch_point > pitch).any(): continue
                item = {'player_id': identity, 'team': roster[j]['team'], 'image_track_id': key,
                        'detection_id': people[i]['detection_id'], 'image_xy_px': people[i]['image_xy_px'],
                        'pitch_xy_m': pitch_point.tolist(), 'source_id': packet['source_id']}
                labelled[i] = item
        self.links = next_links
        result['players'] = list(labelled.values())
        result['identity_fraction'] = len(labelled) / max(1, len(people))
        jumps, comparable = 0, 0
        for p in result['players']:
            old = self.previous_positions.get(p['player_id'])
            p['motion_reliable'] = True
            if old and continuous:
                comparable += 1
                jump = math.dist(old, p['pitch_xy_m']) / (current[3] - self.previous_time) > cfg.max_player_speed_mps
                p['motion_reliable'] = not jump
                jumps += jump
        self.previous_positions = {p['player_id']: p['pitch_xy_m'] for p in result['players']}
        self.previous_time = current[3]
        result['bulk_jump'] = comparable >= 2 * cfg.min_players_per_team and jumps / comparable >= cfg.bulk_jump_fraction
        counts = {t: sum(p['team'] == t for p in result['players']) for t in ('H', 'A')}
        result['view_eligible'] = (min(counts.values()) >= cfg.min_players_per_team
                                   and result['identity_fraction'] >= cfg.min_identity_fraction and not result['bulk_jump'])
        if not result['view_eligible']: return unknown('insufficient_identity_coverage_or_bulk_jump')
        raw = {r['detection_id']: r for r in packet['objects'] if r['kind'] == 'ball_candidate'}
        tracks = [t for t in packet.get('ball_tracking', {}).get('tracks', [])
                  if t['measurement'] is True and t['state'] in ('observed', 'tentative')]
        if len(tracks) != 1 or tracks[0]['state'] != 'observed': return unknown('in_play_ball_ambiguous_or_missing')
        track = tracks[0]
        if track['detection_id'] not in raw: raise ValueError('Ball track missing current image detection')
        ball = raw[track['detection_id']]
        if ball['image_xy_px'] != track['measured_position_px']: raise ValueError('Ball track/image mismatch')
        if ball['confidence'] < cfg.min_confidence: return unknown('ball_confidence_low')
        point = np.array(ball['image_xy_px'], float)
        result['ball'] = {'detection_id': ball['detection_id'], 'track_id': track['track_id'],
                          'image_xy_px': point.tolist(), 'measurement': True, 'ground_verified': False}
        d = np.array([math.dist(point, p['image_xy_px']) / h for p, h in zip(people, height)])
        order = np.argsort(d); first = int(order[0])
        if first not in labelled: return unknown('nearest_person_identity_unknown')
        if d[first] > cfg.control_radius_heights: return unknown('ball_not_near_observed_feet')
        if len(d) > 1 and d[order[1]] - d[first] < cfg.control_margin_heights: return unknown('contested_image_control')
        owner = labelled[first]
        if not owner['motion_reliable']: return unknown('owner_image_motion_implausible')
        # Relative image offset removes common translation, not pan/zoom in general.
        offset = (point - people[first]['image_xy_px']) / height[first]
        old = self.control
        same = (old is not None and old['owner'] == owner['player_id'] and old['ball'] == track['track_id'])
        start = old['start'] if same else current[3]
        if same and np.linalg.norm(offset - old['offset']) / (current[3] - old['time']) > cfg.max_relative_motion_heights_s:
            start = current[3]
        self.control = {'owner': owner['player_id'], 'ball': track['track_id'], 'offset': offset,
                        'time': current[3], 'start': start}
        if current[3] - start + 1 / packet['fps'] + 1e-9 < cfg.control_confirmation_s:
            result['reason'] = 'image_control_unconfirmed'
            return result
        result.update(label=owner['team'], owner_id=owner['player_id'], reason='sustained_image_control_candidate')
        return result


def choose_view(tactical, broadcast, alignment, cfg):
    """Use matched live broadcast control; retain tactical-only people and fallback."""
    allowed, reason, matches, tactical_ids = False, 'no_broadcast_pair', [], set()
    if broadcast is not None and alignment is not None:
        keys = {'primary_source_id', 'primary_frame', 'primary_epoch', 'secondary_source_id',
                'secondary_frame', 'secondary_epoch', 'verified', 'error_bound_s'}
        if set(alignment) != keys: raise ValueError('Exact automatic camera-pair mapping required')
        error = alignment['error_bound_s']
        if (type(alignment['verified']) is not bool or type(error) not in (float, int)
                or not math.isfinite(error) or error < 0): raise ValueError('Finite verified mapping required')
        bound = all(alignment[prefix + '_' + k] == frame[key]
                    for prefix, frame in (('primary', tactical), ('secondary', broadcast))
                    for k, key in (('source_id', 'source_id'), ('frame', 'source_frame'), ('epoch', 'camera_epoch')))
        reason = 'broadcast_alignment_or_view_rejected'
        if (bound and alignment['verified'] and error <= cfg.max_alignment_error_s
                and tactical['source_id'] != broadcast['source_id']
                and tactical['view_eligible'] and broadcast['view_eligible']):
            a = {p['player_id']: p for p in tactical['players']}
            b = {p['player_id']: p for p in broadcast['players']}
            tactical_ids = set(a)
            common = set(a) & set(b)
            matches = [k for k in common if a[k]['team'] == b[k]['team']
                       and a[k]['motion_reliable'] and b[k]['motion_reliable']
                       and math.dist(a[k]['pitch_xy_m'], b[k]['pitch_xy_m']) <= cfg.cross_camera_radius_m]
            allowed = (len(matches) >= cfg.min_common_players
                       and len(matches) / max(1, len(common)) >= cfg.min_identity_fraction)
            reason = 'matched_live_broadcast' if allowed else 'broadcast_image_geometry_conflict'
    players = {p['player_id']: dict(p, camera='tactical') for p in tactical['players']}
    if allowed:
        for p in broadcast['players']:
            if p['motion_reliable'] and (p['player_id'] not in tactical_ids or p['player_id'] in matches):
                players[p['player_id']] = dict(p, camera='broadcast')
    use_broadcast = (allowed and broadcast['label'] in ('H', 'A')
                     and broadcast['owner_id'] in players
                     and players[broadcast['owner_id']]['camera'] == 'broadcast')
    chosen = broadcast if use_broadcast else tactical
    return {'source_frame': tactical['source_frame'], 'video_time_s': tactical['video_time_s'],
            'label': chosen['label'], 'owner_id': chosen['owner_id'],
            'decision_source': 'broadcast' if use_broadcast else 'tactical',
            'decision_reason': chosen['reason'], 'broadcast_allowed': allowed, 'broadcast_reason': reason,
            'players': list(players.values()), 'ball': chosen['ball'], 'tracking_ball_used': False,
            'baseline_owner_used': False, 'selected_release': False, 'dead_ball_enabled': False}
