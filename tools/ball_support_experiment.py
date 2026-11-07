"""Read-only external/synthetic image vs automatic tracking association experiment."""
import argparse
from collections import Counter
import json
from pathlib import Path

from development.ball_tracking_support import SupportConfig, assess, cross_check
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def indexed(path, key):
    result = {}
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            value = row[key]
            if type(value) is not int or value < 0 or value in result:
                raise ValueError('Unique nonnegative native frame index required')
            result[value] = row
    return result


def run(analysis, plan, out, support_registration=None, secondary_run=None, pair_alignment=None):
    analysis, plan, out = Path(analysis), Path(plan), external_output(out)
    if (secondary_run is None) != (pair_alignment is None):
        raise ValueError('Secondary run and pair mapping must be supplied together')
    repo = Path(__file__).resolve().parents[1]
    baseline = _frozen_model(repo)
    spec, registration = read_json(plan), read_json(analysis / 'registration.json')
    if (spec.get('provided_fixture_used') is not False or spec.get('selected_release') is not False
            or spec.get('parameters_origin') != 'Fixed synthetic engineering checks, not football accuracy selection'
            or registration.get('provided_fixture_used') is not False
            or registration['fixture'].get('provided_fixture_used') is not False
            or registration['fixture'].get('source_kind') not in ('permitted_external_video', 'synthetic_fixture')):
        raise ValueError('Registered experimental external/synthetic inputs only')
    cfg = SupportConfig(**spec['parameters'])
    paths = [plan, analysis / 'registration.json', analysis / 'summary.json', analysis / 'frames.jsonl',
             repo / 'development/ball_tracking_support.py', Path(__file__)]
    hints, secondary, pairs = {}, {}, {}
    bundle = None
    if support_registration is not None:
        bundle = read_json(support_registration)
        if (bundle.get('origin') != 'automatic_tracking' or bundle.get('provided_fixture_used') is not False
                or bundle.get('reference_annotations_as_inputs') is not False
                or bundle.get('fixture_id') != registration['fixture']['id']):
            raise ValueError('Same-fixture automatic tracking, never reference-derived support, required')
        paths.append(Path(support_registration))
        for role in ('tracking', 'projections'):
            path = Path(bundle[role + '_path'])
            if sha256(path) != bundle[role + '_sha256']: raise ValueError('Support content hash differs')
            paths.append(path)
        hints = indexed(bundle['projections_path'], 'source_frame')
        if any(h['tracking_sha256'] != bundle['tracking_sha256'] for h in hints.values()):
            raise ValueError('Every projection must identify registered automatic tracking content')
    if secondary_run is not None:
        secondary_run = Path(secondary_run)
        second_reg = read_json(secondary_run / 'registration.json')
        second_summary = read_json(secondary_run / 'summary.json')
        if (second_reg['provided_fixture_used'] is not False
                or second_reg['fixture_id'] != registration['fixture']['id']
                or sha256(secondary_run / 'frames.jsonl') != second_summary['output_sha256']):
            raise ValueError('Intact same-fixture secondary support experiment required')
        secondary = indexed(secondary_run / 'frames.jsonl', 'source_frame')
        pairs = indexed(pair_alignment, 'primary_frame')
        paths += [secondary_run / name for name in ('frames.jsonl', 'registration.json', 'summary.json')]
        paths.append(Path(pair_alignment))
    frozen = {str(p.resolve()): sha256(p) for p in paths}
    expected = read_json(analysis / 'summary.json')
    if expected['output_sha256'] != sha256(analysis / 'frames.jsonl'):
        raise ValueError('Registered project image output changed')
    out.mkdir(parents=True, exist_ok=False)
    before = {'version': 'tracking-ball-support-experiment-v1', 'before_experiment': True,
              'provided_fixture_used': False, 'reference_annotations_as_inputs': False,
              'fixture_id': registration['fixture']['id'], 'plan': spec, 'input_and_source_sha256': frozen,
              'baseline_model_sha256': baseline, 'support_available': bundle is not None,
              'same_image_tracking_errors_may_be_correlated': True}
    (out / 'registration.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    counts, pair_counts, total, previous, used_hints, used_pairs = Counter(), Counter(), 0, None, set(), set()
    with (analysis / 'frames.jsonl').open(encoding='utf-8') as stream, (out / 'frames.jsonl').open('x', encoding='utf-8') as writer:
        for line in stream:
            packet = json.loads(line)
            frame = packet['source_frame']
            if (type(frame) is not int or frame < 0 or (previous is not None and
                (frame != previous['source_frame'] + 1 or packet['source_id'] != previous['source_id']
                 or packet['video_time_s'] <= previous['video_time_s']))):
                raise ValueError('Consecutive source-bound image packets required')
            if frame in hints: used_hints.add(frame)
            evidence = assess(packet, hints.get(frame), cfg)
            pair = pairs.get(frame)
            other = None
            if pair is not None:
                used_pairs.add(frame)
                other_packet = secondary.get(pair['secondary_frame'])
                if other_packet is None: raise ValueError('Pair points to missing secondary frame')
                other = other_packet['tracking_support']
            evidence['cross_check'] = cross_check(evidence, other, pair, cfg)
            counts[evidence['reason']] += 1
            pair_counts[evidence['cross_check']['reason']] += 1
            packet['tracking_support'] = evidence
            writer.write(json.dumps(packet, allow_nan=False) + '\n')
            total += 1
            previous = packet
    if total != expected['frames'] or used_hints != set(hints) or used_pairs != set(pairs):
        raise ValueError('Incomplete frame coverage or unused/misaligned support records')
    if any(sha256(p) != digest for p, digest in frozen.items()) or _frozen_model(repo) != baseline:
        raise ValueError('Input/source/frozen baseline changed during experiment')
    result = {'frames': total, 'support_reasons': dict(counts), 'cross_check_reasons': dict(pair_counts),
              'provided_fixture_used': False, 'selected_release': False, 'possession_updated': False,
              'independent_accuracy_test': False, 'reference_annotations_read': False,
              'support_available': bundle is not None, 'output_sha256': sha256(out / 'frames.jsonl')}
    (out / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('analysis', 'plan', 'out'): parser.add_argument('--' + name, required=True)
    for name in ('support-registration', 'secondary-run', 'pair-alignment'): parser.add_argument('--' + name)
    args = vars(parser.parse_args())
    print(json.dumps(run(**args), indent=2))
