"""Rebuild the v2 model bundle from EXTERNAL data only (never the supplied match).

    python -m possession.train --config possession-v2-config.json \
        --dfl-prepared <dir with J03*/inputs.npz,targets.npz> \
        --metrica-sample <metrica-sports/sample-data checkout> --out models/possession-v2.npz

DFL/Sportec open data (CC-BY 4.0, Bassek et al. 2025) is prepared with tools/sportec_prepare.py
from the pinned IDSSE files; Metrica sample games come from github.com/metrica-sports/sample-data
(pinned commit in possession-v2-plan.json). Every training copy is corrupted with
possession/degrade.py (seeded), features are symmetrised by swapping teams, and two gradient
boosted tree models are fitted with scikit-learn and exported to numpy arrays (trees.py).
If the configuration has a "stack" entry, a second stage is trained on leave-one-fixture-out
stage-1 probabilities (possession/stack.py), exactly as in the validation experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .data import read_dfl_prepared
from .degrade import degrade
from .features import features, FEATURE_VERSION
from .trees import export_hgb
from .stack import stack_features
from .smooth import smooth_positions
from .features import play_blocks
from . import bundle as bundle_io

HERE = Path(__file__).resolve().parent
SOURCES = ('data.py', 'features.py', 'trees.py', 'decode.py', 'pipeline.py', 'bundle.py', 'run.py',
           'stack.py', 'tags.py')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_external(name, dfl_dir, metrica_dir):
    if name.startswith('J03'):
        return read_dfl_prepared(Path(dfl_dir) / name)
    raise KeyError(f'unknown training fixture {name}')


def training_rows(fixtures, seeds, step, dfl_dir, metrica_dir, profile='v2', smooth_half=0):
    plan, total, names = [], 0, None
    for name in fixtures:
        m, lab = load_external(name, dfl_dir, metrica_dir)
        for seed in seeds:
            idx = np.arange(seed % step, len(lab), step)
            idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            plan.append((name, seed, idx))
            total += 2 * len(idx)
    X = y_dead = y_home = None
    src = np.empty(total, np.int16)
    r = 0
    cache = {}
    for name, seed, idx in plan:
        if name not in cache:
            cache.clear()
            cache[name] = load_external(name, dfl_dir, metrica_dir)
        m, lab = cache[name]
        dm = degrade(m, lab, np.random.default_rng(seed), profile=profile)
        if smooth_half:
            dm = smooth_positions(dm, smooth_half)
        for swap in (False, True):
            F, nm = features(dm, swap=swap)
            if X is None:
                names = nm
                X = np.empty((total, len(nm)), np.float64)
                y_dead = np.empty(total, np.int8)
                y_home = np.empty(total, np.int8)
            k = len(idx)
            X[r:r + k] = F[idx]
            y_dead[r:r + k] = lab[idx] == 'D'
            h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
            y_home[r:r + k] = np.where(h >= 0, 1 - h, -1) if swap else h
            src[r:r + k] = fixtures.index(name)
            r += k
            del F
    return X, y_dead, y_home, names, src


def frame_probs(md, mh, match):
    """Symmetrised stage-1 probabilities over the play blocks (as possession.pipeline)."""
    X, _ = features(match)
    Xs, _ = features(match, swap=True)
    n = len(X)
    ok = np.zeros(n, bool)
    for a, b in play_blocks(match['period']):
        ok[a:b] = True
    pd_, ph = np.full(n, 0.5), np.full(n, 0.5)
    pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1.0 - mh.predict_proba(Xs[ok])[:, 1])
    return np.round(pd_, 6), np.round(ph, 6)


def stack_rows(cfg, X, yd, yh, src, dfl_dir, metrica_dir):
    """Leave-one-fixture-out stage-1 probabilities -> stage-2 training rows (both team views)."""
    fixtures, seeds = cfg['train_fixtures'], cfg['seeds']
    step = cfg['stack'].get('step', cfg['step'])  # stage-2 row subsampling (validated: every 3rd frame)
    S_all, d_all, h_all, cols = [], [], [], None
    for i, name in enumerate(fixtures):
        tr = src != i
        md, mh = fit(X[tr], yd[tr], yh[tr], cfg['hyperparameters'])
        m, lab = load_external(name, dfl_dir, metrica_dir)
        for seed in seeds:
            dm = degrade(m, lab, np.random.default_rng(seed), profile=cfg.get('degrade_profile', 'v2'))
            if cfg.get('smooth_half'):
                dm = smooth_positions(dm, cfg['smooth_half'])
            pd_, ph = frame_probs(md, mh, dm)
            idx = np.arange(seed % step, len(lab), step)
            idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            for swap in (False, True):
                S, cols = stack_features(pd_, ph, m['period'], m['fps'], swap=swap)
                S_all.append(S[idx])
                d_all.append((lab[idx] == 'D').astype(np.int8))
                h = np.where(lab[idx] == 'H', 1, np.where(lab[idx] == 'A', 0, -1))
                h_all.append((np.where(h >= 0, 1 - h, -1) if swap else h).astype(np.int8))
        print(json.dumps({'stack_fold_done': name}), flush=True)
        del md, mh
    return np.concatenate(S_all), np.concatenate(d_all), np.concatenate(h_all), cols


def fit(X, y_dead, y_home, hp):
    from sklearn.ensemble import HistGradientBoostingClassifier
    md = HistGradientBoostingClassifier(random_state=0, early_stopping=False, **hp).fit(X, y_dead)
    alive = y_home >= 0
    mh = HistGradientBoostingClassifier(random_state=0, early_stopping=False, **hp).fit(X[alive], y_home[alive])
    return md, mh


def main(config_path, dfl_dir, metrica_dir, out):
    cfg = json.loads(Path(config_path).read_text())
    if cfg['feature_version'] != FEATURE_VERSION:
        raise ValueError('feature version differs from the registered configuration')
    X, yd, yh, names, src = training_rows(cfg['train_fixtures'], cfg['seeds'], cfg['step'], dfl_dir,
                                          metrica_dir, profile=cfg.get('degrade_profile', 'v2'),
                                          smooth_half=cfg.get('smooth_half', 0))
    stack = None
    if cfg.get('stack'):
        S, sd_y, sh_y, cols = stack_rows(cfg, X, yd, yh, src, dfl_dir, metrica_dir)
        sd, sh = fit(S, sd_y, sh_y, cfg['stack']['hyperparameters'])
        stack = (export_hgb(sd), export_hgb(sh), cols)
        del S
    md, mh = fit(X, yd, yh, cfg['hyperparameters'])
    import sklearn
    card = {'version': cfg['version'], 'feature_version': FEATURE_VERSION,
            'train_fixtures': cfg['train_fixtures'], 'seeds': cfg['seeds'], 'step': cfg['step'],
            'hyperparameters': cfg['hyperparameters'], 'rows': int(len(X)),
            'stack': cfg.get('stack'),
            'sklearn_version_used_for_training': sklearn.__version__,
            'source_sha256': {s: sha256(HERE / s) for s in cfg.get('sources', SOURCES)},
            'config_sha256': sha256(config_path), 'provided_fixture_used': False,
            'selection_summary': cfg.get('selection_summary')}
    for key in ('degrade_profile', 'smooth_half'):     # only for configurations that set them (v2.1 card unchanged)
        if key in cfg:
            card[key] = cfg[key]
    bundle_io.save(out, export_hgb(md), export_hgb(mh), names, cfg['decoder'], card, stack=stack)
    print(json.dumps({'out': str(out), 'rows': int(len(X)), 'features': len(names)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--config', required=True)
    p.add_argument('--dfl-prepared', required=True)
    p.add_argument('--metrica-sample', default=None)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    main(a.config, a.dfl_prepared, a.metrica_sample, a.out)
