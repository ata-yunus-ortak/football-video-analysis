"""Local read-only paired video/tracking review, driven by automatic candidates."""
import argparse
import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import threading
from urllib.parse import parse_qs, urlsplit
from .tracking_viewer import Tracking
from .metrica_data import sha256


def validate_segments(segments, tactical, broadcast):
    previous_t, previous_b = -1., -1.
    for segment in segments:
        if (any(not isinstance(segment.get(k), (int, float)) or not math.isfinite(segment[k]) for k in ('t0', 't1', 'b0', 'b1'))
                or not 0 <= segment['t0'] < segment['t1'] <= len(tactical.data) / tactical.fps
                or not 0 <= segment['b0'] < segment['b1'] <= len(broadcast.data) / broadcast.fps
                or segment['t0'] < previous_t - 1e-6 or segment['b0'] < previous_b - 1e-6
                or segment.get('status') not in ('clock_candidate', 'clock_and_tracking_candidate')
                or segment.get('usable_for_possession') is not False):
            raise ValueError('Ordered, non-overlapping automatic review segments required')
        previous_t, previous_b = segment['t1'], segment['b1']


def send_video(handler, path):
    size = path.stat().st_size
    start, end = 0, size - 1
    requested = handler.headers.get('Range')
    if requested:
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested)
        if match is None or not any(match.groups()):
            handler.send_error(416)
            return
        left, right = match.groups()
        if left:
            start = int(left)
            end = min(int(right), size - 1) if right else size - 1
        else:
            start = max(0, size - int(right))
        if start >= size or start > end:
            handler.send_response(416)
            handler.send_header('Content-Range', f'bytes */{size}')
            handler.end_headers()
            return
    handler.send_response(206 if requested else 200)
    handler.send_header('Content-Type', 'video/mp4')
    handler.send_header('Accept-Ranges', 'bytes')
    handler.send_header('Content-Length', str(end - start + 1))
    if requested:
        handler.send_header('Content-Range', f'bytes {start}-{end}/{size}')
    handler.end_headers()
    with path.open('rb') as stream:
        stream.seek(start)
        remaining = end - start + 1
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            handler.wfile.write(chunk)
            remaining -= len(chunk)


def server_for_pair(tactical, broadcast, tactical_video, broadcast_video, segments, port=0):
    validate_segments(segments, tactical, broadcast)
    tracking = {'tactical': tactical, 'broadcast': broadcast}
    videos = {'tactical': Path(tactical_video), 'broadcast': Path(broadcast_video)}
    if any(not path.is_file() for path in videos.values()):
        raise ValueError('Both local source videos are required')
    html = Path(__file__).resolve().parents[1] / 'viewer' / 'paired.html'

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
                self.send_error(403)
                return
            url = urlsplit(self.path)
            try:
                if url.path == '/':
                    payload, kind = html.read_bytes(), 'text/html; charset=utf-8'
                elif url.path == '/api/meta':
                    payload, kind = json.dumps({key: value.metadata() for key, value in tracking.items()},
                                               ensure_ascii=False).encode(), 'application/json'
                elif url.path == '/api/mapping':
                    payload, kind = json.dumps({'segments': segments, 'review_only': True,
                                               'usable_for_possession': False}, allow_nan=False).encode(), 'application/json'
                elif url.path.startswith('/api/frames/'):
                    key = url.path.removeprefix('/api/frames/')
                    query = parse_qs(url.query)
                    data = tracking[key].frames(int(query.get('start', ['0'])[0]), int(query.get('count', ['250'])[0]))
                    payload, kind = json.dumps(data, allow_nan=False, separators=(',', ':')).encode(), 'application/json'
                elif url.path.startswith('/video/'):
                    send_video(self, videos[url.path.removeprefix('/video/')])
                    return
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header('Content-Type', kind)
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self'; connect-src 'self'; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(payload)
            except (ValueError, KeyError):
                self.send_error(400, 'Invalid source or frame range')
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def load_alignment(path):
    result = json.loads(Path(path).read_text(encoding='utf-8'))
    if (result.get('human_anchors_used') is not False
            or result.get('parameters_selected_on_provided_fixture') is not False
            or result.get('usable_for_possession') is not False):
        raise ValueError('Automatic experimental read-only mapping required')
    tracking, videos = {}, {}
    for key in ('tactical', 'broadcast'):
        source = result['sources'][key]
        video = Path(source['video'])
        for field in ('meta', 'tracking', 'homography'):
            if sha256(Path(source[field])) != source[field + '_sha256']:
                raise ValueError('Source sidecar differs from alignment registration')
        if (video.stat().st_size != source['video_bytes'] or video.stat().st_mtime_ns != source['video_mtime_ns']):
            raise ValueError('Video fingerprint differs from automatic alignment')
        tracking[key] = Tracking(source['meta'], source['tracking'])
        videos[key] = video
    validate_segments(result['segments'], tracking['tactical'], tracking['broadcast'])
    return tracking, videos, result['segments']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alignment', required=True)
    parser.add_argument('--port', type=int, default=8768)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    print('Kaynaklar ve otomatik esleme yukleniyor...', flush=True)
    tracking, videos, segments = load_alignment(args.alignment)
    server = server_for_pair(tracking['tactical'], tracking['broadcast'], videos['tactical'], videos['broadcast'], segments, args.port)
    print(f'Hazir: http://127.0.0.1:{server.server_port}', flush=True)
    if args.open:
        import webbrowser
        threading.Timer(.5, lambda: webbrowser.open(f'http://127.0.0.1:{server.server_port}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
