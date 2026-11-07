"""Recheck one frozen candidate; previously accessed external fixtures only.

This is not a fresh held-out test and never selects or modifies the candidate.
Raw sources are verified, then prepared anew. Every prediction is frozen before
any target is read for scoring.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from clean_model.decoder import DecoderConfig
from clean_model.select import digest, infer
from development.sequence_possession import SequenceConfig, predict
from development.sequence_metrics import evaluate
from tools.sequence_selection import write, aggregate
from tools.fresh_check import prepare
from tools.dead_ball_audit import _frozen_model
from tools.metrica_data import external_output, sha256


def run(candidate_path, source_root, out):
    repo = Path(__file__).resolve().parents[1]
    source_root, candidate_path = Path(source_root), Path(candidate_path)
    candidate = json.loads(candidate_path.read_text())
    if not candidate['accepted_external_proxy_candidate'] or candidate['provided_fixture_used']:
        raise ValueError('Externally selected candidate required')
    if any(digest(repo/p) != h for p, h in candidate['source_hashes'].items()):
        raise ValueError('Candidate source freeze mismatch')
    cfg = SequenceConfig(**candidate['selected_config'])
    registry = json.loads((repo/'external-selection.json').read_text())
    manifest_path = source_root/'download-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    model = json.loads((repo/'model.json').read_text())
    baseline_hash = _frozen_model(repo)
    out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    before = {'candidate_sha256': sha256(candidate_path), 'source_hashes': candidate['source_hashes'],
              'recheck_code_sha256': sha256(__file__), 'preparation_code_sha256': sha256(repo/'tools/fresh_check.py'),
              'baseline_model_sha256': baseline_hash, 'manifest_sha256': sha256(manifest_path),
              'fixture_ids': [g['id'] for g in registry['fresh_test_fixtures']],
              'previously_accessed_for_baseline': True, 'fresh_test': False,
              'selection_allowed': False, 'provided_fixture_used': False}
    write(out/'before-access.json', before)
    prepared, frozen = {}, {}
    for mid in before['fixture_ids']:
        mid = str(mid)
        for name in ('match.json', 'tracking.jsonl'):
            path = source_root/'raw'/mid/name
            entry = manifest.get(f'raw\\{mid}\\{name}', manifest.get(f'raw/{mid}/{name}'))
            if not entry or sha256(path) != entry['sha256'] or path.stat().st_size != entry['bytes']:
                raise ValueError('Pinned raw external source differs')
            if registry['commit'] not in entry['url'] or f'/matches/{mid}/' not in entry['url']:
                raise ValueError('Wrong external fixture source')
        prepared[mid] = prepare(source_root/'raw'/mid/'match.json', source_root/'raw'/mid/'tracking.jsonl', out/'prepared'/mid)
        with np.load(out/'prepared'/mid/'inputs.npz', allow_pickle=False) as z:
            x = {k: z[k] for k in z.files}
        params = dict(model['base_config_at_10fps'])
        for key in ('confirmation_frames', 'gap_frames', 'hold_frames'):
            params[key] = int(np.ceil(params[key]*float(x['fps'])/model['training_fps']))
        for name, pred in [('sequence', predict(x, cfg)), ('baseline', infer(x, DecoderConfig(**params), model['policy']))]:
            path = out/f'{mid}-{name}.npy'
            np.save(path, pred, allow_pickle=False)
            frozen[f'{mid}-{name}'] = sha256(path)
        print(json.dumps({'external_recheck_predictions_frozen': mid}), flush=True)
    write(out/'prediction-freeze.json', {'sha256': frozen, 'before_scoring': True, 'prepared': prepared})
    games = {'sequence': [], 'baseline': []}
    for mid in prepared:
        with np.load(out/'prepared'/mid/'provider-targets.npz', allow_pickle=False) as z: y = z['labels']
        with np.load(out/'prepared'/mid/'inputs.npz', allow_pickle=False) as z: period = z['period']
        for name in games:
            path = out/f'{mid}-{name}.npy'
            if sha256(path) != frozen[f'{mid}-{name}']:
                raise ValueError('Prediction changed before scoring')
            games[name].append({'id': mid, 'metrics': evaluate(y, np.load(path, allow_pickle=False), period)})
    if (sha256(candidate_path) != before['candidate_sha256'] or _frozen_model(repo) != baseline_hash
            or any(digest(repo/p) != h for p, h in candidate['source_hashes'].items())):
        raise ValueError('Frozen candidate changed')
    result = {**before, 'games': games, 'means': {k: aggregate(v) for k, v in games.items()},
              'candidate_changed': False, 'human_ground_truth': False, 'competition_score': False,
              'D_validated': False, 'vision_validated': False}
    write(out/'result.json', result)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--candidate', required=True)
    p.add_argument('--source-root', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args(); run(a.candidate, a.source_root, a.out)
