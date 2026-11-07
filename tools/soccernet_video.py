"""Make a lossless, frame-mapped local video from a registered GSR JPEG sample.

Labels are deliberately not read by this input adapter. FPS is an explicit
sequence-clock assumption, not measured original video presentation timestamps.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from .metrica_data import external_output, sha256


def image_members(manifest):
    files = [r for r in manifest['acquired_files'] if r['member'].lower().endswith('.jpg')]
    start, stop = manifest.get('frame_range', [0, 25])
    if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= 750:
        raise ValueError('Explicit bounded source frame range required')
    if (manifest.get('complete') is not True or manifest.get('provided_fixture_used') is not False
            or len(files) != stop - start or any(not r.get('zip_crc_verified') for r in files)):
        raise ValueError('Complete registered external image range required')
    numbers = [int(Path(r['member']).stem) for r in files]
    if numbers != list(range(start + 1, stop + 1)) or len({str(Path(r['member']).parent) for r in files}) != 1:
        raise ValueError('Single sequence consecutive registered images required')
    return files


def run(sample, out, fps):
    import av
    import numpy as np
    from PIL import Image
    sample = Path(sample)
    manifest = json.loads((sample / 'manifest.json').read_text())
    files = image_members(manifest)
    if not 0 < fps <= 120: raise ValueError('Explicit positive sequence clock required')
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'before-decode.json').write_text(json.dumps({
        'sample_manifest_sha256': sha256(sample / 'manifest.json'),
        'source_sha256': sha256(__file__), 'fps': fps,
        'clock_kind': 'explicit_uniform_image_sequence_not_original_video_pts',
        'labels_used_as_input': False, 'provided_fixture_used': False}, indent=2))
    target = out / 'sample-lossless.mkv'
    mapping, decoded_hashes, shape = [], [], None
    with av.open(str(target), 'w') as writer:
        stream = writer.add_stream('ffv1', rate=Fraction(str(fps)))
        stream.pix_fmt = 'bgr0'
        for index, spec in enumerate(files):
            path = sample / 'sample' / spec['member']
            if sha256(path) != spec['sha256']: raise ValueError('Image source changed')
            rgb = np.asarray(Image.open(path).convert('RGB'))
            if shape is None:
                shape = rgb.shape
                stream.width, stream.height = shape[1], shape[0]
            if rgb.shape != shape: raise ValueError('Changing image dimensions')
            frame = av.VideoFrame.from_ndarray(rgb, format='rgb24')
            frame.pts, frame.time_base = index, Fraction(1, 1) / Fraction(str(fps))
            for packet in stream.encode(frame): writer.mux(packet)
            digest = hashlib.sha256(rgb.tobytes()).hexdigest()
            decoded_hashes.append(digest)
            mapping.append({'source_frame': index, 'member': spec['member'], 'rgb_sha256': digest})
        for packet in stream.encode(): writer.mux(packet)
    with av.open(str(target)) as reader:
        actual = [hashlib.sha256(f.to_ndarray(format='rgb24').tobytes()).hexdigest()
                  for f in reader.decode(video=0)]
    if actual != decoded_hashes: raise ValueError('Lossless RGB verification failed')
    (out / 'video-manifest.json').write_text(json.dumps({
        'video': str(target), 'video_sha256': sha256(target), 'fps': fps,
        'clock_kind': 'explicit_uniform_image_sequence_not_original_video_pts',
        'width': shape[1], 'height': shape[0], 'rgb_lossless_verified': True,
        'sample_manifest_sha256': sha256(sample / 'manifest.json'), 'frames': mapping,
        'labels_used_as_input': False, 'provided_fixture_used': False}, indent=2))
    print(json.dumps({'complete': True, 'frames': len(mapping), 'rgb_lossless_verified': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--fps', required=True, type=float)
    args = parser.parse_args()
    run(args.sample, args.out, args.fps)
