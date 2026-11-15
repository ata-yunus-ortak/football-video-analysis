"""Shared code of the v2.14 work: builds the same copies as exp_v213.copy_rows (same seeds -> same copies) and stores the
per-frame probabilities of both model families, so that fusion rules can be compared without recomputing the models.
Nothing here opens the provided match."""
import sys, os, json, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v213')
import exp_v213 as E
from exp_v213 import (load, degrade, sample_params, RANGES, estimate_noise, choose_path, keeper2, play_blocks, packed, sim2,
                      quality, sb3, sc, half_lags, align_auto, register_ball, fuse_gated, apply_view, tinfer, tdecode, tfuse,
                      v2_validation, v2_released, tcn_arrays, members, WEIGHTS, V2_SIDE, REGIMES, STREAM, CLOCK)

PROBS = '/home/claude/work/v214/probs/'
os.makedirs(PROBS, exist_ok=True)


def inputs(name, seed, ci, conditions, sim2_seed=None):
    """Yield (condition, key, path, base_input, labels, period, info) exactly as exp_v213.copy_rows builds them."""
    m, lab = load(name)
    per, fps = m['period'], float(m['fps'])
    graded = per > 0
    blocks = play_blocks(per)
    halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
    T = len(m['ball'])
    key = f'{name}|{seed}'
    need = [c for c in conditions if c != 'tactical_sim2']
    if need:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
        mm = packed(dm)
        noise = estimate_noise(mm)
        path, _ = choose_path(noise)
        fixed, krep = keeper2.correct_goalkeepers(mm)
        info = {'noise_m': {k: round(float(v), 4) for k, v in noise.items() if isinstance(v, float)},
                'ball_visible_in_play': round(float(np.isfinite(mm['ball']).all(1)[graded].mean()), 3)}
    if 'tactical' in need:
        yield 'tactical', key, path, fixed, lab, per, info
    for ri, regime in enumerate(REGIMES):
        cond = f'fill_{regime}'
        if cond not in need:
            continue
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
        base = dict(fixed, ball=fb) if frep['used'] else fixed
        yield cond, key, path, base, lab, per, dict(info, gate_used=bool(frep['used']))
    if 'view42' in need:
        dv, vis = apply_view(dm, m, 42.0)
        mv = packed(dv)
        pv, _ = choose_path(estimate_noise(mv))
        fv, kv = keeper2.correct_goalkeepers(mv)
        yield 'view42', key, pv, fv, lab, per, {}
    if sim2_seed is not None and 'tactical_sim2' in conditions:
        m2 = packed(sim2(m, sim2_seed))
        n2 = estimate_noise(m2)
        p2, _ = choose_path(n2)
        f2, kr2 = keeper2.correct_goalkeepers(m2)
        yield 'tactical_sim2', f'{name}|{sim2_seed}', p2, f2, lab, per, {
            'noise_m': {k: round(float(v), 4) for k, v in n2.items() if isinstance(v, float)},
            'ball_visible_in_play': round(float(np.isfinite(m2['ball']).all(1)[graded].mean()), 3)}


def model_probs(name, path, base_input, per, weights=None, tcn_input=None):
    """v2 side exactly as exp_v213.row_for; TCN probabilities per play block, upsampled to 25 fps as tcn/fuse.py does."""
    if V2_SIDE[name] == 'validation models':
        p11, pd_, ph = v2_validation(path, base_input, per)
    else:
        p11, pd_, ph = v2_released(path, base_input)
    mem = members(weights or WEIGHTS[name])
    tin = base_input if tcn_input is None else tcn_input
    tcn = np.zeros((len(per), 3), np.float32)
    for a, b in play_blocks(per):
        prob = tinfer.probabilities(mem, *tcn_arrays(tin, a, b))
        tcn[a:b] = tdecode.upsample(np.asarray(prob, np.float64), tinfer.STRIDE, b - a)
    return p11, np.asarray(pd_, np.float64), np.asarray(ph, np.float64), tcn


def strided_features(base_input, per):
    """The TCN's inputs as its forward pass sees them (every second frame, float32), both team orders, per play block."""
    out = {}
    for k, (a, b) in enumerate(play_blocks(per)):
        ball, t0, t1 = tcn_arrays(base_input, a, b)
        out[f'x{k}'] = np.asarray(tinfer.features.build(ball, t0, t1)[0][::tinfer.STRIDE], np.float32)
        out[f'w{k}'] = np.asarray(tinfer.features.build(ball, t1, t0)[0][::tinfer.STRIDE], np.float32)
    return out


def forward_strided(w, x):
    """tcn/infer.py forward() for features that are already strided (same arithmetic)."""
    x = x.astype(np.float64)
    x = tinfer._conv(x, w["stem.weight"], w["stem.bias"])
    block = 0
    while "blocks.%d.conv.weight" % block in w:
        p = "blocks.%d." % block
        h = tinfer._conv(x, w[p + "conv.weight"], w[p + "conv.bias"], int(w[p + "dilation"]))
        h = tinfer._gelu(tinfer._group_norm(h, w[p + "norm.weight"], w[p + "norm.bias"]))
        x = x + tinfer._conv(h, w[p + "mix.weight"], w[p + "mix.bias"])
        block += 1
    logit = tinfer._conv(x, w["head.weight"], w["head.bias"])
    logit -= logit.max(axis=1, keepdims=True)
    e = np.exp(logit)
    return e / e.sum(axis=1, keepdims=True)


def tcn_from_features(mem, feats, per):
    """Per-frame TCN probabilities (25 fps) from stored strided features: infer.probabilities + decode.upsample."""
    tcn = np.zeros((len(per), 3), np.float32)
    for k, (a, b) in enumerate(play_blocks(per)):
        total = 0.0
        for w in mem:
            total = total + forward_strided(w, feats[f'x{k}']) + forward_strided(w, feats[f'w{k}'])[:, [1, 0, 2]]
        prob = np.round(total / (2 * len(mem)), tinfer.PROB_DECIMALS)
        tcn[a:b] = tdecode.upsample(np.asarray(prob, np.float64), tinfer.STRIDE, b - a)
    return tcn


def member_probs(w, feats, per):
    """Unrounded strided probabilities of ONE member (mean of both team orders), per play block."""
    out = {}
    for k, _ in enumerate(play_blocks(per)):
        out[f'p{k}'] = 0.5 * (forward_strided(w, feats[f'x{k}']) + forward_strided(w, feats[f'w{k}'])[:, [1, 0, 2]])
    return out


def ensemble_tcn(files, per):
    """25 fps probabilities of an ensemble from stored member probabilities: mean over members, 4 decimals, upsampled
    (the arithmetic of tcn/infer.probabilities up to the order of the floating-point sums)."""
    mem = [np.load(f) for f in files]
    tcn = np.full((len(per), 3), 1.0 / 3.0)
    for k, (a, b) in enumerate(play_blocks(per)):
        prob = np.round(sum(m[f'p{k}'] for m in mem) / len(mem), tinfer.PROB_DECIMALS)
        tcn[a:b] = tdecode.upsample(prob, tinfer.STRIDE, b - a)
    return tcn


def fname(key, cond, tag=''):
    return PROBS + key.replace('|', '_') + '_' + cond + tag + '.npz'


def cache(name, seed, ci, conditions, sim2_seed=None, tag=''):
    for cond, key, path, base, lab, per, info in inputs(name, seed, ci, conditions, sim2_seed):
        f = fname(key, cond, tag)
        if os.path.exists(f):
            continue
        t0 = time.time()
        p11, pd_, ph, tcn = model_probs(name, path, base, per)
        np.savez_compressed(f, lab=np.asarray(lab), per=per, v2_labels=p11, p_dead=pd_, p_home=ph, tcn=tcn,
                            path=path, info=json.dumps(info), ball_seen=np.isfinite(base['ball'][:, 0]))
        np.savez(f[:-4] + '.feat.npz', **strided_features(base, per))
        print(key, cond, path, round(time.time() - t0), 's', flush=True)
