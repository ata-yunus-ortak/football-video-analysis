"""Train the possession model on external matches only, and cross-validate it by match.

    python -m possession.train cache   --dfl DIR --metrica DIR --cache DIR
    python -m possession.train cv      --cache DIR --out DIR      # leave-matches-out
    python -m possession.train final   --cache DIR --out DIR      # all external matches

No file of the competition match is opened by this module.
"""
import argparse
import glob
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from . import data, features
from .degrade import degrade

STRIDE = 2
TRAIN_REPLICAS = 6


def _replica(args):
    half, seed, swap, level = args
    rng = np.random.default_rng(seed)
    ball, team0, team1 = degrade(half["ball"], half["team0"], half["team1"], rng, level)
    label = half["label"]
    if swap:
        team0, team1 = team1, team0
        label = features.swap_labels(label)
    feats, _ = features.build(ball, team0, team1)
    return feats.astype(np.float16), label


def load_matches(dfl_dir, metrica_dir):
    matches = {}
    for path in sorted(glob.glob(os.path.join(dfl_dir, "*.npz"))):
        matches["dfl_" + os.path.basename(path)[:-4]] = data.load_dfl(path)
    if metrica_dir:
        for game in (1, 2):
            matches["metrica_%d" % game] = data.load_metrica_csv(metrica_dir, game)
        matches["metrica_3"] = data.load_metrica_epts(metrica_dir)
    return matches


def build_cache(dfl_dir, metrica_dir, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    matches = load_matches(dfl_dir, metrica_dir)
    jobs, names = [], []
    for m, (name, halves) in enumerate(matches.items()):
        for h, half in enumerate(halves):
            for r in range(TRAIN_REPLICAS):
                jobs.append((half, 1000 * m + 10 * h + r, r % 2 == 1, None))
                names.append("%s_h%d_train%d" % (name, h + 1, r))
            # Fixed evaluation replicas at three severities, original team order.
            for level in (0.2, 0.5, 0.8):
                jobs.append((half, 900000 + 1000 * m + 10 * h + int(level * 10), False, level))
                names.append("%s_h%d_eval%d" % (name, h + 1, int(level * 10)))
    with ProcessPoolExecutor(max_workers=10) as pool:
        for name, (feats, label) in zip(names, pool.map(_replica, jobs, chunksize=1)):
            np.savez(os.path.join(cache_dir, name + ".npz"), x=feats, y=label)
            print(name, feats.shape, flush=True)


def _torch():
    import torch
    return torch


def make_model(hidden=128, dilations=(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32), dropout=0.15):
    """Dilated temporal convolution network: non-causal, so every frame sees past and future.

    At the model rate of 12.5 Hz the receptive field is about +/- 50 s, long enough to carry
    "who had it last" through a loose ball or a long stretch with the ball untracked.
    """
    torch = _torch()
    nn = torch.nn

    class Block(nn.Module):
        def __init__(self, dilation):
            super().__init__()
            self.conv = nn.Conv1d(hidden, hidden, 3, padding=dilation, dilation=dilation)
            self.mix = nn.Conv1d(hidden, hidden, 1)
            self.norm = nn.GroupNorm(8, hidden)
            self.drop = nn.Dropout(dropout)

        def forward(self, x):
            return x + self.mix(self.drop(torch.nn.functional.gelu(self.norm(self.conv(x)))))

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.stem = nn.Conv1d(features.N_FEATURES, hidden, 5, padding=2)
            self.blocks = nn.Sequential(*[Block(d) for d in dilations])
            self.head = nn.Conv1d(hidden, 3, 1)

        def forward(self, x):
            return self.head(self.blocks(self.stem(x.transpose(1, 2)))).transpose(1, 2)

    return Net()


def load_cache(cache_dir, kind):
    out = {}
    for path in sorted(glob.glob(os.path.join(cache_dir, "*_%s*.npz" % kind))):
        blob = np.load(path)
        out[os.path.basename(path)[:-4]] = (blob["x"].astype(np.float32), blob["y"])
    return out


def match_of(name):
    return name.split("_h")[0]


def fit(train_items, epochs, seed, log=print, crop=2048, batch=16):
    torch = _torch()
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = make_model().to(device)
    seqs = [(x[::STRIDE], y[::STRIDE].astype(np.int64)) for x, y in train_items]
    steps = sum(len(x) for x, _ in seqs) // (crop * batch)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=epochs * steps)
    weights = np.array([len(x) for x, _ in seqs], dtype=np.float64)
    weights /= weights.sum()
    for epoch in range(epochs):
        model.train()
        total = 0.0
        for _ in range(steps):
            xs, ys = [], []
            for i in rng.choice(len(seqs), batch, p=weights):
                x, y = seqs[i]
                start = rng.integers(0, len(x) - crop)
                xs.append(x[start:start + crop])
                ys.append(y[start:start + crop])
            xb = torch.from_numpy(np.stack(xs)).to(device)
            yb = torch.from_numpy(np.stack(ys)).to(device)
            loss = torch.nn.functional.cross_entropy(model(xb).reshape(-1, 3), yb.reshape(-1))
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            total += loss.item()
        log("  epoch %d loss %.4f" % (epoch + 1, total / steps))
    return model.cpu()


def predict(model, feats):
    """Class probabilities at the model stride for one half's (T, F) feature matrix."""
    torch = _torch()
    model.eval()
    with torch.no_grad():
        x = torch.from_numpy(np.ascontiguousarray(feats[::STRIDE], dtype=np.float32))[None]
        return torch.softmax(model(x)[0], dim=-1).numpy()


def predict_symmetric(models, feats, feats_swapped):
    """Average over models and over the two team orders (test-time symmetry)."""
    total = 0.0
    for model in models:
        direct = predict(model, feats)
        mirrored = predict(model, feats_swapped)[:, [1, 0, 2]]
        total = total + direct + mirrored
    return total / (2 * len(models))


def run_cv(cache_dir, out_dir, epochs, folds):
    torch = _torch()
    os.makedirs(out_dir, exist_ok=True)
    train = load_cache(cache_dir, "train")
    evals = load_cache(cache_dir, "eval")
    matches = sorted({match_of(name) for name in train})
    for fold in range(folds):
        held = set(matches[fold::folds])
        print("fold %d held out: %s" % (fold, sorted(held)), flush=True)
        items = [value for name, value in train.items() if match_of(name) not in held]
        model = fit(items, epochs, seed=fold)
        torch.save(model.state_dict(), os.path.join(out_dir, "cv_fold%d.pt" % fold))
        for name, (x, y) in evals.items():
            if match_of(name) in held:
                np.savez(os.path.join(out_dir, "oof_" + name + ".npz"), p=predict(model, x), y=y)


def run_final(cache_dir, out_dir, epochs, seeds, exclude=()):
    """Train the shipped models on every cached match whose name has none of the `exclude` prefixes."""
    torch = _torch()
    os.makedirs(out_dir, exist_ok=True)
    train = load_cache(cache_dir, "train")
    used = sorted({match_of(name) for name in train if not match_of(name).startswith(tuple(exclude))})
    print("training matches: %s" % used, flush=True)
    items = [value for name, value in train.items() if match_of(name) in used]
    for seed in range(seeds):
        print("final model seed %d" % seed, flush=True)
        model = fit(items, epochs, seed=100 + seed)
        torch.save(model.state_dict(), os.path.join(out_dir, "model_seed%d.pt" % seed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("cache", "cv", "final"))
    parser.add_argument("--dfl")
    parser.add_argument("--metrica")
    parser.add_argument("--cache", required=True)
    parser.add_argument("--out")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--exclude", nargs="*", default=[], help="match-name prefixes left out of `final`")
    args = parser.parse_args()
    if args.command == "cache":
        build_cache(args.dfl, args.metrica, args.cache)
    elif args.command == "cv":
        run_cv(args.cache, args.out, args.epochs, args.folds)
    else:
        run_final(args.cache, args.out, args.epochs, args.seeds, args.exclude)
