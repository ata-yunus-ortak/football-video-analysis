"""Render registered external/synthetic image observations as a local review video.

No detector is re-run, no boxes edited, no labels inferred, no media uploaded.
Optional slow presentation changes display time only; source timestamps remain.
"""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import numpy as np
from .vision_experiment import read_frames
from .metrica_data import external_output, sha256


def draw(rgb, observation, slowdown, credit):
    import cv2
    canvas = rgb.copy()
    height, width = canvas.shape[:2]
    scale = max(1., width / 1280.)
    thickness, font = max(1, round(1.5 * scale)), .42 * scale
    counts = Counter(row['kind'] for row in observation['objects'])
    band, footer = round(70 * scale), round(28 * scale) if credit else 0
    occupied = []
    ordered = sorted(observation['objects'], key=lambda row: (
        row['kind'] != 'sports ball', -(row['box_xyxy'][2] - row['box_xyxy'][0]) * (row['box_xyxy'][3] - row['box_xyxy'][1])))
    for row in ordered:
        color = (60, 220, 245) if row['kind'] == 'person' else (255, 220, 50)
        x0, y0, x1, y1 = [round(value) for value in row['box_xyxy']]
        cv2.rectangle(canvas, (x0, y0), (x1, y1), color, thickness)
        key = row.get('track_key')
        name = f'#{key}' if key is not None else '?'
        if row['kind'] == 'sports ball': name = 'BALL?'
        text = f'{name} {row["confidence"]:.2f}'
        text_size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font, max(1, thickness - 1))
        tw, th = text_size;gap = round(3 * scale)
        for desired in [(x0, y0 - gap), (x1 + gap, y0 + th), (x0, y1 + th + gap), (x0 - tw - gap, y0 + th)]:
            tx = max(1, min(desired[0], width - tw - 2));ty = max(band + th + gap, min(desired[1], height - footer - baseline - 2))
            area = (tx - 1, ty - th - gap, tx + tw + 1, ty + baseline + 1)
            if any(area[0] < old[2] and area[2] > old[0] and area[1] < old[3] and area[3] > old[1] for old in occupied):continue
            occupied.append(area)
            cv2.rectangle(canvas, area[:2], area[2:], (10, 18, 24), -1)
            cv2.putText(canvas, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font, color, max(1, thickness - 1), cv2.LINE_AA)
            break
        anchor = tuple(round(value) for value in row['anchor_xy'])
        cv2.circle(canvas, anchor, max(2, round(1.5 * scale)), color, -1)
    cv2.rectangle(canvas, (0, 0), (width, band), (10, 18, 24), -1)
    text = (f'Image observations | persons {counts["person"]} | ball candidates {counts["sports ball"]}'
            f' | source frame {observation["source_frame"]} t={observation["video_time_s"]:.2f}s')
    cv2.putText(canvas, text, (round(12 * scale), round(25 * scale)), cv2.FONT_HERSHEY_SIMPLEX,
                font, (235, 242, 248), thickness, cv2.LINE_AA)
    text = f'Display {1 / slowdown:.2f}x | person role/team unknown | model scores are not accuracy'
    cv2.putText(canvas, text, (round(12 * scale), round(54 * scale)), cv2.FONT_HERSHEY_SIMPLEX,
                font * .85, (180, 200, 212), max(1, thickness - 1), cv2.LINE_AA)
    if credit:
        cv2.rectangle(canvas, (0, height - round(28 * scale)), (width, height), (10, 18, 24), -1)
        cv2.putText(canvas, credit, (round(10 * scale), height - round(8 * scale)), cv2.FONT_HERSHEY_SIMPLEX,
                    font * .75, (220, 230, 235), max(1, thickness - 1), cv2.LINE_AA)
    return canvas


def run(observation_dir, out, *, slowdown=1, max_width=1920, credit=''):
    source = Path(observation_dir)
    registration = json.loads((source / 'registration.json').read_text(encoding='utf-8'))
    summary = json.loads((source / 'summary.json').read_text(encoding='utf-8'))
    spec, fixture = registration['config'], registration['config']['fixture']
    if (fixture.get('source_kind') not in ('permitted_external_video', 'synthetic_fixture')
            or fixture.get('provided_fixture_used') is not False
            or registration.get('provided_fixture_used') is not False
            or summary.get('processed_frames') != spec.get('max_frames')
            or type(slowdown) is not int or slowdown < 1
            or type(max_width) is not int or max_width < 16):
        raise ValueError('Completed registered external/synthetic observations and valid display settings required')
    video = Path(registration['video_path'])
    if 'bar-ath' in video.name.lower() or sha256(video) != fixture['video_sha256']:
        raise ValueError('Original registered external/synthetic video required')
    import av
    import cv2
    out = external_output(out);out.mkdir(parents=True, exist_ok=False)
    observation_path = source / 'observations.jsonl'
    before = {'source_registration_sha256': sha256(source / 'registration.json'),
        'observations_sha256': sha256(observation_path), 'source_video_sha256': fixture['video_sha256'],
        'display_slowdown_factor': slowdown, 'max_width': max_width, 'credit': credit,
        'source_provenance': fixture['provenance'], 'frames_uploaded': 0,
        'boxes_are_automatic_measurements': True, 'source_code_sha256': sha256(Path(__file__))}
    (out / 'registration.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    output = out / 'detections.mp4'
    count, encoder, source_fps, last_source_time = 0, None, None, None
    with observation_path.open(encoding='utf-8') as stream, av.open(str(output), 'w') as container:
        line = stream.readline();observation = json.loads(line) if line else None
        for index, timestamp, fps, rgb in read_frames(video):
            if observation is None:
                break
            expected = spec['start_frame'] + count
            if observation['source_frame'] != expected:
                raise ValueError('Observation frame sequence differs from registration')
            if index < expected:
                continue
            if (index != expected or abs(timestamp - observation['video_time_s']) > 1e-6
                    or (rgb.shape[1], rgb.shape[0]) != (observation['width'], observation['height'])
                    or abs(fps - observation['fps']) > 1e-9):
                raise ValueError('Observation/video frame, timestamp, FPS or image dimensions differ')
            annotated = draw(rgb, observation, slowdown, credit)
            if encoder is None:
                source_fps = Fraction(str(fps)).limit_denominator(100000)
                encoder = container.add_stream('libx264', rate=source_fps / slowdown)
                width = min(max_width, rgb.shape[1]);width -= width % 2
                height = max(2, round(rgb.shape[0] * width / rgb.shape[1] / 2) * 2)
                encoder.width, encoder.height, encoder.pix_fmt = width, height, 'yuv420p'
                encoder.options = {'crf': '18', 'preset': 'veryfast'}
            if annotated.shape[:2] != (encoder.height, encoder.width):
                annotated = cv2.resize(annotated, (encoder.width, encoder.height), interpolation=cv2.INTER_AREA)
            if count == 0:
                if not cv2.imwrite(str(out / 'first-frame.jpg'), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)):
                    raise ValueError('Could not save the preview proof frame')
            frame = av.VideoFrame.from_ndarray(np.ascontiguousarray(annotated), format='rgb24')
            frame.pts, frame.time_base = count, slowdown / source_fps
            for packet in encoder.encode(frame):
                container.mux(packet)
            count += 1;last_source_time = timestamp
            line = stream.readline();observation = json.loads(line) if line else None
        if count != summary['processed_frames'] or observation is not None:
            raise ValueError('Not all registered observation frames were rendered')
        for packet in encoder.encode():
            container.mux(packet)
    with av.open(str(output)) as check:
        encoded = check.streams.video[0]
        decoded_count = sum(1 for _ in check.decode(encoded))
        metadata = {'width': encoded.width, 'height': encoded.height,
                    'display_fps': str(encoded.average_rate), 'decoded_frames': decoded_count}
    if decoded_count != count:
        raise ValueError('Preview encoded frame count differs from observations')
    result = {**before, 'output_video': str(output), 'video_sha256': sha256(output), 'frames': count,
        'source_fps': str(source_fps), 'last_source_time_s': last_source_time,
        'display_duration_s': count * slowdown / float(source_fps),
        'frame_timestamps_changed_only_for_display': slowdown != 1, 'frames_duplicated': False,
        'metadata': metadata, 'accuracy_evaluated': False, 'hybrid_ready': False}
    (out / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--slowdown', type=int, default=1)
    parser.add_argument('--max-width', type=int, default=1920)
    parser.add_argument('--credit', default='')
    args = parser.parse_args()
    print(json.dumps(run(args.observations, args.out, slowdown=args.slowdown,
                         max_width=args.max_width, credit=args.credit), indent=2))
