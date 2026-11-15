"""Build a self-contained HTML viewer for one converted PFF game: pitch animation (PFF tracking, 5 fps,
interpolated), our possession-v2.11 labels and the PFF event proxy as timelines, the match clock, and the PFF
events around the current moment. If {game}_analysis.json (analyse_pff.py) exists, the viewer also lists the longest disagreements.
Usage: python3 make_viewer.py 3839  -> viewer_{game}.html"""
import ast
import base64
import json
import os
import sys
from pathlib import Path
import numpy as np

POS_FPS = 5


def rle(lab):
    out, start = [], 0
    for i in range(1, len(lab) + 1):
        if i == len(lab) or lab[i] != lab[start]:
            out.append([int(start), int(i - start), str(lab[start])])
            start = i
    return out


def parse(s):
    if s is None or isinstance(s, (dict, list)):
        return s
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return json.loads(s)


def main(game):
    z = np.load(f'{game}_match.npz')
    lab = np.load(f'{game}_labels.npz')
    summ = json.load(open(f'{game}_summary.json'))
    meta = json.load(open(f'raw/{game}_metadata.json'))[0]
    rpath = f'raw/{game}_rosters.json'          # optional: player names in the viewer
    roster = {(r['team']['name'], int(r['shirtNumber'])): r['player']['nickname'] for r in json.load(open(rpath))} if os.path.exists(rpath) else {}
    step = int(round(z['fps'] / POS_FPS))
    P = z['players'][::step]
    B = z['ball'][::step]
    E = z['ball_estimated'][::step]
    arr = np.concatenate([P, B[:, None], E[:, None]], 1)              # frames x (slots + 2) x 2
    q = np.where(np.isfinite(arr), np.round(arr * 10), -32768).astype('<i2')
    pd_, ph = lab['p_dead'][::step], lab['p_home'][::step]
    probs = np.stack([np.round(np.clip(pd_, 0, 1) * 255), np.round(np.clip(ph, 0, 1) * 255)], 1).astype(np.uint8)
    home, away = meta['homeTeam']['name'], meta['awayTeam']['name']
    names = [roster.get((home if t == 0 else away, int(j)), '') for t, j in zip(z['team'], z['jersey'])]
    TR = {'Spain': 'İspanya', 'Germany': 'Almanya'}
    KIT = {'#cc0000': 'kırmızı', '#ffffff': 'beyaz'}
    events = []
    for e in json.load(open(f'raw/{game}_events.json')):
        g = parse(e['gameEvents']) or {}
        p = parse(e['possessionEvents']) or {}
        typ = g.get('gameEventType')
        if typ in ('OTB', 'OUT', 'FIRSTKICKOFF', 'SECONDKICKOFF'):
            events.append([round(float(e['startTime']), 2), 0 if g.get('homeTeam') else (1 if g.get('homeTeam') is False else -1),
                           typ if typ != 'OTB' else (p.get('possessionEventType') or 'OTB'), g.get('setpieceType') or '',
                           g.get('playerName') or ''])
    events.sort(key=lambda r: r[0])
    data = {'game': game, 'home': TR.get(home, home), 'away': TR.get(away, away), 'date': meta['date'][:10], 'stadium': meta['stadium']['name'],
            'homeKitTr': KIT.get(meta['homeTeamKit']['primaryColor'], ''), 'awayKitTr': KIT.get(meta['awayTeamKit']['primaryColor'], ''),
            'kits': {'home': meta['homeTeamKit'], 'away': meta['awayTeamKit']},
            'start1': meta['startPeriod1'], 'end1': meta['endPeriod1'], 'start2': meta['startPeriod2'], 'end2': meta['endPeriod2'],
            't0': float(z['t_video'][0]), 'fps': float(z['fps']), 'posFps': POS_FPS, 'nPos': int(arr.shape[0]), 'nObj': int(arr.shape[1]),
            'nLab': int(len(lab['ours'])), 'team': z['team'].tolist(), 'jersey': z['jersey'].tolist(), 'names': names,
            'pos': base64.b64encode(q.tobytes()).decode(), 'probs': base64.b64encode(probs.tobytes()).decode(),
            'ours': rle(lab['ours']), 'pff': rle(lab['pff']), 'events': events, 'summary': summ,
            'analysis': json.load(open(f'{game}_analysis.json')) if os.path.exists(f'{game}_analysis.json') else None}
    html = open(Path(__file__).with_name('viewer_template.html'), encoding='utf-8').read().replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False))
    open(f'viewer_{game}.html', 'w', encoding='utf-8').write(html)
    print(f'viewer_{game}.html', round(len(html) / 1e6, 2), 'MB', 'frames', arr.shape)


if __name__ == '__main__':
    main(sys.argv[1])
