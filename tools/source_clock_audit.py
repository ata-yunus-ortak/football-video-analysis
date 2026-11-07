"""Read-only same-camera file/packet-clock audit. Never decodes or exports images.

Matching clocks/counts are structural evidence, not independently measured
tracking-to-image accuracy. No timing-offset search or model selection.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from .metrica_data import external_output, sha256
from .dead_ball_audit import _frozen_model
from .tracking_viewer import Tracking
from development.homography import FrameHomographies


def video_clock(path):
    import av
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        rate, base = stream.average_rate, stream.time_base
        points = [packet.pts for packet in container.demux(stream) if packet.size > 0]
        present = bool(points) and all(p is not None for p in points)
        grid = False
        if present and rate:
            points.sort()
            grid = all(Fraction(b - a) * base * rate == 1 for a, b in zip(points, points[1:]))
        return {'fps': float(rate) if rate else None, 'declared_frames': stream.frames,
            'packet_frames': len(points), 'packet_pts_present': present, 'packet_pts_regular': grid,
            'first_pts_s': float(points[0] * base) if present else None,
            'width': stream.width, 'height': stream.height, 'decoded_images': 0}


def check_clock(info, tracking_fps, tracking_frames, homography_frames):
    exact = info['declared_frames'] == info['packet_frames']
    count = info['packet_frames']
    clock_ok = (info['fps'] == tracking_fps and info['packet_pts_present']
                and info['packet_pts_regular'] and info['first_pts_s'] == 0 and exact)
    range_ok = homography_frames == tracking_frames and tracking_frames in (count, count + 1)
    return {'structural_clock_compatible': bool(clock_ok and range_ok),
            'same_source_frame_mapping': {'video_base': 0, 'tracking_base': 1, 'homography_base': 0},
            'common_frames': min(count, tracking_frames, homography_frames),
            'tracking_frames': tracking_frames, 'homography_frames': homography_frames,
            'video_frames': count, 'unmatched_tracking_tail': max(0, tracking_frames - count),
            'tracking_fps': tracking_fps, 'video': info,
            'independent_image_alignment_validated': False, 'offset_search_performed': False,
            'usable_for_possession': False, 'purpose': 'same_camera_read_only_projection_review'}


def fingerprint(path):
    path = Path(path).resolve();stat = path.stat()
    return {'path': str(path), 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns, 'sha256': sha256(path)}


def run(meta, raw, homography, video, out):
    paths = {k: Path(p).resolve() for k, p in dict(meta=meta, tracking=raw, homography=homography, video=video).items()}
    stem = paths['video'].stem
    if (paths['meta'].stem != stem + '_atd' or paths['tracking'].stem != stem + '_atd'
            or paths['homography'].stem != stem + '_homography'):
        raise ValueError('Same-source file naming contract required; never cross tactical/broadcast')
    out = external_output(out);out.mkdir(parents=True, exist_ok=False)
    baseline = _frozen_model(Path(__file__).resolve().parents[1])
    sources = {k: fingerprint(p) for k, p in paths.items()}
    (out / 'registration.json').write_text(json.dumps({'purpose': 'read_only_structural_clock_audit',
        'sources': sources, 'source_sha256': sha256(__file__), 'baseline_model_sha256': baseline,
        'image_inspection': False, 'human_anchors_used': False, 'parameter_selection': False}, indent=2))
    tracking, geometry = Tracking(meta, raw), FrameHomographies(homography)
    report = check_clock(video_clock(video), tracking.fps, len(tracking.data), len(geometry.matrices))
    report['sources'] = sources
    report['homography'] = geometry.metadata(len(tracking.data))
    if _frozen_model(Path(__file__).resolve().parents[1]) != baseline: raise ValueError('Frozen baseline changed')
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('structural_clock_compatible', 'video_frames', 'tracking_frames',
                    'common_frames', 'independent_image_alignment_validated')}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('meta', 'tracking', 'homography', 'video', 'out'): parser.add_argument('--' + flag, required=True)
    args = parser.parse_args()
    run(args.meta, args.tracking, args.homography, args.video, args.out)
