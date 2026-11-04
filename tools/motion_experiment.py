"""Run unselected motion evidence on registered external audit arrays only."""
import argparse
import csv
import json
import math
from dataclasses import asdict
from pathlib import Path
import numpy as np
from clean_model.decoder import DecoderConfig
from clean_model.select import infer
from development.motion_possession import MotionConfig, predict
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256


def run(audit_dir, config_path, out):
    root = Path(audit_dir)
    report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
    if (report['provided_fixture_used'] is not False
            or report['repository'] != 'https://github.com/metrica-sports/sample-data'):
        raise ValueError('Registered external audit inputs required')
    spec = json.loads(Path(config_path).read_text(encoding='utf-8'))
    if not spec.get('rationale'):
        raise ValueError('Record the configuration rationale, including unselected status')
    config = MotionConfig(**spec['parameters'])
    repo = Path(__file__).resolve().parents[1]
    baseline_hash = _frozen_model(repo)
    model = json.loads((repo / 'model.json').read_text())
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    source_paths = [Path(__file__), repo / 'development' / 'motion_possession.py',
                    repo / 'development' / 'dead_ball_features.py']
    manifest = {'version': 'motion-evidence-experimental-v1', 'selected_release': False,
                'provided_fixture_used': False, 'config': asdict(config),
                'config_sha256': sha256(config_path), 'rationale': spec['rationale'],
                'audit_report_sha256': sha256(root / 'report.json'),
                'baseline_model_sha256': baseline_hash,
                'source_sha256': {p.relative_to(repo).as_posix(): sha256(p) for p in source_paths},
                'metrics_computed': False, 'before_inference': True}
    (out / 'registration.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    summaries = []
    for fixture in report['fixtures']:
        mid = fixture['id']
        if mid not in ('metrica-sample-1', 'metrica-sample-2'):
            raise ValueError('Unexpected external fixture')
        path = root / mid / 'inputs.npz'
        if sha256(path) != fixture['prepared_sha256']['inputs.npz']:
            raise ValueError('Prepared external input hash differs')
        with np.load(path, allow_pickle=False) as archive:
            inputs = {name: archive[name] for name in archive.files}
        params = dict(model['base_config_at_10fps'])
        for key in ('confirmation_frames', 'gap_frames', 'hold_frames'):
            params[key] = math.ceil(params[key] * float(inputs['fps']) / model['training_fps'])
        base = infer(inputs, DecoderConfig(**params), model['policy'])
        result = predict(inputs, base, config)
        with (out / (mid + '.csv')).open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['frame', 'label', 'reason'])
            writer.writerows(zip(inputs['frame'].tolist(), result['labels'].tolist(), result['reasons'].tolist()))
        events = {'contacts': result['contacts'], 'candidate_passes': result['passes'],
                  'contact_verified': False, 'slot_identity_verified': False}
        (out / (mid + '-events.json')).write_text(json.dumps(events, indent=2), encoding='utf-8')
        summaries.append({'id': mid, 'split': fixture['split'], 'frames': len(base),
                          'motion_candidates': len(result['contacts']),
                          'candidate_passes': len(result['passes'])})
    if _frozen_model(repo) != baseline_hash or any(
            sha256(repo / name) != value for name, value in manifest['source_sha256'].items()):
        raise ValueError('Source changed during experiment')
    (out / 'summary.json').write_text(json.dumps({'fixtures': summaries,
        'selected_release': False, 'accuracy_evaluated': False}, indent=2), encoding='utf-8')
    return summaries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    run(args.audit_dir, args.config, args.out)
