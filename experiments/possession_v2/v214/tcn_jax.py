"""Training of the team member's temporal convolution network (branch mtah-possession, commit 167dc7b, possession/train.py)
re-implemented with JAX for a CPU-only machine, so that leave-one-match-out weights and weights trained on replicas of
BOTH corruption simulators can be made here. Architecture and recipe follow his code: stem conv 5 -> 14 residual blocks
(dilated conv 3, GroupNorm 8, GELU, dropout 0.15, 1x1 conv) -> 1x1 head; 12.5 Hz; crops of 2048 steps, batch 16; AdamW
(weight decay 1e-2), one-cycle learning rate up to 2e-3, gradient clipping 1.0. Differences from his torch code: the Adam
momentum is constant (torch's OneCycleLR also cycles it); initialisation and random streams are JAX/NumPy ones.
The exported .npz has his key layout, so his NumPy inference (tcn/infer.py) runs the weights unchanged.

External matches only (six DFL matches of the Sportec open data). Usage:
  tcn_jax.py cache  MATCH [MATCH ...]                 features of the training replicas (both simulators)
  tcn_jax.py train  TAG SEED EPOCHS SIMS MATCH [...]   SIMS = his | ours | both ; resumable (checkpoint per epoch)
"""
import sys, os, json, time, pickle, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v213'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/sc')

V214 = '/home/claude/work/v214/'
CACHE = V214 + 'tcn_cache/'
OUT = V214 + 'tcn_weights/'
STRIDE, CROP, BATCH, HIDDEN, DROPOUT = 2, 2048, 16, 128, 0.15
DILATIONS = (1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32)
REPLICAS = 6                       # per simulator, per half (his TRAIN_REPLICAS); odd replicas have the teams exchanged
MATCHES = ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ', 'J03WN1', 'J03WR9']
CODE = {'H': 0, 'A': 1, 'D': 2}


def build_cache(names):
    from harness import load
    from possession.degrade import degrade, sample_params, RANGES
    from possession.features import play_blocks
    from exp_v213 import tcn_arrays
    from tcn import features as tf, degrade as td
    os.makedirs(CACHE, exist_ok=True)
    for name in names:
        mi = MATCHES.index(name)
        m, lab = load(name)
        y_all = np.array([CODE[c] for c in np.asarray(lab)], np.int8)
        blocks = play_blocks(m['period'])
        for r in range(REPLICAS):
            swap = r % 2 == 1
            # --- his simulator: every half on its own (his seeds: 1000 * match + 10 * half + replica)
            for h, (a, b) in enumerate(blocks):
                f = f'{CACHE}{name}_h{h + 1}_his{r}.npz'
                if not os.path.exists(f):
                    rng = np.random.default_rng(1000 * mi + 10 * h + r)
                    ball, t0, t1 = td.degrade(*tcn_arrays(m, a, b), rng, None)
                    y = y_all[a:b]
                    if swap:
                        t0, t1 = t1, t0; y = tf.swap_labels(y)
                    x, _ = tf.build(ball, t0, t1)
                    np.savez(f, x=x[::STRIDE].astype(np.float16), y=y[::STRIDE])
            # --- our simulator: the whole match at once (v2 profile; seed 500000 + 1000 * match + replica), labels modulate
            #     the dead-ball missingness as in every v2 training copy
            fs = [f'{CACHE}{name}_h{h + 1}_ours{r}.npz' for h in range(len(blocks))]
            if not all(os.path.exists(f) for f in fs):
                rng = np.random.default_rng(500000 + 1000 * mi + r)
                dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
                for h, (a, b) in enumerate(blocks):
                    ball, t0, t1 = tcn_arrays(dm, a, b)
                    y = y_all[a:b]
                    if swap:
                        t0, t1 = t1, t0; y = tf.swap_labels(y)
                    x, _ = tf.build(ball, t0, t1)
                    np.savez(fs[h], x=x[::STRIDE].astype(np.float16), y=y[::STRIDE])
            print(name, 'replica', r, 'done', flush=True)


def init_params(key):
    import jax
    def conv_init(k, o, i, ks):
        bound = 1.0 / np.sqrt(i * ks)          # torch Conv1d default (kaiming_uniform with a = sqrt(5)) and its bias bound
        k1, k2 = jax.random.split(k)
        return (jax.random.uniform(k1, (o, i, ks), minval=-bound, maxval=bound), jax.random.uniform(k2, (o,), minval=-bound, maxval=bound))
    keys = jax.random.split(key, 2 + 2 * len(DILATIONS))
    p = {}
    p['stem.weight'], p['stem.bias'] = conv_init(keys[0], HIDDEN, 37, 5)
    p['head.weight'], p['head.bias'] = conv_init(keys[1], 3, HIDDEN, 1)
    for i in range(len(DILATIONS)):
        p[f'blocks.{i}.conv.weight'], p[f'blocks.{i}.conv.bias'] = conv_init(keys[2 + 2 * i], HIDDEN, HIDDEN, 3)
        p[f'blocks.{i}.mix.weight'], p[f'blocks.{i}.mix.bias'] = conv_init(keys[3 + 2 * i], HIDDEN, HIDDEN, 1)
        p[f'blocks.{i}.norm.weight'] = np.ones(HIDDEN, np.float32); p[f'blocks.{i}.norm.bias'] = np.zeros(HIDDEN, np.float32)
    import jax.numpy as jnp
    return {k: jnp.asarray(v, jnp.float32) for k, v in p.items()}


def make_fns():
    import jax, jax.numpy as jnp
    from jax import lax

    def conv(x, w, b, d=1):                       # x (B, T, C_in), w (C_out, C_in, K): zero 'same' padding as torch
        pad = (w.shape[2] // 2) * d
        return lax.conv_general_dilated(x, w, (1,), [(pad, pad)], rhs_dilation=(d,), dimension_numbers=('NWC', 'OIW', 'NWC')) + b

    def group_norm(x, g, s, groups=8, eps=1e-5):   # torch GroupNorm: statistics per sample over the group's channels and time
        B, T, C = x.shape
        z = x.reshape(B, T, groups, C // groups)
        mean = z.mean(axis=(1, 3), keepdims=True)
        var = ((z - mean) ** 2).mean(axis=(1, 3), keepdims=True)
        return ((z - mean) / jnp.sqrt(var + eps)).reshape(B, T, C) * g + s

    def net(p, x, key, train):
        x = conv(x, p['stem.weight'], p['stem.bias'])
        keys = jax.random.split(key, len(DILATIONS))
        for i, d in enumerate(DILATIONS):
            h = conv(x, p[f'blocks.{i}.conv.weight'], p[f'blocks.{i}.conv.bias'], d)
            h = jax.nn.gelu(group_norm(h, p[f'blocks.{i}.norm.weight'], p[f'blocks.{i}.norm.bias']), approximate=False)
            if train:
                keep = jax.random.bernoulli(keys[i], 1.0 - DROPOUT, h.shape)
                h = jnp.where(keep, h / (1.0 - DROPOUT), 0.0)
            x = x + conv(h, p[f'blocks.{i}.mix.weight'], p[f'blocks.{i}.mix.bias'])
        return conv(x, p['head.weight'], p['head.bias'])

    def loss(p, x, y, key):
        lg = net(p, x, key, True)
        return -jnp.mean(jnp.take_along_axis(jax.nn.log_softmax(lg, axis=-1), y[..., None], axis=-1))

    return net, loss


def load_items(names, sims):
    import glob
    items = []
    kinds = {'his': ('his',), 'ours': ('ours',), 'both': ('his', 'ours')}[sims]
    for name in names:
        for kind in kinds:
            fs = sorted(glob.glob(f'{CACHE}{name}_h*_{kind}*.npz'))
            assert len(fs) == 2 * REPLICAS, (name, kind, len(fs))
            for f in fs:
                d = np.load(f)
                items.append((d['x'].astype(np.float32), d['y'].astype(np.int32)))
    return items


def export(params, path):
    arrays = {}
    for k, v in params.items():
        arrays['m0/' + k] = np.asarray(v, np.float32)
    for b, d in enumerate(DILATIONS):
        arrays['m0/blocks.%d.dilation' % b] = np.int64(d)
    np.savez_compressed(path, **arrays)


def train(tag, seed, epochs, sims, names, steps_scale=1.0):
    import jax, jax.numpy as jnp, optax
    os.makedirs(OUT, exist_ok=True)
    items = load_items(names, sims)
    steps = int(sum(len(x) for x, _ in items) // (CROP * BATCH) * steps_scale)
    total = epochs * steps
    sched = optax.cosine_onecycle_schedule(total, 2e-3, pct_start=0.3, div_factor=25.0, final_div_factor=1e4)
    opt = optax.chain(optax.clip_by_global_norm(1.0), optax.adamw(sched, b1=0.9, b2=0.999, eps=1e-8, weight_decay=1e-2))
    net, loss = make_fns()

    @jax.jit
    def step(p, s, x, y, key):
        v, g = jax.value_and_grad(loss)(p, x, y, key)
        u, s = opt.update(g, s, p)
        return optax.apply_updates(p, u), s, v

    ck = f'{OUT}{tag}.ckpt'
    if os.path.exists(ck):
        st = pickle.load(open(ck, 'rb'))
        params = {k: jnp.asarray(v) for k, v in st['params'].items()}
        opt_state = jax.tree_util.tree_map(lambda a: jnp.asarray(a) if isinstance(a, np.ndarray) else a, st['opt_state'])
        ep0 = st['epoch']; rng = np.random.default_rng(); rng.bit_generator.state = st['rng']; key = jnp.asarray(st['key'])
        print('resumed', tag, 'after epoch', ep0, flush=True)
    else:
        key = jax.random.PRNGKey(seed)
        key, k0 = jax.random.split(key)
        params = init_params(k0); opt_state = opt.init(params); ep0 = 0; rng = np.random.default_rng(seed)
    w = np.array([len(x) for x, _ in items], np.float64); w /= w.sum()
    log = open(f'{OUT}{tag}.log', 'a')
    for ep in range(ep0, epochs):
        t0 = time.time(); tot = 0.0
        for _ in range(steps):
            xs, ys = [], []
            for i in rng.choice(len(items), BATCH, p=w):
                x, y = items[i]
                s0 = int(rng.integers(0, len(x) - CROP))
                xs.append(x[s0:s0 + CROP]); ys.append(y[s0:s0 + CROP])
            key, kk = jax.random.split(key)
            params, opt_state, v = step(params, opt_state, jnp.asarray(np.stack(xs)), jnp.asarray(np.stack(ys)), kk)
            tot += float(v)
        msg = f'{tag} epoch {ep + 1}/{epochs} loss {tot / steps:.4f} steps {steps} {round(time.time() - t0)} s'
        print(msg, flush=True); log.write(msg + '\n'); log.flush()
        tmp = ck + '.tmp'
        pickle.dump({'params': {k: np.asarray(v) for k, v in params.items()},
                     'opt_state': jax.tree_util.tree_map(lambda a: np.asarray(a) if hasattr(a, 'shape') else a, opt_state),
                     'epoch': ep + 1, 'rng': rng.bit_generator.state, 'key': np.asarray(key)}, open(tmp, 'wb'))
        os.replace(tmp, ck)
    export(params, f'{OUT}{tag}.npz')
    json.dump({'tag': tag, 'seed': seed, 'epochs': epochs, 'simulators': sims, 'matches': names, 'steps_per_epoch': steps,
               'replicas_per_simulator_per_half': REPLICAS}, open(f'{OUT}{tag}.json', 'w'), indent=1)
    print('TRAINED', tag, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'cache':
        build_cache(sys.argv[2:])
    else:
        train(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6:])
