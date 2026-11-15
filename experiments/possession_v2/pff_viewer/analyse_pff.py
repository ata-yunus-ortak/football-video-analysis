"""Where and how the frozen v2.11 labels differ from the PFF event proxy on one converted PFF game.

Reads {game}_match.npz, {game}_labels.npz and raw/{game}_events.json (outputs of convert_pff.py and run_pff.py).
Writes {game}_analysis.json: the organisers' metric broken into its parts, the kinds of disagreement, agreement with
and without a visible ball, dead-ball periods found or missed, and the longest disagreement stretches with the
match clock (to look up in the viewer). Description only: nothing here is used to fit or choose anything.
Usage: python3 analyse_pff.py 3839
"""
import ast
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # repository root
from possession.evaluate import score

MIN_RUN_S = 2.0


def parse(s):
    if s is None or isinstance(s, (dict, list)):
        return s
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return json.loads(s)


def runs(mask):
    """[start, end) index pairs of True stretches."""
    m = np.concatenate([[False], mask, [False]]).astype(np.int8)
    d = np.diff(m)
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def clock(t, meta):
    if meta['startPeriod1'] <= t <= meta['endPeriod1']:
        el, base, half = t - meta['startPeriod1'], 0, 1
    elif meta['startPeriod2'] <= t <= meta['endPeriod2']:
        el, base, half = t - meta['startPeriod2'], 45 * 60, 2
    else:
        return 'devre arası'
    f = lambda s: f'{int(s // 60):02d}:{int(s % 60):02d}'
    extra = max(0.0, el - 45 * 60)
    return f'{half}. yarı ' + (f'{f(base + 45 * 60)}+{f(extra)}' if extra > 0 else f(base + el))


def main(game):
    z = np.load(f'{game}_match.npz')
    lab = np.load(f'{game}_labels.npz')
    meta = json.load(open(f'raw/{game}_metadata.json'))[0]
    ours, ref, per, tv = lab['ours'], lab['pff'], z['period'], z['t_video']
    fps = float(z['fps'])
    play = per > 0
    full = score(ref, ours, per)
    out = {'game': game, 'metric_parts': {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else int(v))
                                          for k, v in full.items()}}
    # 1. kinds of disagreement (share of in-play frames)
    o, r = ours[play], ref[play]
    n = len(o)
    out['confusion_in_play_rows_proxy_cols_ours'] = {a: {b: int(np.sum((r == a) & (o == b))) for b in 'HAD'} for a in 'HAD'}
    out['disagreement_share_in_play'] = {
        'ours_dead_proxy_alive': round(float(np.mean((o == 'D') & (r != 'D'))), 4),
        'ours_alive_proxy_dead': round(float(np.mean((o != 'D') & (r == 'D'))), 4),
        'team_swapped_both_alive': round(float(np.mean((o != 'D') & (r != 'D') & (o != r))), 4)}
    # 2. with and without a visible ball (our input has no ball where PFF did not see it)
    vis = np.isfinite(z['ball']).all(1)[play]
    out['ball_visible_share_in_play'] = round(float(vis.mean()), 3)
    out['frame_agreement_ball_visible'] = round(float(np.mean(o[vis] == r[vis])), 4)
    out['frame_agreement_ball_not_visible'] = round(float(np.mean(o[~vis] == r[~vis])), 4)
    both_alive = (o != 'D') & (r != 'D')
    out['team_agreement_both_alive_ball_visible'] = round(float(np.mean(o[both_alive & vis] == r[both_alive & vis])), 4)
    out['team_agreement_both_alive_ball_not_visible'] = round(float(np.mean(o[both_alive & ~vis] == r[both_alive & ~vis])), 4)
    # 3. dead-ball periods of the proxy (>= 2 s): found by us? and our dead periods without a proxy one
    def dead_runs(lbl):
        return [(a, b) for a, b in runs((lbl == 'D') & play) if (b - a) / fps >= MIN_RUN_S]
    pr, orr = dead_runs(ref), dead_runs(ours)
    ours_dead, ref_dead = (ours == 'D'), (ref == 'D')
    found = [ours_dead[a:b].mean() >= 0.5 for a, b in pr]
    real = [ref_dead[a:b].mean() >= 0.5 for a, b in orr]
    starts, ends = [], []
    for a, b in pr:      # our dead stretch that overlaps this proxy stretch the most: start and end offsets
        best = max(((min(b, d) - max(a, c), c, d) for c, d in orr if min(b, d) > max(a, c)), default=None)
        if best:
            starts.append((best[1] - a) / fps)
            ends.append((best[2] - b) / fps)
    q = lambda v: {'median': round(float(np.median(v)), 2), 'iqr': [round(float(np.percentile(v, x)), 2) for x in (25, 75)]} if v else None
    out['dead_periods'] = {'proxy_dead_periods_min2s': len(pr), 'of_which_mostly_dead_in_ours': int(np.sum(found)),
                           'ours_dead_periods_min2s': len(orr), 'of_which_mostly_dead_in_proxy': int(np.sum(real)),
                           'matched_pairs': len(starts),
                           'start_offset_s_ours_minus_proxy': q(starts), 'end_offset_s_ours_minus_proxy': q(ends)}
    alive_r = r != 'D'
    out['ours_dead_when_proxy_alive'] = {'ball_visible': round(float(np.mean(o[alive_r & vis] == 'D')), 4),
                                         'ball_not_visible': round(float(np.mean(o[alive_r & ~vis] == 'D')), 4)}
    # 4. spells (in play, per half) and their typical length
    def spells(lbl):
        res = {'H': [], 'A': [], 'D': []}
        for h in (1, 2):
            idx = np.flatnonzero(per == h)
            seg = lbl[idx]
            cut = np.flatnonzero(seg[1:] != seg[:-1]) + 1
            for s_, e_ in zip(np.r_[0, cut], np.r_[cut, len(seg)]):
                res[seg[s_]].append((e_ - s_) / fps)
        return res
    so, sr = spells(ours), spells(ref)
    out['spells'] = {name: {k: {'count': len(v[k]), 'median_s': round(float(np.median(v[k])), 1) if v[k] else None,
                                'share_under_1s': round(float(np.mean(np.array(v[k]) < 1.0)), 3) if v[k] else None} for k in 'HAD'}
                     for name, v in (('ours', so), ('pff_proxy', sr))}
    # 5. longest disagreement stretches (>= 2 s), with the clock and nearby PFF events
    ev = []
    for e in json.load(open(f'raw/{game}_events.json')):
        g = parse(e['gameEvents']) or {}
        p = parse(e['possessionEvents']) or {}
        typ = g.get('gameEventType')
        if typ in ('OTB', 'OUT', 'FIRSTKICKOFF', 'SECONDKICKOFF', 'END'):
            ev.append((float(e['startTime']), typ if typ != 'OTB' else (p.get('possessionEventType') or 'OTB'),
                       g.get('setpieceType') or '', 'H' if g.get('homeTeam') else ('A' if g.get('homeTeam') is False else '')))
    ev.sort()
    et = np.array([e[0] for e in ev])
    dis = (ours != ref) & play
    stretches = sorted(((b - a, a, b) for a, b in runs(dis)), reverse=True)
    top = []
    for length, a, b in stretches[:15]:
        if length / fps < MIN_RUN_S:
            break
        vals, cnt = np.unique([f'{x}>{y}' for x, y in zip(ref[a:b], ours[a:b])], return_counts=True)
        kind = vals[np.argmax(cnt)]
        lo, hi = np.searchsorted(et, tv[a] - 3), np.searchsorted(et, tv[b - 1] + 1)
        top.append({'start_t': round(float(tv[a]), 2), 'start_clock': clock(float(tv[a]), meta), 'seconds': round(length / fps, 1),
                    'proxy_to_ours': kind, 'ball_visible_share': round(float(np.isfinite(z['ball'][a:b]).all(1).mean()), 2),
                    'pff_events': [{'dt': round(e[0] - float(tv[a]), 1), 'type': e[1], 'setpiece': e[2] if e[2] != 'O' else '',
                                    'team': e[3]} for e in ev[lo:hi]][:8]})
    out['longest_disagreements'] = top
    out['disagreement_stretches_min2s'] = int(sum(1 for L, _, _ in stretches if L / fps >= MIN_RUN_S))
    out['disagreement_frames_in_stretches_min2s_share'] = round(float(sum(L for L, _, _ in stretches if L / fps >= MIN_RUN_S) / max(1, dis.sum())), 3)
    out['note'] = 'description of agreement with an event-derived proxy; not ground truth; nothing fitted or selected'
    json.dump(out, open(f'{game}_analysis.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
