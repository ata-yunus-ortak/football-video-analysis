"""Local read-only ATD viewer. No labels, model inference, or uploads."""
import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET
import numpy as np


class Tracking:
    def __init__(self, meta, raw):
        root = ET.parse(meta).getroot()
        channels = {e.get('id'): (e.findtext('Name'), e.findtext('Unit')) for e in root.iter('Channel')}
        if channels.get('x') != ('position_x', 'normalized') or channels.get('y') != ('position_y', 'normalized') or channels.get('s') != ('speed_kph', 'kph'):
            raise ValueError('Expected normalized x/y and speed_kph channels')
        if [e.get('channelId') for e in root.iter('BallChannelRef')] != ['x', 'y', 's']:
            raise ValueError('Unsupported ball channel order')
        teams = list(root.iter('Team'))
        ids = [e.get('id') for e in teams]
        players = list(root.iter('Player'))
        if len(ids) != 2 or any(e.get('teamId') not in ids for e in players):
            raise ValueError('Two teams and known player membership required')
        self.fps = float(root.findtext('.//FrameRate'))
        field = root.find('.//FieldSize')
        self.pitch = [float(field.findtext('Width')), float(field.findtext('Height'))]
        if not np.isfinite(self.fps) or self.fps <= 0 or not all(np.isfinite(v) and v > 0 for v in self.pitch):
            raise ValueError('Invalid clock or pitch')
        self.objects = [{'id': e.get('id'), 'team': ids.index(e.get('teamId')), 'name': 'Takip ' + str(e.get('id'))} for e in players]
        self.objects.append({'id': 'ball', 'team': -1, 'name': 'Top'})
        self.teams = [e.findtext('Name') or 'Takım ' + str(i + 1) for i, e in enumerate(teams)]
        chunks, current, index = [], np.empty((25000, len(self.objects), 3), np.float32), 0
        with Path(raw).open(encoding='utf-8-sig') as stream:
            for number, line in enumerate(stream, 1):
                parts = line.strip().split(':')
                if len(parts) != 3 or int(parts[0]) != number or len(parts[1].split(';')) != len(players):
                    raise ValueError('Invalid ATD frame or player slots')
                groups = parts[1].split(';') + [parts[2]]
                if any(len(group.split(',')) != 3 for group in groups):
                    raise ValueError('Expected exactly x,y,s for each object')
                values = np.fromstring(','.join(groups), sep=',', dtype=np.float32)
                if len(values) != len(self.objects) * 3:
                    raise ValueError('Malformed ATD values')
                current[index] = values.reshape(-1, 3)
                index += 1
                if index == len(current):
                    chunks.append(current)
                    current, index = np.empty_like(current), 0
        if index:
            chunks.append(current[:index])
        if not chunks:
            raise ValueError('Empty tracking')
        self.data = np.concatenate(chunks)
        self.synthetic = False

    @classmethod
    def demo(cls):
        obj = cls.__new__(cls)
        obj.fps, obj.pitch = 25., [105., 68.]
        obj.objects = [{'id': str(i + 1), 'team': i % 2, 'name': 'Takip ' + str(i + 1)} for i in range(8)] + [{'id': 'ball', 'team': -1, 'name': 'Top'}]
        obj.teams = ['Örnek H', 'Örnek A']
        t = np.arange(250)[:, None] / obj.fps
        k = np.arange(9)[None, :]
        obj.data = np.empty((250, 9, 3), np.float32)
        obj.data[:, :, 0] = .15 + k * .075 + t * .008
        obj.data[:, :, 1] = .2 + (k % 4) * .18 + .02 * np.sin(t)
        obj.data[:, :, 2] = 6.
        obj.data[50:60, -1] = np.nan
        obj.synthetic = True
        return obj

    def metadata(self):
        return {'fps': self.fps, 'pitch': self.pitch, 'objects': self.objects,
                'teams': self.teams, 'frames': len(self.data), 'synthetic': self.synthetic,
                'columns': ['x_normalized', 'y_normalized', 'speed_kph', 'vx_mps', 'vy_mps']}

    def frames(self, start, count):
        if start < 0 or start >= len(self.data) or count < 1 or count > 500:
            raise ValueError('Frame range invalid')
        stop = min(len(self.data), start + count)
        source = self.data[start:stop]
        result = np.full((*source.shape[:2], 5), np.nan, np.float64)
        result[:, :, :3] = source
        first = max(1, start)
        if first < stop:
            before, after = self.data[first - 1:stop - 1, :, :2], self.data[first:stop, :, :2]
            velocity = (after.astype(float) - before.astype(float)) * np.asarray(self.pitch) * self.fps
            velocity[~(np.isfinite(before).all(2) & np.isfinite(after).all(2))] = np.nan
            result[first - start:, :, 3:] = velocity
        result[:, :, :2] = np.round(result[:, :, :2], 5)
        result[:, :, 2:] = np.round(result[:, :, 2:], 2)
        safe = result.astype(object)
        safe[~np.isfinite(result)] = None
        return {'start': start, 'frames': safe.tolist()}


def server_for(tracking, port=0, video=None):
    html = Path(__file__).resolve().parents[1] / 'viewer' / 'index.html'
    video = Path(video).resolve() if video is not None else None
    if video is not None and not video.is_file():
        raise ValueError('Video file not found')

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            allowed_hosts = (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')
            if self.headers.get('Host') not in allowed_hosts:
                self.send_error(403)
                return
            url = urlsplit(self.path)
            try:
                if url.path == '/':
                    payload, content_type = html.read_bytes(), 'text/html; charset=utf-8'
                elif url.path == '/api/meta':
                    payload, content_type = json.dumps({**tracking.metadata(), 'video_available': video is not None}, ensure_ascii=False).encode(), 'application/json'
                elif url.path == '/video' and video is not None:
                    size = video.stat().st_size
                    start, end = 0, size - 1
                    range_value = self.headers.get('Range')
                    if range_value:
                        match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_value)
                        if match is None or not any(match.groups()):
                            self.send_error(416)
                            return
                        a, b = match.groups()
                        if a:
                            start = int(a)
                            end = min(int(b), size - 1) if b else size - 1
                        else:
                            start = max(0, size - int(b))
                        if start >= size or start > end:
                            self.send_response(416)
                            self.send_header('Content-Range', f'bytes */{size}')
                            self.end_headers()
                            return
                    self.send_response(206 if range_value else 200)
                    self.send_header('Content-Type', 'video/mp4')
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Content-Length', str(end - start + 1))
                    if range_value:
                        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                    self.end_headers()
                    with video.open('rb') as stream:
                        stream.seek(start)
                        remaining = end - start + 1
                        while remaining:
                            chunk = stream.read(min(1024 * 1024, remaining))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                    return
                elif url.path == '/api/frames':
                    query = parse_qs(url.query)
                    value = tracking.frames(int(query.get('start', ['0'])[0]), int(query.get('count', ['250'])[0]))
                    payload, content_type = json.dumps(value, allow_nan=False, separators=(',', ':')).encode(), 'application/json'
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self' blob:; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(payload)
            except (ValueError, KeyError):
                self.send_error(400, 'Invalid frame range')
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meta')
    parser.add_argument('--tracking')
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--video', help='Optional local tactical video, served on loopback only')
    parser.add_argument('--open', action='store_true', help='Open the viewer in the default browser')
    args = parser.parse_args()
    if not args.demo and (not args.meta or not args.tracking):
        parser.error('--meta and --tracking are required unless --demo is used')
    print('Tracking yükleniyor...', flush=True)
    tracking = Tracking.demo() if args.demo else Tracking(args.meta, args.tracking)
    server = server_for(tracking, args.port, args.video)
    print('Hazır: http://127.0.0.1:' + str(server.server_port), flush=True)
    if args.open:
        import webbrowser
        threading.Timer(.5, lambda: webbrowser.open('http://127.0.0.1:' + str(server.server_port))).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
