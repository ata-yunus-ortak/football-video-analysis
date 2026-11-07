"""Registered controlled-view checks on other-game tracking, not competition data.

The second view is GENERATED from the same measurements, not an independent
broadcast camera. Its visibility and live/replay flags are synthetic fixture
properties. This exercises fusion gates; it does not evaluate visual accuracy.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import numpy as np
from clean_model.decoder import DecoderConfig
from clean_model.select import infer
from development.hybrid_tracking import HybridConfig
from development.hybrid_pipeline import predict_hybrid
from development.motion_possession import MotionConfig
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256


SCENARIOS = ('visible_subset', 'two_players', 'replay', 'geometry_conflict',
             'collective_jump', 'review_only_alignment', 'unknown_visibility')


def controlled_view(inputs, scenario):
    if scenario not in SCENARIOS:
        raise ValueError('Unregistered camera scenario')
    n, p, _ = inputs['players'].shape
    permutation = np.arange(p)[::-1]
    broadcast = {name: np.array(value, copy=True) for name, value in inputs.items()}
    broadcast['players'] = inputs['players'][:, permutation].copy() + [.05, 0]
    broadcast['teams'] = inputs['teams'][permutation]
    broadcast['player_detected'] = inputs['player_detected'][:, permutation].copy()
    broadcast['ball'] = inputs['ball'].copy() + [.05, 0]
    visible = np.zeros((n, p), bool)
    for frame in range(n):
        for team in (0, 1):
            slots = np.flatnonzero((broadcast['teams'] == team) & broadcast['player_detected'][frame])[:5]
            visible[frame, slots] = True
    view = {'source_kind': 'synthetic_image_observations', 'player_visible': visible,
            'ball_visible': inputs['ball_observed'].copy(), 'ball_ground_valid': np.ones(n, bool),
            'calibration_valid': np.ones(n, bool), 'player_confidence': np.full((n, p), .95),
            'ball_confidence': np.full(n, .95), 'camera_epoch': np.zeros(n, int),
            'frame_kind': np.full(n, 'live', dtype='<U12')}
    alignment = {'source_kind': 'synthetic_known_alignment', 'human_anchors_used': False,
                 'broadcast_frame': np.arange(n), 'verified': np.ones(n, bool), 'error_bound_s': np.zeros(n)}
    if scenario == 'two_players':
        for frame in range(n):
            visible[frame] = False
            visible[frame, np.flatnonzero(broadcast['player_detected'][frame])[:2]] = True
    elif scenario == 'replay':
        view['frame_kind'][:] = 'replay'
    elif scenario == 'geometry_conflict':
        broadcast['players'] += [8., 7.]
    elif scenario == 'collective_jump':
        middle = n // 2
        broadcast['players'][middle:middle + 2] += [40., 0.]
    elif scenario == 'review_only_alignment':
        alignment['source_kind'] = 'automatic_review_candidates'
    elif scenario == 'unknown_visibility':
        view = None
    return broadcast, alignment, view


def run(audit_dir, plan_path, out):
    audit_dir, plan_path = Path(audit_dir), Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    report = json.loads((audit_dir / 'report.json').read_text(encoding='utf-8'))
    fixture_spec = [{'id': 'metrica-sample-1', 'split': 'train'}, {'id': 'metrica-sample-2', 'split': 'validation'}]
    if (plan.get('provided_fixture_used') is not False or report.get('provided_fixture_used') is not False
            or plan.get('selected_release') is not False or plan.get('two_real_cameras_validated') is not False
            or plan.get('parameters_origin') != 'synthetic_engineering_checks_only'
            or plan.get('repository') != 'https://github.com/metrica-sports/sample-data'
            or report.get('repository') != plan['repository'] or report.get('commit') != plan.get('commit')
            or plan.get('fixtures') != fixture_spec or tuple(plan.get('scenarios', [])) != SCENARIOS
            or type(plan.get('max_frames_per_fixture')) is not int or plan['max_frames_per_fixture'] < 3):
        raise ValueError('Pinned other-game controlled-view plan required; no supplied-fixture selection')
    cfg, motion = HybridConfig(**plan['hybrid_parameters']), MotionConfig(**plan['motion_parameters'])
    repo = Path(__file__).resolve().parents[1]
    baseline_hash = _frozen_model(repo)
    model = json.loads((repo / 'model.json').read_text(encoding='utf-8'))
    out = external_output(out);out.mkdir(parents=True, exist_ok=False)
    names = ['tools/hybrid_experiment.py', 'development/hybrid_tracking.py', 'development/hybrid_pipeline.py',
             'development/continuity.py', 'development/dead_ball_features.py', 'development/player_motion.py',
             'development/motion_possession.py', 'development/long_ball.py', 'development/set_piece_dead_ball.py',
             'development/reachability.py', 'development/team_transitions.py']
    hashes = {name: sha256(repo / name) for name in names}
    registration = {'plan': plan, 'plan_sha256': sha256(plan_path),
        'audit_report_sha256': sha256(audit_dir / 'report.json'), 'baseline_model_sha256': baseline_hash,
        'source_sha256': hashes, 'before_external_arrays_read': True,
        'provided_fixture_used': False, 'selected_release': False, 'two_real_cameras_validated': False,
        'visibility_is_synthetic': True, 'accuracy_evaluated': False}
    (out / 'registration.json').write_text(json.dumps(registration, indent=2), encoding='utf-8')
    fixtures = {item['id']: item for item in report['fixtures']}
    summaries = []
    for spec in fixture_spec:
        item = fixtures[spec['id']]
        if item['split'] != spec['split']:
            raise ValueError('External fixture split differs')
        path = audit_dir / spec['id'] / 'inputs.npz'
        if sha256(path) != item['prepared_sha256']['inputs.npz']:
            raise ValueError('Prepared input differs from registered audit')
        with np.load(path, allow_pickle=False) as archive:
            source = {name: archive[name] for name in archive.files}
        total = len(source['ball']);n = min(total, plan['max_frames_per_fixture'])
        inputs = {name: (np.array(value[:n], copy=True) if value.ndim and len(value) == total else np.array(value, copy=True))
                  for name, value in source.items()}
        params = dict(model['base_config_at_10fps'])
        for name in ('confirmation_frames', 'gap_frames', 'hold_frames'):
            params[name] = math.ceil(params[name] * float(inputs['fps']) / model['training_fps'])
        baseline = infer(inputs, DecoderConfig(**params), model['policy'])
        for scenario in SCENARIOS:
            broadcast, alignment, view = controlled_view(inputs, scenario)
            result = predict_hybrid(inputs, broadcast, alignment, view, cfg, baseline, motion)
            overlay = result['hybrid'];case = out / spec['id'] / scenario;case.mkdir(parents=True)
            np.savez_compressed(case / 'inputs.npz', **overlay['inputs'])
            fields = ('player_source', 'ball_source', 'broadcast_slot', 'broadcast_frame', 'frame_allowed',
                      'frame_reason', 'player_reason_code', 'ball_reason_code', 'match_fraction', 'geometry_residual_m')
            np.savez_compressed(case / 'provenance.npz', **{name: overlay[name] for name in fields})
            np.savez_compressed(case / 'motion.npz', velocity_mps=result['velocity_mps'], delta_velocity_mps=result['delta_velocity_mps'])
            if scenario in ('two_players', 'replay', 'review_only_alignment', 'unknown_visibility'):
                if overlay['player_source'].any() or overlay['ball_source'].any():
                    raise ValueError('Rejected broadcast scenario supplied a measurement')
                np.testing.assert_array_equal(overlay['inputs']['players'], inputs['players'])
                np.testing.assert_array_equal(overlay['inputs']['ball'], inputs['ball'])
            if scenario == 'collective_jump':
                region = slice(n // 2 - 1, n // 2 + 3)
                if overlay['player_source'][region].any() or overlay['ball_source'][region].any():
                    raise ValueError('Collective discontinuity was allowed to contribute')
            switches = np.r_[False, np.diff(overlay['ball_source']) != 0]
            if not np.isnan(result['velocity_mps'][switches]).all():
                raise ValueError('Source handoff produced a spurious velocity')
            summary = {'fixture': spec['id'], 'split': spec['split'], 'scenario': scenario, 'frames': n,
                'broadcast_allowed_frames': int(overlay['frame_allowed'].sum()),
                'broadcast_player_measurements': int(overlay['player_source'].sum()),
                'broadcast_ball_measurements': int(overlay['ball_source'].sum()),
                'frame_reasons': dict(Counter(overlay['frame_reason'].tolist())),
                'motion_contacts': len(result['contacts']), 'candidate_passes': len(result['passes']),
                'accuracy_evaluated': False, 'two_real_cameras_validated': False}
            (case / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
            summaries.append(summary)
            print(json.dumps({k: summary[k] for k in ('fixture', 'scenario', 'frames', 'broadcast_allowed_frames')}), flush=True)
    if _frozen_model(repo) != baseline_hash or any(sha256(repo / name) != value for name, value in hashes.items()):
        raise ValueError('Source changed during controlled experiment')
    result = {'fixtures': summaries, 'provided_fixture_used': False, 'selected_release': False,
              'two_real_cameras_validated': False, 'accuracy_evaluated': False}
    (out / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', required=True)
    parser.add_argument('--plan', default='hybrid-data-plan.json')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    run(args.audit_dir, args.plan, args.out)
