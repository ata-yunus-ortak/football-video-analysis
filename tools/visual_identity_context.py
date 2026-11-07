"""Project automatic ATD player coordinates for video identity association only.

Never reads the ATD ball group or any possession/annotation file. Native frame
offsets must be declared. Missing validation evidence stays false, never ready.
"""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from development.homography import FrameHomographies
from .ball_support_experiment import indexed, read_json
from .metrica_data import external_output, sha256


def run(spec_path, out):
    spec_path, out = Path(spec_path), external_output(out)
    spec = read_json(spec_path)
    if (spec.get('provided_fixture_used') is not False or spec.get('reference_annotations_as_inputs') is not False
            or spec.get('source_kind') not in ('permitted_external_video', 'synthetic_fixture')):
        raise ValueError('Registered external/synthetic identity preparation only')
    for key in ('tracking_frame_offset', 'homography_frame_offset'):
        if type(spec[key]) is not int: raise ValueError('Explicit integer native frame offsets required')
    files = {key: Path(spec[key + '_path']) for key in ('tracking', 'metadata', 'homography')}
    for key, path in files.items():
        if not path.is_absolute() or sha256(path) != spec[key + '_sha256']: raise ValueError('Identity source hash differs')
    analysis = Path(spec['analysis_path'])
    reg, summary = read_json(analysis / 'registration.json'), read_json(analysis / 'summary.json')
    if (reg['provided_fixture_used'] is not False or reg['fixture']['provided_fixture_used'] is not False
            or reg['fixture']['id'] != spec['fixture_id'] or reg['fixture']['source_kind'] != spec['source_kind']
            or sha256(analysis / 'frames.jsonl') != summary['output_sha256']):
        raise ValueError('Intact same-fixture image run required')
    # Retain clocks only during preparation, never every detection in a full match.
    packets = {}
    with (analysis / 'frames.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line); f = row['source_frame']
            if type(f) is not int or f < 0 or f in packets: raise ValueError('Unique native frames required')
            packets[f] = {k: row[k] for k in ('source_id', 'source_frame', 'camera_epoch', 'video_time_s', 'fps')}
    if len(packets) != summary['frames']: raise ValueError('Incomplete image run')
    evidence = indexed(spec['camera_evidence_path'], 'source_frame') if spec.get('camera_evidence_path') else {}
    if set(evidence) - set(packets): raise ValueError('Unused camera evidence')
    xml = ET.parse(files['metadata']).getroot()
    teams = [t.get('id') for t in xml.iter('Team')]
    roster = list(xml.iter('Player'))
    if len(teams) != 2 or len(set(teams)) != 2 or None in teams: raise ValueError('Two metadata teams required')
    if not roster or any(p.get('id') is None or p.get('teamId') not in teams for p in roster):
        raise ValueError('Explicit player IDs and metadata team membership required')
    canonical = spec.get('canonical_player_ids', {})
    ids = [canonical.get(p.get('id'), p.get('id')) for p in roster]
    if len(set(ids)) != len(ids): raise ValueError('Canonical identities must be unique within camera')
    dimensions = [float(xml.findtext('.//FieldSize/Width')), float(xml.findtext('.//FieldSize/Height'))]
    fps = float(xml.findtext('.//FrameRate'))
    if any(p['fps'] != fps for p in packets.values()): raise ValueError('Native FPS differs; no implicit resampling')
    geometry = FrameHomographies(files['homography'])
    paths = [spec_path, *files.values(), Path(__file__), Path(__file__).resolve().parents[1] / 'development/homography.py',
             analysis / 'frames.jsonl', analysis / 'registration.json', analysis / 'summary.json']
    if spec.get('camera_evidence_path'):
        path = Path(spec['camera_evidence_path'])
        if sha256(path) != spec['camera_evidence_sha256']: raise ValueError('Camera evidence hash differs')
        paths.append(path)
    hashes = {str(p.resolve()): sha256(p) for p in paths}
    out.mkdir(parents=True, exist_ok=False)
    (out / 'registration.json').write_text(json.dumps({'before_preparation': True,
        'provided_fixture_used': False, 'input_and_source_sha256': hashes,
        'tracking_ball_read': False, 'reference_annotations_read': False}, indent=2), encoding='utf-8')
    wanted = {f + spec['tracking_frame_offset']: f for f in packets}
    if any(f < 0 for f in wanted): raise ValueError('Negative native tracking index')
    found = set()
    with files['tracking'].open(encoding='utf-8-sig') as source, (out / 'contexts.jsonl').open('x', encoding='utf-8') as writer:
        for index, line in enumerate(source):
            # ATD prefix/player segment only. Ball segment is never parsed.
            parts = line.split(':', 2)
            if len(parts) != 3 or int(parts[0]) != index + 1: raise ValueError('Consecutive one-based ATD rows required')
            if index not in wanted: continue
            f = wanted[index]; packet = packets[f]; found.add(f)
            h_index = f + spec['homography_frame_offset']
            rows = parts[1].split(';')
            if len(rows) != len(roster): raise ValueError('ATD slots differ from metadata roster')
            players = []
            for slot, row in enumerate(rows):
                values = row.split(',')
                xy = [float(v) for v in values[:2]]
                if len(xy) != 2: raise ValueError('Player x/y required')
                if np.isfinite(xy).all():
                    players.append({'player_id': ids[slot], 'team': 'H' if roster[slot].get('teamId') == teams[0] else 'A', 'normalized_xy': xy})
            e = evidence.get(f)
            if e is not None:
                expected = {'source_frame', 'source_id', 'camera_epoch', 'video_time_s', 'alignment_validated',
                            'clock_error_bound_s', 'calibration_validated', 'frame_kind', 'origin'}
                if set(e) != expected or e['origin'] != 'automatic_camera_validation':
                    raise ValueError('Source-bound automatic camera validation only')
                if any(e[k] != packet[k] for k in ('source_id', 'source_frame', 'camera_epoch', 'video_time_s')):
                    raise ValueError('Camera evidence bound to different frame')
            matrix_ok = 0 <= h_index < len(geometry.matrices) and bool(geometry.usable[h_index])
            context = {k: packet[k] for k in ('source_id', 'source_frame', 'video_time_s', 'camera_epoch')}
            context.update(origin='automatic_player_tracking', players=players, pitch_m=dimensions,
                **{k + '_sha256': spec[k + '_sha256'] for k in files},
                normalized_pitch_to_image=geometry.matrices[h_index].tolist() if matrix_ok else None,
                alignment_validated=e['alignment_validated'] if e else False,
                clock_error_bound_s=e['clock_error_bound_s'] if e else 0.,
                calibration_validated=bool(matrix_ok and e and e['calibration_validated'] is True),
                frame_kind=e['frame_kind'] if e else 'unknown')
            writer.write(json.dumps(context, allow_nan=False) + '\n')
    if found != set(packets) or any(sha256(p) != digest for p, digest in hashes.items()):
        raise ValueError('Incomplete identity preparation or changed source')
    manifest = {k: spec[k] for k in ('fixture_id', 'source_kind', 'analysis_path')}
    manifest.update(origin='automatic_player_tracking', provided_fixture_used=False, reference_annotations_as_inputs=False,
                    contexts_path=str((out / 'contexts.jsonl').resolve()), contexts_sha256=sha256(out / 'contexts.jsonl'))
    for k, p in files.items(): manifest[k + '_path'], manifest[k + '_sha256'] = str(p), spec[k + '_sha256']
    (out / 'camera-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True); parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.spec, args.out), indent=2))
