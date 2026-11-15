"""Run the frozen possession-v2.11 decision on one converted PFF game and build an event-derived reference.

Our system: the v2.11 release logic without a second camera (noise gate -> goalkeeper team check -> v2.1 or v2.3
path models of models/possession-v2.npz / possession-v23.npz -> decoder), exactly as possession/run211.py does when no
broadcast files exist. Nothing is fitted or tuned here.
Reference (a proxy, not ground truth): PFF's own events. After an on-the-ball event (reception, pass, challenge...)
the ball belongs to that player's team until the next event; after an OUT event (ball out of play or goal) it is
dead until the restart; before a free kick or drop ball not preceded by OUT, the time from 0.5 s after the last
event to the restart is dead. Outside the halves: dead.
Usage: python3 run_pff.py 3839    (writes {game}_labels.npz and {game}_summary.json)
"""
import ast
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # repository root
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.noise import estimate_noise, choose_path
from possession.keeper2 import correct_goalkeepers
from possession.run24 import V21_MODEL, V23_MODEL
from possession.evaluate import score

RESTARTS = {'T', 'C', 'G', 'F', 'K', 'D', 'P'}


def parse(s):
    if s is None or isinstance(s, (dict, list)):
        return s
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return json.loads(s)


def reference(game, t_video, period):
    ev = json.load(open(f'raw/{game}_events.json'))
    rows = []
    for e in ev:
        g = parse(e['gameEvents']) or {}
        typ = g.get('gameEventType')
        if typ not in ('OTB', 'OUT', 'FIRSTKICKOFF', 'SECONDKICKOFF', 'END'):
            continue
        s = float(e['startTime'])
        en = float(e['endTime']) if e['endTime'] is not None else s
        rows.append((s, en, typ, g.get('setpieceType'), g.get('homeTeam')))
    rows.sort(key=lambda r: (r[0], r[2] != 'OUT'))
    lab = np.full(len(t_video), 'D', dtype='<U1')
    times = np.array([r[0] for r in rows])
    state = []
    for s, en, typ, sp, home in rows:
        if typ in ('OUT', 'END'):
            state.append('D')
        else:
            state.append('H' if home else 'A')
    idx = np.searchsorted(times, t_video, side='right') - 1
    ok = idx >= 0
    st = np.array(state)
    lab[ok] = st[idx[ok]]
    # dead time before free kicks / drop balls that do not follow an OUT event
    for k in range(1, len(rows)):
        s, en, typ, sp, home = rows[k]
        if typ == 'OTB' and sp in RESTARTS and rows[k - 1][2] not in ('OUT', 'END'):
            prev_end = max(rows[k - 1][1], rows[k - 1][0])
            m = (t_video >= prev_end + 0.5) & (t_video < s)
            lab[m] = 'D'
    lab[period == 0] = 'D'
    return lab


def main(game):
    z = np.load(f'{game}_match.npz')
    match = {'fps': float(z['fps']), 'pitch': z['pitch'].astype(float), 'ball': z['ball'], 'players': z['players'],
             'team': z['team'].astype(np.int8), 'period': z['period'].astype(np.int8)}
    b21, b23 = load_bundle(V21_MODEL), load_bundle(V23_MODEL)
    noise = estimate_noise(match)
    path, trigger = choose_path(noise)
    model_input, keeper = correct_goalkeepers(match)
    if path == 'v2.3':
        labels, pd_, ph = predict_labels(smooth_positions(model_input, int(b23['card']['smooth_half'])), b23)
    else:
        labels, pd_, ph = predict_labels(model_input, b21)
    ref = reference(game, z['t_video'], z['period'])
    s = score(ref, labels, z['period'])
    play = z['period'] > 0
    out = {'game': game, 'path': path, 'noise_m': {k: (round(float(v), 3) if isinstance(v, float) else v) for k, v in noise.items()},
           'trigger': trigger, 'goalkeeper_moved_pieces': keeper.get('moved_pieces'),
           'bundle': (b23 if path == 'v2.3' else b21)['card'].get('version'),
           'agreement_with_pff_event_proxy': {'spell_f1': round(float(s['spell_f1_mean']), 4), 'macro_f1': round(float(s['macro_f1']), 4),
                                              'frame_agreement_in_play': round(float(np.mean(labels[play] == ref[play])), 4)},
           'label_shares_in_play': {'ours': {k: round(float(np.mean(labels[play] == k)), 3) for k in 'HAD'},
                                    'pff_proxy': {k: round(float(np.mean(ref[play] == k)), 3) for k in 'HAD'}},
           'note': 'agreement with an event-derived proxy built by us from PFF events; not ground truth and not a competition score'}
    np.savez_compressed(f'{game}_labels.npz', ours=labels, pff=ref, p_dead=pd_, p_home=ph)
    json.dump(out, open(f'{game}_summary.json', 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
