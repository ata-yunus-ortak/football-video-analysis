"""Deterministic multi-clip external training gallery with unchanged detector settings."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
import io
import json
from pathlib import Path, PurePosixPath
import zipfile
import struct
import zlib
import time

from .metrica_data import external_output, sha256
from .soccernet_sample import RangeReader


def member_payload(info, raw):
    if len(raw) < 30: raise ValueError('Truncated local ZIP header')
    header = struct.unpack('<IHHHHHIIIHH', raw[:30])
    if header[0] != 0x04034b50 or header[2] & 1 or header[3] != info.compress_type:
        raise ValueError('Invalid or encrypted ZIP member')
    begin = 30 + header[-2] + header[-1]
    encoded_name = raw[30:30 + header[-2]]
    if encoded_name.decode('utf-8' if header[2] & 0x800 else 'cp437') != info.filename:
        raise ValueError('ZIP local/central filename mismatch')
    compressed = raw[begin:begin + info.compress_size]
    if len(compressed) != info.compress_size: raise ValueError('Truncated compressed member')
    if info.compress_type == zipfile.ZIP_DEFLATED:
        decoder = zlib.decompressobj(-15)
        data = decoder.decompress(compressed, info.file_size + 1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('Incomplete or oversized compressed member')
    elif info.compress_type == zipfile.ZIP_STORED: data = compressed
    else: raise ValueError('Unsupported ZIP compression')
    if len(data) != info.file_size or zlib.crc32(data) & 0xffffffff != info.CRC:
        raise ValueError('ZIP member size/CRC differs')
    return data


class BlockReader(io.RawIOBase):
    """Bounded aligned cache avoids a separate HTTP request for every ZIP header."""
    def __init__(self, reader, block=8388608):
        self.reader, self.block, self.position, self.cache = reader, block, 0, OrderedDict()
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        target = offset + (self.position if whence == 1 else self.reader.size if whence == 2 else 0)
        if whence not in (0, 1, 2) or target < 0: raise ValueError('Invalid seek')
        self.position = target
        return target
    def read(self, count=-1):
        count = min(self.reader.size - self.position, count if count >= 0 else self.reader.size)
        if count <= 0: return b''
        chunks = []
        while count:
            begin = self.position // self.block * self.block
            if begin not in self.cache:
                self.reader.seek(begin)
                self.cache[begin] = self.reader.read(min(self.block, self.reader.size - begin))
                if len(self.cache) > 4: self.cache.popitem(last=False)
            self.cache.move_to_end(begin)
            offset = self.position - begin
            length = min(count, len(self.cache[begin]) - offset)
            if length <= 0: raise ValueError('Incomplete archive block')
            chunks.append(self.cache[begin][offset:offset + length])
            self.position += length
            count -= length
        return b''.join(chunks)


def acquire(plan_path, out):
    plan = json.loads(Path(plan_path).read_text())
    if (plan.get('dataset') != 'SoccerNet/SN-GSR-2024' or plan.get('archive') != 'train.zip'
            or plan.get('provided_fixture_used') is not False): raise ValueError('External training plan required')
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'before-access.json').write_text(json.dumps({'plan': plan, 'plan_sha256': sha256(plan_path),
        'source_sha256': sha256(__file__)}, indent=2))
    url = f"https://huggingface.co/datasets/{plan['dataset']}/resolve/{plan['commit']}/{plan['archive']}"
    remote = RangeReader(url, plan['archive_bytes'], plan['max_download_bytes'])
    clips = []
    try:
        with zipfile.ZipFile(remote) as archive:
            members = {r.filename: r for r in archive.infolist()}
            sequences = sorted({name.split('/')[0] for name in members if '/img1/' in name and name.endswith('.jpg')})
            selection = [(sequences[i], start) for i, start in zip(plan['sequence_indices'], plan['starts'])]
            (out / 'selection-before-download.json').write_text(json.dumps(selection))
            for sequence, start in selection:
                sample = out / sequence / 'sample-v2'
                sample.mkdir(parents=True)
                (sample / 'before-access.json').write_text((out / 'before-access.json').read_text())
                filenames = [f'{sequence}/Labels-GameState.json'] + [f'{sequence}/img1/{n:06}.jpg'
                    for n in range(start + 1, start + plan['frames_per_clip'] + 1)]
                records = []
                def download(name):
                    info = members[name]
                    if info.file_size > 50000000 or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                        raise ValueError('Invalid archive member')
                    # Archive order is shuffled: fetch exactly this member with
                    # bounded local-header padding, not multi-MB random blocks.
                    reader = RangeReader(url, plan['archive_bytes'], 55000000)
                    reader.seek(info.header_offset)
                    raw = reader.read(min(info.compress_size + 65566, plan['archive_bytes'] - info.header_offset))
                    data = member_payload(info, raw)
                    target = sample / 'sample' / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    return {'member': name, 'bytes': len(data), 'sha256': sha256(target),
                            'crc32': f'{info.CRC:08x}', 'zip_crc_verified': True}, reader.requests
                expected_bytes = sum(min(members[n].compress_size + 65566,
                                         plan['archive_bytes'] - members[n].header_offset) for n in filenames)
                if remote.downloaded + expected_bytes > plan['max_download_bytes']:
                    raise ValueError('Gallery range budget exceeded')
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for record, requests in pool.map(download, filenames):
                        records.append(record)
                        remote.requests.extend(requests)
                        remote.downloaded += sum(r['end'] - r['start'] + 1 for r in requests)
                labels = json.loads((sample / 'sample' / filenames[0]).read_text())
                if labels['info']['frame_rate'] != plan['fps']: raise ValueError('Unexpected source clock')
                (sample / 'manifest.json').write_text(json.dumps({'complete': True, 'provided_fixture_used': False,
                    'frame_range': [start, start + plan['frames_per_clip']], 'acquired_files': records,
                    'archive_fully_downloaded_or_sha256_verified': False}, indent=2))
                clips.append({'id': sequence, 'study': str(sample.parent), 'start_frame': start,
                              'frames': plan['frames_per_clip'], 'source_game_id': labels['info']['game_id']})
                (out / 'acquisition-progress.json').write_text(json.dumps(clips, indent=2))
                print(json.dumps({'acquired': sequence, 'clips': len(clips), 'verified_range_bytes': remote.downloaded}), flush=True)
        (out / 'acquisition.json').write_text(json.dumps({'complete': True, 'clips': clips,
            'verified_range_bytes': remote.downloaded, 'full_archive_verified': False}, indent=2))
    finally:
        (out / 'range-receipts.json').write_text(json.dumps(remote.requests, indent=2))


def process(root, settings):
    from .soccernet_video import run as make_video
    from .vision_experiment import run as infer
    from .vision_preview import run as preview
    root = Path(root)
    template = json.loads(Path(settings).read_text())
    plan = json.loads((root / 'before-access.json').read_text())['plan']
    (root / 'process-registration.json').write_text(json.dumps({'source_sha256': sha256(__file__),
        'template_sha256': sha256(settings), 'before_inference': True, 'provided_fixture_used': False}, indent=2))
    ready = []
    last_progress = time.monotonic()
    while len(ready) < len(plan['sequence_indices']):
        path = root / ('acquisition.json' if (root / 'acquisition.json').exists() else 'acquisition-progress.json')
        try:
            progress = json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            progress = []
        clips = progress['clips'] if isinstance(progress, dict) else progress
        pending = [c for c in clips if c['id'] not in {r['id'] for r in ready}]
        if not pending:
            if time.monotonic() - last_progress > 900: raise RuntimeError('No completed acquisition progress for 15 minutes')
            time.sleep(2)
            continue
        clip = pending[0]
        study = Path(clip['study'])
        if not (study / 'video-v1/video-manifest.json').exists(): make_video(study / 'sample-v2', study / 'video-v1', 25)
        video = json.loads((study / 'video-v1/video-manifest.json').read_text())
        for mode in ('native', 'sliced'):
            if (study / (mode + '-v1') / 'summary.json').exists(): continue
            spec = json.loads(json.dumps(template))
            spec['fixture'] = {'id': 'soccernet-gallery-' + clip['id'], 'source_kind': 'permitted_external_video',
                'provided_fixture_used': False, 'video_sha256': video['video_sha256'],
                'provenance': {'dataset': 'SoccerNet/SN-GSR-2024', 'split': 'train', 'source_game_id': clip['source_game_id'],
                    'source_start_frame': clip['start_frame'], 'conditions': 'Research only, no redistribution',
                    'manifest_sha256': sha256(study / 'sample-v2/manifest.json')}}
            spec['rationale'] = 'Registered uncurated visual gallery; prior detector settings unchanged. No model selection.'
            spec['start_frame'], spec['max_frames'] = 0, clip['frames']
            spec['parameters']['sliced'] = mode == 'sliced'
            config = study / (mode + '-config.json')
            config.write_text(json.dumps(spec, indent=2))
            infer(video['video'], config, study / (mode + '-v1'))
        if not (study / 'preview-v1/summary.json').exists():
            preview(study / 'sliced-v1', study / 'preview-v1', slowdown=3, credit='SoccerNet GSR / research only / automated detections')
        ready.append(clip)
        (root / 'gallery.json').write_text(json.dumps({'version': 1, 'clips': ready}, indent=2))
        print(json.dumps({'ready': clip['id'], 'completed_clips': len(ready)}), flush=True)
        last_progress = time.monotonic()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan')
    parser.add_argument('--out', required=True)
    parser.add_argument('--settings')
    parser.add_argument('--mode', choices=('acquire', 'process'), required=True)
    args = parser.parse_args()
    if args.mode == 'acquire': acquire(args.plan, args.out)
    else: process(args.out, args.settings)
