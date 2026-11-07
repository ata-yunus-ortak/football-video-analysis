import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from tools.tracking_viewer import Tracking
from tools.paired_viewer import load_alignment, server_for_pair, validate_segments
from tools.metrica_data import sha256


SEGMENTS = [{'t0': 1., 't1': 3., 'b0': 4., 'b1': 6., 'status': 'clock_candidate',
             'usable_for_possession': False}]


class PairedViewerTests(unittest.TestCase):
    def test_order_source_bounds_and_candidate_only_contract(self):
        a, b = Tracking.demo(), Tracking.demo()
        validate_segments(SEGMENTS, a, b)
        for fields in ({'b0': -1}, {'t1': 20}, {'b1': 4}, {'t0': float('nan')},
                       {'usable_for_possession': True}, {'status': 'human_confirmed'}):
            with self.assertRaises(ValueError): validate_segments([{**SEGMENTS[0], **fields}], a, b)
        with self.assertRaises(ValueError): validate_segments(SEGMENTS + SEGMENTS, a, b)

    def test_pair_routes_do_not_mix_videos_or_tracking_and_reject_remote_host(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            videos = [root / 'a.mp4', root / 'b.mp4']
            videos[0].write_bytes(bytes(range(100)))
            videos[1].write_bytes(bytes(reversed(range(100))))
            a, b = Tracking.demo(), Tracking.demo()
            b.data[:, :, 0] += .05
            server = server_for_pair(a, b, *videos, SEGMENTS)
            worker = threading.Thread(target=server.serve_forever, daemon=True);worker.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with urllib.request.urlopen(base + '/api/meta') as r: meta = json.load(r)
                self.assertEqual(set(meta), {'tactical', 'broadcast'})
                with urllib.request.urlopen(base + '/api/mapping') as r: mapping = json.load(r)
                self.assertTrue(mapping['review_only'])
                self.assertFalse(mapping['usable_for_possession'])
                coordinates = []
                for key in ('tactical', 'broadcast'):
                    with urllib.request.urlopen(base + f'/api/frames/{key}?start=0&count=1') as r:
                        coordinates.append(json.load(r)['frames'][0][0][0])
                self.assertAlmostEqual(coordinates[1] - coordinates[0], .05)
                for key, expected in [('tactical', bytes(range(10, 20))), ('broadcast', bytes(range(89, 79, -1)))]:
                    request = urllib.request.Request(base + '/video/' + key, headers={'Range': 'bytes=10-19'})
                    with urllib.request.urlopen(request) as r:
                        self.assertEqual(r.status, 206);self.assertEqual(r.read(), expected)
                requests = [(base + '/api/meta', {'Host': 'untrusted.example'}, 403),
                            (base + '/video/tactical', {'Range': 'bytes=200-'}, 416),
                            (base + '/api/frames/other', {}, 400)]
                for url, headers, expected in requests:
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(urllib.request.Request(url, headers=headers))
                    self.assertEqual(error.exception.code, expected)
            finally:
                server.shutdown();server.server_close();worker.join(timeout=2)

    def test_registered_source_file_change_fails_before_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);sources = {}
            for key in ('tactical', 'broadcast'):
                source = {}
                for field in ('meta', 'tracking', 'homography'):
                    p = root / f'{key}-{field}.synthetic';p.write_bytes(field.encode())
                    source[field], source[field + '_sha256'] = str(p), sha256(p)
                video = root / f'{key}.mp4';video.write_bytes(b'synthetic-video')
                source.update(video=str(video), video_bytes=video.stat().st_size, video_mtime_ns=video.stat().st_mtime_ns)
                sources[key] = source
            data = {'human_anchors_used': False, 'parameters_selected_on_provided_fixture': False,
                    'usable_for_possession': False, 'sources': sources, 'segments': SEGMENTS}
            path = root / 'alignment.json';path.write_text(json.dumps(data))
            with patch('tools.paired_viewer.Tracking', return_value=Tracking.demo()):
                self.assertEqual(len(load_alignment(path)[2]), 1)
                Path(sources['broadcast']['tracking']).write_bytes(b'changed-source')
                with self.assertRaises(ValueError): load_alignment(path)
