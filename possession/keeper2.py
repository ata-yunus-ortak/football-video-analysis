"""Goalkeeper team correction, second version (possession v2.11 candidate).

An automatic tracker decides the team of a track from the kit, and a goalkeeper wears a different kit from
his team-mates. If goalkeeper tracks carry the other team's id, the features see an opponent standing in the
goal, the goalkeeper's possessions go to the wrong side and, with both goalkeepers affected, the attacking
directions of the two teams come out inverted. On external matches this lowered spellF1 by 0.02 to 0.04 for
one goalkeeper and by about 0.3 for both (stress_roles, 11 November 2026). Whether the provided tracking has
this error is not known and is not looked at; this step is a safeguard that leaves correct ids alone.

Differences from possession/keeper.py (v2.10, kept unchanged as validated): evidence counts only frames in which
the piece is clearly the last player (ISO_M nearer to the goal than anybody else), and a piece under the other
team's id is no longer moved on its own evidence alone. It is moved when the goalkeeper evidence of that goal in
that half is mostly under the other id (the goalkeeper carries the wrong id for most of the half), or when the
piece continues a goalkeeper piece in time and place (the goalkeeper carries the wrong id for a while). The first
version moved outfield players when a camera that follows play did not show the far goalkeeper: a forward waiting
up the pitch was then the tracked player nearest to the goal (development on training matches, 11 November).

Goalkeeper tracks are found from positions and track continuity only:
  1. Per half, the team whose players stand further left (median x per frame, averaged over the half; one
     misplaced player does not move a median) defends the left goal.
  2. A frame is "far" from a goal when the median x of all tracked players is at least FAR_M from its goal
     line: play is in the other half.
  3. A track piece is a slot's run of positions of one person (split at gaps longer than GAP frames and at
     impossible jumps). In a far frame the goalkeeper is the tracked player nearest to his goal and far
     behind everybody else: on the training matches he is at least ISO_M nearer to the goal than the second
     nearest player in 96-99% of such frames. A piece with at least MIN_FAR far frames that is nearest to a
     goal by ISO_M, and within ZONE_M of it, in at least SHARE of them has direct evidence ("strong").
  4. A strong piece in a slot of the defending team is a goalkeeper piece of that goal. A strong piece in a
     slot of the other team is one if the direct evidence under the other team's id is at least DOM_FRAMES
     frames and at least DOM_SHARE of all direct evidence of that goal in that half (the goalkeeper carries
     the wrong id for most of the half); otherwise it has to continue a goalkeeper piece (point 5).
  5. While play is near his goal a goalkeeper has no far frames. Such a piece ("weak": nearest to that goal
     in at least LINK_SHARE of its own frames) inherits the status from a goalkeeper piece that it continues
     in time and place (the tracker re-acquired the same person), if no other goalkeeper piece of that goal
     exists at the same time (a goal has one goalkeeper). A piece that carries the same team id as the piece
     it continues, or a strong piece, may follow within LINK_FRAMES and within LINK_M plus LINK_SPEED_M per
     frame of the gap (at most LINK_CAP_M more); a weak piece with the other id only as a direct hand-over
     (within HANDOVER_FRAMES and HANDOVER_M, and at least HANDOVER_LEN frames long).
  6. Goalkeeper pieces in a slot of the team that does not defend their goal are moved to new columns that
     belong to the defending team. Nothing else changes; without such pieces the match is returned as is.
"""
import warnings
import numpy as np
from .features import play_blocks

FAR_M = 50.0          # all-player median x at least this far from the goal line
MIN_FAR = 75          # far frames needed for direct evidence (3 s at 25 fps)
SHARE = 0.5           # nearest to the goal in this share of the far frames
ZONE_M = 50.0         # ... and not further from the goal centre than this
ISO_M = 8.0           # ... and at least this much nearer to it than the second-nearest tracked player
DOM_SHARE = 0.5       # direct evidence under the other team's id: at least this share of the goal's evidence in the half
DOM_FRAMES = 2500     # ... and at least this many frames (100 s)
GAP = 25              # frames a track may be lost and still be the same piece
JUMP_M = 2.5          # larger displacement between consecutive frames = another person
SPEED_M = 0.4         # metres per frame allowed across a gap inside a piece (10 m/s)
LINK_FRAMES = 375     # a goalkeeper piece may be continued after up to 15 s without a track
LINK_M = 4.0
LINK_SPEED_M = 0.12   # metres per frame a goalkeeper may have moved across such a gap (3 m/s)
LINK_CAP_M = 8.0      # ... but not more than this in total
HANDOVER_M = 1.5      # a piece with the other team id continues a goalkeeper piece only this close,
HANDOVER_FRAMES = 5   # ... this soon
HANDOVER_LEN = 13     # ... and only if it lasts at least this long
LINK_SHARE = 0.8      # a continuing piece is nearest to the goal in this share of its own frames
OVERLAP = 25          # frames two goalkeeper pieces of one goal may coexist (hand-over of a track)


def _pieces(xy):
    """[(first frame, end frame)] of the runs of one person in a slot; xy (T, 2) with NaN = missing."""
    idx = np.flatnonzero(np.isfinite(xy).all(1))
    if not len(idx):
        return []
    g = np.diff(idx)
    d = np.linalg.norm(xy[idx[1:]] - xy[idx[:-1]], axis=1)
    cut = np.flatnonzero((g > GAP) | (d > JUMP_M + SPEED_M * (g - 1))) + 1
    bounds = np.r_[0, cut, len(idx)]
    return [(int(idx[a]), int(idx[b - 1]) + 1) for a, b in zip(bounds[:-1], bounds[1:])]


def _block(Q, team, L, W):
    """Goalkeeper pieces of one half that sit in a slot of the wrong team: [(slot, a, b, defending team)], facts."""
    T, S, _ = Q.shape
    fin = np.isfinite(Q).all(2)
    x, y = Q[..., 0], Q[..., 1]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        side_x = [np.nanmean(np.nanmedian(np.where((team == k)[None], x, np.nan), 1)) for k in (0, 1)]
        cx = np.nanmedian(x, 1)
    if not np.isfinite(side_x).all() or side_x[0] == side_x[1]:
        return [], {'decided': False}
    left_team = 0 if side_x[0] < side_x[1] else 1
    pieces = [(j, a, b) for j in range(S) for a, b in _pieces(Q[:, j])]
    out, facts = [], {'decided': True, 'left_team': left_team, 'pieces': len(pieces)}
    rows = np.arange(T)
    for side, defending in (('left', left_team), ('right', 1 - left_team)):
        far = np.nan_to_num(cx if side == 'left' else L - cx, nan=0.0) >= FAR_M
        d = np.hypot(x if side == 'left' else L - x, y - W / 2)
        d = np.where(fin, d, np.inf)
        nearest = np.zeros((T, S), bool)
        alone = np.zeros((T, S), bool)                 # nearest, and ISO_M nearer than anybody else
        has = fin.any(1)
        first = np.argmin(d[has], 1)
        nearest[rows[has], first] = True
        two = np.partition(d[has], 1, axis=1)[:, :2] if S > 1 else np.c_[d[has][:, 0], np.full(int(has.sum()), np.inf)]
        alone[rows[has], first] = two[:, 1] - two[:, 0] >= ISO_M
        strong = np.zeros(len(pieces), bool)           # direct evidence in far frames
        weak = np.zeros(len(pieces), bool)             # not enough far frames, but mostly nearest to this goal
        evidence = np.zeros(len(pieces), np.int64)
        for i, (j, a, b) in enumerate(pieces):
            f = far[a:b] & fin[a:b, j]
            n_far = int(f.sum())
            if n_far >= MIN_FAR:
                evidence[i] = int((f & alone[a:b, j] & (d[a:b, j] <= ZONE_M)).sum())
                strong[i] = evidence[i] >= SHARE * n_far
            else:
                weak[i] = nearest[a:b, j].sum() >= LINK_SHARE * fin[a:b, j].sum()
        pteam = np.array([team[j] for j, _, _ in pieces])
        own = pteam == defending
        ev_own, ev_other = int(evidence[strong & own].sum()), int(evidence[strong & ~own].sum())
        dominant = ev_other >= DOM_FRAMES and ev_other >= DOM_SHARE * (ev_own + ev_other)
        keeper = strong & (own | dominant)
        candidate = (weak | strong) & ~keeper          # may inherit the status through continuity
        # continuity: a weak piece that continues a goalkeeper piece (either direction) is the same person
        start = np.array([Q[a, j] for j, a, b in pieces]).reshape(-1, 2)
        end = np.array([Q[b - 1, j] for j, a, b in pieces]).reshape(-1, 2)
        t0 = np.array([a for _, a, _ in pieces])
        t1 = np.array([b for _, _, b in pieces])
        covered = np.zeros(T, bool)
        for i in np.flatnonzero(keeper):
            j, a, b = pieces[i]
            covered[a:b] |= fin[a:b, j]
        changed = True
        while changed:
            changed = False
            ks = np.flatnonzero(keeper)
            for i in np.flatnonzero(candidate & ~keeper):
                j, a, b = pieces[i]
                if covered[a:b].sum() > OVERLAP:
                    continue
                same = (pteam[ks] == pteam[i]) | strong[i]           # a piece with direct evidence may use the wider link
                ok = False
                for gap, dist in ((t0[i] - t1[ks], np.linalg.norm(end[ks] - start[i], axis=1)),      # i starts after a goalkeeper piece ends
                                  (t0[ks] - t1[i], np.linalg.norm(start[ks] - end[i], axis=1))):     # i ends before a goalkeeper piece starts
                    reach = np.where(same, LINK_M + np.minimum(LINK_SPEED_M * np.maximum(gap, 0), LINK_CAP_M), HANDOVER_M)
                    window = np.where(same, LINK_FRAMES, HANDOVER_FRAMES if b - a >= HANDOVER_LEN else -OVERLAP - 1)
                    ok = ok or bool(((gap >= -OVERLAP) & (gap <= window) & (dist <= reach)).any())
                if ok:
                    keeper[i] = True
                    covered[a:b] |= fin[a:b, j]
                    changed = True
        facts[f'{side}_goalkeeper_pieces'] = int(keeper.sum())
        facts[f'{side}_far_share'] = round(float(far.mean()), 4)
        facts[f'{side}_evidence_frames'] = {'defending_id': ev_own, 'other_id': ev_other, 'other_id_dominant': bool(dominant)}
        out += [(j, a, b, defending) for i, (j, a, b) in enumerate(pieces) if keeper[i] and team[j] != defending]
    facts['moved_pieces'] = len(out)
    return out, facts


def correct_goalkeepers(match):
    """(match with goalkeeper pieces under the id of the team that defends their goal, report with aggregates).
    The input is returned unchanged (the same object) when no piece has to be moved."""
    players = np.asarray(match['players'])
    team = np.asarray(match['team'])
    L, W = [float(v) for v in match['pitch']]
    moves, report = [], {'halves': []}
    for a, b in play_blocks(match['period']):
        found, facts = _block(players[a:b].astype(np.float64), team, L, W)
        report['halves'].append(facts)
        moves += [(j, a + s, a + e, t) for j, s, e, t in found]
    report['moved_pieces'] = len(moves)
    if not moves:
        report.update(moved_frames=0, new_columns=0)
        return match, report
    out = players.copy()
    cols, col_team, col_free = [], [], []
    frames = 0
    for j, a, b, t in sorted(moves, key=lambda m: (m[1], m[0])):
        c = next((i for i in range(len(cols)) if col_team[i] == t and col_free[i] <= a), None)
        if c is None:
            cols.append(np.full((len(players), 2), np.nan, players.dtype))
            col_team.append(t)
            col_free.append(0)
            c = len(cols) - 1
        cols[c][a:b] = players[a:b, j]
        out[a:b, j] = np.nan
        col_free[c] = b
        frames += int(np.isfinite(players[a:b, j]).all(1).sum())
    report.update(moved_frames=frames, new_columns=len(cols))
    fixed = dict(match, players=np.concatenate([out, np.stack(cols, 1)], 1), team=np.r_[team, np.array(col_team, team.dtype)])
    return fixed, report
