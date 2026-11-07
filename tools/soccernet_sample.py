"""Bounded public training-archive acquisition; no protected access or full archive transfer."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import urllib.request
import zipfile
import socket

from .metrica_data import external_output, sha256


class RangeReader(io.RawIOBase):
    def __init__(self, url, size, budget, opener=urllib.request.urlopen, cache_bytes=0):
        self.url, self.size, self.budget, self.opener = url, size, budget, opener
        self.position, self.downloaded, self.requests = 0, 0, []
        self.cache_bytes, self.cache_start, self.cache = cache_bytes, 0, b''

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.position

    def seek(self, offset, whence=0):
        target = offset + (self.position if whence == 1 else self.size if whence == 2 else 0)
        if whence not in (0, 1, 2) or target < 0:
            raise ValueError('Invalid archive seek')
        self.position = target
        return target

    def read(self, count=-1):
        count = min(self.size - self.position, count if count >= 0 else self.size)
        if count <= 0: return b''
        offset = self.position - self.cache_start
        if offset >= 0 and offset + count <= len(self.cache):
            self.position += count
            return self.cache[offset:offset + count]
        requested = count
        count = min(self.size - self.position, max(count, self.cache_bytes))
        if count > 20000000 or self.downloaded + count > self.budget:
            raise ValueError('Bounded sample download budget exceeded')
        start, end = self.position, self.position + count - 1
        request = urllib.request.Request(self.url, headers={'Range': f'bytes={start}-{end}'})
        for attempt in range(3):
            try:
                with self.opener(request, timeout=30) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}':
                        raise ValueError('Server must honor the exact public archive range; no full-download fallback')
                    data = response.read(count + 1)
                break
            except (TimeoutError, socket.timeout):
                if attempt == 2: raise
        if len(data) != count: raise ValueError('Incomplete archive range')
        self.requests.append({'start': start, 'end': end, 'sha256': hashlib.sha256(data).hexdigest()})
        self.downloaded += count
        self.cache_start, self.cache = start, data
        self.position += requested
        return data[:requested]


def run(plan_path, out, acquire=False):
    plan = json.loads(Path(plan_path).read_text(encoding='utf-8'))
    if (plan.get('dataset') != 'SoccerNet/SN-GSR-2024' or plan.get('archive') != 'train.zip'
            or plan.get('provided_fixture_used') is not False):
        raise ValueError('Registered public GSR training scope required')
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'before-access.json').write_text(json.dumps({'plan': plan,
        'plan_sha256': sha256(plan_path), 'source_sha256': sha256(__file__),
        'purpose': 'training_sample_acquisition' if acquire else 'archive_directory_audit'}, indent=2))
    url = f"https://huggingface.co/datasets/{plan['dataset']}/resolve/{plan['commit']}/{plan['archive']}"
    reader = RangeReader(url, plan['archive_bytes'], plan['max_download_bytes'], cache_bytes=1048576)
    files = []
    try:
        with zipfile.ZipFile(reader) as archive:
            members = sorted(archive.infolist(), key=lambda info: info.filename)
            index = [{'name': m.filename, 'bytes': m.file_size, 'compressed_bytes': m.compress_size,
                      'crc32': f'{m.CRC:08x}'} for m in members]
            (out / 'archive-index.json').write_text(json.dumps(index, indent=2))
            if acquire:
                images = [m for m in members if PurePosixPath(m.filename).suffix.lower() == '.jpg']
                if not images: raise ValueError('No training JPEG images')
                parent = PurePosixPath(images[0].filename).parent
                selected = [m for m in images if PurePosixPath(m.filename).parent == parent][:25]
                sequence = parent.parent
                selected += [m for m in members if PurePosixPath(m.filename).parent == sequence
                             and PurePosixPath(m.filename).suffix.lower() in ('.json', '.ini')]
                (out / 'selection-before-download.json').write_text(json.dumps(
                    {'sequence': str(sequence), 'members': [m.filename for m in selected],
                     'rationale': plan['selection']}, indent=2))
                for m in selected:
                    relative = PurePosixPath(m.filename)
                    if relative.is_absolute() or '..' in relative.parts or m.file_size > 50000000:
                        raise ValueError('Unsafe or oversized archive member')
                    data = archive.read(m)  # zipfile verifies CRC after decompression.
                    path = out / 'sample' / Path(*relative.parts)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                    files.append({'member': m.filename, 'bytes': len(data), 'sha256': sha256(path),
                                  'crc32': f'{m.CRC:08x}', 'zip_crc_verified': True})
        result = {'complete': True, 'acquired_files': files, 'downloaded_bytes': reader.downloaded,
                  'archive_fully_downloaded_or_sha256_verified': False,
                  'range_requests': reader.requests, 'provided_fixture_used': False}
        (out / 'manifest.json').write_text(json.dumps(result, indent=2))
        print(json.dumps({'complete': True, 'members_in_archive': len(index),
                          'sample_files': len(files), 'downloaded_bytes': reader.downloaded}))
    finally:
        (out / 'range-receipts.json').write_text(json.dumps(reader.requests, indent=2))
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--acquire', action='store_true')
    args = parser.parse_args()
    run(args.plan, args.out, args.acquire)
