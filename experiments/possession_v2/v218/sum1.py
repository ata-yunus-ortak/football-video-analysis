import json, glob, numpy as np, sys
rows, stats = [], {}
for f in sorted(glob.glob('cam1_*_*.json')) + sorted(glob.glob('cam2_*.json')):
    d = json.load(open(f)); rows += d['rows']; stats.update({k: v for k, v in d['stats'].items() if 'gate_used' in v})
by = {(r['copy'], r['condition']): r for r in rows}
copies = sorted({r['copy'] for r in rows})
def val(c, cond, sysname='fused'):
    r = by.get((c, cond)); return None if r is None else r[sysname]['spell_f1']
print('copies', len(copies), 'rows', len(rows))
for reg in ('sharp', 'good', 'medium'):
    print('==', reg)
    for v in ('T', 'B1', 'B2', 'C', 'P', 'F', 'PF'):
        ref = 'sharp|T' if False else f'{reg}|A'
        d = []
        for c in copies:
            a = val(c, ref); x = val(c, f'{reg}|{v}') if v != 'T' else val(c, 'sharp|T')
            if a is not None and x is not None:
                d.append((c, x - a))
        if not d:
            continue
        v_ = np.array([x for _, x in d]); dfl = np.array([c.startswith('J03') for c, _ in d])
        print(f'  {v:3s} - A: n {len(v_):2d} mean {v_.mean():+.4f}  DFL {v_[dfl].mean() if dfl.any() else float("nan"):+.4f}  Metrica {v_[~dfl].mean() if (~dfl).any() else float("nan"):+.4f}  min {v_.min():+.4f} max {v_.max():+.4f}  better {(v_ > 1e-9).sum()} worse {(v_ < -1e-9).sum()}')
    a = [val(c, f'{reg}|A') for c in copies if val(c, f'{reg}|A') is not None]
    print('  A mean', round(float(np.mean(a)), 4), 'n', len(a))
print('== usage and accuracy statistics (means over the built copies)')
keys = ['share_tactical_ball', 'share_broadcast_ball', 'share_both_balls', 'share_both_within_0.5m', 'share_ball_filled_from_broadcast', 'share_no_ball_after_fill',
        'share_frames_with_an_accepted_broadcast_frame', 'median_error_m_tactical_ball_where_both', 'median_error_m_broadcast_ball_where_both', 'gate_median_distance_m']
for reg in ('sharp', 'good', 'medium'):
    ss = [v for k, v in stats.items() if k.endswith('|' + reg)]
    if not ss:
        continue
    print(reg, 'n', len(ss), 'gate open', sum(s['gate_used'] for s in ss), {k: round(float(np.mean([s[k] for s in ss if s.get(k) is not None])), 3) for k in keys})
    pp = [s['players'] for s in ss if 'players' in s]
    if pp:
        print('   players:', {k: round(float(np.mean([p[k] for p in pp])), 3) for k in ('share_of_tactical_player_positions_replaced', 'share_replaced_among_players_within_15m_of_the_ball',
                                                                                    'median_error_m_of_replaced_tactical_positions', 'median_error_m_of_their_broadcast_positions')})
