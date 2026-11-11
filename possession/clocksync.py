"""Coarse tactical <-> broadcast time mapping from the on-screen match clock (possession v2.5b candidate).

Input: the automatic clock observations that tools/clock_observations.py writes for each video
(observations.jsonl: video_time_s, clock_s or null, confidence). The run/anchor logic is adapted from
development/clock_alignment.py (experiment S002) and keeps its conservative rules: a clock value is
used only when it lies in exactly one consistent run of each video (repeated clocks such as first-
half added time vs. second half are skipped). The result is one lag per tactical half (median of the
anchor lags), with +-1 s uncertainty from the clock's whole seconds; frame-level alignment is left
to the geometric refinement in possession/fusion.py. Replays keep the live clock on screen while
showing old pictures; those frames are rejected later by the player-position check, not here.
Parameters are the registered S002 values (sync-review-plan.json); nothing is fitted to the match.
"""
import json
import math
import numpy as np

MIN_CONFIDENCE = 0.8
MAX_SAMPLE_GAP_S = 15.0
MAX_CLOCK_RESIDUAL_S = 1.1
MIN_RUN_SAMPLES = 3
MIN_RUN_SPAN_S = 10.0
MIN_ANCHORS = 10          # per half
MAX_LAG_IQR_S = 1.5       # per half: anchors must agree


def read_observations(path):
    rows = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                rows.append({'video_time_s': float(r['video_time_s']), 'clock_s': r.get('clock_s'),
                             'confidence': r.get('confidence'), 'period': r.get('period')})
    return rows


def clock_runs(rows):
    """Sequences of confident readings whose clock advances with the video time (within 1.1 s)."""
    result, run = [], []
    prev_time = -math.inf

    def finish():
        if len(run) >= MIN_RUN_SAMPLES and run[-1]['video_time_s'] - run[0]['video_time_s'] >= MIN_RUN_SPAN_S:
            periods = {r.get('period') for r in run if r.get('period') is not None}
            result.append({'id': len(result), 'rows': list(run),
                           'period': next(iter(periods)) if len(periods) == 1 else None})
    for row in rows:
        t = row['video_time_s']
        if not math.isfinite(t) or t <= prev_time:
            raise ValueError('chronological clock observations required')
        prev_time = t
        clock, conf = row.get('clock_s'), row.get('confidence')
        if clock is None or conf is None or not math.isfinite(clock) or conf < MIN_CONFIDENCE:
            continue
        if run:
            p = run[-1]
            elapsed, advance = t - p['video_time_s'], clock - p['clock_s']
            run_period = next((r['period'] for r in run if r.get('period') is not None), None)
            period_change = run_period is not None and row.get('period') is not None and run_period != row['period']
            if elapsed > MAX_SAMPLE_GAP_S or advance <= 0 or period_change or abs(advance - elapsed) > MAX_CLOCK_RESIDUAL_S:
                finish()
                run = []
        run.append(row)
    finish()
    return result


def _contains(run, clock, period):
    return (run['rows'][0]['clock_s'] <= clock <= run['rows'][-1]['clock_s']
            and (period is None or run['period'] is None or period == run['period']))


def clock_anchors(tactical_rows, broadcast_rows):
    """(tactical_time_s, broadcast_time_s) pairs showing the same clock value, unique runs only."""
    tac, bro = clock_runs(tactical_rows), clock_runs(broadcast_rows)
    anchors = []
    for run in tac:
        for row in run['rows']:
            clock = row['clock_s']
            own = [r for r in tac if _contains(r, clock, run['period'])]
            other = [r for r in bro if _contains(r, clock, run['period'])]
            if len(own) != 1 or len(other) != 1:
                continue
            target = other[0]
            bt = float(np.interp(clock, [r['clock_s'] for r in target['rows']],
                                 [r['video_time_s'] for r in target['rows']]))
            anchors.append((row['video_time_s'], bt))
    return sorted(anchors)


def half_lags(tactical_rows, broadcast_rows, fps, halves):
    """{period: lag in frames (tactical = broadcast + lag)} for halves with enough agreeing anchors."""
    anchors = clock_anchors(tactical_rows, broadcast_rows)
    out, report = {}, {'anchors': len(anchors), 'halves': []}
    for per, a, e in halves:
        lags = np.array([round(fps * (tt - bt)) for tt, bt in anchors if a <= round(tt * fps) <= e], float)
        rep = {'period': int(per), 'anchors': int(len(lags))}
        if len(lags) >= MIN_ANCHORS:
            q1, q3 = np.percentile(lags, [25, 75])
            rep.update(lag=int(np.median(lags)), iqr_frames=float(q3 - q1))
            if q3 - q1 <= MAX_LAG_IQR_S * fps:
                out[int(per)] = int(np.median(lags))
        rep['used'] = int(per) in out
        report['halves'].append(rep)
    return out, report
