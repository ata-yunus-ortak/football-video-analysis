"""Exercise real local weights/adapters on generated shapes, never a match.

This verifies runtime wiring only. No expected football detections, accuracy
claim, benchmark selection or competition material is involved.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import numpy as np
from .metrica_data import external_output, sha256
from .vision_experiment import run


def smoke(weights_manifest, out, device='cpu'):
    import av
    import supervision as sv
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    manifest_path = Path(weights_manifest).resolve()
    asset = json.loads(manifest_path.read_text(encoding='utf-8'))
    weights = manifest_path.parent / ('rf-detr-' + asset['size'] + '.pth')
    video = out / 'synthetic-vision.mp4'
    with av.open(str(video), 'w') as container:
        stream = container.add_stream('mpeg4', rate=25)
        stream.width, stream.height, stream.pix_fmt = 320, 192, 'yuv420p'
        for index in range(4):
            rgb = np.full((192, 320, 3), [35, 120, 45], dtype=np.uint8)
            rgb[10:12, 10:310] = 230
            rgb[180:182, 10:310] = 230
            rgb[10:182, 159:161] = 230
            rgb[70:100, 60 + index:70 + index] = [190, 40, 40]
            rgb[90:120, 220 - index:230 - index] = [30, 40, 190]
            rgb[110:114, 130 + index:134 + index] = 245
            frame = av.VideoFrame.from_ndarray(rgb, format='rgb24')
            frame.pts, frame.time_base = index, Fraction(1, 25)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    # Exercise ByteTrack even when a real detector correctly sees no people in
    # abstract generated shapes. Boxes are explicitly synthetic API inputs.
    tracker = sv.ByteTrack(track_activation_threshold=.3, minimum_matching_threshold=.8,
                          lost_track_buffer=30, frame_rate=25, minimum_consecutive_frames=1)
    ids = []
    for index in range(5):
        detection = sv.Detections(xyxy=np.array([[10 + index, 10, 30 + index, 50]], np.float32),
                                 confidence=np.array([.9], np.float32), class_id=np.array([1]))
        tracked = tracker.update_with_detections(detection)
        ids.append(tracked.tracker_id.tolist())
    if any(len(value) != 1 or value != ids[0] for value in ids):
        raise RuntimeError('Synthetic ByteTrack identity continuity failed')
    results = {}
    for sliced in (False, True):
        name = 'sliced' if sliced else 'native'
        spec = {'fixture': {'id': 'generated-vision-smoke-v1', 'source_kind': 'synthetic_fixture',
                'provided_fixture_used': False, 'video_sha256': sha256(video),
                'provenance': {'generator': 'tools/vision_smoke.py', 'sha256': sha256(__file__),
                               'content': 'Generated geometric shapes, no match assets'}},
            'rationale': 'Runtime wiring check only. Numeric values are synthetic engineering settings.',
            'weights': {'path': str(weights), 'sha256': asset['sha256'], 'size': asset['size'],
                        'license': asset['license'], 'source_url': asset['source_url']},
            'start_frame': 0, 'max_frames': 1 if sliced else 2,
            'parameters': dict(size=asset['size'], threshold=.3, sliced=sliced,
                slice_height=192, slice_width=192, overlap_ratio=.2,
                track_activation_threshold=.3, track_matching_threshold=.8,
                lost_track_s=1., min_consecutive_frames=1)}
        config_path = out / (name + '-config.json')
        config_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
        results[name] = run(video, config_path, out / name, device)
    results.update(synthetic_tracker_ids=ids, football_accuracy_evaluated=False,
                   provided_fixture_used=False, selected_release=False)
    (out / 'smoke-summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights-manifest', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    print(json.dumps(smoke(args.weights_manifest, args.out, args.device), indent=2))
