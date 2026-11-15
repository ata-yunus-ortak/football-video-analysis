"""v2.13 validation (possession-v213-plan.json): possession-v2.11 vs the fusion of its second-stage probabilities with a
temporal convolution network (teammate's model; repository branch mtah-possession, commit 167dc7b; byte copies of its
inference modules under v213/tcn/) on 16 new corrupted copies of the four validation matches (DFL J03WN1, J03WR9;
Metrica sample games 1, 2). Tracks are packed into 46 anonymous slots as in the provided file; the noise gate is
decided on the tracking as given and the v2.11 goalkeeper team correction (possession/keeper2.py) is applied, as in
the release entry point.

Conditions (as in the v2.12 validation, exp_v212.py)
  tactical      copies j = 0..3 of each match (16): tactical camera only                         -> gates G1-G5
  fill_good     copies j = 0, 1 (8): simulated broadcast camera (synth_broadcast3 warp simulator, regime 'good' /
  fill_medium   'medium' of exp_v25), simulated clock readings, clock-anchored alignment, player registration and
                the 0.50 m gate exactly as possession.run211; when the gate opens both models see the filled ball
                                                                                                    -> gate G6
  view42        copies j = 0, 1 (8): camera window of +-42 m around the centre of play (camera_view.py), tactical
                camera only                                                                         -> reported
  tactical_sim2 one copy per match made with the teammate's corruption simulator (tcn/degrade.py, per half, random
                severity; no ball height in our prepared data, so its height term is inactive)       -> reported
Systems
  v2_11  on the DFL matches: validation models of the release paths (cache/models_v2.pkl + stack_v2.pkl, v2.3 path
         models_v23.pkl + stack_v23.pkl with +-2 frame smoothing; trained on J03WOH, J03WOY, J03WPY, J03WQQ), line by
         line as exp_v25.run_path. On the Metrica games: the released bundles (models/possession-v2.npz,
         possession-v23.npz; six DFL matches) through possession.pipeline.predict_labels, as possession.run211.
  fused  tcn/fuse.py, nothing chosen here: the v2_11 side's second-stage P(dead), P(home | alive) (6 decimals, as given
         to its own decoder; on the v2.3 path from the smoothed input) become [home, away, dead]; the TCN's
         probabilities (tcn/infer.py: mean over ensemble members and both team orders, 4 decimals, 12.5 Hz) are
         linearly interpolated to 25 fps; arithmetic mean with weight 0.5; one Viterbi pass per play block with switch
         cost 6 for every state change. The v2.11 decoder is not used. TCN input: the tracking the v2 models see
         (goalkeeper-corrected, with the filled ball when the gate opened), never smoothed, in metres from the pitch
         centre, NaN where missing. TCN weights: tcn_dfl5_without_J03WN1.npz / tcn_dfl5_without_J03WR9.npz on those
         matches (five DFL matches, one seed), tcn_dfl6.npz on the Metrica games (six DFL matches, three seeds).
  tcn_alone  the TCN's probabilities through its own decoder (tcn/decode.py, switch cost 6)        -> reported
Seeds: copy seed 13100 + 10 * match_index + j (degrade v2 profile, parameters sampled from the seed as exp_v211);
broadcast stream 43100 + 100 * regime_index + 2 * match_index + j; clock readings 53100 + 100 * regime_index +
2 * match_index + j; teammate's simulator 63100 + match_index; reserved Metrica game 3 (after the decision,
reported): copy seed 33103, copy index 8, teammate's simulator 63108.
Usage: /usr/bin/python3 exp_v213.py PART     PART = 0 | 1 | 2 | 3 (validation match index) | reserved | smoke
(smoke: wiring check on training match J03WOH, training seed 1, in-sample for every model; it computes NO score)
"""
import sys, json, time, os, platform, hashlib, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/work/v213')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.noise import estimate_noise, choose_path
from possession.smooth import smooth_positions
from possession.features import features, play_blocks
from possession.stack import stack_features
from possession.decode import emissions, decode_blocks
from possession.evaluate import score, _with_separators
from possession import official_metrics as pm
from possession import keeper2
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.run24 import V21_MODEL, V23_MODEL
from possession.epts_export import tracklets, pack
from possession.fusion import fuse_gated, align_auto
from possession.register import register_ball
from possession.clocksync import half_lags
from exp_v25 import run_path, quality, MODELS, PATHS
from exp_v210 import SLOT46
from camera_view import apply_view
import synth_broadcast3 as sb3
import synth_clock as sc
from tcn import infer as tinfer, fuse as tfuse, decode as tdecode, degrade as tdegrade

NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
SEED, STREAM, CLOCK, SIM2, RESERVED_SEED = 13100, 43100, 53100, 63100, 33103
REGIMES = ('good', 'medium')            # names of exp_v25.REGIMES
COPIES_TACTICAL, COPIES_OTHER = (0, 1, 2, 3), (0, 1)
V213 = '/home/claude/work/v213/'
WEIGHTS = {'J03WN1': 'tcn_dfl5_without_J03WN1.npz', 'J03WR9': 'tcn_dfl5_without_J03WR9.npz',
           'MET1': 'tcn_dfl6.npz', 'MET2': 'tcn_dfl6.npz', 'MET3': 'tcn_dfl6.npz', 'J03WOH': 'tcn_dfl6.npz'}
V2_SIDE = {'J03WN1': 'validation models', 'J03WR9': 'validation models', 'J03WOH': 'validation models',
           'MET1': 'released bundles', 'MET2': 'released bundles', 'MET3': 'released bundles'}
LETTERS = np.array(['H', 'A', 'D'])
_TCN, _BUNDLE = {}, {}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def members(name):
    if name not in _TCN:
        _TCN[name] = tinfer.load_weights(V213 + 'weights/' + name)
    return _TCN[name]


def bundle(path):
    if path not in _BUNDLE:
        _BUNDLE[path] = load_bundle(V21_MODEL if path == 'v2.1' else V23_MODEL)
    return _BUNDLE[path]


def v2_validation(path, m_in, period):
    """Validation models, line by line exp_v25.run_path. Returns (labels, P(dead), P(home | alive)): the second-stage
    probabilities rounded to 6 decimals, exactly what the v2.11 decoder is given."""
    (md, mh), (sd, sh) = MODELS[path]
    m_ = smooth_positions(m_in, 2) if path == 'v2.3' else m_in
    X, _ = features(m_); Xs, _ = features(m_, swap=True)
    ok = np.isfinite(X).any(1)
    p1 = np.full(len(X), .5); q1 = np.full(len(X), .5)
    p1[ok] = .5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    q1[ok] = .5 * (mh.predict_proba(X[ok])[:, 1] + 1 - mh.predict_proba(Xs[ok])[:, 1])
    del X, Xs
    S = [stack_features(p1, q1, period, swap=sw)[0] for sw in (False, True)]
    ok2 = np.isfinite(S[0][:, 0])
    p2 = np.full(len(p1), .5); q2 = np.full(len(p1), .5)
    p2[ok2] = .5 * (sd.predict_proba(S[0][ok2])[:, 1] + sd.predict_proba(S[1][ok2])[:, 1])
    q2[ok2] = .5 * (sh.predict_proba(S[0][ok2])[:, 1] + 1 - sh.predict_proba(S[1][ok2])[:, 1])
    p2, q2 = np.round(p2, 6), np.round(q2, 6)
    return decode_blocks(emissions(p2, q2), period, PATHS[path][2]), p2, q2


def v2_released(path, m_in):
    """Released bundles through the frozen pipeline, as possession.run211 after the noise gate."""
    b = bundle(path)
    m_ = smooth_positions(m_in, int(bundle('v2.3')['card']['smooth_half'])) if path == 'v2.3' else m_in
    return predict_labels(m_, b)


def tcn_arrays(m_in, a, b):
    """Tracking of frames a..b-1 as the TCN expects it: metres from the pitch centre, float32, NaN where missing."""
    c = np.asarray(m_in['pitch'], np.float64) / 2.0
    team = np.asarray(m_in['team'])
    P = np.asarray(m_in['players'][a:b], np.float64)
    ball = (np.asarray(m_in['ball'][a:b], np.float64)[:, :2] - c).astype(np.float32)
    return ball, (P[:, team == 0] - c).astype(np.float32), (P[:, team == 1] - c).astype(np.float32)


def tcn_labels(mem, m_in, period, p_dead, p_home):
    """(fused labels, TCN-alone labels); every play block is fused and decoded on its own, D outside."""
    fused = np.full(len(period), 'D', dtype='<U1'); alone = fused.copy()
    for a, b in play_blocks(period):
        prob = tinfer.probabilities(mem, *tcn_arrays(m_in, a, b))
        fused[a:b] = LETTERS[tfuse.fuse(prob, p_dead[a:b], p_home[a:b])]
        alone[a:b] = LETTERS[tdecode.decode(prob, tfuse.SWITCH_COST, tinfer.STRIDE, b - a)]
    return fused, alone


def metrics(lab, pred, period):
    """Unrounded values (the gates use them; assemble_v213.py rounds only for display)."""
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


def row_for(name, key, cond, path, base_input, lab, per, check=False, extra=None, with_scores=True):
    t0 = time.time()
    if V2_SIDE[name] == 'validation models':
        p11, pd_, ph = v2_validation(path, base_input, per)
    else:
        p11, pd_, ph = v2_released(path, base_input)
    t1 = time.time()
    fus, alone = tcn_labels(members(WEIGHTS[name]), base_input, per, pd_, ph)
    row = {'copy': key, 'condition': cond, 'path': path, 'v2_side': V2_SIDE[name], 'tcn_weights': WEIGHTS[name]}
    play = per > 0
    if with_scores:
        r11, rf, ra = metrics(lab, p11, per), metrics(lab, fus, per), metrics(lab, alone, per)
        if check:      # the v2_11 arm with validation models is exactly exp_v25.run_path, as in every earlier validation
            ref = run_path(path, base_input, lab, per)
            assert abs(ref[0] - r11['spell_f1']) < 1e-12 and abs(ref[1] - r11['macro_f1']) < 1e-12, (ref, r11)
        row.update(v2_11=r11, fused=rf, tcn_alone=ra, diff_spell_f1=rf['spell_f1'] - r11['spell_f1'],
                   diff_macro_f1=rf['macro_f1'] - r11['macro_f1'])
    else:              # smoke: wiring only, nothing is compared with labels
        assert set(np.unique(fus)) <= {'H', 'A', 'D'} and set(np.unique(alone)) <= {'H', 'A', 'D'}
        assert (fus[~play] == 'D').all() and len(fus) == len(p11) == len(per)
        row.update(label_shares_in_play={k: {c: round(float(np.mean(v[play] == c)), 3) for c in 'HAD'}
                                         for k, v in (('v2_11', p11), ('fused', fus), ('tcn_alone', alone))})
    row['frames_changed'] = int(np.sum(p11 != fus))
    if extra:
        row.update(extra)
    row['seconds_v2'], row['seconds_tcn'] = round(t1 - t0), round(time.time() - t1)
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


def sim2(m, seed):
    """Copy made with the teammate's simulator: every play block on its own, in his coordinates; no tracking outside
    the blocks (nothing there is used)."""
    rng = np.random.default_rng(seed)
    c = (np.asarray(m['pitch'], np.float64) / 2.0).astype(np.float32)
    team = np.asarray(m['team'])
    B = np.full(m['ball'].shape, np.nan, np.float32); P = np.full(m['players'].shape, np.nan, np.float32)
    for a, b in play_blocks(m['period']):
        xy, d0, d1 = tdegrade.degrade(*tcn_arrays(m, a, b), rng)
        B[a:b, :2] = xy + c
        blk = P[a:b]
        blk[:, team == 0] = d0 + c
        blk[:, team == 1] = d1 + c
    return dict(m, ball=B, players=P)


def copy_rows(name, seed, ci, res, OUT, done, conditions, with_scores=True, sim2_seed=None):
    m, lab = load(name)
    per, fps = m['period'], float(m['fps'])
    graded = per > 0
    blocks = play_blocks(per)
    halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
    T = len(m['ball'])
    key = f'{name}|{seed}'
    need = [c for c in conditions if (key, c) not in done]
    if need:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
        mm = packed(dm)
        noise = estimate_noise(mm)
        path, _ = choose_path(noise)                                     # on the tracking as given
        fixed, krep = keeper2.correct_goalkeepers(mm)
        info = {'noise_m': {k: round(float(v), 4) for k, v in noise.items() if isinstance(v, float)},
                'keeper2_moved_pieces': krep.get('moved_pieces'),
                'ball_visible_in_play': round(float(np.isfinite(mm['ball']).all(1)[graded].mean()), 3)}
    if 'tactical' in need:
        first = with_scores and not res.get('run_path_checked') and V2_SIDE[name] == 'validation models'
        row = row_for(name, key, 'tactical', path, fixed, lab, per, check=first, extra=info, with_scores=with_scores)
        if first:
            res['run_path_checked'] = key
        res['rows'].append(row); save(res, OUT)
        print(key, 'tactical', path, row.get('diff_spell_f1'), row['seconds_v2'], row['seconds_tcn'], 's', flush=True)
    for ri, regime in enumerate(REGIMES):
        cond = f'fill_{regime}'
        if cond not in need:
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
        row = row_for(name, key, cond, path, base_input, lab, per, with_scores=with_scores,
                      extra=dict(info, regime=regime, alignment_mode=arep['mode'], gate=gate, simulation_seconds=sim_s,
                                 broadcast_quality={k: round(float(q[k]), 4) for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'invalid')}))
        res['rows'].append(row); save(res, OUT)
        print(key, cond, path, 'gate', gate['used'], row.get('diff_spell_f1'), row['seconds_v2'], row['seconds_tcn'], sim_s, 's', flush=True)
    if 'view42' in need:
        dv, vis = apply_view(dm, m, 42.0)
        mv = packed(dv)
        pv, _ = choose_path(estimate_noise(mv))
        fv, kv = keeper2.correct_goalkeepers(mv)
        row = row_for(name, key, 'view42', pv, fv, lab, per, with_scores=with_scores,
                      extra={'keeper2_moved_pieces': kv.get('moved_pieces')})
        res['rows'].append(row); save(res, OUT)
        print(key, 'view42', pv, row.get('diff_spell_f1'), row['seconds_v2'], row['seconds_tcn'], 's', flush=True)
    if sim2_seed is not None and (f'{name}|{sim2_seed}', 'tactical_sim2') not in done:
        k2 = f'{name}|{sim2_seed}'
        m2 = packed(sim2(m, sim2_seed))
        n2 = estimate_noise(m2)
        p2, _ = choose_path(n2)
        f2, kr2 = keeper2.correct_goalkeepers(m2)
        row = row_for(name, k2, 'tactical_sim2', p2, f2, lab, per, with_scores=with_scores,
                      extra={'noise_m': {k: round(float(v), 4) for k, v in n2.items() if isinstance(v, float)},
                             'keeper2_moved_pieces': kr2.get('moved_pieces'),
                             'ball_visible_in_play': round(float(np.isfinite(m2['ball']).all(1)[graded].mean()), 3)})
        res['rows'].append(row); save(res, OUT)
        print(k2, 'tactical_sim2', p2, row.get('diff_spell_f1'), row['seconds_v2'], row['seconds_tcn'], 's', flush=True)


if __name__ == '__main__':
    import pandas, sklearn
    part = sys.argv[1]
    OUT = f'{V213}exp_v213_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    res['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__,
                          'scikit_learn': sklearn.__version__}
    res['fusion'] = {'weight': tfuse.WEIGHT, 'switch_cost': tfuse.SWITCH_COST, 'stride': tinfer.STRIDE,
                     'prob_decimals': tinfer.PROB_DECIMALS}
    res['sha256'] = {'weights': {w: sha(V213 + 'weights/' + w) for w in sorted(set(WEIGHTS.values()))},
                     'tcn_modules': {f: sha(V213 + 'tcn/' + f) for f in ('infer.py', 'features.py', 'decode.py', 'fuse.py', 'degrade.py')},
                     'exp_v213.py': sha(V213 + 'exp_v213.py')}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if part == 'reserved':
        copy_rows('MET3', RESERVED_SEED, 8, res, OUT, done, ('tactical', 'fill_good', 'fill_medium', 'view42'), sim2_seed=SIM2 + 8)
    elif part == 'smoke':      # wiring check on a TRAINING match, in-sample for every model; no score is computed
        copy_rows('J03WOH', 1, 99, res, OUT, done, ('tactical', 'fill_good', 'view42'), with_scores=False, sim2_seed=99)
        # the code paths the copy above did not take: the v2.3 path of both model sets and the released bundles
        m, lab = load('J03WOH')
        rng = np.random.default_rng(1)
        fixed, _ = keeper2.correct_goalkeepers(packed(degrade(m, lab, rng, sample_params(rng, ranges=RANGES))))
        for side, path in (('validation models', 'v2.3'), ('released bundles', 'v2.1'), ('released bundles', 'v2.3')):
            key = f'J03WOH|1|forced {side} {path}'
            if (key, 'tactical') in done:
                continue
            V2_SIDE['J03WOH'] = side
            row = row_for('J03WOH', key, 'tactical', path, fixed, lab, m['period'], with_scores=False)
            res['rows'].append(row); save(res, OUT)
            print(key, row['frames_changed'], row['seconds_v2'], row['seconds_tcn'], 's', flush=True)
    else:
        i = int(part)
        for j in COPIES_TACTICAL:
            conds = ('tactical',) + (('fill_good', 'fill_medium', 'view42') if j in COPIES_OTHER else ())
            copy_rows(NAMES[i], SEED + 10 * i + j, 2 * i + j, res, OUT, done, conds, sim2_seed=(SIM2 + i) if j == 0 else None)
    save(res, OUT)
    print('V213DONE', part, flush=True)
