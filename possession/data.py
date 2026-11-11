"""Common match representation and readers.

A match is a dict:
  fps (float), pitch (2,) metres, ball (n,2) metres NaN=missing, players (n,S,2) metres,
  team (S,) 0=home 1=away, period (n,) 1/2 for play halves, 0 outside, labels (n,) optional.
Coordinates are metres with origin at a pitch corner (x along length, y along width).
Readers never use event or ground-truth fields as inputs; labels are returned separately.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np


def _empty(n, s):
    return np.full((n, 2), np.nan, np.float32), np.full((n, s, 2), np.nan, np.float32)


def _parse_raw_slow(text, s, xy=(0, 1), bxy=(0, 1)):
    lines = [l for l in text.splitlines() if l.strip()]
    n = len(lines)
    ball, players = _empty(n, s)
    ids = np.zeros(n, np.int64)
    for i, line in enumerate(lines):
        a, b, c = line.strip().split(':')
        ids[i] = int(a)
        groups = b.split(';')
        if len(groups) != s:
            raise ValueError('slot count differs from metadata')
        for j, g in enumerate(groups):
            f = g.split(',')
            players[i, j] = (float(f[xy[0]]), float(f[xy[1]]))
        f = c.split(',')
        ball[i] = (float(f[bxy[0]]), float(f[bxy[1]]))
    return ids, players, ball


def _parse_raw(text, s, xy=(0, 1), bxy=(0, 1)):
    """Fast exact parser (pandas C engine) with a strict layout check; falls back to the slow path."""
    first = text.split('\n', 1)[0].strip()
    a, b, c = first.split(':')
    groups = b.split(';')
    k = len(groups[0].split(','))
    kb = len(c.split(','))
    if len(groups) != s or any(len(g.split(',')) != k for g in groups):
        return _parse_raw_slow(text, s, xy, bxy)
    try:
        import io
        import pandas as pd
        flat = text.replace(':', ',').replace(';', ',')
        arr = pd.read_csv(io.StringIO(flat), header=None, dtype=np.float64, na_values=['NaN', 'nan'],
                          engine='c').to_numpy()
    except Exception:
        return _parse_raw_slow(text, s, xy, bxy)
    if arr.shape[1] != 1 + s * k + kb:
        return _parse_raw_slow(text, s, xy, bxy)
    ids = arr[:, 0].astype(np.int64)
    pl = arr[:, 1:1 + s * k].reshape(len(arr), s, k)[:, :, list(xy)].astype(np.float32)
    bl = arr[:, 1 + s * k:1 + s * k + kb][:, list(bxy)].astype(np.float32)
    return ids, pl, bl


def _epts_layout(root, roster):
    """FIFA/EPTS DataFormatSpecification -> [(start, end, slot of each group, (ix, iy), (bx, by))].

    Each specification lists, for a frame range, which player every ';' group of a raw line
    belongs to (PlayerChannelRef -> PlayerChannel -> playerId). Returns None when the metadata
    has no usable specification; the reader then assumes groups follow the Player list order.
    """
    pc = {c.get('id'): (c.get('playerId'), c.get('channelId')) for c in root.iter('PlayerChannel')}
    slot_of = {pl.get('id'): i for i, pl in enumerate(roster)}
    out = []
    for spec in root.iter('DataFormatSpecification'):
        regs = [r for r in spec if r.tag == 'SplitRegister']
        if not regs or spec.get('startFrame') is None or spec.get('endFrame') is None:
            return None
        slots, xy = [], None
        for g in regs[0]:
            refs = [pc.get(r.get('playerChannelId')) for r in g.iter('PlayerChannelRef')]
            if not refs or None in refs or len({r[0] for r in refs}) != 1 or refs[0][0] not in slot_of:
                return None
            ch = [r[1] for r in refs]
            if 'x' not in ch or 'y' not in ch or (xy is not None and (ch.index('x'), ch.index('y')) != xy):
                return None
            xy = (ch.index('x'), ch.index('y'))
            slots.append(slot_of[refs[0][0]])
        bch = [r.get('channelId') for r in regs[1].iter('BallChannelRef')] if len(regs) > 1 else []
        bxy = (bch.index('x'), bch.index('y')) if 'x' in bch and 'y' in bch else (0, 1)
        out.append((int(spec.get('startFrame')), int(spec.get('endFrame')), slots, xy or (0, 1), bxy))
    return out or None


def read_epts(meta_path, raw_path, pitch=None):
    """Metrica FIFA/EPTS export (competition ATD or Metrica sample game 3).

    Raw line: frame:group;group;...:ball where each group is x,y[,speed] normalised 0-1 and the
    metadata's DataFormatSpecification says which player each group is. Returns (match, info).
    Frames are indexed from 0 (= frame_id - 1).
    """
    root = ET.parse(meta_path).getroot()
    team_el = list(root.iter('Team'))
    teams = [t.get('id') for t in team_el]
    if len(teams) != 2 or len(set(teams)) != 2:
        raise ValueError('EPTS metadata must list two teams')
    # FIFA/EPTS convention (also the organiser baseline and kloppy): first Team = home.
    names = [(t.findtext('Name') or '').strip() for t in team_el]
    roster = list(root.iter('Player'))
    # Slots of any other team id (e.g. officials) are not players of either side: dropped.
    slot_team = np.array([teams.index(p.get('teamId')) if p.get('teamId') in teams else -1
                          for p in roster], np.int8)
    fs = root.find('.//FieldSize')
    meta_pitch = np.array([float(fs.findtext('Width')), float(fs.findtext('Height'))])
    pitch = np.asarray(meta_pitch if pitch is None else pitch, float)
    fps = float(root.findtext('.//FrameRate'))
    text = Path(raw_path).read_text(encoding='utf-8-sig')
    layout = _epts_layout(root, roster)
    P = len(roster)
    if layout is None:
        ids, players, ball = _parse_raw(text, P)
        layout_kind = 'player order (no usable DataFormatSpecification)'
    else:
        layout_kind = 'DataFormatSpecification' + (
            ' (same as player order)' if all(sl == list(range(P)) for _, _, sl, _, _ in layout) else '')
        if len(layout) == 1:
            chunks = [(None, text, layout[0])]
        else:
            lines = [l for l in text.splitlines() if l.strip()]
            fid = np.array([int(l[:l.index(':')]) for l in lines], np.int64)
            chunks = []
            for spec in layout:
                sel = np.flatnonzero((fid >= spec[0]) & (fid <= spec[1]))
                if len(sel):
                    chunks.append((sel, '\n'.join(lines[i] for i in sel) + '\n', spec))
            del lines
        n = len(fid) if len(layout) > 1 else None
        parts = []
        for sel, chunk, (a, b, slots, xy, bxy) in chunks:
            cid, pl, bl = _parse_raw(chunk, len(slots), xy, bxy)
            if cid.min() < a or cid.max() > b:
                raise ValueError('frame outside its EPTS data format specification')
            parts.append((sel, cid, np.asarray(slots), pl, bl))
        if n is None:
            n = len(parts[0][1])
            parts = [(np.arange(n),) + q[1:] for q in parts]
        covered = np.zeros(n, bool)
        ids = np.zeros(n, np.int64)
        players = np.full((n, P, 2), np.nan, np.float32)
        ball = np.full((n, 2), np.nan, np.float32)
        for sel, cid, slots, pl, bl in parts:
            players[sel[:, None], slots[None, :]] = pl
            ball[sel] = bl
            ids[sel] = cid
            covered[sel] = True
        if not covered.all():
            raise ValueError('frames outside every EPTS data format specification')
    n = len(ids)
    if not np.array_equal(ids, np.arange(ids[0], ids[0] + n)):
        raise ValueError('EPTS frame ids must be consecutive')
    keep = slot_team >= 0
    if not keep.any():
        raise ValueError('no track slot belongs to either team')
    players = np.ascontiguousarray(players[:, keep])
    team = slot_team[keep]
    scale = pitch.astype(np.float32)
    ball *= scale
    players *= scale
    match = {'fps': fps, 'pitch': pitch, 'ball': ball, 'players': players, 'team': team,
             'period': np.ones(n, np.int8), 'first_frame_id': int(ids[0])}
    params = {}
    for p in root.iter('ProviderParameter'):
        params[p.findtext('Name')] = p.findtext('Value')
    return match, {'teams': teams, 'team_names': names, 'meta_pitch': meta_pitch.tolist(),
                   'slots': int(P), 'slots_without_team': int((~keep).sum()), 'layout': layout_kind,
                   'format_specifications': 0 if layout is None else len(layout),
                   'provider_parameters': params}


def read_dfl_prepared(directory):
    """Sportec/DFL open data prepared by tools/sportec_prepare.py (inputs.npz + targets.npz)."""
    d = Path(directory)
    x = np.load(d / 'inputs.npz')
    labels = np.load(d / 'targets.npz')['labels'] if (d / 'targets.npz').exists() else None
    ball = x['ball'].astype(np.float32)
    players = x['players'].astype(np.float32)
    ball[~x['ball_observed']] = np.nan
    players[~x['player_detected']] = np.nan
    match = {'fps': float(x['fps']), 'pitch': x['pitch'].astype(float), 'ball': ball,
             'players': players, 'team': x['teams'].astype(np.int8),
             'period': x['period'].astype(np.int8)}
    return match, labels


def read_metrica_csv(home_csv, away_csv):
    """Metrica sample games 1-2 (CSV). Coordinates normalised, origin top-left, 105x68 m."""
    import pandas as pd
    h = pd.read_csv(home_csv, skiprows=2)
    a = pd.read_csv(away_csv, skiprows=2)
    if len(h) != len(a):
        raise ValueError('home/away tracking length differ')
    def xy(df):
        cols = list(df.columns)
        out = []
        for k, c in enumerate(cols):
            if c.startswith('Player') and k + 1 < len(cols) and cols[k + 1].startswith('Unnamed'):
                out.append(df.iloc[:, [k, k + 1]].to_numpy(float))
        return np.stack(out, 1)
    ph, pa = xy(h), xy(a)
    bcol = list(h.columns).index('Ball')
    ball = h.iloc[:, [bcol, bcol + 1]].to_numpy(float)
    pitch = np.array([105.0, 68.0])
    players = np.concatenate([ph, pa], 1) * pitch
    team = np.r_[np.zeros(ph.shape[1]), np.ones(pa.shape[1])].astype(np.int8)
    period = h['Period'].to_numpy().astype(np.int8)
    return {'fps': 25.0, 'pitch': pitch, 'ball': (ball * pitch).astype(np.float32),
            'players': players.astype(np.float32), 'team': team, 'period': period}


def slice_match(m, a, b):
    out = dict(m)
    for k in ('ball', 'players', 'period', 'labels'):
        if k in m and m[k] is not None:
            out[k] = m[k][a:b]
    return out
