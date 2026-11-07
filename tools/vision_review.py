"""Loopback visual comparison of a registered external training sample, read only."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .metrica_data import sha256
from .soccernet_box_audit import reference_rows
from .soccernet_video import image_members
from development.image_analysis import SCHEMA


def project_observations(folder, source_registration, observations_path):
    folder = Path(folder)
    registration = json.loads((folder / 'registration.json').read_text())
    summary = json.loads((folder / 'summary.json').read_text())
    path = folder / 'frames.jsonl'
    if (registration['detector_observations_sha256'] != sha256(observations_path)
            or summary['schema'] != SCHEMA or summary['output_sha256'] != sha256(path)
            or summary['reference_annotations_read'] is not False):
        raise ValueError('Same-source project analysis required')
    source_id = (source_registration['config']['fixture']['video_sha256'] + ':'
                 + source_registration['config_sha256'])
    rows = []
    for line in path.read_text().splitlines():
        packet = json.loads(line)
        if packet['schema'] != SCHEMA or packet['source_id'] != source_id or packet['fusion_eligible'] is not False:
            raise ValueError('Unvalidated project measurement contract required')
        objects = []
        for item in packet['objects']:
            if (item['kind'] not in ('person_candidate', 'ball_candidate') or item['team'] is not None
                    or item['person_role'] not in (None, 'unknown') or item['fusion_eligible'] is not False):
                raise ValueError('Reference role/team cannot replace a model observation')
            track = item['image_track_id']
            objects.append({'kind': 'person' if item['kind'] == 'person_candidate' else 'sports ball',
                'confidence': item['confidence'], 'box_xyxy': item['box_xyxy_px'],
                'track_id': track.rsplit('/', 1)[-1] if track else None})
        rows.append({'source_frame': packet['source_frame'], 'video_time_s': packet['video_time_s'],
                     'width': packet['image_size_px'][0], 'height': packet['image_size_px'][1], 'objects': objects,
                     'ball_tracking': packet.get('ball_tracking')})
    return rows


def load_review(root, project_analysis=None):
    root = Path(root)
    sample = root / 'sample-v2'
    receipt = json.loads((sample / 'before-access.json').read_text())
    if (receipt['plan']['dataset'] != 'SoccerNet/SN-GSR-2024'
            or receipt['plan']['archive'] != 'train.zip'
            or receipt['plan']['provided_fixture_used'] is not False):
        raise ValueError('Registered external training sample required')
    manifest = json.loads((sample / 'manifest.json').read_text())
    members = image_members(manifest)
    video = json.loads((root / 'video-v1/video-manifest.json').read_text())
    if video['sample_manifest_sha256'] != sha256(sample / 'manifest.json') or len(video['frames']) != len(members):
        raise ValueError('Sample/video provenance differs')
    sources = []
    for member in members:
        path = (sample / 'sample' / member['member']).resolve()
        if (sample.resolve() not in path.parents or sha256(path) != member['sha256']):
            raise ValueError('Image source differs')
        sources.append(path)
    labels_spec = next(r for r in manifest['acquired_files'] if r['member'].endswith('Labels-GameState.json'))
    label_path = sample / 'sample' / labels_spec['member']
    if sha256(label_path) != labels_spec['sha256']: raise ValueError('Reference source differs')
    labels = json.loads(label_path.read_text())
    images = {r['file_name']: r for r in labels['images']}
    names = {r['id']: r['name'] for r in labels['categories']}
    predictions = {}
    for mode in ('native', 'sliced'):
        folder = root / (mode + '-v1')
        registration = json.loads((folder / 'registration.json').read_text())
        summary = json.loads((folder / 'summary.json').read_text())
        fixture = registration['config']['fixture']
        if (registration['provided_fixture_used'] is not False
                or fixture['source_kind'] != 'permitted_external_video'
                or fixture['provided_fixture_used'] is not False
                or fixture['video_sha256'] != video['video_sha256']
                or registration['config']['start_frame'] != 0
                or summary['processed_frames'] != len(members)):
            raise ValueError('Same-source completed external predictions required')
        if project_analysis is None:
            predictions[mode] = [json.loads(line) for line in (folder / 'observations.jsonl').read_text().splitlines()]
        else:
            predictions[mode] = project_observations(Path(project_analysis) / mode, registration, folder / 'observations.jsonl')
        if len(predictions[mode]) != len(members): raise ValueError('Incomplete predictions')
    frames = []
    for index, (member, mapping) in enumerate(zip(members, video['frames'])):
        image = images[Path(member['member']).name]
        if mapping['member'] != member['member'] or mapping['source_frame'] != index:
            raise ValueError('Video/image mapping differs')
        row = {'source_frame': index, 'file_name': image['file_name'], 'reference': reference_rows(labels, image['image_id'], names)}
        for mode, observations in predictions.items():
            frame = observations[index]
            if (frame['source_frame'] != index or (frame['width'], frame['height']) != (image['width'], image['height'])):
                raise ValueError('Prediction frame/dimensions differ')
            row[mode] = frame['objects']
            if frame.get('ball_tracking') is not None:
                row.setdefault('ball_tracking', {})[mode] = frame['ball_tracking']
        frames.append(row)
    if video['fps'] != labels['info']['frame_rate']: raise ValueError('Frame clock differs')
    return {'fps': video['fps'], 'width': video['width'], 'height': video['height'],
            'sequence': labels['info']['name'], 'training_sample': True, 'frames': frames,
            'source_start_frame': int(Path(members[0]['member']).stem) - 1,
            'source_game_id': labels['info']['game_id'],
            'project_analysis_connected': project_analysis is not None,
            'reference_is_model_input': False, 'read_only': True}, sources


def server_for_review(payload, sources, port=0, gallery=None, project_analysis=None):
    html = Path(__file__).resolve().parents[1] / 'viewer/vision.html'
    cache = {'first': (payload, sources)}
    catalog = {'first': {'id': 'first', 'title': payload.get('sequence', 'İlk örnek'),
                         'frames': len(payload['frames']), 'fps': payload.get('fps', 25)}}

    def entries():
        if gallery and Path(gallery).is_file():
            try:
                for clip in json.loads(Path(gallery).read_text())['clips']:
                    catalog[clip['id']] = {'id': clip['id'], 'title': clip['id'], 'study': clip['study'],
                        'frames': clip['frames'], 'fps': 25, 'game_id': clip['source_game_id']}
            except json.JSONDecodeError:
                pass  # A completed manifest may be replaced while the gallery grows.
        return list(catalog.values())

    def clip_data(key):
        entries()
        if key not in catalog: raise KeyError(key)
        if key not in cache:
            project = Path(project_analysis) / key if project_analysis else None
            cache[key] = load_review(catalog[key]['study'], project)
        return cache[key]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
                self.send_error(403)
                return
            url = urlsplit(self.path)
            path = url.path
            if path == '/': data, content_type = html.read_bytes(), 'text/html; charset=utf-8'
            elif path == '/api/clips':
                data, content_type = json.dumps([dict(id=c['id'], title=c['title'], frames=c['frames'], fps=c['fps']) for c in entries()]).encode(), 'application/json'
            elif path == '/api/review':
                key = parse_qs(url.query).get('clip', ['first'])[0]
                try: selected, _ = clip_data(key)
                except KeyError:
                    self.send_error(404)
                    return
                result = dict(selected, image_base='/image/' + key + '/') if url.query else selected
                data, content_type = json.dumps(result).encode(), 'application/json'
            elif path.startswith('/image/') and len(path.split('/')) == 4:
                _, _, key, number = path.split('/')
                try:
                    _, paths = clip_data(key)
                    if not number.isdigit() or int(number) >= len(paths): raise KeyError(number)
                    data, content_type = paths[int(number)].read_bytes(), 'image/jpeg'
                except KeyError:
                    self.send_error(404)
                    return
            elif path.startswith('/image/') and path[7:].isdigit() and int(path[7:]) < len(sources):
                data, content_type = sources[int(path[7:])].read_bytes(), 'image/jpeg'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args): pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True)
    parser.add_argument('--port', type=int, default=8769)
    parser.add_argument('--gallery', help='Optional growing gallery.json of completed external studies')
    parser.add_argument('--project-analysis', help='Optional project image analysis directory, including first/')
    args = parser.parse_args()
    payload, sources = load_review(args.study, Path(args.project_analysis) / 'first' if args.project_analysis else None)
    server = server_for_review(payload, sources, args.port, gallery=args.gallery, project_analysis=args.project_analysis)
    print(f'External training review: http://127.0.0.1:{server.server_port}/', flush=True)
    server.serve_forever()
