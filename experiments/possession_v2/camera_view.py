"""Development (training matches only): a tactical camera that follows play and does not always show the far
goalkeeper. Players outside a horizontal window around the centre of play are not tracked.

  window(m, half_width): boolean (T, S) 'in view' mask from the clean match: the camera centre is the median x of
  all players smoothed over 2 s; a player is in view while |x - centre| <= half_width (with 2 m of hysteresis so
  that tracks do not flicker at the edge)."""
import numpy as np
from scipy.ndimage import uniform_filter1d


def window(m, half_width, fps=25.0, hyst=2.0):
    P = np.asarray(m['players'], np.float64)
    x = P[..., 0]
    with np.errstate(all='ignore'):
        c = np.nanmedian(x, 1)
    idx = np.maximum.accumulate(np.where(np.isfinite(c), np.arange(len(c)), -1))
    c = np.where(idx >= 0, c[np.maximum(idx, 0)], m['pitch'][0] / 2)
    c = uniform_filter1d(c, int(2 * fps), mode='nearest')
    d = np.abs(x - c[:, None])
    inside = d <= half_width - hyst
    outside = ~(d <= half_width + hyst)                   # NaN counts as outside
    vis = np.zeros(x.shape, bool)
    state = np.zeros(x.shape[1], bool)
    for t in range(len(x)):
        state = np.where(inside[t], True, np.where(outside[t], False, state))
        vis[t] = state
    return vis


def apply_view(dm, clean, half_width):
    """Corrupted copy dm (columns 0..S-1 = the clean columns, extra columns = wrong-team tracklets of the corruption)
    with every position outside the camera window removed. The window is computed on the clean match."""
    S = clean['players'].shape[1]
    vis = window(clean, half_width)
    P = np.asarray(dm['players']).copy()
    L = clean['pitch'][0]
    x = np.asarray(clean['players'], np.float64)[..., 0]
    with np.errstate(all='ignore'):
        c = np.nanmedian(x, 1)
    P[:, :S][~vis] = np.nan
    # extra columns (short wrong-team tracklets): drop positions outside the window around the same centre
    idx = np.maximum.accumulate(np.where(np.isfinite(c), np.arange(len(c)), -1))
    c = np.where(idx >= 0, c[np.maximum(idx, 0)], L / 2)
    c = uniform_filter1d(c, 50, mode='nearest')
    extra = P[:, S:]
    out = ~(np.abs(extra[..., 0] - c[:, None]) <= half_width)
    extra[out] = np.nan
    return dict(dm, players=P), vis
