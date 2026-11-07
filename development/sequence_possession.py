"""Symmetric, offline team evidence accumulation; external selection only.

The decoder accepts evidence, not labels, so image-derived evidence can later
use the same temporal layer after separate calibration. Tracking evidence is
an explicit adapter, not a substitute for the experimental video-led path.
"""
from dataclasses import dataclass
import numpy as np
from .continuity import pair_masks


@dataclass(frozen=True)
class SequenceConfig:
    radius_m: float
    relative_speed_scale_mps: float
    max_gap_s: float
    switch_cost_s: float
    mode: str

    def __post_init__(self):
        for name in ('radius_m', 'relative_speed_scale_mps', 'max_gap_s'):
            v = getattr(self, name)
            if not np.isfinite(v) or v <= 0:
                raise ValueError('Positive finite external calibration required')
        if not np.isfinite(self.switch_cost_s) or self.switch_cost_s < 0:
            raise ValueError('Nonnegative finite switch cost required')
        if self.mode not in ('geometry', 'relative_motion'):
            raise ValueError('Unknown evidence mode')


FIELDS = {'players', 'ball', 'teams', 'period', 'frame', 'fps', 'pitch',
          'ball_observed', 'player_detected', 'ball_pair_valid',
          'player_pair_valid', 'hybrid_tracking_version'}


def measurements(inputs):
    if set(inputs) - FIELDS:
        raise ValueError('Only measurement fields allowed; no targets or events')
    b, p = np.asarray(inputs['ball'], float), np.asarray(inputs['players'], float)
    teams, period = np.asarray(inputs['teams']), np.asarray(inputs['period'])
    n, fps = len(b), float(inputs['fps'])
    pitch = np.asarray(inputs['pitch'], float)
    if (n == 0 or p.ndim != 3 or p.shape[0] != n or p.shape[2] != 2
            or b.shape != (n, 2) or teams.shape != (p.shape[1],)
            or not np.isin(teams, (0, 1)).all() or period.shape != (n,)
            or not np.isfinite(fps) or fps <= 0 or pitch.shape != (2,)
            or not np.isfinite(pitch).all() or (pitch <= 0).any()):
        raise ValueError('Aligned metric measurements and positive FPS required')
    bp, pp = pair_masks(inputs)
    observed = np.asarray(inputs['ball_observed']) & np.isfinite(b).all(1)
    observed &= np.isin(period, (1, 2)) & (b >= 0).all(1) & (b <= pitch).all(1)
    detected = np.asarray(inputs.get('player_detected', np.isfinite(p).all(2)))
    d = np.linalg.norm(p - b[:, None], axis=2)
    d[~detected | ~np.isfinite(d)] = np.inf
    nearest = np.full((n, 2), np.inf)
    relative = np.full((n, 2), np.nan)
    velocity = np.full_like(p, np.nan)
    velocity[1:] = (np.diff(p, axis=0) - np.diff(b, axis=0)[:, None]) * fps
    velocity[~(pp & bp[:, None])] = np.nan
    for team in (0, 1):
        ids = np.flatnonzero(teams == team)
        if not len(ids):
            continue
        slot = ids[np.argmin(d[:, ids], axis=1)]
        nearest[:, team] = d[np.arange(n), slot]
        relative[:, team] = np.linalg.norm(velocity[np.arange(n), slot], axis=1)
    usable = observed & np.isfinite(nearest).all(1)
    return nearest, relative, usable


def evidence(nearest, relative, usable, cfg):
    # Bounded evidence prevents one tracking jump dominating a whole spell.
    affinity = np.exp(-nearest / cfg.radius_m)
    if cfg.mode == 'relative_motion':
        # Unknown motion is neutral, not a zero-speed observation. Apply only
        # when both teams have comparable, continuous measured motion.
        both = np.isfinite(relative).all(1)
        affinity[both] /= 1 + relative[both] / cfg.relative_speed_scale_mps
    signed = affinity[:, 0] - affinity[:, 1]
    signed[~usable] = 0
    return signed


def decode(signed, usable, period, frame, fps, cfg):
    """Maximize dt-weighted evidence minus a cost per ownership change.

    No evidence -> X. Reset at period/frame breaks and long unsupported runs.
    No interpolation of ball positions. Mid-gap transition placement remains
    uncertain and is returned as X instead of claiming an observed receiver.
    """
    signed, usable = np.asarray(signed, float), np.asarray(usable)
    period, frame = np.asarray(period), np.asarray(frame)
    n = len(signed)
    if (signed.shape != (n,) or usable.shape != (n,) or usable.dtype.kind != 'b'
            or period.shape != (n,) or frame.shape != (n,)
            or not np.isfinite(signed).all() or np.any(np.abs(signed) > 1 + 1e-9)
            or not np.isfinite(fps) or fps <= 0):
        raise ValueError('Aligned bounded evidence and boolean support required')
    out = np.full(n, 'X', dtype='<U1')
    if not n:
        return out
    breaks = np.r_[True, (np.diff(frame) != 1) | (period[1:] != period[:-1])]
    starts = np.flatnonzero(breaks)
    max_gap = int(np.floor(cfg.max_gap_s * fps + 1e-9))
    for a, b in zip(starts, np.r_[starts[1:], n]):
        if period[a] not in (1, 2):
            continue
        support = np.flatnonzero(usable[a:b] & (signed[a:b] != 0)) + a
        if not len(support):
            continue
        cuts = np.r_[0, np.flatnonzero(np.diff(support) - 1 > max_gap) + 1, len(support)]
        for l, r in zip(cuts[:-1], cuts[1:]):
            first, stop = int(support[l]), int(support[r - 1]) + 1
            costs = [0., 0.]
            back = np.zeros((stop - first, 2), np.int8)
            for j, value in enumerate(signed[first:stop] / fps):
                h, away = costs
                # Prefer staying on exact ties; team-swapping symmetry holds
                # except truly symmetric paths, which are abstained below.
                back[j, 0] = int(away - cfg.switch_cost_s > h)
                back[j, 1] = int(away >= h - cfg.switch_cost_s)
                costs = [max(h, away - cfg.switch_cost_s) + value,
                         max(away, h - cfg.switch_cost_s) - value]
            if abs(costs[0] - costs[1]) < 1e-12:
                continue
            state = int(costs[1] > costs[0])
            for j in range(stop - first - 1, -1, -1):
                out[first + j] = 'A' if state else 'H'
                state = int(back[j, state])
            # Never claim direct control on unobserved frames. The inferred
            # spell can bridge these gaps, with provenance retained as X.
            out[first:stop][~usable[first:stop]] = 'X'
    return out


def predict(inputs, cfg):
    d, relative, usable = measurements(inputs)
    signed = evidence(d, relative, usable, cfg)
    return decode(signed, usable, inputs['period'], inputs['frame'], float(inputs['fps']), cfg)
