"""Video-led ownership experiment on registered external/synthetic measurements.

Camera manifests bind completed image analysis, automatic player-only identity
contexts, and the raw metadata/tracking/homography hashes. No old owner input.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from development.visual_possession import VisualCamera, VisualPossessionConfig, choose_view
from .ball_support_experiment import indexed, read_json
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256


def camera_frames(path, context_path, expected, spec):
    """Read long matches with one native frame/context in memory."""
    previous, count = None, 0
    with Path(path).open(encoding='utf-8') as images, Path(context_path).open(encoding='utf-8') as contexts:
        def next_context():
            line = contexts.readline()
            return json.loads(line) if line else None
        context, last_context = next_context(), -1
        for line in images:
            frame = json.loads(line); f = frame['source_frame']
            if type(f) is not int or f < 0 or frame.get('schema') != 'project-image-analysis-v1' or frame.get('possession') is not None:
                raise ValueError('Source-bound image measurements only')
            if previous is not None and (frame['source_id'] != previous['source_id']
                    or f != previous['source_frame'] + 1 or frame['video_time_s'] <= previous['video_time_s']
                    or frame['fps'] != previous['fps']):
                raise ValueError('Stable native camera sequence required')
            chosen = None
            if context is not None:
                cf = context['source_frame']
                if type(cf) is not int or cf <= last_context or cf < f:
                    raise ValueError('Ordered unique, used identity contexts required')
                if cf == f:
                    chosen = context; last_context = cf; context = next_context()
                    if any(chosen[k + '_sha256'] != spec[k + '_sha256'] for k in ('tracking', 'metadata', 'homography')):
                        raise ValueError('Identity context provenance differs')
            previous, count = frame, count + 1
            yield frame, chosen
        if context is not None or count != expected: raise ValueError('Incomplete image/context coverage')


def load_camera(manifest_path):
    manifest_path = Path(manifest_path)
    spec = read_json(manifest_path)
    if (spec.get('provided_fixture_used') is not False or spec.get('reference_annotations_as_inputs') is not False
            or spec.get('source_kind') not in ('permitted_external_video', 'synthetic_fixture')
            or spec.get('origin') != 'automatic_player_tracking'):
        raise ValueError('Registered external/synthetic player-identity manifest required')
    paths = [manifest_path]
    for role in ('tracking', 'metadata', 'homography', 'contexts'):
        p = Path(spec[role + '_path'])
        if not p.is_absolute() or sha256(p) != spec[role + '_sha256']: raise ValueError('Identity input content changed')
        paths.append(p)
    analysis = Path(spec['analysis_path'])
    reg, summary = read_json(analysis / 'registration.json'), read_json(analysis / 'summary.json')
    if (reg.get('provided_fixture_used') is not False or reg['fixture']['provided_fixture_used'] is not False
            or reg['fixture']['id'] != spec['fixture_id']
            or reg['fixture']['source_kind'] != spec['source_kind']
            or sha256(analysis / 'frames.jsonl') != summary['output_sha256']):
        raise ValueError('Intact same-fixture image analysis required')
    paths += [analysis / name for name in ('registration.json', 'summary.json', 'frames.jsonl')]
    frames = camera_frames(analysis / 'frames.jsonl', spec['contexts_path'], summary['frames'], spec)
    return spec, frames, summary['frames'], paths


def run(tactical_manifest, plan, out, broadcast_manifest=None, pair_alignment=None):
    if (broadcast_manifest is None) != (pair_alignment is None): raise ValueError('Broadcast and automatic pair mapping required together')
    repo, out, plan = Path(__file__).resolve().parents[1], external_output(out), Path(plan)
    baseline = _frozen_model(repo)
    spec = read_json(plan)
    if (spec.get('provided_fixture_used') is not False or spec.get('selected_release') is not False
            or spec.get('parameters_origin') != 'synthetic_engineering_checks_only'):
        raise ValueError('Registered unselected external-only video-led plan required')
    cfg = VisualPossessionConfig(**spec['parameters'])
    t_spec, tactical, total_tactical, paths = load_camera(tactical_manifest)
    broadcast, pairs = iter(()), {}
    if broadcast_manifest is not None:
        b_spec, broadcast, _, b_paths = load_camera(broadcast_manifest)
        if t_spec['fixture_id'] != b_spec['fixture_id']: raise ValueError('Same match canonical roster required')
        pairs = indexed(pair_alignment, 'primary_frame')
        paths += b_paths + [Path(pair_alignment)]
    paths += [plan, repo / 'development/visual_possession.py', Path(__file__)]
    hashes = {str(p.resolve()): sha256(p) for p in paths}
    out.mkdir(parents=True, exist_ok=False)
    (out / 'registration.json').write_text(json.dumps({'before_inference': True, 'plan': spec,
        'input_source_sha256': hashes, 'baseline_model_sha256': baseline,
        'provided_fixture_used': False, 'selected_release': False, 'reference_annotations_as_inputs': False,
        'tracking_ball_used': False, 'baseline_owner_used': False}, indent=2), encoding='utf-8')
    t_engine, b_engine = VisualCamera(cfg), VisualCamera(cfg)
    # Consume broadcast chronologically with one result cached, not a whole match.
    broadcast = iter(broadcast)
    last_b, broadcast_done, used_pairs = None, False, set()
    counts, reasons, sources, total, previous_pair = Counter(), Counter(), Counter(), 0, None
    with (out / 'frames.jsonl').open('x', encoding='utf-8') as records, (out / 'possession.csv').open('x', newline='', encoding='utf-8') as table:
        writer = csv.writer(table); writer.writerow(['frame', 'label', 'owner_id', 'decision_source', 'reason'])
        for packet, context in tactical:
            f = packet['source_frame']
            t = t_engine.consume(packet, context)
            pair = pairs.get(f)
            if pair is not None:
                used_pairs.add(f)
                native_pair = (f, pair['secondary_frame'])
                if (previous_pair is not None and f == previous_pair[0] + 1
                        and pair['secondary_frame'] != previous_pair[1] + 1):
                    pair = dict(pair, verified=False)
                previous_pair = native_pair
            b = None
            if pair is not None:
                target = pair['secondary_frame']
                if type(target) is not int or target < 0: raise ValueError('Native broadcast index required')
                while not broadcast_done and (last_b is None or last_b['source_frame'] < target):
                    item = next(broadcast, None)
                    if item is None:
                        broadcast_done = True
                    else:
                        bp, bc = item; last_b = b_engine.consume(bp, bc)
                if last_b is not None and last_b['source_frame'] == target: b = last_b
                elif last_b is None or target > last_b['source_frame']:
                    raise ValueError('Mapped broadcast frame absent')
                # Backward/reused camera mappings cannot revive cached ownership.
            result = choose_view(t, b, pair, cfg)
            records.write(json.dumps(result, allow_nan=False) + '\n')
            writer.writerow([f, result['label'], result['owner_id'], result['decision_source'], result['decision_reason']])
            counts[result['label']] += 1; reasons[result['decision_reason']] += 1; sources[result['decision_source']] += 1
            total += 1
    for _ in broadcast: pass  # Validate remaining frame/context structure without retaining it.
    if used_pairs != set(pairs) or total != total_tactical: raise ValueError('Unused mapping or incomplete tactical run')
    if _frozen_model(repo) != baseline or any(sha256(p) != digest for p, digest in hashes.items()):
        raise ValueError('Input, inference source or frozen baseline changed')
    result = {'frames': total, 'label_counts': dict(counts), 'decision_sources': dict(sources),
              'decision_reasons': dict(reasons), 'tracking_ball_used': False, 'baseline_owner_used': False,
              'provided_fixture_used': False, 'accuracy_evaluated': False, 'selected_release': False,
              'dead_ball_enabled': False, 'output_sha256': sha256(out / 'frames.jsonl'),
              'csv_sha256': sha256(out / 'possession.csv')}
    (out / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('tactical-manifest', 'plan', 'out'): parser.add_argument('--' + key, required=True)
    for key in ('broadcast-manifest', 'pair-alignment'): parser.add_argument('--' + key)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
