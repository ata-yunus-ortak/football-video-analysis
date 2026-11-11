"""Write tracking arrays as a Metrica FIFA/EPTS pair laid out like the provided ATD (external and synthetic data only).

Corrupted copies of external matches are written as files so that the frozen release entry point
(possession.run29) can be run on them exactly as on the provided bundle: the final test on the reserved
external match (tools/possession_final_test.py) and rehearsals use this. The release itself never imports
this module.

DATA.md describes the provided ATD as anonymous track slots ("Track 1" .. "Track 46") that "appear, vanish and
swap identity as the tracker loses and re-acquires people", one record per video frame numbered from 1, every
group "x,y,speed" normalised to 0-1, NaN for a missing observation. pack() turns per-player columns into such
slots; write_epts() writes the pair with a DataFormatSpecification in the structure of Metrica's public sample
game 3 export.
"""
from pathlib import Path
import numpy as np


def tracklets(players, team):
    """[(start, end, team, key, xy)] for every run of finite positions of every column (key = column index)."""
    fin = np.isfinite(players).all(2)
    out = []
    for j in range(players.shape[1]):
        d = np.diff(np.r_[0, fin[:, j].astype(np.int8), 0])
        for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            out.append((int(a), int(b), int(team[j]), j, players[a:b, j]))
    return out


def pack(n, items, slot_team, gap=25):
    """Tracklets into anonymous slots of their team. A track that reappears within `gap` frames returns to its
    slot if that is still free; otherwise it takes the slot of its team that has been free the longest.
    Returns ((n, slots, 2) array, largest number of simultaneous tracks per team)."""
    slot_team = np.asarray(slot_team)
    out = np.full((n, len(slot_team), 2), np.nan, np.float32)
    free_at = np.zeros(len(slot_team), np.int64)
    last = {}
    slots_of = [np.flatnonzero(slot_team == k) for k in (0, 1)]
    peak = [0, 0]
    for a, b, t, key, xy in sorted(items, key=lambda r: (r[0], str(r[3]))):
        sl = slots_of[t]
        free = sl[free_at[sl] <= a]
        if not len(free):
            raise ValueError('more simultaneous tracks than slots')
        peak[t] = max(peak[t], len(sl) - len(free) + 1)
        slot = None
        if key in last and a - last[key][1] <= gap and free_at[last[key][0]] <= a:
            slot = last[key][0]
        if slot is None:
            slot = free[np.argmin(free_at[free])]
        out[a:b, slot] = xy
        free_at[slot] = b
        last[key] = (slot, b)
    return out, peak


def _speed(p, fps):
    v = np.zeros(p.shape[:-1], np.float32)
    v[1:-1] = np.nan_to_num(np.linalg.norm(p[2:] - p[:-2], axis=-1) * fps / 2)
    return v


def write_epts(folder, stem, players, ball, slot_team, pitch=(105.0, 68.0), names=('Home', 'Away'), fps=25.0):
    """<folder>/<stem>_atd.xml and <stem>_atd.txt; players (n, slots, 2) and ball (n, 2) in metres, NaN = missing.
    The first Team of the metadata is the home side (team 0)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    players, ball = np.asarray(players, np.float32), np.asarray(ball, np.float32)
    n, slots, _ = players.shape
    scale = np.asarray(pitch, np.float32)
    X, Bn = players / scale, ball / scale
    sp, bs = _speed(players, fps), _speed(ball, fps)
    seen, bseen = np.isfinite(X).all(2), np.isfinite(Bn).all(1)
    with open(folder / f'{stem}_atd.txt', 'w', encoding='ascii', newline='\n') as fh:
        for a in range(0, n, 4000):
            xs, ss, oks = X[a:a + 4000].tolist(), sp[a:a + 4000].tolist(), seen[a:a + 4000].tolist()
            bn, bsp, bok = Bn[a:a + 4000].tolist(), bs[a:a + 4000].tolist(), bseen[a:a + 4000].tolist()
            lines = []
            for i, (xi, si, ok) in enumerate(zip(xs, ss, oks)):
                groups = [f'{xy[0]:.5f},{xy[1]:.5f},{v:.3f}' if o else 'NaN,NaN,NaN' for xy, v, o in zip(xi, si, ok)]
                b = f'{bn[i][0]:.5f},{bn[i][1]:.5f},{bsp[i]:.3f}' if bok[i] else 'NaN,NaN,NaN'
                lines.append(f'{a + i + 1}:' + ';'.join(groups) + ':' + b + '\n')
            fh.write(''.join(lines))
    ids = [str(k + 1) for k in range(slots)]
    roster = ''.join(f'<Player id="{ids[j]}" teamId="{"TA" if slot_team[j] == 0 else "TB"}"><Name>Track {j + 1}</Name>'
                     f'<ShirtNumber>{j + 1}</ShirtNumber></Player>' for j in range(slots))
    channels = ''.join(f'<PlayerChannel channelId="{c}" id="player{ids[j]}_{c}" playerId="{ids[j]}"/>' for j in range(slots) for c in 'xys')
    refs = ''.join('<SplitRegister separator=",">' + ''.join(f'<PlayerChannelRef playerChannelId="player{ids[j]}_{c}"/>' for c in 'xys')
                   + '</SplitRegister>' for j in range(slots))
    (folder / f'{stem}_atd.xml').write_text(
        '<?xml version="1.0" encoding="utf-8"?><main><Metadata><GlobalConfig><ProviderName>Metrica Sports</ProviderName>'
        f'<FrameRate>{fps:g}</FrameRate><ProviderGlobalParameters>'
        + ''.join(f'<ProviderParameter><Name>{k}</Name><Value>{v}</Value></ProviderParameter>' for k, v in
                  (('first_half_start', 1), ('first_half_end', n // 2), ('second_half_start', n // 2 + 1), ('second_half_end', n)))
        + '</ProviderGlobalParameters></GlobalConfig><Sessions><Session id="session1"><SessionType>Match</SessionType>'
        f'<FieldSize><Width>{float(pitch[0]):g}</Width><Height>{float(pitch[1]):g}</Height></FieldSize></Session></Sessions>'
        f'<Teams><Team id="TA"><Name>{names[0]}</Name></Team><Team id="TB"><Name>{names[1]}</Name></Team></Teams>'
        f'<Players>{roster}</Players><Devices><Device id="device1"><Name>Device 1</Name><Sensors>'
        '<Sensor id="position"><Name>Position</Name><Channels><Channel id="x"><Name>position_x</Name><Unit>normalized</Unit></Channel>'
        '<Channel id="y"><Name>position_y</Name><Unit>normalized</Unit></Channel></Channels></Sensor>'
        '<Sensor id="speed"><Name>Speed</Name><Channels><Channel id="s"><Name>speed</Name><Unit>m/s</Unit></Channel></Channels></Sensor>'
        f'</Sensors></Device></Devices><PlayerChannels>{channels}</PlayerChannels></Metadata>'
        f'<DataFormatSpecifications><DataFormatSpecification endFrame="{n}" separator=":" startFrame="1">'
        f'<StringRegister name="frameCount"/><SplitRegister separator=";">{refs}</SplitRegister>'
        '<SplitRegister separator=","><BallChannelRef channelId="x"/><BallChannelRef channelId="y"/><BallChannelRef channelId="s"/>'
        '</SplitRegister></DataFormatSpecification></DataFormatSpecifications></main>', encoding='utf-8')


def write_homography(path, valid):
    """Homography CSV in the documented column layout; only the valid flag is meaningful (the matrix is a constant)."""
    with open(path, 'w', encoding='ascii', newline='\n') as fh:
        fh.write('frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid\n')
        for i, v in enumerate(np.asarray(valid, bool).tolist()):
            fh.write(f'{i},1822.663,-511.2005,44.48168,1.698323,169.2971,255.7303,-0.01907188,-0.5269586,1,0.2910854,1\n' if v
                     else f'{i},NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,0\n')


def write_packed(folder, stem, players, ball, team, slots, pitch, names=('Home', 'Away'), fps=25.0):
    """Pack per-player columns into `slots` anonymous slots (half per team, the larger half for team 0) and write the pair.
    Returns the largest number of simultaneous tracks per team."""
    slot_team = np.r_[np.zeros(slots - slots // 2, np.int8), np.ones(slots // 2, np.int8)]
    packed, peak = pack(len(ball), tracklets(players, team), slot_team)
    write_epts(folder, stem, packed, ball, slot_team, pitch, names, fps)
    return peak
