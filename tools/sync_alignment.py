"""Build discontinuous clock/geometry review mappings; never fuse possession."""
import argparse
from collections import Counter
import json
from pathlib import Path
import time
import numpy as np
from development.clock_alignment import AlignmentConfig, GeometrySyncConfig, clock_anchors, mapping_segments, refine_anchor
from development.homography import FrameHomographies
from .tracking_viewer import Tracking
from .metrica_data import external_output, sha256


def remove_crossings(segments):
    """Reject both sides of a time-order contradiction rather than picking one."""
    rejected = set()
    for i, left in enumerate(segments):
        for j in range(i + 1, len(segments)):
            if left['b1'] > segments[j]['b0'] + 1e-6:
                rejected.update((i, j))
    return [segment for i, segment in enumerate(segments) if i not in rejected]


def load_clock_source(source):
    folder = Path(source['clock_dir'])
    registration = json.loads((folder / 'registration.json').read_text(encoding='utf-8'))
    summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    if (registration.get('purpose') != 'automatic_read_only_synchronization'
            or registration.get('human_anchors_used') is not False
            or registration.get('parameters_selected_on_provided_fixture') is not False
            or summary.get('source_read_complete') is not True
            or summary.get('accuracy_evaluated') is not False):
        raise ValueError('Completed automatic clock observations without manual selection required')
    path = Path(source['video'])
    if (str(path.resolve()) != registration['video_path']
            or path.stat().st_size != registration['video_bytes']
            or path.stat().st_mtime_ns != registration['video_mtime_ns']):
        raise ValueError('Video differs from automatic clock registration')
    repo = Path(__file__).resolve().parents[1]
    if any(sha256(repo / name) != digest for name, digest in registration['source_sha256'].items()):
        raise ValueError('OCR source differs from registered automatic observations')
    observations = [json.loads(line) for line in (folder / 'observations.jsonl').read_text(encoding='utf-8').splitlines()]
    if any(row.get('human_annotated') is not False for row in observations):
        raise ValueError('Only automatic clock observations allowed')
    return observations, registration


def run(bundle_path, plan_path, out):
    bundle_path, plan_path = Path(bundle_path), Path(plan_path)
    bundle = json.loads(bundle_path.read_text(encoding='utf-8'))
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if (plan.get('selected_for_submission') is not False
            or plan.get('parameters_origin') != 'synthetic_engineering_checks_only'):
        raise ValueError('This tool only produces an unselected automatic review mapping')
    cfg, geometry_cfg = AlignmentConfig(**plan['clock_alignment']), GeometrySyncConfig(**plan['geometry_support'])
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    sources, readings, registrations, arrays, geometry, identities = {}, {}, {}, {}, {}, {}
    for key in ('tactical', 'broadcast'):
        source = bundle[key]
        readings[key], registrations[key] = load_clock_source(source)
        arrays[key] = Tracking(source['meta'], source['tracking'])
        geometry[key] = FrameHomographies(source['homography'])
        tracking = arrays[key]
        import av
        with av.open(source['video']) as container:
            video_stream = container.streams.video[0]
            video_frames = video_stream.frames
            video_fps = float(video_stream.average_rate or 0)
        if (video_fps != tracking.fps or video_frames <= 0
                or abs(video_frames - len(tracking.data)) > 1):
            raise ValueError('Source video/ATD frame-rate or frame-count contract differs')
        if len(geometry[key].matrices) != len(tracking.data):
            raise ValueError('Homography/tracking frame counts must agree within each source')
        identities[key] = np.array([obj['team'] for obj in tracking.objects])
        sources[key] = {**source, 'video_sha256': registrations[key]['video_sha256'],
                        'video_bytes': registrations[key]['video_bytes'],
                        'video_mtime_ns': registrations[key]['video_mtime_ns'],
                        'fps': tracking.fps, 'frames': len(tracking.data),
                        'video_frames': video_frames,
                        'meta_sha256': sha256(Path(source['meta'])),
                        'tracking_sha256': sha256(Path(source['tracking'])),
                        'homography_sha256': sha256(Path(source['homography'])),
                        'clock_observations_sha256': sha256(Path(source['clock_dir']) / 'observations.jsonl')}
    tactical, broadcast = arrays['tactical'], arrays['broadcast']
    if not np.array_equal(tactical.pitch, broadcast.pitch):
        raise ValueError('Sources must use the same pitch coordinate dimensions')
    if set(tactical.teams) != set(broadcast.teams) or len(set(tactical.teams)) != 2:
        raise ValueError('Team metadata must identify the same two distinct teams')
    # Team numbers are local to each XML. Names, never slot IDs, establish team order.
    bteams = identities['broadcast'].copy()
    for old, name in enumerate(broadcast.teams):
        bteams[identities['broadcast'] == old] = tactical.teams.index(name)
    repo = Path(__file__).resolve().parents[1]
    files = [Path(__file__), repo / 'development' / 'clock_alignment.py', repo / 'development' / 'homography.py',
             repo / 'tools' / 'tracking_viewer.py', repo / 'tools' / 'clock_observations.py']
    source_hashes = {p.relative_to(repo).as_posix(): sha256(p) for p in files}
    registration = {'sources': sources, 'plan': plan, 'plan_sha256': sha256(plan_path),
                    'source_sha256': source_hashes, 'human_anchors_used': False,
                    'selected_for_submission': False, 'before_alignment': True}
    (out / 'registration.json').write_text(json.dumps(registration, indent=2), encoding='utf-8')
    anchors = clock_anchors(readings['tactical'], readings['broadcast'], cfg)
    refined, started = [], time.monotonic()
    for index, anchor in enumerate(anchors):
        refined.append(refine_anchor(anchor,
            tactical.data[:sources['tactical']['video_frames'], :, :2],
            broadcast.data[:sources['broadcast']['video_frames'], :, :2],
            identities['tactical'], bteams, tactical.pitch, tactical.fps, broadcast.fps, geometry_cfg,
            geometry['tactical'].usable, geometry['broadcast'].usable))
        if (index + 1) % 100 == 0:
            print(json.dumps({'anchors_processed': index + 1, 'anchors_total': len(anchors),
                              'elapsed_s': round(time.monotonic() - started, 1)}), flush=True)
    raw_segments = mapping_segments(refined, cfg)
    segments = remove_crossings(raw_segments)
    result = {'version': 'automatic-review-alignment-v1', 'selected_for_submission': False,
              'usable_for_possession': False, 'human_anchors_used': False,
              'parameters_selected_on_provided_fixture': False, 'sources': sources,
              'segments': segments, 'anchors': refined,
              'summary': {'clock_anchors': len(anchors), 'segments': len(segments),
                          'geometry_support': dict(Counter(a['geometry_status'] for a in refined)),
                          'mapped_tactical_seconds': sum(s['t1'] - s['t0'] for s in segments),
                          'discarded_crossing_segments': len(raw_segments) - len(segments),
                          'accuracy_evaluated': False, 'cross_source_player_ids_merged': False}}
    if any(sha256(repo / name) != digest for name, digest in source_hashes.items()):
        raise ValueError('Alignment source changed during inference')
    (out / 'alignment.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    return result['summary']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.bundle, args.plan, args.out), indent=2), flush=True)
