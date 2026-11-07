"""Explicit user-requested local demonstration, never validation or development.

Keeps the external-only experiment/preview guards intact. Reuses an already
completed external run's exact detector settings and weights. No labels,
corrections, metrics, image uploads or frame-level observation export.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from development.vision import LocalVision, VisionConfig
from .vision_preview import draw
from .metrica_data import external_output, sha256
from .dead_ball_audit import _frozen_model


def draw_ball_tracks(image, packet):
    """Display observations/forecasts only; never select or score a ball."""
    import cv2
    for row in packet['ball_tracking']['tracks']:
        state = row['state']
        point = row['measured_position_px'] if row['measurement'] else row['predicted_position_px']
        if point is None: continue
        x, y = [round(v) for v in point]
        color = {'observed': (65, 255, 120), 'tentative': (255, 210, 45),
                 'predicted': (255, 80, 210)}[state]
        if state == 'predicted':
            for start in range(0, 360, 60):
                cv2.ellipse(image, (x, y), (15, 15), 0, start, start + 35, color, 2)
        else:
            cv2.circle(image, (x, y), 15, color, 2)
        label = state + ' ' + row['track_id'].rsplit('/', 1)[-1]
        cv2.putText(image, label, (max(0, x + 18), max(90, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, .6, color, 2, cv2.LINE_AA)
    return image


def external_settings(folder):
    folder = Path(folder)
    reg = json.loads((folder / 'registration.json').read_text())
    summary = json.loads((folder / 'summary.json').read_text())
    fixture = reg['config']['fixture']
    if (reg.get('provided_fixture_used') is not False
            or fixture.get('source_kind') != 'permitted_external_video'
            or fixture.get('provided_fixture_used') is not False
            or summary.get('processed_frames') != reg['config']['max_frames']):
        raise ValueError('Completed permitted external run required; no demo-derived settings')
    repo = Path(__file__).resolve().parents[1]
    if any(sha256(repo / name) != digest for name, digest in reg['source_sha256'].items()):
        raise ValueError('Detector implementation differs from completed external run')
    return reg


def run(alignment_path, external_run, out, ball_tracking_plan=None):
    import av
    import cv2
    reg = external_settings(external_run)
    alignment = json.loads(Path(alignment_path).read_text())
    source = alignment['sources']['tactical']
    video = Path(source['video'])
    if video.stat().st_size != source['video_bytes'] or video.stat().st_mtime_ns != source['video_mtime_ns']:
        raise ValueError('Video fingerprint changed')
    # A deterministic automatic interval, never a human/public-reference anchor.
    segment = next(s for s in alignment['segments']
                   if s['status'] == 'clock_and_tracking_candidate' and s['t1'] - s['t0'] >= 2.1)
    fps = float(source['fps']);start = math.ceil(segment['t0'] * fps);count = 50
    cfg = VisionConfig(**reg['config']['parameters'])
    analysis, continuity, measurements, plan = None, None, None, None
    if ball_tracking_plan is not None:
        from development.ball_tracking import BallTrackingConfig
        from development.image_analysis import ImageAnalysis
        from development.vision_measurements import SceneChangeConfig, SceneContinuity, VisionMeasurements
        plan = json.loads(Path(ball_tracking_plan).read_text())
        if (plan.get('provided_fixture_used') is not False or plan.get('selected_release') is not False
                or plan.get('parameters_origin') != 'Fixed synthetic engineering checks, not football accuracy selection'
                or 'foot_context_parameters' in plan):
            raise ValueError('Existing external-only temporal plan required, without new demo-selected heuristics')
        analysis = ImageAnalysis('local-display-only', BallTrackingConfig(**plan['parameters']))
        scene = reg['config'].get('scene_parameters')
        continuity = SceneContinuity(fps, SceneChangeConfig(**scene) if scene else None)
        measurements = VisionMeasurements(fps)
    weights = Path(reg['config']['weights']['path'])
    if sha256(weights) != reg['config']['weights']['sha256']:
        raise ValueError('Checkpoint changed')
    repo = Path(__file__).resolve().parents[1];baseline = _frozen_model(repo)
    out = external_output(out);out.mkdir(parents=True, exist_ok=False)
    receipt = {'purpose': 'user_requested_local_read_only_demonstration_not_validation',
        'training': False, 'threshold_selection': False, 'accuracy_evaluation': False,
        'human_annotations': False, 'uploads': False, 'source_frames': [start, start + count - 1],
        'source_video': str(video), 'parameters': reg['config']['parameters'],
        'external_run_registration_sha256': sha256(Path(external_run) / 'registration.json'),
        'weights_sha256': reg['config']['weights']['sha256'], 'baseline_model_sha256': baseline,
        'source_sha256': {name: sha256(repo / name) for name in
            ['tools/vision_local_demo.py', 'development/vision.py', 'tools/vision_preview.py']},
        'display_slowdown': 5, 'before_decode': True}
    if plan is not None:
        receipt.update(ball_tracking_plan=plan, ball_tracking_plan_sha256=sha256(ball_tracking_plan),
                       frame_level_measurements_exported=False, tracking_support_enabled=False,
                       two_camera_fusion_enabled=False, possession_inferred=False)
        for name in ('development/ball_tracking.py', 'development/image_analysis.py',
                     'development/vision_measurements.py'):
            receipt['source_sha256'][name] = sha256(repo / name)
    (out / 'registration.json').write_text(json.dumps(receipt, indent=2))
    engine = LocalVision(cfg, weights, fps, 'cpu')
    target = out / 'local-demo.mp4';processed = 0
    with av.open(str(video)) as container, av.open(str(target), 'w') as writer:
        stream = container.streams.video[0]
        origin = float(stream.start_time * stream.time_base)
        container.seek(int((origin + start / fps) / stream.time_base), stream=stream)
        encoder = None
        for frame in container.decode(stream):
            time = float(frame.pts * frame.time_base) - origin
            index = round(time * fps)
            if index < start:continue
            if index != start + processed:raise ValueError('Unexpected source frame sequence')
            rgb = frame.to_ndarray(format='rgb24')
            context = continuity.observe(rgb, index, time) if continuity is not None else None
            if context and context['continuity_reset']: engine.reset_tracking()
            rows = engine.process(rgb)
            packet = None
            if analysis is not None:
                rows, evidence = measurements.annotate(rows, index, time, int(rgb.shape[1]), int(rgb.shape[0]), context)
                packet = analysis.consume({'source_frame': index, 'video_time_s': time, 'fps': fps,
                    'width': int(rgb.shape[1]), 'height': int(rgb.shape[0]), 'objects': rows,
                    'frame_evidence': evidence, 'possession_inferred': False})
            else:
                for row in rows:
                    row['track_key'] = str(row['track_id']) if row['track_id'] is not None else None
            image = draw(rgb, {'source_frame': index, 'video_time_s': time, 'objects': rows},
                         5, 'LOCAL VIEW ONLY - no validation, annotations or tuning')
            if packet is not None: image = draw_ball_tracks(image, packet)
            if encoder is None:
                encoder = writer.add_stream('libx264', rate=Fraction(str(fps)) / 5)
                width = min(1920, image.shape[1]);width -= width % 2
                height = max(2, round(image.shape[0] * width / image.shape[1] / 2) * 2)
                encoder.width, encoder.height, encoder.pix_fmt = width, height, 'yuv420p'
                encoder.options = {'crf': '18', 'preset': 'veryfast'}
            image = cv2.resize(image, (encoder.width, encoder.height), interpolation=cv2.INTER_AREA)
            output = av.VideoFrame.from_ndarray(image, format='rgb24')
            output.pts, output.time_base = processed, Fraction(5, 1) / Fraction(str(fps))
            for packet in encoder.encode(output):writer.mux(packet)
            processed += 1
            if processed % 10 == 0: print('Local display frames: ' + str(processed) + '/' + str(count), flush=True)
            if processed == count:break
        if processed != count:raise ValueError('Incomplete local demonstration')
        for packet in encoder.encode():writer.mux(packet)
    if _frozen_model(repo) != baseline:raise ValueError('Baseline changed')
    with av.open(str(target)) as check:
        if check.streams.video[0].frames != count:raise ValueError('Encoded frame count differs')
    (out / 'complete.json').write_text(json.dumps({'complete': True, 'accuracy_evaluated': False,
        'output': str(target), 'output_sha256': sha256(target), 'images_uploaded': 0}, indent=2))
    print('Local demonstration ready: ' + str(target), flush=True)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alignment', required=True)
    parser.add_argument('--external-run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--ball-tracking-plan')
    args = parser.parse_args()
    run(args.alignment, args.external_run, args.out, args.ball_tracking_plan)
