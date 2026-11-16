"""Train the TCN (architecture of commit 167dc7b, unchanged) on the v216u cache. Run from football-video-analysis.
Usage: train216.py TAG SEED EPOCHS DROPOUT MATCH [MATCH ...]"""
import sys, glob, os, time, numpy as np, torch
from possession.train import make_model
from possession import infer
C = '/Users/umut/BARCELONA/work/v216u/'
tag, seed, epochs, dropout = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
YFLIP = '_b_' in tag            # variant b: mirror the pitch across its long axis in half of the crops
YCOLS = [2, 17, 27]             # ball y, mean y of team 0, mean y of team 1
matches = sys.argv[5:]
CROP, BATCH = 2048, 16
seqs = []
for m in matches:
    for f in sorted(glob.glob(f'{C}cache{os.environ.get("FEAT", "")}/{m}_h*_*.npz')):
        b = np.load(f); seqs.append((b['x'].astype(np.float32), b['y'].astype(np.int64)))
print(tag, 'sequences', len(seqs), flush=True)
torch.manual_seed(seed); rng = np.random.default_rng(seed)
dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
model = make_model(hidden=int(os.environ.get('HIDDEN', 128)), dropout=dropout)
if seqs[0][0].shape[1] != model.stem.in_channels:
    model.stem = torch.nn.Conv1d(seqs[0][0].shape[1], model.stem.out_channels, 5, padding=2)
model = model.to(dev)
steps = sum(len(x) for x, _ in seqs) // (CROP * BATCH)
opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=epochs * steps)
w = np.array([len(x) for x, _ in seqs], float); w /= w.sum()
t0 = time.time()
for ep in range(epochs):
    model.train(); tot = 0.0
    for _ in range(steps):
        xs, ys = [], []
        for i in rng.choice(len(seqs), BATCH, p=w):
            x, y = seqs[i]; s = rng.integers(0, len(x) - CROP)
            c = x[s:s + CROP]
            if YFLIP and rng.random() < 0.5:
                c = c.copy(); c[:, YCOLS] *= -1
            xs.append(c); ys.append(y[s:s + CROP])
        xb = torch.from_numpy(np.stack(xs)).to(dev); yb = torch.from_numpy(np.stack(ys)).to(dev)
        loss = torch.nn.functional.cross_entropy(model(xb).reshape(-1, 3), yb.reshape(-1))
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step()
        tot += loss.item()
    print('  epoch %d loss %.4f  %ds' % (ep + 1, tot / steps, time.time() - t0), flush=True)
pt = f'{C}weights/{tag}.pt'
torch.save(model.cpu().state_dict(), pt)
infer.export(pt, f'{C}weights/{tag}.npz'); os.remove(pt)
print('wrote', tag, flush=True)
