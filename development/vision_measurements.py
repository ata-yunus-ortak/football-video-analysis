"""Image-derived positions, discontinuity-safe motion and optional pitch candidates.

People are not automatically players. A homography provides a plane mapping,
not a role, team, measured ball height or independently validated calibration.
"""
from collections import Counter
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SceneChangeConfig:
    pixel_difference_threshold: float
    changed_fraction_threshold: float
    max_pair_gap_s: float

    def __post_init__(self):
        if (any(not np.isfinite(v) or not 0 < v <= 1 for v in
                (self.pixel_difference_threshold, self.changed_fraction_threshold))
                or not np.isfinite(self.max_pair_gap_s) or self.max_pair_gap_s <= 0):
            raise ValueError('Explicit scene-change fractions and positive time-gap guard required')


class SceneContinuity:
    def __init__(self, fps, config=None):
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError('Positive source FPS required')
        self.fps, self.config = float(fps), config
        self.previous, self.epoch = None, 0

    def observe(self, rgb, frame, timestamp):
        if (rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8 or min(rgb.shape[:2]) < 1
                or type(frame) is not int or frame < 0 or not np.isfinite(timestamp) or timestamp < 0):
            raise ValueError('RGB uint8 frame with native index/time required')
        ys = np.linspace(0, rgb.shape[0] - 1, 36).astype(int)
        xs = np.linspace(0, rgb.shape[1] - 1, 64).astype(int)
        thumbnail = rgb[ys[:, None], xs].astype(np.float32) / 255.
        reset, appearance, fraction, reason = False, False, None, None
        if self.previous is not None:
            old_frame, old_time, old_shape, old_thumbnail = self.previous
            if timestamp <= old_time or frame <= old_frame:
                raise ValueError('Increasing source index and presentation time required')
            limit = self.config.max_pair_gap_s if self.config is not None else 1.5 / self.fps
            if frame != old_frame + 1 or timestamp - old_time > limit:
                reset, reason = True, 'source_frame_or_time_gap'
            elif rgb.shape != old_shape:
                reset, reason = True, 'image_dimensions_changed'
            elif self.config is not None:
                difference = np.mean(np.abs(thumbnail - old_thumbnail), axis=2)
                fraction = float(np.mean(difference >= self.config.pixel_difference_threshold))
                appearance = fraction >= self.config.changed_fraction_threshold
                if appearance:
                    reset, reason = True, 'appearance_jump_candidate'
        if reset:
            self.epoch += 1
        self.previous = frame, float(timestamp), rgb.shape, thumbnail
        return {'camera_epoch': self.epoch, 'continuity_reset': reset,
                'continuity_reset_reason': reason, 'scene_change_candidate': appearance,
                'changed_pixel_fraction': fraction, 'scene_monitor_enabled': self.config is not None,
                'frame_kind': 'unknown', 'live_or_replay_classified': False}


class VisionMeasurements:
    def __init__(self, fps, geometry=None, pitch=None, max_pair_gap_s=None):
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError('Positive source FPS required')
        self.fps, self.geometry = float(fps), geometry
        self.pitch = None if pitch is None else np.asarray(pitch, float)
        if geometry is not None and (self.pitch is None or self.pitch.shape != (2,)
                or not np.isfinite(self.pitch).all() or (self.pitch <= 0).any()):
            raise ValueError('Explicit pitch dimensions required with homography')
        self.max_gap = max_pair_gap_s if max_pair_gap_s is not None else 1.5 / self.fps
        if not np.isfinite(self.max_gap) or self.max_gap <= 0:
            raise ValueError('Positive observation adjacency guard required')
        self.previous, self.history = None, {}

    def annotate(self, rows, frame, timestamp, width, height, context):
        epoch = context['camera_epoch']
        if (type(frame) is not int or frame < 0 or not np.isfinite(timestamp) or timestamp < 0
                or width < 1 or height < 1 or type(epoch) is not int or epoch < 0):
            raise ValueError('Valid source frame, dimensions and camera epoch required')
        continuous = False
        if self.previous is not None:
            index, time, shape, old_epoch = self.previous
            if frame <= index or timestamp <= time:
                raise ValueError('Chronological image observations required')
            continuous = (frame == index + 1 and timestamp - time <= self.max_gap
                          and shape == (width, height) and epoch == old_epoch
                          and not context['continuity_reset'])
        if not continuous:
            self.history = {}
        ids = Counter(row.get('track_id') for row in rows if row['kind'] == 'person' and row.get('track_id') is not None)
        result, next_history = [], {}
        geometry_ok = (self.geometry is not None and frame < len(self.geometry.matrices)
                       and self.geometry.usable[frame])
        for source in rows:
            row = dict(source)
            if row['kind'] not in ('person', 'sports ball'):
                raise ValueError('Only image person/ball candidates enter this adapter')
            box, point = np.asarray(row['box_xyxy'], float), np.asarray(row['anchor_xy'], float)
            score = row['confidence']
            if (box.shape != (4,) or point.shape != (2,) or not np.isfinite(box).all()
                    or not np.isfinite(point).all() or not np.isfinite(score) or not 0 <= score <= 1
                    or box[0] < 0 or box[1] < 0 or box[2] > width or box[3] > height
                    or box[2] <= box[0] or box[3] <= box[1]):
                raise ValueError('Finite in-image detection box/anchor and confidence required')
            track = row.get('track_id')
            if track is not None and (type(track) is not int or track < 0):
                raise ValueError('Native integer track ID or unknown required')
            person = row['kind'] == 'person'
            ambiguous = bool(track is not None and ids[track] > 1)
            key = f'{epoch}:{track}' if person and track is not None and not ambiguous else None
            truncated = bool(row.get('anchor_truncated', False)
                             or box[0] <= 0 or box[1] <= 0 or box[2] >= width or box[3] >= height)
            row.update(camera_epoch=epoch, track_key=key, track_identity_ambiguous=ambiguous,
                       person_role='unknown' if person else None, team=None,
                       pixel_velocity_px_s=None, pitch_xy_m=None, pitch_velocity_mps=None,
                       projection_inside_pitch=None, anchor_truncated=truncated,
                       calibration_validated=False, ball_ground_valid=False,
                       hybrid_usable=False)
            if not person:
                row['projection_status'] = 'ball_height_or_ground_contact_unknown'
            elif truncated:
                row['projection_status'] = 'anchor_truncated'
            elif not geometry_ok:
                row['projection_status'] = 'homography_missing_or_unusable'
            else:
                projected = self.geometry.project(frame, [point], pitch=self.pitch)[0]
                if np.isfinite(projected).all():
                    row['pitch_xy_m'] = projected.tolist()
                    row['projection_inside_pitch'] = bool((projected >= 0).all() and (projected <= self.pitch).all())
                    row['projection_status'] = 'ground_plane_candidate'
                else:
                    row['projection_status'] = 'projective_horizon_or_invalid_point'
            if key is not None:
                previous = self.history.get(key)
                if previous is not None:
                    dt = timestamp - previous['time']
                    row['pixel_velocity_px_s'] = ((point - previous['point']) / dt).tolist()
                    if (row['pitch_xy_m'] is not None and previous['pitch'] is not None
                            and row['projection_inside_pitch'] and previous['inside']):
                        row['pitch_velocity_mps'] = ((np.asarray(row['pitch_xy_m']) - previous['pitch']) / dt).tolist()
                next_history[key] = {'time': timestamp, 'point': point,
                                     'pitch': row['pitch_xy_m'], 'inside': row['projection_inside_pitch']}
            result.append(row)
        self.previous, self.history = (frame, float(timestamp), (width, height), epoch), next_history
        counts = Counter(row['kind'] for row in result)
        frame_evidence = {**context, 'person_candidate_count': counts['person'],
            'ball_candidate_count': counts['sports ball'],
            'tracked_person_count': sum(row['track_key'] is not None for row in result if row['kind'] == 'person'),
            'projected_person_candidate_count': sum(row['pitch_xy_m'] is not None for row in result),
            'homography_mathematically_usable': bool(geometry_ok),
            'calibration_validated': False, 'teams_assigned': False, 'hybrid_ready': False}
        return result, frame_evidence
