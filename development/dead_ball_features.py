"""Tracking-only measurements for a future D layer; never emits D labels.

An out-of-pitch point or a stationary/missing ball is evidence to inspect, not
proof that play stopped. No interpolation or tuned classification threshold is
used here. Positions use metres with the pitch's top-left corner as the origin.
"""
import warnings
import numpy as np
from .continuity import pair_masks


def _run_age(mask, period, fps, pairs=None):
    age = np.zeros(len(mask), float)
    first = 0
    for index in range(len(mask)):
        if index == 0 or not mask[index - 1] or period[index] != period[index - 1] or pairs is not None and not pairs[index]:
            first = index
        if mask[index]:
            age[index] = (index - first) / fps
    return age


def extract(inputs):
    if {"labels", "targets", "events", "possession", "manual_annotations"}.intersection(inputs):
        raise ValueError("Feature extraction accepts tracking inputs only")
    ball = np.asarray(inputs["ball"], float)
    players = np.asarray(inputs["players"], float)
    period = np.asarray(inputs["period"])
    frame = np.asarray(inputs["frame"])
    observed = np.asarray(inputs["ball_observed"])
    fps = float(inputs["fps"])
    pitch = np.asarray(inputs["pitch"], float)
    n = len(ball)
    if (n == 0 or ball.shape != (n, 2) or players.ndim != 3
            or players.shape[0] != n or players.shape[2] != 2
            or period.shape != (n,) or frame.shape != (n,) or observed.shape != (n,)
            or observed.dtype.kind != "b" or not np.isfinite(fps) or fps <= 0
            or pitch.shape != (2,) or not np.all(np.isfinite(pitch) & (pitch > 0))
            or not np.all(np.diff(frame) == 1)):
        raise ValueError("Aligned consecutive tracking, boolean visibility, pitch and positive FPS required")

    active = np.isin(period, (1, 2))
    present = observed & np.isfinite(ball).all(axis=1) & active
    margin = np.min(np.column_stack((ball[:, 0], pitch[0] - ball[:, 0],
                                    ball[:, 1], pitch[1] - ball[:, 1])), axis=1)
    margin[~present] = np.nan
    outside = present & (margin < 0)
    adjacent = np.zeros(n, bool)
    adjacent[1:] = active[1:] & (period[1:] == period[:-1])
    ball_pair, player_pair = pair_masks(inputs)
    ball_pair[1:] &= present[1:] & present[:-1]
    speed = np.full(n, np.nan)
    step = np.linalg.norm(np.diff(ball, axis=0), axis=1) * fps
    speed[1:] = np.where(ball_pair[1:], step, np.nan)
    player_speed = np.linalg.norm(np.diff(players, axis=0), axis=2) * fps
    player_speed[~player_pair[1:]] = np.nan
    median_player_speed = np.full(n, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        median_player_speed[1:] = np.nanmedian(player_speed, axis=1)
    exit_step = np.zeros(n, bool)
    return_step = np.zeros(n, bool)
    exit_step[1:] = ball_pair[1:] & outside[1:] & ~outside[:-1]
    return_step[1:] = ball_pair[1:] & ~outside[1:] & outside[:-1]
    outside_age = _run_age(outside, period, fps, ball_pair)
    outside_age[~outside] = np.nan
    missing_age = _run_age(~present & active, period, fps)
    missing_age[~active] = np.nan
    return {
        "ball_present": present,
        "ball_edge_margin_m": margin,
        "ball_outside_point": outside,
        "ball_speed_mps": speed,
        "median_player_speed_mps": median_player_speed,
        "ball_missing_run_s": missing_age,
        "observed_outside_run_s": outside_age,
        "observed_exit_step": exit_step,
        "observed_return_step": return_step,
    }
