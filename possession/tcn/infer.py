"""Dependency-light inference for the possession network: NumPy only, float64, CPU.

Training uses PyTorch (possession.train); the shipped weights are exported to one .npz and run
here, so regenerating the submission needs nothing but NumPy. Probabilities are rounded to
PROB_DECIMALS before decoding: last-bit differences between BLAS builds or operating systems
then cannot move a decision unless a value sits exactly on a rounding boundary.

    python -m possession.infer export --models MODEL_DIR --out possession/weights/tcn.npz
"""
import argparse
import glob
import os

import numpy as np

from . import features

STRIDE = 2            # the network runs at 12.5 Hz on 25 fps tracking
GROUPS = 8
PROB_DECIMALS = 4


def _erf(x):
    # Abramowitz & Stegun 7.1.26, |error| < 1.5e-7; plain arithmetic so it is the same everywhere.
    sign = np.sign(x)
    x = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * x)
    poly = ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t
    return sign * (1.0 - poly * np.exp(-x * x))


def _gelu(x):
    return 0.5 * x * (1.0 + _erf(x / np.sqrt(2.0)))


def _conv(x, weight, bias, dilation=1):
    """x (T, C_in); weight (C_out, C_in, K) as stored by torch Conv1d; zero 'same' padding."""
    taps = weight.shape[2]
    half = (taps // 2) * dilation
    padded = np.zeros((len(x) + 2 * half, x.shape[1]))
    padded[half:half + len(x)] = x
    out = np.zeros((len(x), weight.shape[0]))
    for k in range(taps):
        out += padded[k * dilation:k * dilation + len(x)] @ weight[:, :, k].T
    return out + bias


def _group_norm(x, gain, shift, eps=1e-5):
    """torch GroupNorm on (C, T): statistics over each group's channels and the whole sequence."""
    n, c = x.shape
    g = x.reshape(n, GROUPS, c // GROUPS)
    mean = g.mean(axis=(0, 2), keepdims=True)
    var = ((g - mean) ** 2).mean(axis=(0, 2), keepdims=True)
    return ((g - mean) / np.sqrt(var + eps)).reshape(n, c) * gain + shift


def forward(w, feats):
    """Class probabilities (T', 3) at the model stride for one (T, F) feature matrix."""
    x = np.asarray(feats[::STRIDE], dtype=np.float32).astype(np.float64)
    x = _conv(x, w["stem.weight"], w["stem.bias"])
    block = 0
    while "blocks.%d.conv.weight" % block in w:
        p = "blocks.%d." % block
        h = _conv(x, w[p + "conv.weight"], w[p + "conv.bias"], int(w[p + "dilation"]))
        h = _gelu(_group_norm(h, w[p + "norm.weight"], w[p + "norm.bias"]))
        x = x + _conv(h, w[p + "mix.weight"], w[p + "mix.bias"])
        block += 1
    logit = _conv(x, w["head.weight"], w["head.bias"])
    logit -= logit.max(axis=1, keepdims=True)
    e = np.exp(logit)
    return e / e.sum(axis=1, keepdims=True)


def load_weights(path):
    """One dict of float64 arrays per ensemble member."""
    blob = np.load(path)
    members = sorted({key.split("/")[0] for key in blob.files})
    return [{key.split("/", 1)[1]: blob[key].astype(np.float64) for key in blob.files
             if key.startswith(m + "/")} for m in members]


def probabilities(members, ball, team0, team1):
    """(T', 3) probabilities [team0, team1, dead] at the model stride.

    Averaged over ensemble members and over the two team orders, then rounded.
    """
    feats, _ = features.build(ball, team0, team1)
    swapped, _ = features.build(ball, team1, team0)
    total = 0.0
    for w in members:
        total = total + forward(w, feats) + forward(w, swapped)[:, [1, 0, 2]]
    return np.round(total / (2 * len(members)), PROB_DECIMALS)


def dead_and_home(prob, n):
    """Per-frame P(dead) and P(team0 | alive) on the full 25 fps grid, for fusion with other models."""
    from .decode import upsample
    full = upsample(prob, STRIDE, n)
    alive = np.maximum(full[:, 0] + full[:, 1], 1e-9)
    return np.round(full[:, 2], PROB_DECIMALS), np.round(full[:, 0] / alive, PROB_DECIMALS)


def export(model_dir, out_path):
    """torch state dicts (a folder of model_seed*.pt, or one .pt file) -> one compressed npz, float32."""
    import torch
    from .train import make_model
    dilations = [b.conv.dilation[0] for b in make_model().blocks]
    arrays = {}
    paths = [model_dir] if os.path.isfile(model_dir) else sorted(glob.glob(os.path.join(model_dir, "model_seed*.pt")))
    for i, path in enumerate(paths):
        state = torch.load(path, map_location="cpu")
        for key, value in state.items():
            arrays["m%d/%s" % (i, key)] = value.numpy().astype(np.float32)
        for b, d in enumerate(dilations):
            arrays["m%d/blocks.%d.dilation" % (i, b)] = np.int64(d)
    if not arrays:
        raise IOError("no model_seed*.pt in %s" % model_dir)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    np.savez_compressed(out_path, **arrays)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("export",))
    parser.add_argument("--models", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    export(args.models, args.out)
    print("wrote", args.out)
