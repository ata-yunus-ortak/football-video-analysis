"""K016 exploration (development matches, simulated second camera): which camera should supply a position that both see?
The release (v2.15) takes everything from the tactical tracking and uses the broadcast tracking only for the ball where the
tactical ball is missing, behind the 0.50 m agreement gate, after the player-based registration. Variants tried here, all
with the release's alignment, registration and gate unchanged:
  T   tactical tracking only (no second camera): what the second camera gives at all
  A   the release (fill only)
  B1  as A, and where both see the ball and agree within 0.5 m the broadcast ball is used        (the proposal)
  B2  as A, and where both see the ball the broadcast ball is used, agreeing or not
  C   as A, and where both agree within 0.5 m the mean of the two balls is used
  P   as B1, and a tactical player whose registered broadcast counterpart lies within 0.5 m gets the broadcast position
Simulated broadcast streams (synth_broadcast3.simulate_warp) in three regimes: 'sharp' (broadcast clearly more precise than
the tactical copy; new here), 'good' and 'medium' (as in the v2.5 / v2.9 / v2.15 validations).
Reporting only; nothing here opens the provided match. Usage: cam1.py PART PASS   (PART 0|1 splits the matches, PASS 1|2)"""
import sys, json, os, time, platform, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v215')
import exp_v215 as X
E = X.E
from possession.fusion import project
from possession.register import frame_offsets, _nan_window, MEDIAN_HALF_S
from possession.features import play_blocks
import synth_broadcast as sbase
import synth_broadcast3 as sb3
import synth_clock as sc
import exp_v25

SEED, STREAM, CLOCK = 23100, 53100, 63100
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
REG = {'sharp': ((0.0, 0.05), (0.01, 0.05), (0.01, 0.05)), 'good': exp_v25.REGIMES['good'], 'medium': exp_v25.REGIMES['medium']}
ORDER = ['sharp', 'good', 'medium']
TAU = 0.5
V = '/home/claude/work/v218/'


def quality(rng, regime):
    q = sbase.sample_quality(rng, 'default')
    (b0, b1), (s0, s1), (p0, p1) = REG[regime]
    q.update(bias_sd=float(rng.uniform(b0, b1)), b_sd=float(rng.uniform(s0, s1)), p_sd=float(rng.uniform(p0, p1)))
    return q


def nearest_clean(pos, clean):
    """distance of each (n, 2) position to the nearest clean player of its frame; clean is (n, S, 2)"""
    d = np.linalg.norm(clean - pos[:, None], axis=2)
    d[~np.isfinite(d)] = np.inf
    return d.min(1)


def players_priority(mm, bro2, t_of_b, fps, clean_players, tau=TAU):
    """Tactical players replaced by their registered broadcast counterpart where the two lie within tau metres.
    Returns (players array, statistics)."""
    ball = np.asarray(bro2['ball'], np.float64)
    bro_p, bro_team = np.asarray(bro2['players'], np.float64), np.asarray(bro2['team'])
    tac_p, tac_team = np.asarray(mm['players']), np.asarray(mm['team'])
    off = frame_offsets(bro_p, bro_team, ball, tac_p, tac_team, t_of_b)
    sm = _nan_window(off, int(round(MEDIAN_HALF_S * fps)), np.nanmedian)
    sm[t_of_b < 0] = np.nan
    out = tac_p.copy()
    acc = np.flatnonzero((t_of_b >= 0) & np.isfinite(sm).all(1))
    n_rep = n_seen = 0
    e_old, e_new = [], []
    for s in range(0, len(acc), 2000):
        idx = acc[s:s + 2000]; tt = t_of_b[idx]
        for k in (0, 1):
            bi, ti = np.flatnonzero(bro_team == k), np.flatnonzero(tac_team == k)
            if not len(bi) or not len(ti):
                continue
            bp = bro_p[idx][:, bi] - sm[idx][:, None]
            tp = tac_p[tt][:, ti].astype(np.float64)
            d = np.linalg.norm(bp[:, :, None] - tp[:, None], axis=3)
            d[~np.isfinite(d)] = np.inf
            jb, ib = d.argmin(2), d.argmin(1)
            rows = np.arange(len(idx))[:, None]; cols = np.arange(len(bi))[None]
            dmin = d[rows, cols, jb]
            ok = (ib[rows, jb] == cols) & (dmin <= tau)
            n_seen += int(np.isfinite(bp).all(2).sum())
            r, c = np.nonzero(ok)
            if not len(r):
                continue
            out[tt[r], ti[jb[r, c]]] = bp[r, c]
            n_rep += len(r)
            if len(e_old) < 40:                       # error sample against the clean players
                sel = slice(None, None, 7)
                e_old.append(nearest_clean(tp[r, jb[r, c]][sel], clean_players[tt[r]][sel]))
                e_new.append(nearest_clean(bp[r, c][sel], clean_players[tt[r]][sel]))
    eo, en = (np.concatenate(e_old), np.concatenate(e_new)) if e_old else (np.array([np.nan]), np.array([np.nan]))
    return out, {'player_positions_replaced': n_rep, 'broadcast_player_positions_on_accepted_frames': n_seen,
                 'median_error_m_of_replaced_tactical_positions': round(float(np.median(eo)), 3),
                 'median_error_m_of_their_broadcast_positions': round(float(np.median(en)), 3)}


_TAC = {}


def tactical(name, mi, j):
    key = (name, j)
    if key not in _TAC:
        _TAC.clear()
        m, lab = E.load(name)
        seed = SEED + 10 * mi + j
        rng = np.random.default_rng(seed)
        dm = E.degrade(m, lab, rng, E.sample_params(rng, ranges=E.RANGES))
        mm = E.packed(dm)
        noise = E.estimate_noise(mm)
        path, _ = E.choose_path(noise)
        fixed, _ = E.keeper2.correct_goalkeepers(mm)
        _TAC[key] = (m, lab, seed, mm, path, fixed)
    return _TAC[key]


def variants(name, mi, j, regime):
    """{variant: model input}, statistics. Only the ball (and for P the player positions) differ between variants."""
    m, lab, seed, mm, path, fixed = tactical(name, mi, j)
    per, fps = m['period'], float(m['fps'])
    graded = per > 0
    blocks = play_blocks(per)
    halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
    T = len(m['ball'])
    ri = ORDER.index(regime)
    rb = np.random.default_rng(STREAM + 100 * ri + 2 * mi + j)
    q = quality(rb, regime)
    bro, valid, true_t, clock_t = sb3.simulate_warp(m, lab, rb, q)
    rc = np.random.default_rng(CLOCK + 100 * ri + 2 * mi + j)
    pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
    pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
    lags, crep = E.half_lags(sc.observations(np.arange(T), blocks, fps, rc, pr_t, pm_t),
                             sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b), fps, halves)
    bro2, t_of_b, arep = E.align_auto(mm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
    reg_ball, rrep = E.register_ball(bro2, mm, t_of_b, fps)
    fb, frep = E.fuse_gated(mm['ball'], reg_ball, t_of_b, fps, graded)
    tac = np.asarray(mm['ball'], np.float64)
    bb = project(reg_ball, t_of_b, T)
    tf, bf = np.isfinite(tac).all(1), np.isfinite(bb).all(1)
    both = tf & bf
    d = np.full(T, np.inf); d[both] = np.linalg.norm(tac[both] - bb[both], axis=1)
    cons = both & (d <= TAU)
    clean = np.asarray(m['ball'], np.float64)[:, :2]
    cf = np.isfinite(clean).all(1)
    g = graded
    filled = g & ~tf & np.isfinite(np.asarray(fb, np.float64)).all(1)
    st = {'gate_used': bool(frep['used']), 'gate_median_distance_m': frep.get('median_distance_m'), 'path': path,
          'quality': {k: round(float(q[k]), 3) for k in ('bias_sd', 'b_sd', 'p_sd', 'hx', 'hy', 'ball_frac', 'invalid')},
          'graded_frames': int(g.sum()),
          'share_tactical_ball': round(float(tf[g].mean()), 4), 'share_broadcast_ball': round(float(bf[g].mean()), 4),
          'share_both_balls': round(float(both[g].mean()), 4), 'share_both_within_0.5m': round(float(cons[g].mean()), 4),
          'share_ball_filled_from_broadcast': round(float(filled.sum() / g.sum()), 4),
          'share_no_ball_after_fill': round(float(1 - np.isfinite(np.asarray(fb, np.float64)).all(1)[g].mean()), 4),
          'share_frames_with_an_accepted_broadcast_frame': round(float(np.isin(np.arange(T), t_of_b[t_of_b >= 0])[g].mean()), 4),
          'median_error_m_tactical_ball_where_both': round(float(np.median(np.linalg.norm(tac[both & cf] - clean[both & cf], axis=1))), 3),
          'median_error_m_broadcast_ball_where_both': round(float(np.median(np.linalg.norm(bb[both & cf] - clean[both & cf], axis=1))), 3),
          'median_error_m_broadcast_ball_where_filled': round(float(np.median(np.linalg.norm(bb[filled & cf] - clean[filled & cf], axis=1))), 3) if (filled & cf).any() else None}
    out = {'T': fixed}
    if not frep['used']:
        return out, st, (m, lab, seed, path, per)
    fb = np.asarray(fb)
    b1 = fb.copy(); b1[cons] = bb[cons]
    b2 = fb.copy(); b2[both] = bb[both]
    c = fb.copy(); c[cons] = 0.5 * (tac[cons] + bb[cons])
    pl, pst = players_priority(mm, bro2, t_of_b, fps, np.asarray(m['players'], np.float64))
    tp = np.asarray(mm['players'])
    fin = np.isfinite(tp).all(2)
    near = fin & (np.linalg.norm(tp - np.where(np.isfinite(fb).all(1)[:, None], fb, np.nan)[:, None], axis=2) <= 15.0)
    changed = fin & (np.abs(pl - tp).max(2) > 0)
    pst.update(share_of_tactical_player_positions_replaced=round(float(changed[g].sum() / max(fin[g].sum(), 1)), 4),
               share_replaced_among_players_within_15m_of_the_ball=round(float((changed & near)[g].sum() / max(near[g].sum(), 1)), 4))
    st['players'] = pst
    fixed_p, _ = E.keeper2.correct_goalkeepers(dict(mm, players=pl))      # the goalkeeper check runs on what the models will see
    out.update(A=dict(fixed, ball=fb), B1=dict(fixed, ball=b1), B2=dict(fixed, ball=b2), C=dict(fixed, ball=c),
               P=dict(fixed_p, ball=b1))
    return out, st, (m, lab, seed, path, per)


if __name__ == '__main__':
    part, pas = int(sys.argv[1]), int(sys.argv[2])
    OUT = f'{V}cam1_{part}_{pas}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': [], 'stats': {}}
    import pandas, sklearn
    res['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__, 'scikit_learn': sklearn.__version__}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    j = pas - 1
    plan = ([('sharp', ('T', 'A', 'B1', 'P', 'C', 'B2')), ('good', ('A', 'B1', 'P', 'C', 'B2')), ('medium', ('A', 'B1', 'P'))] if pas == 1 else
            [('sharp', ('T', 'A', 'B1', 'P')), ('good', ('A', 'B1', 'P'))])
    for mi, name in enumerate(NAMES):
        if mi % 2 != part:
            continue
        for regime, vs in plan:
            key0 = f'{name}|{SEED + 10 * mi + j}'
            if all((key0, f'{regime}|{v}') in done for v in vs):
                continue
            inp, st, (m, lab, seed, path, per) = variants(name, mi, j, regime)
            res['stats'][f'{key0}|{regime}'] = st
            for v in vs:
                if (key0, f'{regime}|{v}') in done or v not in inp:
                    continue
                row = X.row_for(name, key0, f'{regime}|{v}', path, inp[v], lab, per)
                res['rows'].append(row); done.add((key0, f'{regime}|{v}'))
                json.dump(res, open(OUT + '.tmp', 'w'), indent=0); os.replace(OUT + '.tmp', OUT)
                print(time.strftime('%H:%M:%S'), key0, regime, v, path, 'v2.11', round(row['v2_11']['spell_f1'], 4), 'v2.15', round(row['fused']['spell_f1'], 4),
                      row['seconds_v2'], row['seconds_tcn'], flush=True)
            del inp
    print('done', flush=True)
