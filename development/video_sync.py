"""Conservative candidates from independently observed on-screen clocks.

Whole-second clocks cannot establish frame-accurate live-play correspondence.
Repeated/frozen bins remain unresolved. Even a unique clock candidate still
requires independently validated geometric/temporal confirmation before fusion.
This module neither reads OCR nor invents a global broadcast-to-tactical offset.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ClockSyncConfig:
    min_confidence: float
    max_sample_gap_s: float
    max_bin_span_s: float
    clock_resolution_s: float

    def __post_init__(self):
        if (not math.isfinite(self.min_confidence) or not 0 < self.min_confidence <= 1
                or any(not math.isfinite(v) or v <= 0 for v in
                       (self.max_sample_gap_s, self.max_bin_span_s, self.clock_resolution_s))):
            raise ValueError('Explicit finite clock confidence and timing settings required')


def _validate(readings):
    previous = -math.inf
    for row in readings:
        if (row.get('source_kind') != 'automatic_clock_observation'
                or row.get('period') not in (1, 2)
                or any(not isinstance(row.get(k), (int, float)) or not math.isfinite(row[k])
                       for k in ('video_time_s', 'clock_s', 'confidence'))
                or row['video_time_s'] <= previous or row['video_time_s'] < 0
                or row['clock_s'] < 0 or not 0 <= row['confidence'] <= 1):
            raise ValueError('Chronological automatic period/clock observations required')
        previous = row['video_time_s']


def clock_candidates(tactical, broadcast, cfg):
    _validate(tactical)
    _validate(broadcast)
    bins = {}
    for row in broadcast:
        if row['confidence'] < cfg.min_confidence:
            continue
        key = (row['period'], math.floor(row['clock_s'] / cfg.clock_resolution_s))
        bins.setdefault(key, []).append(row['video_time_s'])
    result = []
    for row in tactical:
        base = {'tactical_time_s': row['video_time_s'], 'period': row['period'],
                'clock_s': row['clock_s'], 'broadcast_interval_s': None,
                'usable_for_possession': False, 'geometry_confirmed': False}
        key = (row['period'], math.floor(row['clock_s'] / cfg.clock_resolution_s))
        candidates = bins.get(key, []) if row['confidence'] >= cfg.min_confidence else []
        if not candidates:
            base['status'] = 'no_confident_clock_match'
        elif (candidates[-1] - candidates[0] > cfg.max_bin_span_s
              or any(b - a > cfg.max_sample_gap_s for a, b in zip(candidates, candidates[1:]))):
            base['status'] = 'repeated_frozen_or_discontinuous_clock'
        else:
            base['status'] = 'clock_candidate_requires_geometry'
            base['broadcast_interval_s'] = [max(0., candidates[0] - cfg.max_sample_gap_s),
                                             candidates[-1] + cfg.max_sample_gap_s]
            base['clock_quantization_s'] = cfg.clock_resolution_s
        result.append(base)
    return result
