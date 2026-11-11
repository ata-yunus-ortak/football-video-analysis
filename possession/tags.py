"""Smart Tagging (SportsCode XML) reader, team mapping and tag-derived per-frame features.

Optional input (v2.1 candidate). External matches have no Metrica Smart Tagging, so training and
validation use tags SIMULATED from the external ground truth with randomised recall, timing and
error rates (simulate_tags); real tags are read only at inference on the provided match.
"""
import re
import xml.etree.ElementTree as ET
import numpy as np

SETPIECE_TYPES = ('throw-in', 'corner kick', 'goal kick', 'free kick', 'kick off')
# Phase codes whose Team is the team IN possession vs the team DEFENDING (OVERVIEW.md definitions)
ATTACK_CODES = {'build up', 'progression', 'creating chances', 'attacking transition', 'long ball',
                'ball in final third', 'ball in the box', 'players in the box'}
DEFEND_CODES = {'defending in attacking third', 'defending in middle third',
                'defending in defensive third', 'defensive transition'}


def _norm(s):
    return re.sub(r'[^a-z]', ' ', (s or '').lower()).split()


def map_team(tag_team, home_name, away_name, threshold=0.75):
    """0 home, 1 away, None if unknown/N/A: best fuzzy token similarity (difflib), ties -> None."""
    from difflib import SequenceMatcher
    stop = {'fc', 'cf', 'club', 'de', 'sad', 'cd', 'ud', 'n', 'a'}
    t = [w for w in _norm(tag_team) if w not in stop and len(w) >= 4]
    if not t:
        return None
    def score(name):
        ws = [w for w in _norm(name) if w not in stop and len(w) >= 4]
        return max((SequenceMatcher(None, a, b).ratio() for a in t for b in ws), default=0.0)
    sh, sa = score(home_name), score(away_name)
    if max(sh, sa) < threshold or abs(sh - sa) < 1e-9:
        return None
    return 0 if sh > sa else 1


def read_smart_tagging(path, fps, home_name, away_name):
    out = []
    for inst in ET.parse(path).iter('instance'):
        tags = {}
        for lab in inst.findall('label'):
            tags[(lab.findtext('group') or '').strip()] = (lab.findtext('text') or '').strip()
        code = (inst.findtext('code') or '').strip().lower()
        start, end = float(inst.findtext('start')), float(inst.findtext('end'))
        out.append({'code': code, 'start': int(round(start * fps)), 'end': int(round(end * fps)),
                    'team': map_team(tags.get('Team', ''), home_name, away_name),
                    'type': (tags.get('Type') or '').strip().lower()})
    return out


def tag_features(tags, n, period_blocks, fps, cap=30.0):
    """Per-frame set-piece and phase evidence. Returns (common dict, [persp home, persp away])."""
    sp = [t for t in tags if t['code'] == 'set pieces']
    ph = [t for t in tags if t['code'] in ATTACK_CODES or t['code'] in DEFEND_CODES]
    inside = np.zeros(n, bool)
    starts = np.zeros(n, bool)
    ends = np.zeros(n, bool)
    sp_team = np.zeros((n, 2))
    for t in sp:
        a, b = max(0, t['start']), min(n, max(t['end'], t['start'] + 1))
        if a >= n:
            continue
        inside[a:b] = True
        starts[a] = True
        ends[min(n - 1, b - 1)] = True
        if t['team'] is not None:
            sp_team[a:b, t['team']] = 1
    poss = np.zeros((n, 2))
    for t in ph:
        a, b = max(0, t['start']), min(n, t['end'])
        if a >= b or t['team'] is None:
            continue
        k = t['team'] if t['code'] in ATTACK_CODES else 1 - t['team']
        poss[a:b, k] += 1
    from .features import since, until, wmean
    C = {'sp_inside': inside.astype(float), 'sp_t_since_start': since(starts, fps, cap),
         'sp_t_until_start': until(starts, fps, cap), 'sp_t_since_end': since(ends, fps, cap),
         'sp_t_until_end': until(ends, fps, cap)}
    P = []
    for k in (0, 1):
        P.append({'sp_team': sp_team[:, k] - sp_team[:, 1 - k],
                  'phase_now': poss[:, k] - poss[:, 1 - k],
                  'phase_c5': wmean(poss[:, k] - poss[:, 1 - k], -int(5 * fps), int(5 * fps))})
    return C, P


def _restart_type(pos, L, W):
    if not np.isfinite(pos).all():
        return 'free kick'
    x, y = pos
    dt, dg = min(y, W - y), min(x, L - x)
    if np.hypot(x - L / 2, y - W / 2) < 3:
        return 'kick off'
    if dt < 3 and dg < 3:
        return 'corner kick'
    if dg < 6 and abs(y - W / 2) < 10:
        return 'goal kick'
    if dt < 2:
        return 'throw-in'
    return 'free kick'


def simulate_tags(labels, ball, period, pitch, fps, rng, p=None):
    """Simulated Smart Tagging from EXTERNAL ground truth (development only).

    Set pieces: each D->alive restart is tagged with a type-dependent recall, as a window of
    3-7 s containing the restart; team = restarting team, N/A for throw-ins. False windows are
    added at random live frames. Phases: parts of possession spells longer than 4 s are covered
    with a team tag (attack semantics) with random team errors.
    """
    from .features import play_blocks
    p = p or {}
    rec = p.get('recall', {k: rng.uniform(0.2, 1.0) for k in SETPIECE_TYPES})
    fp_rate = p.get('fp_per_restart', rng.uniform(0.0, 0.3))
    phase_cov = p.get('phase_coverage', rng.uniform(0.3, 0.9))
    phase_err = p.get('phase_team_error', rng.uniform(0.0, 0.2))
    L, W = pitch
    tags = []
    lab = np.asarray(labels)
    for a, b in play_blocks(period):
        seg = lab[a:b]
        for t in np.flatnonzero((seg[1:] != 'D') & (seg[:-1] == 'D')) + 1:
            f = a + int(t)
            back = ball[max(a, f - 2 * int(fps)):f + 1]
            ok = np.isfinite(back).all(1)
            pos = back[ok][-1] if ok.any() else np.array([np.nan, np.nan])
            kind = _restart_type(pos, L, W)
            if rng.random() > rec[kind]:
                continue
            length = rng.uniform(3, 7) * fps
            start = int(f - rng.uniform(0.2, 0.8) * length)
            team = None if kind == 'throw-in' else {'H': 0, 'A': 1}.get(lab[min(f, len(lab) - 1)])
            tags.append({'code': 'set pieces', 'start': start, 'end': int(start + length),
                         'team': team, 'type': kind})
        alive = np.flatnonzero(np.isin(seg, ('H', 'A')))
        n_rest = int(np.sum((seg[1:] != 'D') & (seg[:-1] == 'D')))
        for _ in range(rng.poisson(fp_rate * max(n_rest, 1))):
            if len(alive):
                f = a + int(alive[rng.integers(len(alive))])
                tags.append({'code': 'set pieces', 'start': f, 'end': f + int(5 * fps), 'team': None,
                             'type': SETPIECE_TYPES[rng.integers(len(SETPIECE_TYPES))]})
        edges = np.flatnonzero(np.r_[True, seg[1:] != seg[:-1]])
        for s, e in zip(edges, np.r_[edges[1:], len(seg)]):
            if seg[s] not in ('H', 'A') or (e - s) < 4 * fps or rng.random() > phase_cov:
                continue
            st = a + s + int(rng.uniform(0, 3) * fps)
            en = min(a + e + int(rng.uniform(-3, 3) * fps), st + int(rng.uniform(3, 15) * fps))
            team = {'H': 0, 'A': 1}[seg[s]]
            if rng.random() < phase_err:
                team = 1 - team
            tags.append({'code': 'build up', 'start': st, 'end': max(en, st + 1), 'team': team, 'type': ''})
    return tags
