"""Rebuild the v2.12 model bundle from EXTERNAL data only (never the supplied match).

    python -m possession.train212 --config possession-v212-config.json \
        --dfl-prepared <dir with J03*/inputs.npz,targets.npz> --out models/possession-v212.npz

Exactly possession/train.py (same fixtures, seeded corruption, rows, team-swap symmetrisation, hyperparameters and
leave-one-fixture-out second stage), with the 36 touch columns of possession/touch.py appended to the 227
possession.features columns of every stage-1 row. The touch columns of a training copy are computed on the same
corrupted copy as its base columns (training copies have no broadcast fill). Models are fitted with scikit-learn and
exported to numpy arrays (trees.py); possession/pipeline212.py reads the bundle.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from .degrade import degrade
from .features import features, play_blocks, FEATURE_VERSION
from .touch import touch_features
from .trees import export_hgb
from .stack import stack_features
from . import bundle as bundle_io
from .train import load_external, fit, sha256, HERE, SOURCES as V21_TRAIN_SOURCES

SOURCES = V21_TRAIN_SOURCES + ('touch.py', 'pipeline212.py', 'train212.py')


def stage1_features(match, swap):
    X, names = features(match, swap=swap)
    T, tnames = touch_features(match, swap=swap)
    return np.concatenate([X, T], 1), names + tnames


def training_rows(fixtures, seeds, step, dfl_dir, metrica_dir, profile='v2'):
    plan, total = [], 0
    for name in fixtures:
        m, lab = load_external(name, dfl_dir, metrica_dir)
        for seed in seeds:
            idx = np.arange(seed % step, len(lab), step)
            idx = idx[np.isin(lab[idx], ('H', 'A', 'D'))]
            plan.append((name, seed, idx))
            total += 2 * len(idx)
    X = y_dead = y_home = names = None
    src = np.empty(total, np.int16)
    r = 0
    cache = {}
    for name, seed, idx in plan:
        if name not in cache:
            cache.clear()
            cache[name] = load_external(name, dfl_dir, metrica_dir)
        m, lab = cache[name]
        dm = degrade(m, lab, np.random.default_rng(seed), profile=profile)
        for swap in (False, True):
            F, nm = stage1_features(dm, swap)
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
        print(json.dumps({'rows_done': name, 'seed': seed}), flush=True)
    return X, y_dead, y_home, names, src


def frame_probs(md, mh, match):
    """Symmetrised stage-1 probabilities over the play blocks (as possession.pipeline212)."""
    X, _ = stage1_features(match, False)
    Xs, _ = stage1_features(match, True)
    n = len(X)
    ok = np.zeros(n, bool)
    for a, b in play_blocks(match['period']):
        ok[a:b] = True
    pd_, ph = np.full(n, 0.5), np.full(n, 0.5)
    pd_[ok] = 0.5 * (md.predict_proba(X[ok])[:, 1] + md.predict_proba(Xs[ok])[:, 1])
    ph[ok] = 0.5 * (mh.predict_proba(X[ok])[:, 1] + 1.0 - mh.predict_proba(Xs[ok])[:, 1])
    return np.round(pd_, 6), np.round(ph, 6)


def stack_rows(cfg, X, yd, yh, src, dfl_dir, metrica_dir):
    """Leave-one-fixture-out stage-1 probabilities -> stage-2 training rows (both team views), as possession.train."""
    fixtures, seeds = cfg['train_fixtures'], cfg['seeds']
    step = cfg['stack'].get('step', cfg['step'])
    S_all, d_all, h_all, cols = [], [], [], None
    for i, name in enumerate(fixtures):
        tr = src != i
        md, mh = fit(X[tr], yd[tr], yh[tr], cfg['hyperparameters'])
        m, lab = load_external(name, dfl_dir, metrica_dir)
        for seed in seeds:
            dm = degrade(m, lab, np.random.default_rng(seed), profile=cfg.get('degrade_profile', 'v2'))
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


def check_export(clf, exported, X, n=20000):
    """The exported numpy trees must give the scikit-learn probabilities on training rows (every k-th row)."""
    from .trees import predict_proba
    rows = X[np.linspace(0, len(X) - 1, min(n, len(X))).astype(np.int64)]
    diff = float(np.max(np.abs(clf.predict_proba(rows)[:, 1] - predict_proba(exported, rows))))
    if diff > 1e-9:
        raise ValueError(f'exported trees differ from scikit-learn by {diff}')
    return diff


def main(config_path, dfl_dir, metrica_dir, out):
    cfg = json.loads(Path(config_path).read_text())
    if cfg['feature_version'] != FEATURE_VERSION:
        raise ValueError('feature version differs from the registered configuration')
    if cfg.get('smooth_half') or cfg.get('degrade_profile', 'v2') != 'v2':
        raise ValueError('v2.12 trains the v2.1 path only (v2 profile, no smoothing)')
    if cfg['touch_sha256'] != sha256(HERE / 'touch.py'):
        raise ValueError('possession/touch.py differs from the registered configuration')
    X, yd, yh, names, src = training_rows(cfg['train_fixtures'], cfg['seeds'], cfg['step'], dfl_dir, metrica_dir)
    S, sd_y, sh_y, cols = stack_rows(cfg, X, yd, yh, src, dfl_dir, metrica_dir)
    sd, sh = fit(S, sd_y, sh_y, cfg['stack']['hyperparameters'])
    stack = (export_hgb(sd), export_hgb(sh), cols)
    export_diff = {'stack_dead': check_export(sd, stack[0], S), 'stack_home': check_export(sh, stack[1], S)}
    del S
    md, mh = fit(X, yd, yh, cfg['hyperparameters'])
    dead, home = export_hgb(md), export_hgb(mh)
    export_diff.update(dead=check_export(md, dead, X), home=check_export(mh, home, X))
    import sklearn
    card = {'version': cfg['version'], 'feature_version': FEATURE_VERSION, 'touch_columns': len(names) - 227,
            'train_fixtures': cfg['train_fixtures'], 'seeds': cfg['seeds'], 'step': cfg['step'],
            'hyperparameters': cfg['hyperparameters'], 'rows': int(len(X)), 'stack': cfg.get('stack'),
            'sklearn_version_used_for_training': sklearn.__version__,
            'source_sha256': {s: sha256(HERE / s) for s in SOURCES},
            'config_sha256': sha256(config_path), 'provided_fixture_used': False,
            'export_max_abs_difference_on_training_rows': export_diff,
            'selection_summary': cfg.get('selection_summary')}
    bundle_io.save(out, dead, home, names, cfg['decoder'], card, stack=stack)
    print(json.dumps({'out': str(out), 'rows': int(len(X)), 'features': len(names), 'export_diff': export_diff}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--config', required=True)
    p.add_argument('--dfl-prepared', required=True)
    p.add_argument('--metrica-sample', default=None)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    main(a.config, a.dfl_prepared, a.metrica_sample, a.out)
