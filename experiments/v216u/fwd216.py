"""Member probabilities of TCN weight files on the development copies, with torch (development speed only; the
release arithmetic is the NumPy one, agreement about 1e-6). Run from football-video-analysis.
Usage: fwd216.py PATTERN W.npz [W.npz ...]      PATTERN = 'J03*' or 'MET*' """
import sys, glob, os, numpy as np, torch
from possession.train import make_model
D = '/Users/umut/BARCELONA/work/v216u/dev/'
dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
def members(path):
    blob = np.load(path); out = []
    for m in sorted({k.split('/')[0] for k in blob.files}):
        model = make_model()
        model.load_state_dict({k.split('/', 1)[1]: torch.from_numpy(blob[k]) for k in blob.files if k.startswith(m + '/') and not k.endswith('dilation')})
        out.append(model.eval().to(dev))
    return out
def fwd(model, x):
    with torch.no_grad():
        return torch.softmax(model(torch.from_numpy(x.astype(np.float32))[None].to(dev))[0], -1).cpu().numpy().astype(np.float64)
for wpath in sys.argv[2:]:
    name = os.path.basename(wpath)[:-4]
    mem = members(wpath)
    for f in sorted(glob.glob(D + sys.argv[1] + '.npz')):
        for i, model in enumerate(mem):
            o = f'{D}probs/{name}.m{i}__{os.path.basename(f)}'
            if os.path.exists(o):
                continue
            z = np.load(f); out = {}; k = 0
            while f'x{k}' in z.files:
                out[f'p{k}'] = 0.5 * (fwd(model, z[f'x{k}']) + fwd(model, z[f'w{k}'])[:, [1, 0, 2]]); k += 1
            np.savez(o, **out)
    print('done', name, flush=True)
