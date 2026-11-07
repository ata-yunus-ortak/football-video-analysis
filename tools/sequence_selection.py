"""Registered external sequence study, with no supplied-fixture inputs."""
import argparse
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import time
import numpy as np
from clean_model.decoder import DecoderConfig
from clean_model.select import digest, infer, load
from development.sequence_possession import SequenceConfig, measurements, evidence, decode
from development.sequence_metrics import evaluate
from tools.dead_ball_audit import _frozen_model
from tools.metrica_data import external_output


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')


def aggregate(games):
    keys = ('provider_filled_spell_f1', 'provider_macro_f1_HA',
            'provider_team_spell_iou_f1', 'provider_frame_agreement', 'abstention_fraction')
    return {k: float(np.mean([g['metrics'][k] for g in games])) for k in keys}


def run(local_plan, study_plan, out):
    repo = Path(__file__).resolve().parents[1]
    spec = json.loads(Path(study_plan).read_text(encoding='utf-8'))
    registry = json.loads((repo / 'external-selection.json').read_text())
    local = json.loads(Path(local_plan).read_text())
    if (spec['provided_fixture_used'] is not False
            or local['provided_fixture_used_for_selection'] is not False
            or local['commit'] != registry['commit']
            or local['repository'] != registry['repository']):
        raise ValueError('Pinned external-only study required')
    entries = local['development_fixtures']
    if set(entries) != set(registry['development_fixtures']):
        raise ValueError('Unregistered fixture set')
    for mid, entry in entries.items():
        if (entry['split'] != registry['development_fixtures'][mid]['split']
                or entry['game']['id'] != int(mid)
                or entry['game']['competition_id'] != 61):
            raise ValueError('Original external split required')
    baseline_hash = _frozen_model(repo)
    source_files = [Path(__file__), repo/'development/sequence_possession.py',
                    repo/'development/sequence_metrics.py', repo/'development/continuity.py']
    hashes = {p.relative_to(repo).as_posix(): digest(p) for p in source_files}
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'before-access.json', {
        'version': spec['version'], 'provided_fixture_used': False,
        'source_hashes': hashes, 'baseline_model_sha256': baseline_hash,
        'study_plan_sha256': digest(study_plan), 'local_plan_sha256': digest(local_plan),
        'data_registry_sha256': digest(repo/'external-selection.json'),
        'entries': entries, 'previous_external_exposure': True,
        'fresh_test_used': False, 'human_ground_truth': False})
    radii, relative_speeds, gaps = [], [], []
    start = time.perf_counter()
    for mid, entry in entries.items():
        if entry['split'] != 'train':
            continue
        x, y = load(entry)
        d, relative, usable = measurements(x)
        known = usable & np.isin(y, ('H', 'A'))
        owner = np.where(y == 'H', 0, 1)
        own_d = d[np.arange(len(y)), owner]
        own_speed = relative[np.arange(len(y)), owner]
        radii.extend(own_d[known].tolist())
        relative_speeds.extend(own_speed[known & np.isfinite(own_speed)].tolist())
        missing = ~usable
        bounds = np.r_[0, np.flatnonzero((missing[1:] != missing[:-1]) | (x['period'][1:] != x['period'][:-1])) + 1, len(y)]
        for a, b in zip(bounds[:-1], bounds[1:]):
            if missing[a] and a > 0 and b < len(y) and x['period'][a] in (1, 2) and x['period'][a-1] == x['period'][b] == x['period'][a]:
                gaps.append((b-a)/float(x['fps']))
        print(json.dumps({'calibrated_external_fixture': mid}), flush=True)
    if not radii or not relative_speeds or not gaps:
        raise ValueError('Insufficient external calibration')
    calibration = {'radii': np.maximum(.01, np.quantile(radii, spec['radius_training_quantiles'])).tolist(),
                   'relative_speed_scale_mps': max(.01, float(np.median(relative_speeds))),
                   'max_gap_s': max(.1, float(np.median(gaps))),
                   'training_fixture_count': sum(e['split'] == 'train' for e in entries.values())}
    write(out/'calibration.json', calibration)
    configs = [SequenceConfig(r, calibration['relative_speed_scale_mps'], calibration['max_gap_s'], s, mode)
               for r, s, mode in itertools.product(calibration['radii'], spec['switch_cost_seconds'], spec['evidence_modes'])]
    # Explicit unsmoothed ablations for each evidence adapter and radius.
    configs += [SequenceConfig(r, calibration['relative_speed_scale_mps'], calibration['max_gap_s'], 0., mode)
                for r, mode in itertools.product(calibration['radii'], spec['evidence_modes'])]
    write(out/'candidate-freeze.json', {'configs': [asdict(c) for c in configs], 'before_validation': True})
    validation = []
    model = json.loads((repo/'model.json').read_text())
    controls = {name: [] for name in ('frozen_baseline', 'nearest')}
    for mid, entry in entries.items():
        if entry['split'] != 'validation':
            continue
        x, y = load(entry)
        d, relative, usable = measurements(x)
        params = dict(model['base_config_at_10fps'])
        for k in ('confirmation_frames', 'gap_frames', 'hold_frames'):
            params[k] = int(np.ceil(params[k] * float(x['fps']) / model['training_fps']))
        for name, policy, config in [('frozen_baseline', model['policy'], DecoderConfig(**params)), ('nearest', 'nearest', None)]:
            pred = infer(x, config, policy)
            controls[name].append({'id': mid, 'metrics': evaluate(y, pred, x['period'])})
        validation.append((mid, x, y, d, relative, usable))
    results = []
    for number, cfg in enumerate(configs):
        games = []
        for mid, x, y, d, relative, usable in validation:
            signed = evidence(d, relative, usable, cfg)
            pred = decode(signed, usable, x['period'], x['frame'], float(x['fps']), cfg)
            games.append({'id': mid, 'metrics': evaluate(y, pred, x['period'])})
        results.append({'config': asdict(cfg), 'games': games, 'mean': aggregate(games)})
        if (number+1) % 6 == 0:
            print(json.dumps({'external_candidates_done': number+1, 'total': len(configs),
                              'seconds': round(time.perf_counter()-start, 1)}), flush=True)
    results.sort(key=lambda r: (-r['mean']['provider_filled_spell_f1'],
                               -r['mean']['provider_macro_f1_HA'], json.dumps(r['config'], sort_keys=True)))
    write(out/'validation-results.json', {'candidates': results, 'controls': controls})
    selected = results[0]
    baseline = aggregate(controls['frozen_baseline'])
    wins = sum(g['metrics']['provider_filled_spell_f1'] > b['metrics']['provider_filled_spell_f1']
               for g, b in zip(selected['games'], controls['frozen_baseline']))
    accepted = (selected['mean']['provider_filled_spell_f1'] > baseline['provider_filled_spell_f1']
                and selected['mean']['provider_macro_f1_HA'] >= baseline['provider_macro_f1_HA'] and wins >= 3)
    if _frozen_model(repo) != baseline_hash or any(digest(repo/p) != h for p, h in hashes.items()):
        raise ValueError('Sources changed during study')
    result = {'version': spec['version'], 'selected_config': selected['config'],
              'selected_mean': selected['mean'], 'baseline_mean': baseline,
              'selected_games': selected['games'], 'validation_spell_wins': wins,
              'accepted_external_proxy_candidate': bool(accepted), 'candidate_count': len(configs),
              'source_hashes': hashes, 'provided_fixture_used': False, 'fresh_test_used': False,
              'human_ground_truth': False, 'competition_score': False,
              'selected_combined_release': False, 'D_validated': False, 'vision_validated': False,
              'calibration': calibration, 'elapsed_seconds': time.perf_counter()-start}
    write(out/'result.json', result)
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--local-plan', required=True)
    p.add_argument('--study-plan', default='sequence-selection-plan.json')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    run(a.local_plan, a.study_plan, a.out)
