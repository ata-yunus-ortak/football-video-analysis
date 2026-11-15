"""v2.12 validation (possession-v212-plan.json): possession-v2.11 vs possession-v2.12 on 16 new corrupted copies of the
four validation matches (DFL J03WN1, J03WR9; Metrica sample games 1, 2). Tracks are packed into 46 anonymous slots as
in the provided file; the noise gate is decided on the tracking as given and the v2.11 goalkeeper team correction
(possession/keeper2.py) is applied in both systems, as in the release entry point.

Conditions
  tactical      copies j = 0..3 of each match (16): tactical camera only                         -> gates G1-G5
  fill_good     copies j = 0, 1 (8): simulated broadcast camera (synth_broadcast3 warp simulator, regime 'good' of
  fill_medium   exp_v25), simulated clock readings, clock-anchored alignment, player registration and the 0.50 m
                gate exactly as possession.run211; when the gate opens the base features of both systems see the
                filled ball; the touch columns of v2.12 are computed on the tactical ball as given (before the fill)
                                                                                                    -> gate G6
  view42        copies j = 0, 1 (8): camera window of +-42 m around the centre of play (camera_view.py), tactical
                camera only                                                                         -> reported
Systems
  v2_11  validation models of the release paths: v2.1 path cache/models_v2.pkl + cache/stack_v2.pkl (decoder switch 3),
         v2.3 path cache/models_v23.pkl + stack_v23.pkl with +-2 frame smoothing (exp_v25.run_path)
  v2_12  identical except on the v2.1 path: stage-1 input = possession.features columns + possession.touch columns
         (touch on the keeper-corrected tactical tracking before any fill), models v212/models_v212_val.pkl +
         v212/stack_v212_val.pkl (train_val.py: four DFL training matches only). On the v2.3 path v2_12 = v2_11.
Seeds: copy seed 12100 + 10 * match_index + j (degrade v2 profile, parameters sampled from the seed as exp_v211);
broadcast stream 42100 + 100 * regime_index + 2 * match_index + j; clock readings 52100 + 100 * regime_index +
2 * match_index + j; reserved Metrica game 3 (after the decision, reported): copy seed 32103, regime index as above,
copy index 8.
Usage: /usr/bin/python3 exp_v212.py PART     PART = 0 | 1 | 2 | 3 (validation match index) | reserved | smoke
(smoke: wiring check on training match J03WOH, training seed 1, in-sample for both model sets, numbers meaningless)
"""
import sys, json, time, os, pickle, platform, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/work/v212')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.noise import estimate_noise, choose_path
from possession.features import features, play_blocks
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score, _with_separators
from possession import official_metrics as pm
from possession import keeper2
from possession.touch import touch_features
from possession.epts_export import tracklets, pack
from possession.fusion import fuse_gated, align_auto
from possession.register import register_ball
from possession.clocksync import half_lags
from exp_v25 import run_path, quality, MODELS, PATHS
from exp_v210 import SLOT46
from camera_view import apply_view
import synth_broadcast3 as sb3
import synth_clock as sc

NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
SEED, STREAM, CLOCK, RESERVED_SEED = 12100, 42100, 52100, 32103
REGIMES = ('good', 'medium')            # names of exp_v25.REGIMES
COPIES_TACTICAL, COPIES_OTHER = (0, 1, 2, 3), (0, 1)
V212 = '/home/claude/work/v212/'
M12 = pickle.load(open(V212 + 'models_v212_val.pkl', 'rb'))
S12 = pickle.load(open(V212 + 'stack_v212_val.pkl', 'rb'))
DEC21 = PATHS['v2.1'][2]


def predict(models, stack, X, Xs, period, dec):
    """Stage 1 -> stage 2 -> decoder, line by line as exp_v25.run_path (v2.1 path, no smoothing)."""
    (md, mh), (sd, sh) = models, stack
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    S = [stack_features(p1, q1, period, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(p1), .5); q2 = np.full(len(p1), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    return decode_blocks(emissions(np.round(p2, 6), np.round(q2, 6)), period, dec)


def metrics(lab, pred, period):
    """Unrounded values (the gates use them; assemble_v212.py rounds only for display)."""
    s = score(lab, pred, period)
    g, p = pm.label_codes(_with_separators(lab, period)), pm.label_codes(_with_separators(pred, period))
    runs = pm.valid_runs(g)
    gs, ps = pm.possession_spells(g, runs), pm.possession_spells(p, runs)
    hit = pm.matched_gt_flags(pm.spell_overlaps(gs, ps), len(gs), 0.3)
    L = np.array([b - a for a, b, _ in gs])
    Lp = np.array([b - a for a, b, _ in ps])
    return {'spell_f1': float(s['spell_f1_mean']), 'macro_f1': float(s['macro_f1']),
            'trans_f1_12': float(s['trans_f1_12']), 'trans_f1_25': float(s['trans_f1_25']),
            'n_gt_spells': int(len(gs)), 'n_pred_spells': int(len(ps)), 'pred_spells_under_2s': int((Lp < 50).sum()),
            'gt_spells_under_2s': int((L < 50).sum()), 'found_under_2s_iou03': int(hit[L < 50].sum()),
            'gt_spells_under_1s': int((L < 25).sum()), 'found_under_1s_iou03': int(hit[L < 25].sum())}


def both(Tp, base_input, lab, per, check=False):
    """(v2_11 labels, v2_12 labels) on the v2.1 path. Tp: touch columns (both views) of the keeper-corrected tactical
    tracking; base_input: what the base features see (the same tracking, or it with the filled ball)."""
    Xb = features(base_input)[0]; Xbs = features(base_input, swap=True)[0]
    p11 = predict(MODELS['v2.1'][0], MODELS['v2.1'][1], Xb, Xbs, per, DEC21)
    p12 = predict(M12, S12, np.concatenate([Xb, Tp[0]], 1), np.concatenate([Xbs, Tp[1]], 1), per, DEC21)
    if check:      # the comparator is exactly exp_v25.run_path, as in every earlier validation
        ref = run_path('v2.1', base_input, lab, per)
        mine = score(lab, p11, per)
        assert abs(ref[0] - mine['spell_f1_mean']) < 1e-12 and abs(ref[1] - mine['macro_f1']) < 1e-12, (ref, mine)
    return p11, p12


def touch_pair(fixed):
    return touch_features(fixed)[0], touch_features(fixed, swap=True)[0]


def row_for(key, cond, path, Tp, base_input, lab, per, check=False, extra=None):
    t0 = time.time()
    if path == 'v2.3':
        a = run_path('v2.3', base_input, lab, per)
        row = {'copy': key, 'condition': cond, 'path': path,
               'v2_11': {'spell_f1': float(a[0]), 'macro_f1': float(a[1])}, 'v2_12': 'identical (v2.3 path unchanged)'}
        row['diff_spell_f1'], row['diff_macro_f1'] = 0.0, 0.0
    else:
        p11, p12 = both(Tp(), base_input, lab, per, check)
        r11, r12 = metrics(lab, p11, per), metrics(lab, p12, per)
        row = {'copy': key, 'condition': cond, 'path': path, 'v2_11': r11, 'v2_12': r12,
               'diff_spell_f1': r12['spell_f1'] - r11['spell_f1'],
               'diff_macro_f1': r12['macro_f1'] - r11['macro_f1'],
               'frames_changed': int(np.sum(p11 != p12))}
    if extra:
        row.update(extra)
    row['seconds'] = round(time.time() - t0)
    return row


def save(res, OUT):
    tmp = OUT + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(res, f, indent=1)
    os.replace(tmp, OUT)


def packed(dv):
    n = len(dv['ball'])
    P, _ = pack(n, tracklets(dv['players'], dv['team']), SLOT46)
    return dict(dv, players=P, team=SLOT46)


def copy_rows(name, seed, ci, copy_j, res, OUT, done, conditions):
    m, lab = load(name)
    per, fps = m['period'], float(m['fps'])
    graded = per > 0
    blocks = play_blocks(per)
    halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
    T = len(m['ball'])
    rng = np.random.default_rng(seed)
    dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
    key = f'{name}|{seed}'
    mm = packed(dm)
    noise = estimate_noise(mm)
    path, _ = choose_path(noise)                                     # on the tracking as given
    fixed, krep = keeper2.correct_goalkeepers(mm)
    info = {'noise_m': {k: round(float(v), 4) for k, v in noise.items() if isinstance(v, float)},
            'keeper2_moved_pieces': krep.get('moved_pieces'),
            'ball_visible_in_play': round(float(np.isfinite(mm['ball']).all(1)[graded].mean()), 3)}
    first = not res.get('run_path_checked') and path == 'v2.1'
    memo = {}
    Tp = lambda: memo['t'] if 't' in memo else memo.setdefault('t', touch_pair(fixed))   # once per copy, v2.1 path only
    if 'tactical' in conditions and (key, 'tactical') not in done:
        row = row_for(key, 'tactical', path, Tp, fixed, lab, per, check=first, extra=info)
        if first:
            res['run_path_checked'] = key
        res['rows'].append(row); save(res, OUT)
        print(key, 'tactical', path, row['diff_spell_f1'], row['seconds'], 's', flush=True)
    for ri, regime in enumerate(REGIMES):
        cond = f'fill_{regime}'
        if cond not in conditions or (key, cond) in done:
            continue
        t0 = time.time()
        rb = np.random.default_rng(STREAM + 100 * ri + ci)
        q = quality(rb, regime)
        bro, valid, true_t, clock_t = sb3.simulate_warp(m, lab, rb, q)
        rc = np.random.default_rng(CLOCK + 100 * ri + ci)
        pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
        pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
        lags, crep = half_lags(sc.observations(np.arange(T), blocks, fps, rc, pr_t, pm_t),
                               sc.observations(clock_t, blocks, fps, rc, pr_b, pm_b), fps, halves)
        bro2, t_of_b, arep = align_auto(mm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
        reg_ball, rrep = register_ball(bro2, mm, t_of_b, fps)
        fb, frep = fuse_gated(mm['ball'], reg_ball, t_of_b, fps, graded)
        sim_s = round(time.time() - t0)
        gate = {k: frep.get(k) for k in ('used', 'median_distance_m', 'filled', 'ball_visible_graded_before', 'ball_visible_graded_after')}
        base_input = dict(fixed, ball=fb) if frep['used'] else fixed
        row = row_for(key, cond, path, Tp, base_input, lab, per,
                      extra=dict(info, regime=regime, alignment_mode=arep['mode'], gate=gate, simulation_seconds=sim_s,
                                 broadcast_quality={k: round(float(q[k]), 4) for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'invalid')}))
        res['rows'].append(row); save(res, OUT)
        print(key, cond, path, 'gate', gate['used'], row['diff_spell_f1'], row['seconds'] + sim_s, 's', flush=True)
    if 'view42' in conditions and (key, 'view42') not in done:
        dv, vis = apply_view(dm, m, 42.0)
        mv = packed(dv)
        pv, _ = choose_path(estimate_noise(mv))
        fv, kv = keeper2.correct_goalkeepers(mv)
        row = row_for(key, 'view42', pv, lambda: touch_pair(fv), fv, lab, per, extra={'keeper2_moved_pieces': kv.get('moved_pieces')})
        res['rows'].append(row); save(res, OUT)
        print(key, 'view42', pv, row['diff_spell_f1'], row['seconds'], 's', flush=True)


if __name__ == '__main__':
    part = sys.argv[1]
    OUT = f'{V212}exp_v212_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    res['environment'] = {'python': platform.python_version(), 'numpy': np.__version__}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if part == 'reserved':
        copy_rows('MET3', RESERVED_SEED, 8, 0, res, OUT, done, ('tactical', 'fill_good', 'fill_medium', 'view42'))
    elif part == 'smoke':      # wiring check on a TRAINING match (in-sample for both model sets: numbers meaningless)
        copy_rows('J03WOH', 1, 99, 0, res, OUT, done, ('tactical', 'fill_good', 'view42'))
    else:
        i = int(part)
        for j in COPIES_TACTICAL:
            conds = ('tactical',) + (('fill_good', 'fill_medium', 'view42') if j in COPIES_OTHER else ())
            copy_rows(NAMES[i], SEED + 10 * i + j, 2 * i + j, j, res, OUT, done, conds)
    save(res, OUT)
    print('V212DONE', part, flush=True)
