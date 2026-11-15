"""PFF FC World Cup 2022 broadcast tracking (one game) -> our match format at 25 fps.

Input: raw/{game}.jsonl.bz2 (29.97 fps, coordinates in metres from the pitch centre) and raw/{game}_metadata.json.
Output: {game}_match.npz with ball (n,2), ball_estimated (n,2: PFF's estimate where the ball is not visible; for the
viewer only), players (n,P,2), team (P,), jersey (P,), period (n,), t_video (n,), fps=25, pitch=(105, 68).
Coordinates are shifted to the corner origin our features use (x in [0,105], y in [0,68]).
Players: PFF's smoothed positions, visible or estimated off screen, one slot per (team, shirt number).
Ball: PFF's smoothed ball only where PFF marks it VISIBLE; otherwise NaN (our models were trained with ball gaps,
not with filled-in balls). Resampled to a 25 fps grid of video time by linear interpolation between neighbouring
PFF frames (a value is kept only where both neighbours have it, or within half a PFF frame of one that has it).
Usage: python3 convert_pff.py 3839
"""
import bz2
import json
import sys
import numpy as np

FPS = 25.0
L, W = 105.0, 68.0


def main(game):
    meta = json.load(open(f'raw/{game}_metadata.json'))[0]
    rows = [json.loads(line) for line in bz2.open(f'raw/{game}.jsonl.bz2', 'rt')]
    rows.sort(key=lambda d: d['videoTimeMs'])
    t = np.array([d['videoTimeMs'] / 1000.0 for d in rows])
    slots = []
    for d in rows:
        for side, key in ((0, 'homePlayersSmoothed'), (1, 'awayPlayersSmoothed')):
            for p in d.get(key) or []:
                s = (side, str(p['jerseyNum']))
                if s not in slots:
                    slots.append(s)
    slots.sort(key=lambda s: (s[0], int(s[1])))
    index = {s: i for i, s in enumerate(slots)}
    n, P = len(rows), len(slots)
    pl = np.full((n, P, 2), np.nan)
    ball = np.full((n, 2), np.nan)
    ball_est = np.full((n, 2), np.nan)
    for i, d in enumerate(rows):
        for side, key in ((0, 'homePlayersSmoothed'), (1, 'awayPlayersSmoothed')):
            for p in d.get(key) or []:
                if p.get('x') is not None and p.get('y') is not None:
                    pl[i, index[(side, str(p['jerseyNum']))]] = (p['x'] + L / 2, p['y'] + W / 2)
        b = d.get('ballsSmoothed')
        if b and b.get('x') is not None:
            xy = (b['x'] + L / 2, b['y'] + W / 2)
            ball_est[i] = xy
            if b.get('visibility') == 'VISIBLE':
                ball[i] = xy
    # 25 fps grid over video time, from the first kick-off to the end of the second half
    t0, t1 = meta['startPeriod1'], meta['endPeriod2']
    grid = t0 + np.arange(int(np.floor((t1 - t0) * FPS)) + 1) / FPS
    period = np.zeros(len(grid), np.int8)
    period[(grid >= meta['startPeriod1']) & (grid <= meta['endPeriod1'])] = 1
    period[(grid >= meta['startPeriod2']) & (grid <= meta['endPeriod2'])] = 2
    j = np.clip(np.searchsorted(t, grid), 1, n - 1)
    ta, tb = t[j - 1], t[j]
    w = np.clip((grid - ta) / np.maximum(tb - ta, 1e-9), 0, 1)
    half_frame = 0.5 / 29.97
    near_a, near_b = np.abs(grid - ta) <= half_frame, np.abs(grid - tb) <= half_frame
    gap = (tb - ta) > 3.0 / 29.97          # no interpolation across holes in the PFF timeline

    def resample(a):
        A, B = a[j - 1], a[j]
        wv = w.reshape((-1,) + (1,) * (a.ndim - 1))
        out = A + (B - A) * wv
        both = np.isfinite(A) & np.isfinite(B)
        na = near_a.reshape(wv.shape) & np.isfinite(A) & ~np.isfinite(B)
        nb = near_b.reshape(wv.shape) & np.isfinite(B) & ~np.isfinite(A)
        out = np.where(both, out, np.where(na, A, np.where(nb, B, np.nan)))
        out[gap] = np.nan
        return out.astype(np.float32)

    players, ball25, est25 = resample(pl), resample(ball), resample(ball_est)
    players[period == 0] = np.nan
    ball25[period == 0] = np.nan
    team = np.array([s[0] for s in slots], np.int8)
    jersey = np.array([int(s[1]) for s in slots], np.int16)
    np.savez_compressed(f'{game}_match.npz', ball=ball25, ball_estimated=est25, players=players, team=team,
                        jersey=jersey, period=period, t_video=grid, fps=FPS, pitch=np.array([L, W]))
    play = period > 0
    print(json.dumps({'game': game, 'home': meta['homeTeam']['name'], 'away': meta['awayTeam']['name'],
                      'pff_frames': n, 'grid_frames': len(grid), 'slots': P, 'home_slots': int((team == 0).sum()),
                      'ball_visible_share_in_play': round(float(np.isfinite(ball25[play]).all(1).mean()), 3),
                      'players_present_mean': round(float(np.isfinite(players[play]).all(2).sum(1).mean()), 1),
                      'period_frames': {k: int((period == k).sum()) for k in (0, 1, 2)}}))


if __name__ == '__main__':
    main(sys.argv[1])
