"""Learned dead-ball (D) mask from player tracking only.

Trained on external IDSSE/DFL matches whose position feed has a per-frame
BallStatus (alive/dead). The ball is NOT a feature: the DFL ball position is
frozen during every dead frame, so ball features would leak the label and
would not transfer to feeds where the ball is missing in stoppages.

No events, tags, labels or ball coordinates enter `features`. Inputs follow the
repository convention: player metres from the pitch corner (normalised x/y
times pitch size). Everything is expressed in seconds and metres, so the
model does not depend on the frame rate.
"""
import warnings

import numpy as np

MAX_PLAYER_SPEED_MPS = 12.5      # physical guard; faster steps are unreliable


def centred(players, pitch):
    """Corner-origin metres -> pitch-centred metres."""
    return np.asarray(players, float) - np.asarray(pitch, float) / 2


def _rolling_mean(a, w, mode):
    """NaN-aware rolling mean; mode c(entred), p(ast) or f(uture)."""
    n = len(a)
    finite = np.isfinite(a)
    cs = np.concatenate([[0.0], np.cumsum(np.where(finite, a, 0.0))])
    cn = np.concatenate([[0], np.cumsum(finite)])
    i = np.arange(n)
    lo, hi = {"c": (i - w // 2, i + w // 2 + 1), "p": (i - w + 1, i + 1), "f": (i, i + w)}[mode]
    lo, hi = np.clip(lo, 0, n), np.clip(hi, 0, n)
    count = cn[hi] - cn[lo]
    return np.where(count > 0, (cs[hi] - cs[lo]) / np.maximum(count, 1), np.nan)


def _frame_features(p, teams, fps, pitch):
    """Instantaneous features for one period. p: (F, P, 2) centred metres."""
    length, width = pitch
    out = {}
    for base_s in (1.0, 3.0):    # displacement over 1 s / 3 s: robust to position jitter
        h = max(1, int(round(fps * base_s / 2)))
        v = np.full(p.shape[:2], np.nan)
        if len(p) > 2 * h:
            v[h:-h] = np.linalg.norm(p[2 * h:] - p[:-2 * h], axis=2) / (2 * h / fps)
        v = np.where(v > MAX_PLAYER_SPEED_MPS, np.nan, v)
        tag = f"{int(base_s)}s"
        for name, sel in (("all", slice(None)), ("t0", teams == 0), ("t1", teams == 1)):
            out[f"spd{tag}_mean_{name}"] = np.nanmean(v[:, sel], 1)
            out[f"spd{tag}_p90_{name}"] = np.nanpercentile(v[:, sel], 90, axis=1)
        fin = np.isfinite(v)
        n = np.maximum(fin.sum(1), 1)
        out[f"spd{tag}_frac_still"] = np.where(fin, v < 1.0, False).sum(1) / n
        out[f"spd{tag}_frac_walk"] = np.where(fin, v < 2.0, False).sum(1) / n
        out[f"spd{tag}_frac_run"] = np.where(fin, v > 4.0, False).sum(1) / n
    x, y = p[..., 0], p[..., 1]
    centroid = {}
    for t in (0, 1):
        xs, ys = x[:, teams == t], y[:, teams == t]
        centroid[t] = (np.nanmean(xs, 1), np.nanmean(ys, 1))
        out[f"spread_x_t{t}"] = np.nanstd(xs, 1)
        out[f"spread_y_t{t}"] = np.nanstd(ys, 1)
    out["centroid_gap"] = np.hypot(centroid[0][0] - centroid[1][0], centroid[0][1] - centroid[1][1])
    out["centroid_absx"] = np.abs((centroid[0][0] + centroid[1][0]) / 2)
    out["centroid_absy"] = np.abs((centroid[0][1] + centroid[1][1]) / 2)
    # set-piece shapes
    out["n_near_touch"] = np.sum(np.abs(y) > width / 2 - 1.5, 1)
    out["n_off_pitch"] = np.sum((np.abs(x) > length / 2) | (np.abs(y) > width / 2), 1)
    out["n_in_box"] = np.sum((np.abs(x) > length / 2 - 16.5) & (np.abs(y) < 20.16), 1)
    out["min_dist_centre"] = np.nanmin(np.hypot(x, y), 1)
    # kickoff shape: each team on its own side of halfway
    side0 = np.sign(np.nanmean(x[:, teams == 0], 1))
    own = np.where(teams == 0, side0[:, None], -side0[:, None]) * x
    out["frac_own_half"] = np.nanmean(own > -0.5, 1)
    return out


def features(players, teams, period, fps, pitch, *, origin="corner"):
    """Per-frame feature matrix (F, K) and names. Windows never cross a period boundary."""
    players = np.asarray(players, float)
    teams, period = np.asarray(teams), np.asarray(period)
    if players.ndim != 3 or players.shape[2] != 2 or teams.shape != (players.shape[1],):
        raise ValueError("players (F, P, 2) and aligned team slots required")
    if period.shape != (len(players),) or not np.isin(teams, (0, 1)).all():
        raise ValueError("aligned period and 0/1 teams required")
    fps = float(fps)
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError("positive frame rate required")
    if origin == "corner":
        players = centred(players, pitch)
    elif origin != "centre":
        raise ValueError("origin must be 'corner' or 'centre'")
    names = None
    blocks_all = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN frames give NaN features
        for value in np.unique(period):
            m = period == value
            blocks = {}
            for key, v in _frame_features(players[m], teams, fps, pitch).items():
                v = v.astype(float)
                blocks[key] = v
                for sec in (1, 3, 8):
                    blocks[f"{key}_c{sec}"] = _rolling_mean(v, max(1, int(round(sec * fps))), "c")
                w = max(1, int(round(3 * fps)))
                blocks[f"{key}_p3"] = _rolling_mean(v, w, "p")
                blocks[f"{key}_f3"] = _rolling_mean(v, w, "f")
            names = list(blocks)
            blocks_all.append((m, np.column_stack([blocks[k] for k in names])))
    rows = np.full((len(players), len(names)), np.nan, np.float32)
    for m, block in blocks_all:
        rows[m] = block
    return rows, names


def corrupt(players, rng, missing_frac, jitter_m, fps, gap_mean_s=3.0):
    """Training augmentation: smooth drift + white jitter and per-player missing segments."""
    p = np.array(players, float, copy=True)
    n, slots, _ = p.shape
    if jitter_m > 0:
        k = max(1, int(fps))
        drift = np.cumsum(rng.normal(0, jitter_m, (n + k, slots, 2)), 0)
        p += (drift[k:] - drift[:-k]) / np.sqrt(k) + rng.normal(0, jitter_m / 2, p.shape)
    if missing_frac > 0:
        gap = max(1, int(gap_mean_s * fps))
        for j in range(slots):
            for start in rng.integers(0, n, rng.poisson(missing_frac * n / gap)):
                p[start:start + max(1, int(rng.exponential(gap))), j] = np.nan
    return p


def _runs(mask):
    d = np.diff(np.r_[0, mask.astype(int), 0])
    return zip(np.where(d == 1)[0], np.where(d == -1)[0])


def smooth(prob, period, fps, window_s, threshold, min_run_s):
    """Centred mean of D probability, threshold, then remove D/live runs shorter than min_run_s.

    Runs touching a period edge are kept.
    """
    prob, period = np.asarray(prob, float), np.asarray(period)
    out = np.zeros(len(prob), bool)
    for value in np.unique(period):
        idx = np.where(period == value)[0]
        w = max(1, int(round(window_s * fps)))
        q = np.convolve(np.pad(prob[idx], (w // 2, w - 1 - w // 2), mode="edge"), np.ones(w) / w, "valid")
        lab = q >= threshold
        shortest = int(round(min_run_s * fps))
        for state in (True, False):
            for a, b in list(_runs(lab == state)):
                if b - a < shortest and a > 0 and b < len(lab):
                    lab[a:b] = not state
        out[idx] = lab
    return out


def predict_mask(model, inputs, smoothing):
    """Boolean D mask for a repository input dict (players, teams, period, fps, pitch)."""
    x, _ = features(inputs["players"], inputs["teams"], inputs["period"], inputs["fps"], inputs["pitch"])
    prob = model.predict_proba(x)[:, 1]
    window_s, threshold, min_run_s = smoothing
    return smooth(prob, inputs["period"], float(inputs["fps"]), window_s, threshold, min_run_s)
