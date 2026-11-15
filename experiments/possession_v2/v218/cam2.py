"""K016 exploration, second part: players the tactical tracking lost but the second camera sees.
  F   as A (the release), and a registered broadcast player with no tactical player of either team within 1.5 m is added
      (one extra slot per broadcast track, team as the broadcast tracking says)
  PF  as P of cam1.py (broadcast ball and players where the cameras agree within 0.5 m) plus F
The simulated broadcast stream never loses a player inside its window, so F is an upper bound of what a real stream could give.
Reporting only; nothing here opens the provided match. Usage: cam2.py PART   (PART 0|1 splits the matches)"""
import sys, json, os, time, platform, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v218')
sys.path.insert(0, '/home/claude/sc')
from possession.register import frame_offsets, _nan_window, MEDIAN_HALF_S

EMPTY_R = 1.5


def players_fill(tac_p, tac_team, bro_p, bro_team, bro_ball, t_of_b, fps, base=None, empty_r=EMPTY_R):
    """(players with extra slots, team with extra entries, number of added positions). tac_p is used for the search of an
    empty spot; base (default tac_p) is the array the extra slots are appended to."""
    tac_p = np.asarray(tac_p); bro_p = np.asarray(bro_p, np.float64); bro_team = np.asarray(bro_team)
    off = frame_offsets(bro_p, bro_team, np.asarray(bro_ball, np.float64), tac_p, np.asarray(tac_team), t_of_b)
    sm = _nan_window(off, int(round(MEDIAN_HALF_S * fps)), np.nanmedian)
    sm[t_of_b < 0] = np.nan
    T, Sb = len(tac_p), bro_p.shape[1]
    extra = np.full((T, Sb, 2), np.nan, np.float32)
    acc = np.flatnonzero((t_of_b >= 0) & np.isfinite(sm).all(1))
    n_add = 0
    for s in range(0, len(acc), 2000):
        idx = acc[s:s + 2000]; tt = t_of_b[idx]
        bp = bro_p[idx] - sm[idx][:, None]                                   # (n, Sb, 2) registered
        tp = tac_p[tt].astype(np.float64)                                    # (n, St, 2) both teams
        d = np.linalg.norm(bp[:, :, None] - tp[:, None], axis=3)
        d[~np.isfinite(d)] = np.inf
        lonely = np.isfinite(bp).all(2) & (d.min(2) > empty_r)
        r, c = np.nonzero(lonely)
        extra[tt[r], c] = bp[r, c]
        n_add += len(r)
    base = tac_p if base is None else np.asarray(base)
    return np.concatenate([base, extra.astype(base.dtype)], 1), np.r_[np.asarray(tac_team), bro_team].astype(np.int8), n_add


if __name__ == '__main__':
    import cam1 as C
    X, E = C.X, C.E
    from possession.fusion import project
    from possession.features import play_blocks
    part = int(sys.argv[1])
    OUT = f'{C.V}cam2_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': [], 'stats': {}}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    j = 0
    for mi, name in enumerate(C.NAMES):
        if mi % 2 != part:
            continue
        for regime in ('sharp', 'good'):
            key0 = f'{name}|{C.SEED + 10 * mi + j}'
            if all((key0, f'{regime}|{v}') in done for v in ('F', 'PF')):
                continue
            # the same copy and stream as cam1.variants (same seeds), rebuilt to get at the aligned broadcast stream
            m, lab, seed, mm, path, fixed = C.tactical(name, mi, j)
            per, fps = m['period'], float(m['fps']); graded = per > 0
            blocks = play_blocks(per); halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
            T = len(m['ball']); ri = C.ORDER.index(regime)
            rb = np.random.default_rng(C.STREAM + 100 * ri + 2 * mi + j)
            q = C.quality(rb, regime)
            bro, valid, true_t, clock_t = C.sb3.simulate_warp(m, lab, rb, q)
            rc = np.random.default_rng(C.CLOCK + 100 * ri + 2 * mi + j)
            pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
            pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
            lags, crep = E.half_lags(C.sc.observations(np.arange(T), blocks, fps, rc, pr_t, pm_t),
                                     C.sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b), fps, halves)
            bro2, t_of_b, arep = E.align_auto(mm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
            reg_ball, rrep = E.register_ball(bro2, mm, t_of_b, fps)
            fb, frep = E.fuse_gated(mm['ball'], reg_ball, t_of_b, fps, graded)
            if not frep['used']:
                continue
            fb = np.asarray(fb)
            tac = np.asarray(mm['ball'], np.float64); bb = project(reg_ball, t_of_b, T)
            both = np.isfinite(tac).all(1) & np.isfinite(bb).all(1)
            d = np.full(T, np.inf); d[both] = np.linalg.norm(tac[both] - bb[both], axis=1)
            cons = both & (d <= C.TAU)
            b1 = fb.copy(); b1[cons] = bb[cons]
            pf, tf, n_add = players_fill(mm['players'], mm['team'], bro2['players'], bro2['team'], bro2['ball'], t_of_b, fps)
            fin = np.isfinite(np.asarray(mm['players'])).all(2)
            # how many of the added positions are a real player the tactical copy has lost (within 1 m of a clean player)
            ex = pf[:, np.asarray(mm['players']).shape[1]:]
            rr, cc = np.nonzero(np.isfinite(ex).all(2))
            sel = slice(None, None, 11)
            err = C.nearest_clean(ex[rr, cc][sel].astype(np.float64), np.asarray(m['players'], np.float64)[rr[sel]])
            res['stats'][f'{key0}|{regime}'] = {'added_player_positions': int(n_add), 'tactical_player_positions': int(fin.sum()),
                                                'added_as_share_of_tactical_positions': round(float(n_add / fin.sum()), 4),
                                                'share_of_added_within_1m_of_a_clean_player': round(float(np.mean(err <= 1.0)), 3),
                                                'share_of_frames_with_an_added_player': round(float(np.isfinite(ex).all(2).any(1)[graded].mean()), 4)}
            inp = {}
            fixed_f, _ = E.keeper2.correct_goalkeepers(dict(mm, players=pf, team=tf))
            inp['F'] = dict(fixed_f, ball=fb)
            pl, _ = C.players_priority(mm, bro2, t_of_b, fps, np.asarray(m['players'], np.float64))
            ppf, tpf, _ = players_fill(mm['players'], mm['team'], bro2['players'], bro2['team'], bro2['ball'], t_of_b, fps, base=pl)
            fixed_pf, _ = E.keeper2.correct_goalkeepers(dict(mm, players=ppf, team=tpf))
            inp['PF'] = dict(fixed_pf, ball=b1)
            del bro, bro2, pf, ppf, pl, ex
            for v in ('F', 'PF'):
                if (key0, f'{regime}|{v}') in done:
                    continue
                row = X.row_for(name, key0, f'{regime}|{v}', path, inp[v], lab, per)
                res['rows'].append(row); done.add((key0, f'{regime}|{v}'))
                json.dump(res, open(OUT + '.tmp', 'w'), indent=0); os.replace(OUT + '.tmp', OUT)
                print(time.strftime('%H:%M:%S'), key0, regime, v, path, 'v2.11', round(row['v2_11']['spell_f1'], 4), 'v2.15', round(row['fused']['spell_f1'], 4), flush=True)
            del inp
    print('done', flush=True)
