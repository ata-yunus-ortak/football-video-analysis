"""Smart Tagging (Metrica SportsCode XML) as evidence for possession v3.

Smart Tagging is Metrica's AUTOMATIC annotation of the tactical video (no manual review): phases
of play with the team concerned, and set pieces (restart windows of ~5 s, team = taker, N/A for
throw-ins). Here it becomes per-frame evidence for the second stage, never a label copy.

- read():       SportsCode XML -> tag records on the video-frame timeline (seconds x fps).
- features():   per-frame tag evidence, team-symmetric (swap=True mirrors the teams).
- gate():       run-time consistency check; a tag group whose team disagrees with the tracking-only
                stage-1 model is dropped (threshold fixed a priori in possession-v3-plan.json).
- simulate():   tags generated from EXTERNAL matches' labels and clean positions, corrupted with
                randomised errors -- used only for training/validation, because no external match
                has Metrica Smart Tagging. Nothing here reads or fits the provided match.

Code semantics (assumed from the code names and DATA.md; the gate guards against a mistake):
ATTACK codes carry the team in possession, DEFEND codes the team without the ball.
"""
import re
import xml.etree.ElementTree as ET
import numpy as np
from .features import wmean, since, until, play_blocks, attack_dirs

ATTACK = ('build up', 'progression', 'creating chances', 'attacking transition', 'ball in final third',
          'ball in the box', 'players in the box', 'long ball')
DEFEND = ('defending in attacking third', 'defending in middle third', 'defending in defensive third',
          'defensive transition')
SETPIECE = 'set pieces'
SP_TYPES = ('throw-in', 'corner kick', 'goal kick', 'free kick', 'kick off')
GROUPS = ('attack', 'defend', 'setpiece')
CAP = 30.0
TAU, MIN_FRAMES = 0.60, 625          # gate, fixed in possession-v3-plan.json before any result
# Documented team strings of the provided Smart Tagging (DATA.md): used if fuzzy matching fails.
TEAM_ALIASES = {'BAR-ATH': {'barcelona': 'home', 'fc barcelona': 'home', 'atletic club': 'away',
                            'athletic club': 'away', 'athletic bilbao': 'away'}}


def _code(s):
    return re.sub(r'\s+', ' ', (s or '').strip().lower())


def sp_type(s):
    s = _code(s)
    if 'throw' in s:
        return 'throw-in'
    if 'corner' in s:
        return 'corner kick'
    if 'goal kick' in s:
        return 'goal kick'
    if 'free' in s:
        return 'free kick'
    if 'kick off' in s or 'kick-off' in s or 'kickoff' in s:
        return 'kick off'
    return 'other'


def _team_index(value, names, aliases):
    """0 = home, 1 = away, None = N/A or unknown. names = [home name, away name] of the ATD."""
    v = _code(value)
    if not v or v in ('n/a', 'na', 'none', '-'):
        return None
    from .tags import map_team
    k = map_team(value, names[0], names[1])
    if k is None and aliases:
        side = aliases.get(v)
        k = {'home': 0, 'away': 1}.get(side)
    return k


def read(path, fps, names, game=None):
    """Tag records {code, start, end (exclusive), team, type} from a SportsCode XML file."""
    aliases = TEAM_ALIASES.get(game, {})
    out = []
    for inst in ET.parse(path).iter('instance'):
        try:
            a, b = float(inst.findtext('start')), float(inst.findtext('end'))
        except (TypeError, ValueError):
            continue
        if not (np.isfinite(a) and np.isfinite(b)) or b <= a:
            continue
        labels = {}
        for lab in inst.findall('label'):
            labels[(lab.findtext('group') or '').strip().lower()] = (lab.findtext('text') or '').strip()
        code = _code(inst.findtext('code'))
        out.append({'code': code, 'start': int(round(a * fps)), 'end': int(round(b * fps)),
                    'team': _team_index(labels.get('team', ''), names, aliases),
                    'type': sp_type(labels.get('type', '')) if code == SETPIECE else ''})
    return out


def _evidence(tags, n, use):
    """Coverage arrays. att[:, k]: an attacking code of team k is active; dfd[:, k]: defending code
    of team k; tr[:, k]: a transition implying team k gains the ball; sp_*: set-piece windows."""
    att, dfd, tr = np.zeros((n, 2)), np.zeros((n, 2)), np.zeros((n, 2))
    sp_in, sp_team = np.zeros(n), np.zeros((n, 2))
    sp_type_in = np.zeros((n, len(SP_TYPES)))
    sp_start, sp_end, tr_start = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    sp_last_team = np.full(n, np.nan)
    for t in tags:
        a, b = max(0, int(t['start'])), min(n, int(t['end']))
        if a >= n or b <= 0:
            continue
        b = max(b, a + 1)
        k, c = t.get('team'), t['code']
        if c == SETPIECE:
            sp_in[a:b] = 1
            sp_start[a] = True
            sp_end[b - 1] = True
            if t.get('type') in SP_TYPES:
                sp_type_in[a:b, SP_TYPES.index(t['type'])] = 1
            if k is not None and 'setpiece' in use:
                sp_team[a:b, k] = 1
                sp_last_team[a] = 1.0 if k == 0 else -1.0
            elif np.isnan(sp_last_team[a]):
                sp_last_team[a] = 0.0
        elif k is not None and c in ATTACK and 'attack' in use:
            att[a:b, k] = 1
            if c == 'attacking transition':
                tr[a:b, k] = 1
                tr_start[a] = True
        elif k is not None and c in DEFEND and 'defend' in use:
            dfd[a:b, k] = 1
            if c == 'defensive transition':
                tr[a:b, 1 - k] = 1
                tr_start[a] = True
    return att, dfd, tr, sp_in, sp_team, sp_type_in, sp_start, sp_end, tr_start, sp_last_team


NAMES = ['tg_e', 'tg_e_m2', 'tg_e_m5', 'tg_e_p3', 'tg_e_f3', 'tg_any', 'tg_any_m5', 'tg_chg_since',
         'tg_chg_until', 'tg_tr_e', 'tg_tr_since', 'sp_in', 'sp_since_start', 'sp_until_start',
         'sp_since_end', 'sp_until_end', 'sp_team', 'sp_team_last'] + ['sp_' + s.replace(' ', '_')
                                                                         for s in SP_TYPES]
SIGNED = {'tg_e', 'tg_e_m2', 'tg_e_m5', 'tg_e_p3', 'tg_e_f3', 'tg_tr_e', 'sp_team', 'sp_team_last'}


def features(tags, n, period, fps, swap=False, use=GROUPS):
    """(n, len(NAMES)) float array; NaN outside play blocks. swap=True mirrors the teams."""
    att, dfd, tr, sp_in, sp_team, sp_type_in, sp_start, sp_end, tr_start, sp_last = _evidence(tags, n, set(use))
    e = (att[:, 0] - att[:, 1]) + (dfd[:, 1] - dfd[:, 0])
    tre = tr[:, 0] - tr[:, 1]
    spt = sp_team[:, 0] - sp_team[:, 1]
    anyt = ((att.sum(1) + dfd.sum(1)) > 0).astype(float)
    F = np.full((n, len(NAMES)), np.nan)
    f2, f3, f5, f15 = int(round(2 * fps)), int(round(3 * fps)), int(round(5 * fps)), int(round(15 * fps))
    for a, b in play_blocks(period):
        eb = e[a:b]
        chg = np.r_[False, eb[1:] != eb[:-1]]
        # team of the most recent set-piece start, kept for 15 s
        last = sp_last[a:b].copy()
        idx = np.where(np.isfinite(last), np.arange(b - a), -1)
        idx = np.maximum.accumulate(idx)
        lt = np.where(idx >= 0, last[np.maximum(idx, 0)], 0.0)
        lt[(np.arange(b - a) - idx) > f15] = 0.0
        lt[idx < 0] = 0.0
        cols = [eb, wmean(eb, -f2, f2), wmean(eb, -f5, f5), wmean(eb, -f3, -1), wmean(eb, 1, f3),
                anyt[a:b], wmean(anyt[a:b], -f5, f5), since(chg, fps, CAP), until(chg, fps, CAP),
                tre[a:b], since(tr_start[a:b], fps, CAP), sp_in[a:b], since(sp_start[a:b], fps, CAP),
                until(sp_start[a:b], fps, CAP), since(sp_end[a:b], fps, CAP), until(sp_end[a:b], fps, CAP),
                spt[a:b], lt] + [sp_type_in[a:b, j] for j in range(len(SP_TYPES))]
        F[a:b] = np.column_stack(cols)
    F = np.where(np.isnan(F) & np.isfinite(F[:, :1]), 0.0, F)  # empty windows -> no evidence
    if swap:
        for j, nm in enumerate(NAMES):
            if nm in SIGNED:
                F[:, j] = -F[:, j]
    return F, list(NAMES)


def group_evidence(tags, n):
    """Signed home-possession evidence implied by each group alone (+1 home, -1 away, 0 none)."""
    out = {}
    for g in GROUPS:
        att, dfd, tr, sp_in, sp_team, *_ = _evidence(tags, n, {g})
        if g == 'attack':
            out[g] = att[:, 0] - att[:, 1]
        elif g == 'defend':
            out[g] = dfd[:, 1] - dfd[:, 0]
        else:
            out[g] = sp_team[:, 0] - sp_team[:, 1]
    return out


def gate(tags, p_dead, p_home, period, tau=TAU, min_frames=MIN_FRAMES):
    """Groups whose team agrees with the tracking-only stage 1 where it is confident.

    Returns (groups to use, report). Fixed rule (possession-v3-plan.json): frames inside play
    blocks with p_dead < 0.3 and |p_home - 0.5| > 0.2 and non-zero group evidence; a group needs
    >= min_frames such frames and agreement >= tau.
    """
    n = len(p_home)
    blk = np.zeros(n, bool)
    for a, b in play_blocks(period):
        blk[a:b] = True
    conf = blk & (np.asarray(p_dead) < 0.3) & (np.abs(np.asarray(p_home) - 0.5) > 0.2)
    s1 = np.sign(np.asarray(p_home) - 0.5)
    use, rep = [], {}
    for g, ev in group_evidence(tags, n).items():
        m = conf & (ev != 0)
        k = int(m.sum())
        agree = float(np.mean(np.sign(ev[m]) == s1[m])) if k else None
        ok = k >= min_frames and agree is not None and agree >= tau
        rep[g] = {'frames': k, 'agreement': None if agree is None else round(agree, 4), 'used': bool(ok)}
        if ok:
            use.append(g)
    return tuple(use), rep


# ----------------------------------------------------------------------------- simulation (external only)
# Published counts of the provided file (DATA.md) per graded minute (158,857 frames = 105.9 min).
# Only these public per-code counts calibrate how MANY tags the simulator emits; the provided tags
# themselves are never read for any choice.
_MIN = 158857 / 25.0 / 60.0
RATE = {'build up': 22, 'progression': 66, 'creating chances': 30, 'attacking transition': 24,
        'ball in final third': 93, 'ball in the box': 72, 'players in the box': 97, 'long ball': 29,
        'throw-in': 26, 'corner kick': 12, 'goal kick': 10, 'free kick': 5, 'kick off': 6}
RATE = {k: v / _MIN for k, v in RATE.items()}
MIRROR = {'build up': 'defending in attacking third', 'progression': 'defending in middle third',
          'creating chances': 'defending in defensive third', 'attacking transition': 'defensive transition'}


def sample_params(rng, regime='default'):
    """Tag-error parameters for one corrupted copy (ranges registered in possession-v3-plan.json)."""
    p = {'scale': {c: rng.uniform(0.5, 1.5) for c in RATE}, 'p_merge': rng.uniform(0.0, 0.8),
         'lag': rng.uniform(-1.5, 1.5), 'sigma': rng.uniform(0.3, 3.0), 'team_err': rng.uniform(0.0, 0.15),
         'na_rate': rng.uniform(0.0, 0.05), 'false_rate': rng.uniform(0.0, 0.15),
         'p_mirror': rng.uniform(0.5, 1.0), 'none': rng.random() < 0.1,
         'drop': [g for g in GROUPS if rng.random() < 0.1], 'invert_defend': False}
    if regime == 'none':
        p['none'] = True
    elif regime == 'clean':
        p.update(scale={c: 1.0 for c in RATE}, lag=0.0, sigma=0.3, team_err=0.0, na_rate=0.0,
                 false_rate=0.0, p_mirror=1.0, none=False, drop=[])
    elif regime == 'noisy':
        p.update(scale={c: 0.5 for c in RATE}, lag=1.5, sigma=3.0, team_err=0.15, false_rate=0.15,
                 none=False, drop=[])
    elif regime == 'bad_team':
        p.update(team_err=0.30, none=False, drop=[])
    elif regime == 'inverted_defending':
        p.update(invert_defend=True, none=False, drop=[])
    elif regime != 'default':
        raise ValueError(regime)
    return p


def _runs(mask):
    m = np.r_[False, np.asarray(mask, bool), False]
    d = np.flatnonzero(np.diff(m.astype(np.int8)))
    return list(zip(d[::2], d[1::2]))


def _zone_runs(z, min_len):
    """Runs of a zone sequence; runs shorter than min_len are absorbed by the previous run."""
    edges = np.flatnonzero(np.r_[True, z[1:] != z[:-1]])
    out = []
    for s, e in zip(edges, np.r_[edges[1:], len(z)]):
        r = [int(s), int(e), int(z[s])]
        if out and (r[1] - r[0] < min_len or out[-1][2] == r[2]):
            out[-1][1] = r[1]
        else:
            out.append(r)
    return [tuple(r) for r in out]


def _restart_type(pos, L, W):
    from .tags import _restart_type as rt
    return rt(pos, L, W)


def _candidates(lab, ball, players, team, period, pitch, fps, rng, p_merge):
    """All candidate tags (before count calibration and corruption) of an external match."""
    L, W = float(pitch[0]), float(pitch[1])
    cand = []
    s15, s05 = int(1.5 * fps), int(0.5 * fps)
    for a0, b0 in play_blocks(period):
        seg, bx = lab[a0:b0], ball[a0:b0]
        dirs = attack_dirs(players[a0:b0], team, L)
        n = b0 - a0
        for t in np.flatnonzero((seg[1:] != 'D') & (seg[:-1] == 'D')) + 1:   # restarts
            if seg[t] not in ('H', 'A'):
                continue
            back = bx[max(0, t - 2 * int(fps)):t + 1]
            ok = np.isfinite(back).all(1)
            typ = _restart_type(back[ok][-1] if ok.any() else np.array([np.nan, np.nan]), L, W)
            k = None if typ == 'throw-in' else (0 if seg[t] == 'H' else 1)
            cand.append((typ, SETPIECE, a0 + t - rng.uniform(0.5, 4) * fps, a0 + t + rng.uniform(1, 5) * fps, k, typ))
        edges = np.flatnonzero(np.r_[True, seg[1:] != seg[:-1]])
        spans = list(zip(edges, np.r_[edges[1:], n]))
        for i, (s, e) in enumerate(spans):
            if seg[s] not in ('H', 'A'):
                continue
            k = 0 if seg[s] == 'H' else 1
            d = dirs[k]
            xr = bx[s:e, 0] if d > 0 else L - bx[s:e, 0]
            fin = np.isfinite(xr)
            if i > 0 and seg[spans[i - 1][0]] in ('H', 'A') and seg[spans[i - 1][0]] != seg[s]:
                cand.append(('attacking transition', 'attacking transition', a0 + s,
                             a0 + s + rng.uniform(3, 8) * fps, k, ''))
            if fin.sum() < 2:
                continue
            idx = np.maximum.accumulate(np.where(fin, np.arange(e - s), -1))
            xr = np.where(idx >= 0, xr[np.maximum(idx, 0)], xr[np.argmax(fin)])
            z = np.digitize(xr, [L / 3, 2 * L / 3])
            runs = _zone_runs(z, s15)
            merged = []
            for u, v, zz in runs:
                if merged and rng.random() < p_merge:
                    merged[-1][1] = v
                else:
                    merged.append([u, v, zz])
            for u, v, zz in merged:
                code = ('build up', 'progression', 'creating chances')[zz]
                cand.append((code, code, a0 + s + u, a0 + s + v, k, ''))
            for u, v, zz in runs:
                if zz == 2:
                    cand.append(('ball in final third', 'ball in final third', a0 + s + u, a0 + s + v, k, ''))
            by = bx[s:e, 1]
            box = (xr > L - 16.5) & (np.abs(np.where(np.isfinite(by), by, W / 2) - W / 2) < 20.16)
            for u, v in _runs(box):
                if v - u >= int(0.4 * fps):
                    cand.append(('ball in the box', 'ball in the box', a0 + s + u - s05, a0 + s + v + s05, k, ''))
            pk = players[a0 + s:a0 + e][:, team == k]
            pxr = pk[..., 0] if d > 0 else L - pk[..., 0]
            inbox = ((pxr > L - 16.5) & (np.abs(pk[..., 1] - W / 2) < 20.16)).sum(1) >= 2
            for u, v in _runs(inbox):
                if v - u >= int(fps):
                    cand.append(('players in the box', 'players in the box', a0 + s + u, a0 + s + v, k, ''))
            if e - s > s15:
                bb = bx[s:e]
                dd = np.linalg.norm(bb[s15:] - bb[:-s15], axis=1)
                last = -10 ** 9
                for u in np.flatnonzero(np.isfinite(dd) & (dd > 30.0)):
                    if u - last > 5 * fps:
                        cand.append(('long ball', 'long ball', a0 + s + u, a0 + s + u + 2.5 * fps, k, ''))
                        last = u
    return cand


def simulate(lab, ball, players, team, period, pitch, fps, rng, params):
    """Smart-Tagging-like records from an EXTERNAL match's labels and clean positions.

    Candidate tags come from the labels (restarts, spells split by ball zone along the attack
    direction, box occupancy, long balls, open-play team changes). Each code keeps a random
    subset whose expected size per graded minute equals the published rate of the provided file
    times a random scale; then timing, team, N/A and false-tag errors are applied.
    """
    p = params
    if p.get('none'):
        return []
    lab = np.asarray(lab)
    minutes = sum(b - a for a, b in play_blocks(period)) / fps / 60.0
    cand = _candidates(lab, ball, players, team, period, pitch, fps, rng, p['p_merge'])
    count = {}
    for c in cand:
        count[c[0]] = count.get(c[0], 0) + 1
    tags = []
    for key, code, a, b, k, typ in cand:
        if rng.random() >= min(1.0, RATE[key] * minutes * p['scale'][key] / count[key]):
            continue
        tags.append({'code': code, 'start': a, 'end': b, 'team': k, 'type': typ})
        if code in MIRROR and rng.random() < p['p_mirror']:
            j = rng.normal(0, 0.3, 2) * fps
            tags.append({'code': MIRROR[code], 'start': a + j[0], 'end': b + j[1],
                         'team': k if p['invert_defend'] else 1 - k, 'type': ''})
    out = []
    for t in tags:
        a = t['start'] + (p['lag'] + rng.normal(0, p['sigma'])) * fps
        b = t['end'] + (p['lag'] + rng.normal(0, p['sigma'])) * fps
        b = max(b, a + 0.2 * fps)
        k = t['team']
        if k is not None and t['code'] != SETPIECE and rng.random() < p['team_err']:
            k = 1 - k
        if k is not None and rng.random() < p['na_rate']:
            k = None
        out.append(dict(t, start=int(round(a)), end=int(round(b)), team=k))
    alive = np.flatnonzero(np.isin(lab, ('H', 'A')))
    codes = ATTACK + DEFEND
    for _ in range(rng.poisson(p['false_rate'] * len(out)) if len(alive) else 0):
        f = int(alive[rng.integers(len(alive))])
        if rng.random() < 0.1:
            typ = SP_TYPES[rng.integers(len(SP_TYPES))]
            out.append({'code': SETPIECE, 'start': f, 'end': f + int(rng.uniform(3, 7) * fps),
                        'team': None if typ == 'throw-in' else int(rng.integers(2)), 'type': typ})
        else:
            out.append({'code': codes[rng.integers(len(codes))], 'start': f,
                        'end': f + int(rng.uniform(2, 10) * fps), 'team': int(rng.integers(2)), 'type': ''})
    drop = set(p.get('drop', []))
    keep = []
    for t in out:
        g = 'setpiece' if t['code'] == SETPIECE else ('attack' if t['code'] in ATTACK else 'defend')
        if g in drop:
            if g != 'setpiece':
                continue
            t = dict(t, team=None)
        keep.append(t)
    return keep
