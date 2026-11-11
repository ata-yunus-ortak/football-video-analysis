"""Switch hazard: probability that a team change happens within +-0.5 s of a frame (possession v2.6 candidate).

Inputs per frame: the 227 stage-1 features and the 48 stage-2 (stack) features computed from the stage-1
probabilities; the model is evaluated in both team views and averaged (a change is a change for either
team). The decoder in possession/decode2.py turns it into a frame-dependent switch cost. Trained on
external data only, with out-of-fold stage-1 probabilities, exactly like the second stage:

    python -m possession.hazard --config possession-v26-config.json --dfl-prepared <prepared dir> \
        --out models/possession-v26-hazard.npz
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .features import features, play_blocks
from .stack import stack_features
from .trees import predict_proba, export_hgb, FIELDS

K_FRAMES = 12
KEYS = FIELDS + ('offsets', 'baseline')


def switch_target(lab, k=K_FRAMES):
    lab = np.asarray(lab)
    alive = np.isin(lab, ('H', 'A'))
    ch = np.zeros(len(lab), bool)
    ch[1:] = alive[1:] & alive[:-1] & (lab[1:] != lab[:-1])
    c = np.r_[0, np.cumsum(ch)]
    n = len(lab)
    lo, hi = np.clip(np.arange(n) - k, 0, n), np.clip(np.arange(n) + k + 1, 0, n)
    return ((c[hi] - c[lo]) > 0).astype(np.int8)


def hazard_matrix(match, p1, q1, swap, idx=None):
    X, xn = features(match, swap=swap)
    S, sn = stack_features(p1, q1, match['period'], match['fps'], swap=swap)
    if idx is not None:
        X, S = X[idx], S[idx]
    return np.hstack([X, S]), xn + ['stack_' + c for c in sn]


def predict(model, match, p1, q1):
    """Team-symmetric hazard over the play blocks (0 elsewhere)."""
    n = len(match['ball'])
    ok = np.zeros(n, bool)
    for a, b in play_blocks(match['period']):
        ok[a:b] = True
    out = np.zeros(n)
    for sw in (False, True):
        Z, names = hazard_matrix(match, p1, q1, sw)
        if names != model['feature_names']:
            raise ValueError('hazard feature layout differs from the frozen model')
        fin = ok & np.isfinite(Z).any(1)
        v = np.zeros(n)
        v[fin] = predict_proba(model['trees'], Z[fin])
        out += 0.5 * v
    return np.round(out, 6)


def save(path, trees, feature_names, card):
    arrays = {f'hz__{k}': np.asarray(trees[k]) for k in KEYS}
    arrays['feature_names'] = np.array(json.dumps(feature_names))
    arrays['card'] = np.array(json.dumps(card, sort_keys=True))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        np.savez_compressed(f, **arrays)


def load(path):
    z = np.load(path, allow_pickle=False)
    return {'trees': {k: z[f'hz__{k}'] for k in KEYS}, 'feature_names': json.loads(str(z['feature_names'])),
            'card': json.loads(str(z['card'])), 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def main(config_path, dfl_dir, metrica_dir, out):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from .train import training_rows, fit, frame_probs, load_external, sha256, HERE
    from .degrade import degrade
    from .smooth import smooth_positions
    cfg = json.loads(Path(config_path).read_text())
    fixtures, seeds = cfg['train_fixtures'], cfg['seeds']
    X, yd, yh, _, src = training_rows(fixtures, seeds, cfg['step'], dfl_dir, metrica_dir,
                                      profile=cfg.get('degrade_profile', 'v2'), smooth_half=cfg.get('smooth_half', 0))
    rows, ys, names = [], [], None
    step = cfg['hazard']['step']
    for i, name in enumerate(fixtures):
        md, mh = fit(X[src != i], yd[src != i], yh[src != i], cfg['hyperparameters'])
        m, lab = load_external(name, dfl_dir, metrica_dir)
        y_all = switch_target(lab)
        for seed in seeds:
            dm = degrade(m, lab, np.random.default_rng(seed), profile=cfg.get('degrade_profile', 'v2'))
            if cfg.get('smooth_half'):
                dm = smooth_positions(dm, cfg['smooth_half'])
            p1, q1 = frame_probs(md, mh, dm)
            idx = np.arange(seed % step, len(lab), step)
            idx = idx[np.isin(lab[idx], ('H', 'A'))]
            for sw in (False, True):
                Z, names = hazard_matrix(dm, p1, q1, sw, idx)
                rows.append(Z.astype(np.float32))
                ys.append(y_all[idx])
        print(json.dumps({'hazard_fold_done': name}), flush=True)
        del md, mh
    del X
    Z, y = np.concatenate(rows), np.concatenate(ys)
    clf = HistGradientBoostingClassifier(random_state=0, early_stopping=False, **cfg['hazard']['hyperparameters']).fit(Z, y)
    import sklearn
    card = {'version': cfg['version'], 'role': 'switch hazard (+-0.5 s) for possession/decode2.py',
            'train_fixtures': fixtures, 'seeds': seeds, 'rows': int(len(Z)), 'positive_rate': round(float(y.mean()), 4),
            'hazard': cfg['hazard'], 'degrade_profile': cfg.get('degrade_profile', 'v2'),
            'sklearn_version_used_for_training': sklearn.__version__,
            'source_sha256': {s: sha256(HERE / s) for s in cfg['sources']},
            'config_sha256': sha256(config_path), 'provided_fixture_used': False}
    save(out, export_hgb(clf), names, card)
    print(json.dumps({'out': str(out), 'rows': int(len(Z)), 'features': len(names)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--config', required=True)
    p.add_argument('--dfl-prepared', required=True)
    p.add_argument('--metrica-sample', default=None)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    main(a.config, a.dfl_prepared, a.metrica_sample, a.out)
