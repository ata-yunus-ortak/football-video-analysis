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
from development.player_motion import DribbleConfig
from development.team_transitions import TransitionConfig
from development.set_piece_dead_ball import DeadBallConfig
from development.long_ball import LongBallConfig
from development.reachability import ReachabilityConfig
from .smart_tag_view import load_tags
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
    dribble = DribbleConfig(**spec['dribble_parameters']) if 'dribble_parameters' in spec else None
    transition = TransitionConfig(**spec['transition_parameters']) if 'transition_parameters' in spec else None
    dead_ball = DeadBallConfig(**spec['dead_ball_parameters']) if 'dead_ball_parameters' in spec else None
    long_ball = LongBallConfig(**spec['long_ball_parameters']) if 'long_ball_parameters' in spec else None
    arrival = ReachabilityConfig(**spec['reachability_parameters']) if 'reachability_parameters' in spec else None
    if transition is not None and dribble is None:
        raise ValueError('Transition parameters require dribble/player-motion parameters')
    repo = Path(__file__).resolve().parents[1]
    baseline_hash = _frozen_model(repo)
    model = json.loads((repo / 'model.json').read_text())
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    source_paths = [Path(__file__), repo / 'development' / 'motion_possession.py',
                    repo / 'development' / 'dead_ball_features.py', repo / 'development' / 'player_motion.py',
                    repo / 'development' / 'team_transitions.py', repo / 'development' / 'set_piece_dead_ball.py',
                    repo / 'tools' / 'smart_tag_view.py', repo / 'development' / 'long_ball.py',
                    repo / 'development' / 'reachability.py', repo / 'development' / 'continuity.py']
    manifest = {'version': 'motion-evidence-experimental-v1', 'selected_release': False,
                'provided_fixture_used': False, 'config': asdict(config),
                'dribble_config': asdict(dribble) if dribble is not None else None,
                'transition_config': asdict(transition) if transition is not None else None,
                'dead_ball_config': asdict(dead_ball) if dead_ball is not None else None,
                'long_ball_config': asdict(long_ball) if long_ball is not None else None,
                'reachability_config': asdict(arrival) if arrival is not None else None,
                'automatic_tags': spec.get('automatic_tag_files', {}),
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
        tag_data = None
        if dead_ball is not None or long_ball is not None:
            tag_spec = spec.get('automatic_tag_files', {}).get(mid)
            if (not tag_spec or tag_spec.get('fixture_id') != mid
                    or tag_spec.get('source_kind') != 'automatic_provider_tags' or not tag_spec.get('provenance')):
                raise ValueError('Registered automatic-tag provenance for this external fixture required')
            tag_path = Path(tag_spec['path'])
            if not tag_path.is_absolute():
                tag_path = Path(config_path).resolve().parent / tag_path
            if sha256(tag_path) != tag_spec['sha256']:
                raise ValueError('Automatic tag source hash differs')
            tag_data = load_tags(tag_path, float(inputs['fps']), len(base))
        result = predict(inputs, base, config, dribble, transition,
                         dead_ball_config=dead_ball, automatic_tags=tag_data, long_ball_config=long_ball,
                         reachability_config=arrival)
        if arrival is not None:
            names = ('arrival_time_s', 'team_arrival_time_s', 'arrival_team_counts',
                     'arrival_player_velocity_mps')
            np.savez_compressed(out / (mid + '-arrival.npz'), **{name: result[name] for name in names})
        if dribble is not None:
            names = ('dribble_slot', 'dribble_velocity_error_mps', 'player_velocity_mps',
                     'team_mean_velocity_mps', 'team_mean_speed_mps', 'team_velocity_counts')
            np.savez_compressed(out / (mid + '-player-motion.npz'), **{name: result[name] for name in names})
        with (out / (mid + '.csv')).open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['frame', 'label', 'reason'])
            writer.writerows(zip(inputs['frame'].tolist(), result['labels'].tolist(), result['reasons'].tolist()))
        events = {'contacts': result['contacts'], 'candidate_passes': result['passes'],
                  'team_transitions': result.get('team_transition_events', []),
                  'dead_ball_events': result.get('dead_ball_events', []),
                  'long_ball_events': result.get('long_ball_events', []),
                  'long_ball_unresolved_tags': result.get('long_ball_unresolved_tags', []),
                  'contact_verified': False, 'slot_identity_verified': False}
        (out / (mid + '-events.json')).write_text(json.dumps(events, indent=2), encoding='utf-8')
        summaries.append({'id': mid, 'split': fixture['split'], 'frames': len(base),
                          'motion_candidates': len(result['contacts']),
                          'candidate_passes': len(result['passes']),
                          'arrival_supported_contacts': sum(e['assignment_evidence'] == 'motion_and_arrival_time'
                                                            for e in result['contacts']),
                          'dribble_frames': int((result['dribble_slot'] >= 0).sum()) if dribble is not None else 0,
                          'dead_ball_frames': int((result['labels'] == 'D').sum()),
                          'long_ball_candidates': len(result.get('long_ball_events', []))})
        if transition is not None:
            names = ('team_vector_change_mps', 'team_speed_change_mps', 'team_change_cohort_counts')
            np.savez_compressed(out / (mid + '-team-transitions.npz'), **{name: result[name] for name in names})
        if long_ball is not None:
            np.savez_compressed(out / (mid + '-long-ball.npz'), flight_mask=result['long_ball_flight_mask'])
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
