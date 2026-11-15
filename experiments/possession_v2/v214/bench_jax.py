import time, numpy as np, jax, jax.numpy as jnp
from jax import lax
H, T, B, F = 128, 2048, 16, 37
dil = (1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32)
def conv(x, w, b, d=1):   # x (B, T, C), w (O, I, K)
    y = lax.conv_general_dilated(x, w, (1,), [((w.shape[2] // 2) * d,) * 2], rhs_dilation=(d,), dimension_numbers=('NWC', 'OIW', 'NWC'))
    return y + b
def gn(x, g, s, groups=8, eps=1e-5):
    Bn, Tn, C = x.shape
    z = x.reshape(Bn, Tn, groups, C // groups)
    m = z.mean(axis=(1, 3), keepdims=True); v = ((z - m) ** 2).mean(axis=(1, 3), keepdims=True)
    return ((z - m) / jnp.sqrt(v + eps)).reshape(Bn, Tn, C) * g + s
def net(p, x):
    x = conv(x, p['stem_w'], p['stem_b'])
    for i, d in enumerate(dil):
        h = conv(x, p[f'c{i}_w'], p[f'c{i}_b'], d)
        h = jax.nn.gelu(gn(h, p[f'n{i}_g'], p[f'n{i}_s']), approximate=False)
        x = x + conv(h, p[f'm{i}_w'], p[f'm{i}_b'])
    return conv(x, p['head_w'], p['head_b'])
rng = np.random.default_rng(0)
p = {'stem_w': rng.normal(0, .05, (H, F, 5)), 'stem_b': np.zeros(H), 'head_w': rng.normal(0, .05, (3, H, 1)), 'head_b': np.zeros(3)}
for i in range(len(dil)):
    p.update({f'c{i}_w': rng.normal(0, .05, (H, H, 3)), f'c{i}_b': np.zeros(H), f'n{i}_g': np.ones(H), f'n{i}_s': np.zeros(H),
              f'm{i}_w': rng.normal(0, .05, (H, H, 1)), f'm{i}_b': np.zeros(H)})
p = {k: jnp.asarray(v, jnp.float32) for k, v in p.items()}
def loss(p, x, y):
    lg = net(p, x)
    return -jnp.mean(jnp.take_along_axis(jax.nn.log_softmax(lg), y[..., None], axis=-1))
g = jax.jit(jax.value_and_grad(loss))
x = jnp.asarray(rng.normal(size=(B, T, F)), jnp.float32); y = jnp.asarray(rng.integers(0, 3, (B, T)))
t0 = time.time(); v, gr = g(p, x, y); v.block_until_ready(); print('compile+first', round(time.time() - t0, 1))
t0 = time.time()
for _ in range(3):
    v, gr = g(p, x, y); v.block_until_ready()
print('s/step', round((time.time() - t0) / 3, 2))
