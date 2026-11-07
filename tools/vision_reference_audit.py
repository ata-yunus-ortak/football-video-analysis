"""Inspect external MOT reference contracts before computing any accuracy.

Does not guess frame base, reinterpret -1 flags as truth, or compute metrics.
Image dimensions/frame count are container metadata, not a full decode audit.
"""
import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
from .metrica_data import external_output, sha256


def inspect_reference(path, width, height, frame_count):
    columns, flags, classes, visibility = (Counter() for _ in range(4))
    frames, identities = set(), set()
    invalid, outside, rows = 0, 0, 0
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.reader(stream):
            rows += 1
            columns[len(row)] += 1
            try:
                values = list(map(float, row))
                if len(values) not in (9, 10) or not all(math.isfinite(v) for v in values):
                    raise ValueError
                frame, identity, x, y, w, h, flag, category, vis = values[:9]
                if frame != int(frame) or identity != int(identity) or w <= 0 or h <= 0:
                    raise ValueError
                frames.add(int(frame));identities.add(int(identity))
                flags[str(flag)] += 1;classes[str(category)] += 1;visibility[str(vis)] += 1
                outside += int(x < 0 or y < 0 or x + w > width or y + h > height)
            except (ValueError, OverflowError):
                invalid += 1
    documented = (bool(frames) and invalid == 0 and min(frames) >= 1
                  and max(frames) <= frame_count and min(identities) >= 0 and set(flags) <= {'0.0', '1.0'}
                  and set(classes) == {'1.0'}
                  and all(0 <= float(key) <= 1 for key in visibility))
    return {'rows': rows, 'column_counts': dict(columns), 'invalid_rows': invalid,
            'minimum_reference_frame': min(frames) if frames else None,
            'maximum_reference_frame': max(frames) if frames else None,
            'reference_frame_count': len(frames), 'identities': len(identities),
            'flag_counts': dict(flags), 'class_counts': dict(classes),
            'boxes_crossing_image_bounds': outside,
            'matches_documented_mot_contract': documented,
            'frame_base_selected': None, 'accuracy_evaluation_approved': False,
            'reason': 'Schema match alone does not establish independent reference quality or clip synchronization.'}


def run(manifest_path, out):
    import av
    manifest_path = Path(manifest_path)
    spec = json.loads(manifest_path.read_text(encoding='utf-8'))
    if spec.get('provided_fixture_used') is not False or spec.get('split') != 'train':
        raise ValueError('Registered external training artifact required')
    for name in ('video', 'reference'):
        if sha256(spec[name]['path']) != spec[name]['sha256']:
            raise ValueError('Downloaded artifact hash changed')
    with av.open(spec['video']['path']) as container:
        stream = container.streams.video[0]
        meta = {'width': stream.width, 'height': stream.height,
                'frame_count_from_container': stream.frames,
                'fps': float(stream.average_rate) if stream.average_rate else None,
                'duration_s': float(stream.duration * stream.time_base) if stream.duration else None}
    report = {'fixture_id': spec['fixture_id'], 'split': 'train', 'provided_fixture_used': False,
              'metadata': meta, 'reference': inspect_reference(spec['reference']['path'],
                  meta['width'], meta['height'], meta['frame_count_from_container']),
              'download_manifest_sha256': sha256(manifest_path), 'source_sha256': sha256(__file__)}
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.manifest, args.out), indent=2))
