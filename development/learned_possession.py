"""Learned H/A possession for live-ball frames from player and (optional) ball tracking.

Trained on IDSSE/DFL per-frame BallPossession, live frames only (D is handled by
learned_dead_ball). Inputs follow the repository convention: corner-origin metres.
The ball may be missing (NaN); features are designed to degrade to player shape then.
No events, tags or labels are inputs. Seconds and metres only: frame-rate independent.
"""
import warnings

import numpy as np

from .learned_dead_ball import MAX_PLAYER_SPEED_MPS, _rolling_mean, _runs, centred

MAX_BALL_SPEED_MPS = 40.0


def _speed(p, fps, base_s, limit):
    h = max(1, int(round(fps * base_s / 2)))
    v = np.full(p.shape[:-1], np.nan)
    if len(p) > 2 * h:
        v[h:-h] = np.linalg.norm(p[2 * h:] - p[:-2 * h], axis=-1) / (2 * h / fps)
    return np.where(v > limit, np.nan, v)


def _frame_features(p, ball, teams, fps, pitch):
    """p (F, P, 2), ball (F, 2), centred metres. Team 0 is home (H)."""
    length, _ = pitch
    out = {}
    x = p[..., 0]
    # attacking direction: each team defends the side of its own centroid
    side0 = np.sign(np.nanmean(x[:, teams == 0], 1))
    side0 = np.where(side0 == 0, 1.0, side0)
    attack = {0: -side0, 1: side0}                 # +1 means the team attacks towards +x
    vx = np.full(x.shape, np.nan)
    h = max(1, int(round(fps / 2)))
    if len(p) > 2 * h:
        vx[h:-h] = (x[2 * h:] - x[:-2 * h]) / (2 * h / fps)
    vx = np.where(np.abs(vx) > MAX_PLAYER_SPEED_MPS, np.nan, vx)
    for t in (0, 1):
        sel = teams == t
        ax = attack[t]
        out[f"t{t}_advance"] = np.nanmean(x[:, sel], 1) * ax          # how far up the pitch
        out[f"t{t}_front"] = np.nanmax(x[:, sel] * ax[:, None], 1)
        out[f"t{t}_forward_speed"] = np.nanmean(vx[:, sel] * ax[:, None], 1)
        out[f"t{t}_spread_x"] = np.nanstd(x[:, sel], 1)
        out[f"t{t}_spread_y"] = np.nanstd(p[:, sel, 1], 1)
    out["advance_diff"] = out["t0_advance"] - out["t1_advance"]
    out["forward_speed_diff"] = out["t0_forward_speed"] - out["t1_forward_speed"]
    out["spread_y_diff"] = out["t0_spread_y"] - out["t1_spread_y"]
    # ball relations, NaN when the ball is missing
    seen = np.isfinite(ball).all(1)
    out["ball_seen"] = seen.astype(float)
    d = np.linalg.norm(p - ball[:, None, :], axis=2)
    for t in (0, 1):
        dt = np.sort(np.where(np.isfinite(d[:, teams == t]), d[:, teams == t], np.inf), 1)
        near = np.where(np.isfinite(dt[:, 0]), dt[:, 0], np.nan)
        out[f"t{t}_ball_d1"] = near
        out[f"t{t}_ball_d2"] = np.where(np.isfinite(dt[:, 1]), dt[:, 1], np.nan)
        out[f"t{t}_within5"] = np.where(seen, np.sum(dt < 5, 1), np.nan)
    out["ball_d1_diff"] = out["t0_ball_d1"] - out["t1_ball_d1"]
    out["ball_x_home_attack"] = ball[:, 0] * attack[0]
    out["ball_absy"] = np.abs(ball[:, 1])
    bv = _speed(ball, fps, 0.4, MAX_BALL_SPEED_MPS)
    out["ball_speed"] = bv
    bvx = np.full(len(ball), np.nan)
    hb = max(1, int(round(fps * 0.2)))
    if len(ball) > 2 * hb:
        bvx[hb:-hb] = (ball[2 * hb:, 0] - ball[:-2 * hb, 0]) / (2 * hb / fps)
    out["ball_vx_home_attack"] = np.where(np.abs(bvx) > MAX_BALL_SPEED_MPS, np.nan, bvx) * attack[0]
    return out


def features(players, teams, ball, period, fps, pitch, *, origin="corner"):
    players, ball = np.asarray(players, float), np.asarray(ball, float)
    teams, period = np.asarray(teams), np.asarray(period)
    if players.ndim != 3 or ball.shape != (len(players), 2) or teams.shape != (players.shape[1],):
        raise ValueError("aligned players (F, P, 2), ball (F, 2) and team slots required")
    if period.shape != (len(players),) or not np.isin(teams, (0, 1)).all():
        raise ValueError("aligned period and 0/1 teams required")
    if origin == "corner":
        players, ball = centred(players, pitch), centred(ball, pitch)
    elif origin != "centre":
        raise ValueError("origin must be 'corner' or 'centre'")
    fps = float(fps)
    names, parts = None, []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        for value in np.unique(period):
            m = period == value
            blocks = {}
            for key, v in _frame_features(players[m], ball[m], teams, fps, pitch).items():
                v = v.astype(float)
                blocks[key] = v
                for sec in (1, 3):
                    blocks[f"{key}_c{sec}"] = _rolling_mean(v, max(1, int(round(sec * fps))), "c")
                w = max(1, int(round(2 * fps)))
                blocks[f"{key}_p2"] = _rolling_mean(v, w, "p")
                blocks[f"{key}_f2"] = _rolling_mean(v, w, "f")
            names = list(blocks)
            parts.append((m, np.column_stack([blocks[k] for k in names])))
    x = np.full((len(players), len(names)), np.nan, np.float32)
    for m, block in parts:
        x[m] = block
    return x, names


def corrupt_ball(ball, rng, missing_frac, jitter_m, fps, gap_mean_s=1.0):
    """Augmentation: ball jitter and missing segments."""
    b = np.array(ball, float, copy=True)
    if jitter_m > 0:
        b += rng.normal(0, jitter_m, b.shape)
    if missing_frac > 0:
        gap = max(1, int(gap_mean_s * fps))
        for start in rng.integers(0, len(b), rng.poisson(missing_frac * len(b) / gap)):
            b[start:start + max(1, int(rng.exponential(gap)))] = np.nan
    return b


def decode(prob_home, dead, period, fps, window_s, margin, min_spell_s):
    """H/A/D labels: smoothed home probability with hysteresis, short spells merged, D on top.

    prob_home: P(H) per frame. A team change needs the smoothed probability to cross
    0.5 +/- margin. Spells shorter than min_spell_s inside live play are absorbed by
    the previous spell.
    """
    prob_home, dead, period = np.asarray(prob_home, float), np.asarray(dead, bool), np.asarray(period)
    labels = np.full(len(prob_home), "D", dtype="<U1")
    w = max(1, int(round(window_s * fps)))
    shortest = int(round(min_spell_s * fps))
    for value in np.unique(period):
        idx = np.where(period == value)[0]
        q = np.convolve(np.pad(prob_home[idx], (w // 2, w - 1 - w // 2), mode="edge"), np.ones(w) / w, "valid")
        state = q[0] >= 0.5
        home = np.empty(len(idx), bool)
        for i, v in enumerate(q):
            if state and v < 0.5 - margin:
                state = False
            elif not state and v > 0.5 + margin:
                state = True
            home[i] = state
        live = ~dead[idx]
        for a, b in _runs(live):
            seg = home[a:b]
            changes = np.flatnonzero(seg[1:] != seg[:-1]) + 1
            bounds = np.r_[0, changes, len(seg)]
            for k in range(1, len(bounds) - 1):
                if bounds[k + 1] - bounds[k] < shortest:
                    seg[bounds[k]:bounds[k + 1]] = seg[bounds[k] - 1]
            home[a:b] = seg
        lab = np.where(home, "H", "A")
        lab[~live] = "D"
        labels[idx] = lab
    return labels
