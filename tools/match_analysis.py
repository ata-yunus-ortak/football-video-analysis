"""Project image-analysis entry point: registered video or completed detector run.

Exports source-bound project measurements, not reference labels or possession.
The frozen release and supplied-match development restrictions stay unchanged.
"""
import argparse
import json
from pathlib import Path

from development.image_analysis import ImageAnalysis
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256


def integrate(vision_run, out, ball_tracking_config=None):
    source, out = Path(vision_run), external_output(out)
    reg = json.loads((source / 'registration.json').read_text())
    summary = json.loads((source / 'summary.json').read_text())
    fixture, config = reg['config']['fixture'], reg['config']
    if (reg.get('provided_fixture_used') is not False
            or fixture.get('provided_fixture_used') is not False
            or fixture.get('source_kind') not in ('permitted_external_video', 'synthetic_fixture')
            or summary['processed_frames'] != config['max_frames']
            or summary.get('possession_inferred') is not False
            or summary.get('teams_assigned') is not False):
        raise ValueError('Completed registered external/synthetic image-only run required')
    repo = Path(__file__).resolve().parents[1]
    baseline = _frozen_model(repo)
    # The canonical adapter never imports a dataset label/reference loader.
    video = Path(reg['video_path'])
    observations = source / 'observations.jsonl'
    if sha256(video) != fixture['video_sha256']: raise ValueError('Registered video changed')
    hashes = {name: sha256(repo / name) for name in ['tools/match_analysis.py', 'development/image_analysis.py']}
    ball_config, ball_plan, foot_config = None, None, None
    if ball_tracking_config is not None:
        from development.ball_tracking import BallTrackingConfig
        ball_plan = json.loads(Path(ball_tracking_config).read_text())
        if (ball_plan.get('provided_fixture_used') is not False or ball_plan.get('selected_release') is not False
                or ball_plan.get('parameters_origin') != 'Fixed synthetic engineering checks, not football accuracy selection'):
            raise ValueError('Registered experimental external-only ball tracking plan required')
        ball_config = BallTrackingConfig(**ball_plan['parameters'])
        hashes['development/ball_tracking.py'] = sha256(repo / 'development/ball_tracking.py')
        if 'foot_context_parameters' in ball_plan:
            from development.ball_foot_context import FootContextConfig
            foot_config = FootContextConfig(**ball_plan['foot_context_parameters'])
            hashes['development/ball_foot_context.py'] = sha256(repo / 'development/ball_foot_context.py')
    expected_sources = {'tools/vision_experiment.py', 'development/vision.py',
                        'development/vision_measurements.py', 'development/homography.py'}
    if (set(reg['source_sha256']) != expected_sources
            or any(sha256(repo / name) != digest for name, digest in reg['source_sha256'].items())):
        raise ValueError('Detector implementation differs from registered observations')
    out.mkdir(parents=True, exist_ok=False)
    prediction_hash = sha256(observations)
    registration = {'version': 'project-image-integration-v1', 'provided_fixture_used': False,
        'selected_release': False, 'baseline_model_sha256': baseline, 'source_sha256': hashes,
        'detector_registration_sha256': sha256(source / 'registration.json'),
        'detector_observations_sha256': prediction_hash, 'fixture': fixture,
        'before_integration': True, 'reference_annotations_read': False}
    if ball_plan is not None:
        registration['ball_tracking_plan'] = ball_plan
        registration['ball_tracking_plan_sha256'] = sha256(ball_tracking_config)
    (out / 'registration.json').write_text(json.dumps(registration, indent=2))
    engine = ImageAnalysis(fixture['video_sha256'] + ':' + reg['config_sha256'], ball_config, foot_config)
    first, last = None, None
    with observations.open(encoding='utf-8') as rows, (out / 'frames.jsonl').open('x', encoding='utf-8') as writer:
        for line in rows:
            packet = engine.consume(json.loads(line))
            if first is None:
                first = packet['source_frame']
                if first != config['start_frame']: raise ValueError('Registered starting frame differs')
            last = packet['source_frame']
            writer.write(json.dumps(packet, allow_nan=False) + '\n')
    result = engine.summary()
    if result['frames'] != config['max_frames'] or sha256(observations) != prediction_hash:
        raise ValueError('Incomplete or changed detector observations')
    if _frozen_model(repo) != baseline or any(sha256(repo / name) != digest for name, digest in hashes.items()):
        raise ValueError('Project integration source or frozen baseline changed')
    result.update(source_frame_range=[first, last], reference_annotations_read=False,
        output_sha256=sha256(out / 'frames.jsonl'), provided_fixture_used=False, selected_release=False)
    (out / 'summary.json').write_text(json.dumps(result, indent=2))
    return result


def run(out, *, vision_run=None, video=None, config=None, device='cpu', ball_tracking_config=None):
    out = external_output(out)
    if vision_run is not None:
        if video is not None or config is not None: raise ValueError('Choose completed run or video/config')
        return integrate(vision_run, out, ball_tracking_config)
    if video is None or config is None: raise ValueError('Video and registered configuration required')
    from .vision_experiment import run as detect
    out.mkdir(parents=True, exist_ok=False)
    detect(video, config, out / 'detector', device)
    return integrate(out / 'detector', out / 'analysis', ball_tracking_config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--vision-run')
    parser.add_argument('--video')
    parser.add_argument('--config')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--ball-tracking-config', help='Optional registered temporal ball tracking plan')
    args = parser.parse_args()
    print(json.dumps(run(args.out, vision_run=args.vision_run, video=args.video,
                         config=args.config, device=args.device, ball_tracking_config=args.ball_tracking_config), indent=2))
