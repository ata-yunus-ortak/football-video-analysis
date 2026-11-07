"""Automatic clock parsing and conservative, discontinuous review alignment.

No human anchors, supplied-fixture tuning, global offset, or possession fusion.
Even geometry-supported links remain experimental observations, not ground truth.
"""
from dataclasses import dataclass
import math
import re
import numpy as np


def parse_clock(text):
    """Read an unambiguous football MM:SS or explicit added-time clock.

    Digits are never repaired from letters. A score such as 1-0 is not a clock.
    A separate '+2' added-time allocation is not an elapsed-time measurement.
    """
    text = str(text).replace('：', ':')
    added = re.findall(r'(?<![\d:])(45|90)\s*(?::00)?\s*\+\s*(\d{1,2}):([0-5]\d)(?![\d:])', text)
    clocks = re.findall(r'(?<![\d:])(\d{1,3}):([0-5]\d)(?![\d:])', text)
    if len(added) == 1:
        base, minute, second = map(int, added[0])
        if minute <= 30:
            return (base + minute) * 60 + second
        return None
    values = {int(minute) * 60 + int(second) for minute, second in clocks if int(minute) <= 130}
    return float(next(iter(values))) if len(values) == 1 else None


def observe_tokens(tokens, min_confidence):
    """Tokens are local OCR observations: {'text': str, 'confidence': float}."""
    candidates = []
    period_values = set()
    for token in tokens:
        score = float(token['confidence'])
        if not math.isfinite(score) or not min_confidence <= score <= 1:
            continue
        text = token['text']
        clock = parse_clock(text)
        if clock is not None:
            candidates.append((clock, score))
        for period, pattern in [(1, r'\b(?:1ST(?:\s+HALF)?|1H|1T)\b'), (2, r'\b(?:2ND(?:\s+HALF)?|2H|2T)\b')]:
            if re.search(pattern, text, re.I):
                period_values.add(period)
    distinct = {clock for clock, _ in candidates}
    if len(distinct) != 1:
        return {'clock_s': None, 'confidence': None, 'period': None,
                'status': 'ambiguous_clock' if distinct else 'no_confident_clock'}
    value = distinct.pop()
    return {'clock_s': value, 'confidence': max(score for clock, score in candidates if clock == value),
            'period': next(iter(period_values)) if len(period_values) == 1 else None,
            'status': 'observed_clock'}


@dataclass(frozen=True)
class AlignmentConfig:
    min_confidence: float
    max_sample_gap_s: float
    max_clock_residual_s: float
    min_run_samples: int
    min_run_span_s: float
    clock_uncertainty_s: float
    max_mapping_rate_error: float

    def __post_init__(self):
        if (not math.isfinite(self.min_confidence) or not 0 < self.min_confidence <= 1
                or type(self.min_run_samples) is not int or self.min_run_samples < 3
                or any(not math.isfinite(v) or v <= 0 for v in
                       (self.max_sample_gap_s, self.max_clock_residual_s, self.min_run_span_s,
                        self.clock_uncertainty_s, self.max_mapping_rate_error))
                or self.max_mapping_rate_error >= 1):
            raise ValueError('Explicit conservative clock alignment settings required')


def clock_runs(rows, cfg):
    result, run = [], []
    previous_time = -math.inf
    def finish():
        if len(run) >= cfg.min_run_samples and run[-1]['video_time_s'] - run[0]['video_time_s'] >= cfg.min_run_span_s:
            periods = {r.get('period') for r in run if r.get('period') is not None}
            result.append({'id': len(result), 'rows': list(run),
                           'period': next(iter(periods)) if len(periods) == 1 else None})
    for row in rows:
        time = row.get('video_time_s')
        if (row.get('source_kind') != 'automatic_clock_observation'
                or not isinstance(time, (int, float)) or not math.isfinite(time)
                or time < 0 or time <= previous_time or row.get('period') not in (None, 1, 2)):
            raise ValueError('Chronological automatic clock observations required')
        previous_time = time
        clock, confidence = row.get('clock_s'), row.get('confidence')
        if clock is None:
            continue
        if (not isinstance(clock, (int, float)) or not math.isfinite(clock) or clock < 0
                or not isinstance(confidence, (int, float)) or not math.isfinite(confidence)
                or not 0 <= confidence <= 1):
            raise ValueError('Invalid observed clock/confidence')
        if confidence < cfg.min_confidence:
            continue
        if run:
            previous = run[-1]
            elapsed, advance = time - previous['video_time_s'], clock - previous['clock_s']
            run_period = next((r['period'] for r in run if r.get('period') is not None), None)
            known_period_change = (run_period is not None and row.get('period') is not None
                                   and run_period != row['period'])
            if (elapsed > cfg.max_sample_gap_s or advance <= 0 or known_period_change
                    or abs(advance - elapsed) > cfg.max_clock_residual_s):
                finish()
                run = []
        run.append(row)
    finish()
    return result


def _contains(run, clock, period):
    return (run['rows'][0]['clock_s'] <= clock <= run['rows'][-1]['clock_s']
            and (period is None or run['period'] is None or period == run['period']))


def clock_anchors(tactical_rows, broadcast_rows, cfg):
    tactical, broadcast = clock_runs(tactical_rows, cfg), clock_runs(broadcast_rows, cfg)
    anchors = []
    for run in tactical:
        for row in run['rows']:
            clock = row['clock_s']
            own = [r for r in tactical if _contains(r, clock, run['period'])]
            other = [r for r in broadcast if _contains(r, clock, run['period'])]
            if len(own) != 1 or len(other) != 1:
                continue
            target = other[0]
            time = float(np.interp(clock, [r['clock_s'] for r in target['rows']],
                                   [r['video_time_s'] for r in target['rows']]))
            anchors.append({'tactical_time_s': row['video_time_s'], 'broadcast_time_s': time,
                            'clock_s': clock, 'period': run['period'],
                            'tactical_run': run['id'], 'broadcast_run': target['id'],
                            'uncertainty_s': cfg.clock_uncertainty_s,
                            'status': 'clock_candidate', 'geometry_supported': False,
                            'usable_for_possession': False})
    return sorted(anchors, key=lambda r: r['tactical_time_s'])


def mapping_segments(anchors, cfg):
    segments = []
    for left, right in zip(anchors, anchors[1:]):
        dt = right['tactical_time_s'] - left['tactical_time_s']
        db = right['broadcast_time_s'] - left['broadcast_time_s']
        if (dt <= 0 or dt > cfg.max_sample_gap_s or db <= 0
                or any(a.get('geometry_status') == 'source_geometry_disagrees' for a in (left, right))
                or any(left[k] != right[k] for k in ('tactical_run', 'broadcast_run'))
                or abs(db / dt - 1) > cfg.max_mapping_rate_error):
            continue
        supported = left['geometry_supported'] and right['geometry_supported']
        segments.append({'t0': left['tactical_time_s'], 't1': right['tactical_time_s'],
                         'b0': left['broadcast_time_s'], 'b1': right['broadcast_time_s'],
                         'status': 'clock_and_tracking_candidate' if supported else 'clock_candidate',
                         'uncertainty_s': max(left['uncertainty_s'], right['uncertainty_s']),
                         'usable_for_possession': False})
    # A replay must not silently map two tactical intervals to overlapping broadcast time.
    by_broadcast = sorted(segments, key=lambda r: r['b0'])
    rejected = set()
    for previous, current in zip(by_broadcast, by_broadcast[1:]):
        if current['b0'] < previous['b1'] - 1e-6:
            rejected.update((id(previous), id(current)))
    return [s for s in segments if id(s) not in rejected]


def mapped_time(segments, time):
    """Never extrapolate past anchors or bridge an unresolved interval."""
    for segment in segments:
        if segment['t0'] <= time <= segment['t1']:
            fraction = (time - segment['t0']) / (segment['t1'] - segment['t0'])
            return segment['b0'] + fraction * (segment['b1'] - segment['b0'])
    return None


@dataclass(frozen=True)
class GeometrySyncConfig:
    search_radius_s: float
    temporal_step_s: float
    min_pairs_per_team: int
    min_pair_fraction: float
    max_distance_m: float
    peak_exclusion_s: float
    min_peak_margin_m: float

    def __post_init__(self):
        if (type(self.min_pairs_per_team) is not int or self.min_pairs_per_team < 2
                or not math.isfinite(self.min_pair_fraction) or not 0 < self.min_pair_fraction <= 1
                or any(not math.isfinite(v) or v <= 0 for v in
                       (self.search_radius_s, self.temporal_step_s, self.max_distance_m,
                        self.peak_exclusion_s, self.min_peak_margin_m))):
            raise ValueError('Explicit geometry timing/coverage settings required')


def _team_cost(tactical, broadcast, tteams, bteams, pitch, cfg):
    costs = []
    for team in (0, 1):
        a, b = tactical[tteams == team], broadcast[bteams == team]
        a, b = a[np.isfinite(a).all(1)], b[np.isfinite(b).all(1)]
        if min(len(a), len(b)) < cfg.min_pairs_per_team:
            return None
        distances = np.linalg.norm((a[:, None, :] - b[None, :, :]) * pitch, axis=2)
        nearest_b, nearest_a = distances.argmin(1), distances.argmin(0)
        mutual_a = np.flatnonzero(nearest_a[nearest_b] == np.arange(len(a)))
        if (len(mutual_a) < cfg.min_pairs_per_team
                or len(mutual_a) / min(len(a), len(b)) < cfg.min_pair_fraction):
            return None
        costs.append(float(np.median(distances[mutual_a, nearest_b[mutual_a]])))
    return float(np.mean(costs))


def refine_anchor(anchor, tactical, broadcast, tteams, bteams, pitch, tfps, bfps, cfg,
                  tactical_valid=None, broadcast_valid=None):
    """Look for distinct team-position agreement around a clock candidate.

    IDs across sources are not paired; mutual nearest positions are transient
    geometric support only. All three temporal samples must be supported.
    Static/ambiguous peaks do not become a frame-accurate alignment.
    """
    if any(not math.isfinite(v) or v <= 0 for v in (tfps, bfps)):
        raise ValueError('Positive source FPS required')
    tactical, broadcast = np.asarray(tactical), np.asarray(broadcast)
    tteams, bteams, pitch = np.asarray(tteams), np.asarray(bteams), np.asarray(pitch, float)
    if (tactical.ndim != 3 or broadcast.ndim != 3 or tactical.shape[2] != 2 or broadcast.shape[2] != 2
            or tteams.shape != (tactical.shape[1],) or bteams.shape != (broadcast.shape[1],)
            or pitch.shape != (2,) or not np.isfinite(pitch).all() or (pitch <= 0).any()):
        raise ValueError('Normalized source positions, team slots and pitch dimensions required')
    t0, b0 = anchor['tactical_time_s'], anchor['broadcast_time_s']
    candidates, costs = [], []
    lo = max(0, math.ceil((b0 - cfg.search_radius_s) * bfps))
    hi = min(len(broadcast) - 1, math.floor((b0 + cfg.search_radius_s) * bfps))
    for bf in range(lo, hi + 1):
        samples = []
        for offset in (-cfg.temporal_step_s, 0., cfg.temporal_step_s):
            ti, bi = round((t0 + offset) * tfps), round(bf + offset * bfps)
            if (ti < 0 or bi < 0 or ti >= len(tactical) or bi >= len(broadcast)
                    or tactical_valid is not None and not tactical_valid[ti]
                    or broadcast_valid is not None and not broadcast_valid[bi]):
                break
            cost = _team_cost(tactical[ti], broadcast[bi], tteams, bteams, pitch, cfg)
            if cost is None:
                break
            samples.append(cost)
        if len(samples) == 3:
            candidates.append(bf / bfps)
            costs.append(float(np.mean(samples)))
    result = dict(anchor)
    result['geometry_status'] = 'insufficient_geometry'
    if not costs:
        return result
    best = int(np.argmin(costs))
    alternative = [cost for time, cost in zip(candidates, costs)
                   if abs(time - candidates[best]) >= cfg.peak_exclusion_s]
    margin = min(alternative) - costs[best] if alternative else None
    result.update(geometry_residual_m=costs[best], geometry_peak_margin_m=margin)
    if costs[best] > cfg.max_distance_m:
        result['geometry_status'] = 'source_geometry_disagrees'
    elif margin is None or margin < cfg.min_peak_margin_m:
        result['geometry_status'] = 'ambiguous_geometry_peak'
    else:
        result.update(broadcast_time_s=candidates[best], geometry_supported=True,
                      status='clock_and_tracking_candidate', geometry_status='supported',
                      uncertainty_s=cfg.peak_exclusion_s)
    return result
