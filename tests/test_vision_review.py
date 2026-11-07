import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from tools.vision_review import load_review, server_for_review


class VisionReviewTests(unittest.TestCase):
    def test_gallery_selection_keeps_clip_images_separate(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            first, second = root / 'first.jpg', root / 'second.jpg'
            first.write_bytes(b'first-clip')
            second.write_bytes(b'second-clip')
            manifest = root / 'gallery.json'
            manifest.write_text(json.dumps({'clips': [{'id': 'SNGS-068', 'study': str(root / 'second'),
                'frames': 75, 'source_game_id': '9'}]}))
            payload = {'frames': [], 'fps': 25}
            with patch('tools.vision_review.load_review', return_value=(payload, [second])) as loader:
                server = server_for_review(payload, [first], gallery=manifest)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f'http://127.0.0.1:{server.server_port}'
                try:
                    with urllib.request.urlopen(base + '/api/clips') as response:
                        self.assertEqual([r['id'] for r in json.load(response)], ['first', 'SNGS-068'])
                    with urllib.request.urlopen(base + '/image/SNGS-068/0') as response:
                        self.assertEqual(response.read(), b'second-clip')
                    with urllib.request.urlopen(base + '/image/first/0') as response:
                        self.assertEqual(response.read(), b'first-clip')
                    self.assertEqual(loader.call_count, 1)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join()

    def test_supplied_fixture_cannot_enter_development_review(self):
        with tempfile.TemporaryDirectory() as root:
            sample = Path(root) / 'sample-v2'
            sample.mkdir()
            (sample / 'before-access.json').write_text(json.dumps({'plan': {
                'dataset': 'SoccerNet/SN-GSR-2024', 'archive': 'train.zip', 'provided_fixture_used': True}}))
            with self.assertRaises(ValueError): load_review(root)

    def test_loopback_read_only_routes_and_invalid_image_paths(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'fixture.jpg'
            path.write_bytes(b'synthetic-image-bytes')
            payload = {'frames': [], 'read_only': True}
            server = server_for_review(payload, [path])
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with urllib.request.urlopen(base + '/api/review') as response:
                    self.assertEqual(json.load(response), payload)
                with urllib.request.urlopen(base + '/api/review?clip=first') as response:
                    self.assertEqual(json.load(response)['image_base'], '/image/first/')
                with urllib.request.urlopen(base + '/api/clips') as response:
                    self.assertEqual(json.load(response)[0]['id'], 'first')
                with urllib.request.urlopen(base + '/image/first/0') as response:
                    self.assertEqual(response.read(), path.read_bytes())
                with urllib.request.urlopen(base + '/image/0') as response:
                    self.assertEqual(response.read(), path.read_bytes())
                    self.assertIn("connect-src 'self'", response.headers['Content-Security-Policy'])
                for suffix in ('/image/1', '/image/-1', '/image/../../fixture.jpg', '/api/save',
                               '/api/review?clip=not-registered', '/image/not-registered/0', '/image/first/1'):
                    with self.subTest(suffix=suffix), self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(base + suffix)
                    self.assertEqual(error.exception.code, 404)
                request = urllib.request.Request(base + '/api/review', headers={'Host': 'elsewhere.invalid'})
                with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(request)
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(urllib.request.Request(base + '/api/save', data=b'{}'))
                self.assertEqual(error.exception.code, 501)
            finally:
                server.shutdown()
                server.server_close()
                worker.join()
