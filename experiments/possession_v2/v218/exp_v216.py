"""v2.16 validation (possession-v216-plan.json): possession-v2.15 against the same system with the players that the
tactical tracking has lost added from the broadcast tracking (possession/playerfill.py), on new corrupted copies with a
simulated second camera. Both arms share the copy, the stream, the alignment, the registration, the ball fill and the
models; only the candidate arm adds players, and only when the accuracy gate is open.
  arms        v2_15      model input = goalkeeper-checked tactical tracking, ball filled behind the gate (run215)
              candidate  playerfill.fill_players on the tactical tracking as given, goalkeeper check on the result,
                         the same filled ball
  conditions  good            16 copies (j = 0..3): simulated broadcast, regime good (exp_v25.REGIMES)
              medium           8 copies (j = 0, 1): regime medium
              good_degraded    8 copies (j = 0, 1): the stream of condition good of that copy, with players lost, invented
                               and under the wrong team (cam3.degrade_bro, unchanged)
              sim2_good        4 copies (one per match): tactical copy made with the team member's simulator, regime good
  seeds       copy 28100 + 10 * match_index + j; stream 58100 + 100 * regime_index + 4 * match_index + j (regime_index
              good 0, medium 1, sim2_good 3); clock readings 68100 + the same offset; stream degradation
              78100 + 4 * match_index + j; other simulator 88100 + match_index
Usage: /usr/bin/python3 exp_v216.py PART      PART = 0 | 1 | 2 | 3 (match index) | wiring
(wiring: one development copy of the exploration, to check that this script reproduces its rows; no validation copy)"""
import sys, json, os, time, platform, hashlib, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v218'); sys.path.insert(0, '/home/claude/sc')
import cam1 as C
import cam3
from possession import playerfill
from possession.features import play_blocks
X, E = C.X, C.E

V = '/home/claude/work/v218/'
SEED, STREAM, CLOCK, DEG, SIM2 = 28100, 58100, 68100, 78100, 88100
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
RI = {'good': 0, 'medium': 1, 'sim2_good': 3}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def stream(m, lab, mm, regime, sseed, cseed, deg_seed=None):
    """Simulated broadcast stream of one copy, aligned and registered; (bro2, t_of_b, filled ball, gate report, extra)."""
    per, fps = m['period'], float(m['fps'])
    blocks = play_blocks(per)
    halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
    T = len(m['ball'])
    rb = np.random.default_rng(sseed)
    q = C.quality(rb, regime)
    bro, valid, true_t, clock_t = C.sb3.simulate_warp(m, lab, rb, q)
    extra = {}
    if deg_seed is not None:
        bro, extra = cam3.degrade_bro(bro, np.random.default_rng(deg_seed), fps)
    rc = np.random.default_rng(cseed)
    pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
    pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
    lags, crep = E.half_lags(C.sc.observations(np.arange(T), blocks, fps, rc, pr_t, pm_t),
                             C.sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b), fps, halves)
    bro2, t_of_b, arep = E.align_auto(mm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
    reg_ball, rrep = E.register_ball(bro2, mm, t_of_b, fps)
    fb, frep = E.fuse_gated(mm['ball'], reg_ball, t_of_b, fps, per > 0)
    return bro2, t_of_b, fb, frep, extra


def arms(m, mm, fixed, bro2, t_of_b, fb, frep):
    """{arm: model input}, statistics of the candidate arm (counts on an external copy)."""
    if not frep['used']:
        return {'v2_15': fixed, 'candidate': fixed}, {'gate_used': False}
    fb = np.asarray(fb)
    pf, tf, rep = playerfill.fill_players(mm, bro2, t_of_b, float(m['fps']))
    S = np.asarray(mm['players']).shape[1]
    ex = pf[:, S:]
    rr, cc = np.nonzero(np.isfinite(ex).all(2))
    sel = slice(None, None, 11)
    err = C.nearest_clean(ex[rr, cc][sel].astype(np.float64), np.asarray(m['players'], np.float64)[rr[sel]]) if len(rr) else np.array([np.nan])
    graded = m['period'] > 0
    st = dict(rep, gate_used=True, gate_median_distance_m=frep.get('median_distance_m'),
              tactical_player_positions=int(np.isfinite(np.asarray(mm['players'])).all(2).sum()),
              share_of_added_within_1m_of_a_clean_player=round(float(np.mean(err <= 1.0)), 3),
              share_of_graded_frames_with_an_added_player=round(float(np.isfinite(ex).all(2).any(1)[graded].mean()), 4))
    fixed_f, krep = E.keeper2.correct_goalkeepers(dict(mm, players=pf, team=tf))
    return {'v2_15': dict(fixed, ball=fb), 'candidate': dict(fixed_f, ball=fb)}, st


def run_condition(res, OUT, done, name, key, cond, m, lab, mm, path, fixed, regime, sseed, cseed, deg_seed=None):
    if all((key, f'{cond}|{a}') in done for a in ('v2_15', 'candidate')):
        return
    per = m['period']
    bro2, t_of_b, fb, frep, extra = stream(m, lab, mm, regime, sseed, cseed, deg_seed)
    inp, st = arms(m, mm, fixed, bro2, t_of_b, fb, frep)
    del bro2
    res['stats'][f'{key}|{cond}'] = dict(st, **extra)
    first = None
    for a in ('v2_15', 'candidate'):
        if (key, f'{cond}|{a}') in done:
            continue
        if a == 'candidate' and not st['gate_used'] and first is not None:      # gate closed: the candidate is the release
            row = dict(first, condition=f'{cond}|{a}')
        else:
            row = X.row_for(name, key, f'{cond}|{a}', path, inp[a], lab, per)
        first = row if a == 'v2_15' else first
        res['rows'].append(row); done.add((key, f'{cond}|{a}'))
        json.dump(res, open(OUT + '.tmp', 'w'), indent=0); os.replace(OUT + '.tmp', OUT)
        print(time.strftime('%H:%M:%S'), key, cond, a, path, 'gate', st['gate_used'], round(row['fused']['spell_f1'], 4), flush=True)


if __name__ == '__main__':
    import pandas, sklearn
    part = sys.argv[1]
    OUT = f'{V}exp_v216_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': [], 'stats': {}}
    res['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__, 'scikit_learn': sklearn.__version__}
    res['sha256'] = {'possession/playerfill.py': sha('/home/claude/sc/possession/playerfill.py'), 'possession/register.py': sha('/home/claude/sc/possession/register.py'),
                     'possession/fusion.py': sha('/home/claude/sc/possession/fusion.py'), 'possession/keeper2.py': sha('/home/claude/sc/possession/keeper2.py'),
                     'exp_v216.py': sha(V + 'exp_v216.py'), 'cam1.py': sha(V + 'cam1.py'), 'cam3.py': sha(V + 'cam3.py'),
                     'exp_v215.py': sha('/home/claude/work/v215/exp_v215.py'), 'exp_v213.py': sha('/home/claude/work/v213/exp_v213.py'),
                     'pooling.py': sha('/home/claude/work/v215/pooling.py')}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if part == 'wiring':        # a development copy of the exploration (cam1 / cam2 / cam3 seeds): must reproduce those rows
        mi, j, name = 0, 0, 'J03WN1'
        m, lab, seed, mm, path, fixed = C.tactical(name, mi, j)
        key = f'{name}|{seed}'
        run_condition(res, OUT, done, name, key, 'good', m, lab, mm, path, fixed, 'good', C.STREAM + 100 * 1 + 2 * mi + j, C.CLOCK + 100 * 1 + 2 * mi + j)
        sys.exit(0)
    mi = int(part); name = NAMES[mi]
    m, lab = E.load(name)
    for j in (0, 1, 2, 3):
        seed = SEED + 10 * mi + j
        key = f'{name}|{seed}'
        conds = [('good', 'good', None)] + ([('medium', 'medium', None), ('good_degraded', 'good', DEG + 4 * mi + j)] if j < 2 else [])
        if all((key, f'{c}|{a}') in done for c, _, _ in conds for a in ('v2_15', 'candidate')):
            continue
        rng = np.random.default_rng(seed)
        mm = E.packed(E.degrade(m, lab, rng, E.sample_params(rng, ranges=E.RANGES)))
        path, _ = E.choose_path(E.estimate_noise(mm))
        fixed, _ = E.keeper2.correct_goalkeepers(mm)
        for cond, regime, deg in conds:
            off = 100 * RI[regime] + 4 * mi + j
            run_condition(res, OUT, done, name, key, cond, m, lab, mm, path, fixed, regime, STREAM + off, CLOCK + off, deg)
        del mm, fixed
    key = f'{name}|{SIM2 + mi}'
    if not all((key, f'sim2_good|{a}') in done for a in ('v2_15', 'candidate')):
        m2 = E.packed(E.sim2(m, SIM2 + mi))
        path2, _ = E.choose_path(E.estimate_noise(m2))
        fixed2, _ = E.keeper2.correct_goalkeepers(m2)
        off = 100 * RI['sim2_good'] + 4 * mi
        run_condition(res, OUT, done, name, key, 'sim2_good', m, lab, m2, path2, fixed2, 'good', STREAM + off, CLOCK + off)
    print('done', flush=True)
