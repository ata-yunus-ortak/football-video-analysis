"""Conservative multi-candidate pixel ball tracks, not in-play ball selection.

Constant-velocity forecasts are separate from measured detections. An optional
automatic person-box context can withhold foot-like candidates; no role/team,
event, reference label or pitch-plane input enters association.
"""
from collections import Counter
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BallTrackingConfig:
    min_confidence: float
    confirmation_observations: int
    max_missing_s: float
    match_radius_diagonal: float
    prediction_growth_diagonal_per_s: float
    max_speed_diagonal_per_s: float
    confidence_weight: float
    size_weight: float
    ambiguity_margin: float
    velocity_smoothing: float
    duplicate_iou: float
    duplicate_center_diagonal: float

    def __post_init__(self):
        if type(self.confirmation_observations) is not int or self.confirmation_observations < 2:
            raise ValueError('At least two confirmation observations required')
        for name, value in vars(self).items():
            if name == 'confirmation_observations': continue
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Explicit finite positive ball tracking parameters required')
        if any(getattr(self, key) > 1 for key in ('min_confidence', 'velocity_smoothing', 'duplicate_iou')):
            raise ValueError('Confidence, smoothing and IoU must be in (0,1]')


def overlap(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return intersection / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection)


class TemporalBallTracker:
    def __init__(self, source_id, config, foot_context_config=None):
        self.source_id, self.cfg = source_id, config
        self.tracks, self.previous, self.serial, self.counts = {}, None, 0, Counter()
        self.foot_cfg = foot_context_config

    def consume(self, packet, reset=False):
        frame, time, fps = packet['source_frame'], packet['video_time_s'], packet['fps']
        width, height = packet['image_size_px'];epoch = packet['camera_epoch']
        if (type(frame) is not int or frame < 0 or type(epoch) is not int or epoch < 0
                or not all(math.isfinite(v) and v > 0 for v in (width, height, fps))
                or not math.isfinite(time) or time < 0): raise ValueError('Valid native image clock required')
        reason = None
        if self.previous:
            old_f, old_t, old_fps, old_shape, old_epoch = self.previous
            if frame <= old_f or time <= old_t or epoch < old_epoch: raise ValueError('Increasing source clock/epoch required')
            if reset or epoch != old_epoch: reason = 'camera_discontinuity'
            elif (width, height) != old_shape: reason = 'image_dimensions_changed'
            elif frame != old_f + 1 or fps != old_fps or time - old_t > 1.5 / fps: reason = 'source_clock_gap'
        events = []
        if reason:
            events.extend(self._output(key, t, 'lost', reason=reason) for key, t in self.tracks.items())
            self.tracks.clear()
        self.previous = frame, time, fps, (width, height), epoch
        diagonal = math.hypot(width, height)
        candidates, exclusions = [], []
        for row in packet['objects']:
            if row['kind'] != 'ball_candidate': continue
            point, box, score = row['image_xy_px'], row['box_xyxy_px'], row['confidence']
            if (len(point) != 2 or len(box) != 4 or not all(math.isfinite(v) for v in point + box)
                    or not 0 <= point[0] < width or not 0 <= point[1] < height
                    or not 0 <= box[0] < box[2] <= width or not 0 <= box[1] < box[3] <= height
                    or not math.isfinite(score) or not 0 <= score <= 1): raise ValueError('Valid ball detection required')
            if score < self.cfg.min_confidence:
                exclusions.append({'detection_id': row['detection_id'], 'reason': 'low_confidence'})
            else:
                candidates.append({'id': row['detection_id'], 'point': list(point), 'box': list(box),
                    'score': score, 'area': (box[2] - box[0]) * (box[3] - box[1]), 'source':row,
                    'foot_blocked':self.foot_cfg is not None and row.get('ball_context',{}).get('withhold_unprotected_track',False),
                    'independent':self.foot_cfg is not None and row.get('ball_context',{}).get('independent_motion_evidence',False)})
                if self.foot_cfg is not None and row.get('ball_context'):
                    row['ball_context']['tracking_decision']='withheld_foot_like' if candidates[-1]['foot_blocked'] else 'eligible'
        unique = []
        for row in sorted(candidates, key=lambda r: (-r['score'], r['id'])):
            if any(math.dist(row['point'], other['point']) / diagonal <= self.cfg.duplicate_center_diagonal
                   and overlap(row['box'], other['box']) >= self.cfg.duplicate_iou for other in unique):
                exclusions.append({'detection_id': row['id'], 'reason': 'overlapping_duplicate'})
            else: unique.append(row)
        candidates = unique
        # Expiry happens before matching: a late observation never revives an old ID.
        for key, track in list(self.tracks.items()):
            if time - track['time'] > self.cfg.max_missing_s:
                events.append(self._output(key, track, 'lost', reason='missing_timeout'))
                del self.tracks[key]
        costs, foot_hits = {}, set()
        for key, track in self.tracks.items():
            dt = time - track['time']
            predicted = [track['point'][i] + (track['velocity'][i] * dt if track['velocity'] else 0) for i in range(2)]
            radius = diagonal * (self.cfg.match_radius_diagonal + self.cfg.prediction_growth_diagonal_per_s * dt)
            for c, row in enumerate(candidates):
                distance = math.dist(predicted, row['point'])
                speed = math.dist(track['point'], row['point']) / dt / diagonal
                if distance <= radius and speed <= self.cfg.max_speed_diagonal_per_s:
                    if row['foot_blocked'] and track.get('independent_observations',0)<self.foot_cfg.independent_observations:
                        foot_hits.add(key);continue
                    costs[key, c] = (distance / radius + self.cfg.confidence_weight * (1 - row['score'])
                        + self.cfg.size_weight * abs(math.log(row['area'] / track['area'])))
        for key in foot_hits:
            if not any(k==key for k,c in costs):
                events.append(self._output(key,self.tracks.pop(key),'lost',reason='suspected_foot_attachment'))
        ambiguous, blocked = set(), set()
        for key in self.tracks:
            choices = sorted((value, c) for (k, c), value in costs.items() if k == key)
            if len(choices) > 1 and choices[1][0] - choices[0][0] < self.cfg.ambiguity_margin:
                ambiguous.add(key)
                blocked.update(c for value, c in choices if value - choices[0][0] < self.cfg.ambiguity_margin)
        for c in range(len(candidates)):
            choices = sorted((value, key) for (key, candidate), value in costs.items() if candidate == c)
            if len(choices) > 1 and choices[1][0] - choices[0][0] < self.cfg.ambiguity_margin:
                blocked.add(c)
                ambiguous.update(key for value, key in choices if value - choices[0][0] < self.cfg.ambiguity_margin)
        for key in ambiguous:
            events.append(self._output(key, self.tracks.pop(key), 'ambiguous', reason='association_ambiguous'))
        assignment, used = {}, set()
        for key in sorted(self.tracks):
            choices = sorted((value, c) for (k, c), value in costs.items() if k == key and c not in blocked)
            if not choices: continue
            c = choices[0][1]
            peers = sorted((value, k) for (k, candidate), value in costs.items() if candidate == c and k in self.tracks)
            if peers and peers[0][1] == key and c not in used:
                assignment[key] = c;used.add(c)
        for key, track in list(self.tracks.items()):
            if key in assignment:
                row = candidates[assignment[key]];dt = time - track['time']
                measured_velocity = [(row['point'][i] - track['point'][i]) / dt for i in range(2)]
                gain = self.cfg.velocity_smoothing
                velocity = measured_velocity if track['velocity'] is None else [
                    gain * measured_velocity[i] + (1 - gain) * track['velocity'][i] for i in range(2)]
                track.update(point=row['point'], time=time, velocity=velocity, area=row['area'],
                             score=row['score'], detection_id=row['id'], hits=track['hits'] + 1)
                track['independent_observations']=track.get('independent_observations',0)+int(row['independent'])
                if row['foot_blocked']:
                    row['source']['ball_context']['tracking_decision']='retained_independent_track'
                events.append(self._output(key, track, 'observed' if track['hits'] >= self.cfg.confirmation_observations else 'tentative'))
            elif track['hits'] < self.cfg.confirmation_observations:
                events.append(self._output(key, track, 'lost', reason='unconfirmed_gap'));del self.tracks[key]
            else:
                dt = time - track['time']
                forecast = [track['point'][i] + track['velocity'][i] * dt for i in range(2)]
                if not 0 <= forecast[0] < width or not 0 <= forecast[1] < height:
                    events.append(self._output(key, track, 'lost', reason='prediction_outside_image'));del self.tracks[key]
                else:
                    events.append(self._output(key, track, 'predicted', forecast=forecast, age=dt,
                        radius=diagonal * (self.cfg.match_radius_diagonal + self.cfg.prediction_growth_diagonal_per_s * dt)))
        for c, row in enumerate(candidates):
            if c in used or c in blocked: continue
            if row['foot_blocked']:
                exclusions.append({'detection_id':row['id'],'reason':'suspected_foot_attachment'});continue
            if any(candidate == c for key, candidate in costs):
                exclusions.append({'detection_id': row['id'], 'reason': 'unresolved_existing_track'});continue
            self.serial += 1;key = f'{self.source_id}/ball/{epoch}:{self.serial}'
            track = {'point': row['point'], 'time': time, 'velocity': None, 'score': row['score'],
                     'area': row['area'], 'hits': 1, 'detection_id': row['id'],
                     'independent_observations':int(row['independent'])}
            self.tracks[key] = track;events.append(self._output(key, track, 'tentative'))
        self.counts.update(row['state'] for row in events)
        return {'schema': 'image-ball-tracks-v1', 'tracks': events, 'candidate_exclusions': exclusions,
                'in_play_ball_selected': False, 'physical_velocity_measured': False, 'reset_reason': reason}

    def _output(self, key, track, state, *, reason=None, forecast=None, age=0., radius=None):
        measured = state in ('observed', 'tentative')
        return {'track_id': key, 'state': state, 'measurement': measured,
            'detection_id': track['detection_id'] if measured else None,
            'measured_position_px': list(track['point']) if measured else None,
            'predicted_position_px': forecast, 'prediction_age_s': age if forecast else None,
            'search_radius_px': radius, 'search_radius_is_calibrated_uncertainty': False,
            'last_detection_confidence': track['score'], 'estimated_velocity_px_s': track['velocity'],
            'confirmation_observations': track['hits'], 'reason': reason,
            'selected_in_play_ball': False, 'fusion_eligible': False}

    def summary(self):
        return {'schema': 'image-ball-tracks-v1', 'track_state_observations': dict(self.counts),
                'created_track_ids': self.serial, 'in_play_ball_selected': False}
