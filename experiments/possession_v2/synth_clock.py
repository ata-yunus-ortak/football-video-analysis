"""Simulated automatic clock observations (development only): every 5 s a reading of the match clock
(whole seconds from the kick-off of each half, second half starting at 45:00) shown at the live time
of that video frame; unreadable with probability 1 - p_read, misread (random clock) with p_misread."""
import numpy as np


def observations(live_time, blocks, fps, rng, p_read, p_misread, interval_s=5.0):
    """live_time: tactical frame shown live at each frame of this video (-1 = none)."""
    n = len(live_time)
    step = int(round(interval_s * fps))
    rows = []
    for f in range(int(rng.integers(0, step)), n, step):
        lt = int(live_time[f])
        clock = None
        for h, (a, e) in enumerate(blocks):
            if a <= lt < e:
                clock = float((lt - a) // int(fps) + 2700 * h)
        u = rng.random()
        if clock is not None and u < p_read:
            row = {'clock_s': clock, 'confidence': 0.95}
        elif u < p_read + p_misread:
            row = {'clock_s': float(rng.integers(0, 5700)), 'confidence': 0.9}
        else:
            row = {'clock_s': None, 'confidence': None}
        rows.append(dict(row, video_time_s=f / fps, period=None))
    return rows
