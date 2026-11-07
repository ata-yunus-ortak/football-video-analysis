"""Registered local video measurements on external/synthetic fixtures only.

No provided-match tuning, cloud API, annotation UI, team labels or possession
output. Retains presentation times relative to the first decoded frame,
and every processed frame,
including empty detections. Match inputs and outputs stay outside this repo.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import time
import math
from collections import Counter
from development.vision import VisionConfig, LocalVision
from development.vision_measurements import SceneChangeConfig, SceneContinuity, VisionMeasurements
from development.homography import FrameHomographies
from .metrica_data import external_output, sha256
from .dead_ball_audit import _frozen_model


def read_frames(path):
    import av
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        if not stream.average_rate:
            raise ValueError('Video must expose a frame rate for the tracking clock')
        fps = float(stream.average_rate)
        origin = None
        for index, frame in enumerate(container.decode(stream)):
            if frame.pts is None:
                raise ValueError('Presentation timestamp absent; no invented frame clock')
            pts = float(frame.pts * frame.time_base)
            if origin is None:
                origin = pts
            yield index, pts - origin, fps, frame.to_ndarray(format='rgb24')


def run(video, config_path, out, device='cpu', *, frame_reader=read_frames, factory=LocalVision):
    video, config_path = Path(video), Path(config_path)
    spec = json.loads(config_path.read_text(encoding='utf-8'))
    fixture = spec.get('fixture', {})
    if (fixture.get('source_kind') not in ('permitted_external_video', 'synthetic_fixture')
            or fixture.get('provided_fixture_used') is not False or not fixture.get('id')
            or not fixture.get('provenance') or not spec.get('rationale')
            or 'bar-ath' in video.name.lower()):
        raise ValueError('Registered permitted external/synthetic fixture and rationale required')
    cfg = VisionConfig(**spec['parameters'])
    scene_cfg = SceneChangeConfig(**spec['scene_change_parameters']) if 'scene_change_parameters' in spec else None
    weights = Path(spec['weights']['path'])
    if not weights.is_absolute():
        weights = config_path.resolve().parent / weights
    if (spec['weights'].get('license') != 'Apache-2.0' or not spec['weights'].get('source_url')
            or spec['weights'].get('size') != cfg.size):
        raise ValueError('Reviewed checkpoint size, source and license required')
    if sha256(video) != fixture.get('video_sha256') or sha256(weights) != spec['weights'].get('sha256'):
        raise ValueError('Video/checkpoint hash differs from registration')
    start, count = spec['start_frame'], spec['max_frames']
    if type(start) is not int or start < 0 or type(count) is not int or count < 1:
        raise ValueError('Explicit nonnegative start and positive frame count required')
    geometry, pitch = None, None
    if 'geometry' in spec:
        data = spec['geometry']
        path = Path(data['path'])
        if not path.is_absolute():
            path = Path(config_path).resolve().parent / path
        if (data.get('fixture_id') != fixture['id'] or data.get('source_video_sha256') != fixture['video_sha256']
                or 'bar-ath' in path.name.lower() or sha256(path) != data.get('sha256')):
            raise ValueError('Same-fixture/video homography provenance and content hash required')
        geometry, pitch = FrameHomographies(path), data['pitch_m']
    repo = Path(__file__).resolve().parents[1]
    baseline_hash = _frozen_model(repo)
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), repo / 'development' / 'vision.py',
               repo / 'development' / 'vision_measurements.py', repo / 'development' / 'homography.py']
    packages = {}
    for name in ('torch', 'torchvision', 'rfdetr', 'sahi', 'supervision', 'numpy', 'av'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    registration = {'version': 'local-vision-experimental-v2', 'selected_release': False,
        'provided_fixture_used': False, 'config': spec, 'config_sha256': sha256(config_path),
        'device': device, 'packages': packages, 'before_inference': True,
        'video_path': str(video.resolve()),
        'baseline_model_sha256': baseline_hash,
        'source_sha256': {p.relative_to(repo).as_posix(): sha256(p) for p in sources}}
    (out / 'registration.json').write_text(json.dumps(registration, indent=2), encoding='utf-8')
    engine, continuity, measurements = None, None, None
    processed, objects = 0, 0
    kind_counts, tracked_people, projected_people, ball_frames, resets = Counter(), 0, 0, 0, 0
    clock_previous, fps_previous = None, None
    begin = time.perf_counter()
    with (out / 'observations.jsonl').open('x', encoding='utf-8') as stream:
        for index, timestamp, fps, rgb in frame_reader(video):
            if index < start:
                continue
            if processed >= count:
                break
            if type(index) is not int or index != start + processed:
                raise ValueError('Registered source frame sequence is not fully covered')
            if not math.isfinite(timestamp) or not math.isfinite(fps) or fps <= 0:
                raise ValueError('Finite presentation timestamp and positive FPS required')
            if clock_previous is not None and (timestamp <= clock_previous or fps != fps_previous):
                raise ValueError('Non-increasing PTS or changing FPS; split the video into registered segments')
            if engine is None:
                engine = factory(cfg, weights, fps, device)
                continuity = SceneContinuity(fps, scene_cfg)
                measurements = VisionMeasurements(fps, geometry, pitch,
                    scene_cfg.max_pair_gap_s if scene_cfg is not None else None)
            context = continuity.observe(rgb, index, timestamp)
            if context['continuity_reset']:
                if not hasattr(engine, 'reset_tracking'):
                    raise ValueError('Detector adapter must reset tracking at a source discontinuity')
                engine.reset_tracking()
                resets += 1
            rows, frame_evidence = measurements.annotate(engine.process(rgb), index, timestamp,
                int(rgb.shape[1]), int(rgb.shape[0]), context)
            stream.write(json.dumps({'source_frame': index, 'video_time_s': timestamp,
                'fps': fps, 'width': int(rgb.shape[1]), 'height': int(rgb.shape[0]),
                'objects': rows, 'frame_evidence': frame_evidence, 'possession_inferred': False}, allow_nan=False) + '\n')
            processed += 1
            objects += len(rows)
            kind_counts.update(row['kind'] for row in rows)
            tracked_people += frame_evidence['tracked_person_count']
            projected_people += frame_evidence['projected_person_candidate_count']
            ball_frames += frame_evidence['ball_candidate_count'] > 0
            clock_previous, fps_previous = timestamp, fps
            if processed % 25 == 0:
                stream.flush()
                print(json.dumps({'processed_frames': processed, 'requested_frames': count,
                                  'elapsed_s': round(time.perf_counter() - begin, 1)}), flush=True)
    if processed != count:
        raise ValueError('Registered frame range is not fully covered; partial observations retained')
    if any(sha256(repo / path) != digest for path, digest in registration['source_sha256'].items()):
        raise ValueError('Vision source changed during inference')
    if _frozen_model(repo) != baseline_hash:
        raise ValueError('Frozen baseline changed during vision inference')
    summary = {'processed_frames': processed, 'requested_frames': count, 'objects': objects,
        'elapsed_s_including_model_load': time.perf_counter() - begin, 'accuracy_evaluated': False,
        'selected_release': False, 'teams_assigned': False, 'possession_inferred': False}
    summary.update(detection_counts=dict(kind_counts), tracked_person_observations=tracked_people,
        projected_person_candidates=projected_people, frames_with_ball_candidates=ball_frames,
        tracking_resets=resets, calibration_validated=False, hybrid_ready=False)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    print(json.dumps(run(args.video, args.config, args.out, args.device), indent=2))
