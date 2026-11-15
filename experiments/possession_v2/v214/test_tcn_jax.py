import sys, numpy as np, tempfile, os
sys.path.insert(0, '/home/claude/work/v213')
import jax, jax.numpy as jnp
import tcn_jax as T
from tcn import infer
key = jax.random.PRNGKey(3)
p = T.init_params(key)
# make norm params non-trivial
p = {k: (v * 1.3 + 0.1 if 'norm' in k else v) for k, v in p.items()}
net, loss = T.make_fns()
rng = np.random.default_rng(0)
feats = rng.normal(size=(5001, 37)).astype(np.float32)          # 25 fps features
x = jnp.asarray(feats[::2])[None]
prob_jax = np.asarray(jax.nn.softmax(net(p, x, key, False)[0], axis=-1), np.float64)
d = tempfile.mkdtemp(); f = os.path.join(d, 'w.npz'); T.export(p, f)
w = infer.load_weights(f)
prob_np = infer.forward(w[0], feats)
print('shapes', prob_jax.shape, prob_np.shape, 'max abs diff', float(np.abs(prob_jax - prob_np).max()))
# gradient sanity: loss decreases on a repeated tiny batch
import optax
opt = optax.adam(1e-3); s = opt.init(p)
xb = jnp.asarray(rng.normal(size=(2, 256, 37)), jnp.float32); yb = jnp.asarray(rng.integers(0, 3, (2, 256)))
g = jax.jit(jax.value_and_grad(loss))
l0 = None
for i in range(30):
    v, gr = g(p, xb, yb, jax.random.PRNGKey(i))
    u, s = opt.update(gr, s); p = optax.apply_updates(p, u)
    l0 = l0 or float(v)
print('loss first', round(l0, 4), 'last', round(float(v), 4))
