"""Event-derived H/A/D frame labels for Metrica sample games (external, public).

Possession semantics follow Metrica's event definitions: a team holds possession from its
recovery/set piece/first on-ball action until an opponent RECOVERY (significant interference)
or the ball goes dead. Dead-ball intervals: BALL OUT end / goal / foul / forced stop until the
next SET PIECE start. Frames whose state cannot be derived are X (unscored).
"""
import numpy as np, pandas as pd

POSS = {'SET PIECE','RECOVERY','PASS','SHOT','BALL LOST','BALL OUT','FAULT RECEIVED','CARRY'}

def labels_from_events(ev, n_frames):
    # kind='stable' since 11 Nov 2026 (log entry K005): a set piece and the pass that takes it share a start frame, and the
    # dead-ball interval before them is found only if the set piece stays first, as in the file. With the default sort the
    # order of such ties depends on the pandas / numpy build: under Python 3.13 / pandas 3.0.5 / numpy 2.5.3, where every
    # validation and reserved test ran, it is the file order and the labels are unchanged by this argument; under
    # Python 3.10 / pandas 2.1.4 / numpy 1.26.4 about half of the dead-ball intervals were lost.
    ev = ev.sort_values(['Start Frame'], kind='stable').reset_index(drop=True)
    lab = np.full(n_frames + 1, 'X', dtype='<U1')   # index = Metrica frame (1-based)
    team_of = {'Home': 'H', 'Away': 'A'}
    # 1) dead intervals
    dead = []
    rows = ev.to_dict('records')
    def next_restart(i):
        for j in range(i + 1, len(rows)):
            if rows[j]['Type'] == 'SET PIECE':
                return j
            if rows[j]['Type'] in ('PASS', 'RECOVERY', 'SHOT') and rows[j]['Type'] != 'SET PIECE':
                # play resumed without a recorded set piece (e.g., drop ball) -> stop search
                return j
        return None
    for i, r in enumerate(rows):
        t, st = r['Type'], str(r['Subtype'])
        start = None
        if t == 'BALL OUT':
            start = int(r['End Frame']) if r['End Frame'] > 0 else int(r['Start Frame'])
        elif t == 'SHOT' and 'GOAL' in st:
            start = int(r['End Frame']) if r['End Frame'] > 0 else int(r['Start Frame'])
        elif t == 'FAULT RECEIVED':
            start = int(r['Start Frame'])
        elif t == 'BALL LOST' and ('FORCED' in st or 'OFFSIDE' in st or 'END HALF' in st):
            start = int(r['End Frame']) if r['End Frame'] > 0 else int(r['Start Frame'])
        elif t == 'CHALLENGE' and 'FAULT' in st and 'ADVANTAGE' not in st:
            start = int(r['Start Frame'])
        if start is None:
            continue
        j = next_restart(i)
        if j is None:
            continue
        end = int(rows[j]['Start Frame'])
        if rows[j]['Type'] == 'SET PIECE' and end > start and rows[j]['Period'] == r['Period']:
            dead.append((start, end))
    # 2) possession owner at each event start, persisting until changed
    owner = np.full(n_frames + 1, '', dtype='<U1')
    last = ''
    marks = []
    for r in rows:
        if r['Type'] in POSS and r['Team'] in team_of:
            marks.append((int(r['Start Frame']), team_of[r['Team']], int(r['Period'])))
    marks.sort()
    for k, (f, tm, p) in enumerate(marks):
        g = marks[k + 1][0] if k + 1 < len(marks) else n_frames + 1
        owner[f:g] = tm
    lab[owner != ''] = owner[owner != '']
    for a, b in dead:
        lab[a:b] = 'D'
    # before first event of each period and after last: X
    return lab[1:], dead


def game3_events_df(path):
    import json
    d = json.load(open(path))
    home = None
    rows = []
    for e in d['data']:
        team = e['team']['id'] if e.get('team') else None
        st = e.get('subtypes')
        if isinstance(st, list):
            st = '-'.join(s['name'] for s in st if s)
        elif isinstance(st, dict):
            st = st['name']
        rows.append({'TeamId': team, 'Type': e['type']['name'], 'Subtype': st, 'Period': e['period'],
                     'Start Frame': e['start']['frame'], 'End Frame': e['end']['frame'] if e.get('end') else e['start']['frame']})
    df = pd.DataFrame(rows)
    df['Team'] = df['TeamId'].map({'FIFATMA': 'Home', 'FIFATMB': 'Away'})
    return df
