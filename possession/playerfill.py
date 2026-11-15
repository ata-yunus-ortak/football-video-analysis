"""Players the tactical tracking has lost, added from the broadcast tracking (possession v2.16 candidate).

The tactical tracker loses players for a second or two, most often where players are close together. The
broadcast camera follows the ball and often still sees them. After the time alignment and the player-based
registration of possession/register.py (the same per-frame offset that corrects the broadcast ball), a broadcast
player with no tactical player of either team within EMPTY_R_M metres is taken as a player the tactical tracking
does not have at that moment and is added, under the team the broadcast tracking gives it, in an extra slot
(one extra slot per broadcast track, so an added player keeps its slot while the broadcast track lasts).
Tactical positions are never moved or removed. Frames without an accepted broadcast frame or without a usable
offset get nothing. The step is used only when the accuracy gate of possession/fusion.py is open (the two
cameras agree on the ball), and the goalkeeper team check then runs on the tracking with the added players.

Fixed constants (possession-v216-plan.json); nothing is fitted to the provided match. NumPy only.
"""
import numpy as np
from .register import frame_offsets, _nan_window, MEDIAN_HALF_S

EMPTY_R_M = 1.5        # no tactical player of either team within this distance of the registered broadcast player
CHUNK = 2000


def fill_players(tac, bro, t_of_b, fps):
    """tac, bro: tracking dicts (players (n, S, 2), team (S,), ball (n, 2)); bro is the oriented broadcast tracking
    and t_of_b its tactical frame per broadcast frame (-1 = not accepted), both from the alignment.

    Returns (players with Sb extra slots, team with Sb extra entries, report). The report holds counts only.
    """
    tac_p, tac_team = np.asarray(tac['players']), np.asarray(tac['team'])
    bro_p, bro_team = np.asarray(bro['players'], np.float64), np.asarray(bro['team'])
    t_of_b = np.asarray(t_of_b)
    off = frame_offsets(bro_p, bro_team, np.asarray(bro['ball'], np.float64), tac_p, tac_team, t_of_b)
    sm = _nan_window(off, int(round(MEDIAN_HALF_S * fps)), np.nanmedian)
    sm[t_of_b < 0] = np.nan
    T, Sb = len(tac_p), bro_p.shape[1]
    extra = np.full((T, Sb, 2), np.nan, tac_p.dtype)
    acc = np.flatnonzero((t_of_b >= 0) & np.isfinite(sm).all(1))
    added = 0
    for s in range(0, len(acc), CHUNK):
        idx = acc[s:s + CHUNK]
        tt = t_of_b[idx]
        bp = bro_p[idx] - sm[idx][:, None]                         # registered broadcast players
        tp = tac_p[tt].astype(np.float64)                          # tactical players of both teams
        d = np.linalg.norm(bp[:, :, None] - tp[:, None], axis=3)
        d[~np.isfinite(d)] = np.inf
        lonely = np.isfinite(bp).all(2) & (d.min(2) > EMPTY_R_M) if tp.shape[1] else np.isfinite(bp).all(2)
        r, c = np.nonzero(lonely)
        extra[tt[r], c] = bp[r, c]
        added += len(r)
    has = np.isfinite(extra).all(2)
    rep = {'frames_with_a_usable_offset': int(len(acc)), 'player_positions_added': int(has.sum()),
           'frames_with_an_added_player': int(has.any(1).sum()), 'extra_slots': int(Sb),
           'extra_slots_used': int(has.any(0).sum()), 'empty_radius_m': EMPTY_R_M}
    return (np.concatenate([tac_p, extra], 1), np.r_[tac_team, bro_team].astype(tac_team.dtype), rep)
