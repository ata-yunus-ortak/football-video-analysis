"""Project-facing image measurement contract; roles and ownership stay unknown.

Consumes automatic detector observations only. Dataset reference annotations
are not inputs. Pixel measurements are never silently promoted to pitch metres.
"""
from collections import Counter
import math


SCHEMA = 'project-image-analysis-v1'
BLOCKERS = ('person_role_and_team_unvalidated', 'pitch_calibration_unvalidated',
            'in_play_ball_and_ground_contact_unvalidated', 'live_replay_classification_unvalidated')


def vector(value, length):
    if value is None: return None
    if len(value) != length or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in value):
        raise ValueError('Finite measurement vector or unknown required')
    return list(value)


class ImageAnalysis:
    def __init__(self, source_id, ball_tracking_config=None, foot_context_config=None):
        if not isinstance(source_id, str) or not source_id: raise ValueError('Registered image source ID required')
        self.source_id, self.previous, self.counts, self.frames = source_id, None, Counter(), 0
        self.ball_tracker = None
        self.foot_context = None
        if foot_context_config is not None:
            if ball_tracking_config is None: raise ValueError('Foot context requires temporal association')
            from .ball_foot_context import BallFootContext
            self.foot_context = BallFootContext(foot_context_config)
        if ball_tracking_config is not None:
            from .ball_tracking import TemporalBallTracker
            self.ball_tracker = TemporalBallTracker(source_id, ball_tracking_config, foot_context_config)

    def consume(self, observation):
        if set(observation) - {'source_frame', 'video_time_s', 'fps', 'width', 'height',
                              'objects', 'frame_evidence', 'possession_inferred'}:
            raise ValueError('Only detector observation fields accepted; no labels/references/events')
        f, time, fps = observation['source_frame'], observation['video_time_s'], observation['fps']
        w, h = observation['width'], observation['height']
        evidence = observation['frame_evidence']
        epoch = evidence['camera_epoch']
        if (type(f) is not int or f < 0 or not math.isfinite(time) or time < 0
                or not math.isfinite(fps) or fps <= 0 or type(w) is not int or type(h) is not int or min(w, h) < 1
                or type(epoch) is not int or epoch < 0 or observation['possession_inferred'] is not False
                or evidence.get('teams_assigned') is not False or evidence.get('hybrid_ready') is not False):
            raise ValueError('Automatic measurement-only frame and valid clock/dimensions required')
        if self.previous is not None:
            pf, pt, rate, previous_epoch = self.previous
            if f != pf + 1 or time <= pt or fps != rate or epoch < previous_epoch:
                raise ValueError('Consecutive source frames, stable FPS and nondecreasing camera epoch required')
        keys = Counter(r.get('track_key') for r in observation['objects'] if r['kind'] == 'person' and r.get('track_key'))
        objects = []
        for index, row in enumerate(observation['objects']):
            if {'attributes', 'bbox_image', 'bbox_pitch', 'reference', 'labels', 'targets'}.intersection(row):
                raise ValueError('Reference/label fields cannot enter image analysis')
            person = row['kind'] == 'person'
            if (row['kind'] not in ('person', 'sports ball') or row.get('team') is not None
                    or row.get('person_role') not in (None, 'unknown') or row.get('hybrid_usable') is not False
                    or row.get('calibration_validated') is not False or row.get('ball_ground_valid') is not False
                    or row.get('measurement') is not True or row.get('camera_epoch') != epoch):
                raise ValueError('Current contract accepts unclassified person/ball measurements only')
            box, point = vector(row['box_xyxy'], 4), vector(row['anchor_xy'], 2)
            score = row['confidence']
            if (box is None or point is None or not math.isfinite(score) or not 0 <= score <= 1
                    or not 0 <= box[0] < box[2] <= w or not 0 <= box[1] < box[3] <= h
                    or not 0 <= point[0] <= w or not 0 <= point[1] <= h):
                raise ValueError('Valid image-space box, anchor and confidence required')
            key = row.get('track_key') if person else None
            if key is not None and (not isinstance(key, str) or not key.startswith(str(epoch) + ':')):
                raise ValueError('Camera-epoch-scoped image track key required')
            key = key if key and keys[key] == 1 and not row.get('track_identity_ambiguous') else None
            kind = 'person_candidate' if person else 'ball_candidate'
            objects.append({'detection_id': f'{self.source_id}/frame-{f}/object-{index}', 'kind': kind,
                'confidence': score, 'box_xyxy_px': box, 'image_xy_px': point,
                'image_velocity_px_s': vector(row.get('pixel_velocity_px_s'), 2) if key else None,
                'image_track_id': f'{self.source_id}/{key}' if key else None,
                'person_role': 'unknown' if person else None, 'team': None, 'canonical_player_id': None,
                'pitch_candidate_xy_m': vector(row.get('pitch_xy_m'), 2) if person else None,
                'pitch_position_validated': False, 'selected_in_play_ball': False, 'fusion_eligible': False})
            self.counts[kind] += 1
        self.previous, self.frames = (f, time, fps, epoch), self.frames + 1
        packet = {'schema': SCHEMA, 'source_id': self.source_id, 'source_frame': f,
                'video_time_s': time, 'fps': fps, 'image_size_px': [w, h], 'camera_epoch': epoch,
                'frame_kind': 'unknown', 'objects': objects, 'fusion_eligible': False,
                'fusion_blockers': list(BLOCKERS), 'possession': None}
        if self.ball_tracker is not None:
            if self.foot_context is not None:
                packet['ball_context_report'] = self.foot_context.annotate(packet, reset=evidence.get('continuity_reset', False))
            packet['ball_tracking'] = self.ball_tracker.consume(packet, reset=evidence.get('continuity_reset', False))
        return packet

    def summary(self):
        result = {'schema': SCHEMA, 'frames': self.frames, 'candidate_observations': dict(self.counts),
                'roles_predicted': False, 'teams_predicted': False, 'possession_inferred': False,
                'fusion_eligible': False, 'fusion_blockers': list(BLOCKERS)}
        if self.ball_tracker is not None: result['ball_tracking'] = self.ball_tracker.summary()
        return result
