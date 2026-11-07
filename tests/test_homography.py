import csv
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import numpy as np
from development.homography import FrameHomographies
from tools.tracking_viewer import Tracking, server_for


def write_csv(path, matrices, flags=None):
    flags = [1] * len(matrices) if flags is None else flags
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(FrameHomographies.COLUMNS)
        for frame, (matrix, flag) in enumerate(zip(matrices, flags)):
            writer.writerow([frame, *np.asarray(matrix).reshape(-1), float('nan'), flag])


class HomographyTests(unittest.TestCase):
    def test_direction_units_perspective_and_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.csv'
            write_csv(path, [[[1000, 0, 100], [0, 500, 20], [.1, 0, 1]]])
            geometry = FrameHomographies(path)
            normalized = np.array([[0, 0], [.5, .4], [1, 1]])
            pixels = geometry.project(0, normalized)
            np.testing.assert_allclose(pixels[1], [600 / 1.05, 220 / 1.05])
            np.testing.assert_allclose(geometry.project(0, pixels, pitch=[105, 68]), normalized * [105, 68], atol=1e-10)
            self.assertEqual(geometry.metadata(1)['direction'], 'normalized_pitch_to_image_pixels')
            self.assertIsNone(geometry.frames(0, 1)[0]['reprojection_error'])

    def test_invalid_missing_singular_and_infinite_points_are_not_filled(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.csv'
            write_csv(path, [np.eye(3), np.eye(3), np.zeros((3, 3)), np.full((3, 3), np.nan),
                             [[1, 0, 0], [0, 1, 0], [1, 0, 1]]], [1, 0, 1, 1, 1])
            geometry = FrameHomographies(path)
            for frame in (1, 2, 3):
                self.assertTrue(np.isnan(geometry.project(frame, [[.2, .3]])).all())
                self.assertIsNone(geometry.frames(frame, 1)[0]['matrix'])
            result = geometry.project(4, [[-1, .4], [np.nan, .2], [np.inf, .2], [0, .4]])
            self.assertTrue(np.isnan(result[:3]).all())
            np.testing.assert_allclose(result[3], [0, .4])
            self.assertEqual(geometry.frames(4, 2)[1], None)
            self.assertFalse(geometry.metadata(6)['tracking_frame_count_matches'])
            self.assertEqual(geometry.metadata(5)['usable_matrix_frames'], 2)
            with self.assertRaises(ValueError): geometry.project(0, [[1, 2]], pitch=[0, 68])
            with self.assertRaises(ValueError): geometry.project(5, [[1, 2]])

    def test_wrong_schema_clock_and_flags_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.csv'
            for bad in ('frame,valid\n0,1\n', ','.join(FrameHomographies.COLUMNS) + '\n'):
                path.write_text(bad, encoding='utf-8')
                with self.assertRaises(ValueError): FrameHomographies(path)
            write_csv(path, [np.eye(3)])
            text = path.read_text()
            path.write_text(text.replace('\n0,', '\n1,'))
            with self.assertRaises(ValueError): FrameHomographies(path)
            write_csv(path, [np.eye(3)], [2])
            with self.assertRaises(ValueError): FrameHomographies(path)

    def test_viewer_keeps_each_source_and_its_geometry_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.csv'
            write_csv(path, [np.eye(3), np.eye(3)], [1, 0])
            tracking = Tracking.demo()
            tracking.synthetic = False
            tracking.data = tracking.data[:3]
            servers = [server_for(tracking, homography=path, source_name='Yayın örneği'),
                       server_for(Tracking.demo(), source_name='Taktik örneği')]
            workers = [threading.Thread(target=s.serve_forever, daemon=True) for s in servers]
            for worker in workers: worker.start()
            def read(index, route):
                with urllib.request.urlopen(f'http://127.0.0.1:{servers[index].server_port}{route}') as response:
                    return json.load(response)
            try:
                meta = read(0, '/api/meta')
                self.assertEqual(meta['source_name'], 'Yayın örneği')
                self.assertFalse(meta['homography']['tracking_frame_count_matches'])
                data = read(0, '/api/frames?start=1&count=3')
                self.assertEqual(len(data['frames']), 2)
                self.assertFalse(data['homography'][0]['usable'])
                self.assertIsNone(data['homography'][1])
                self.assertFalse(read(0, '/api/tags')['available'])
                self.assertEqual(read(1, '/api/meta')['source_name'], 'Taktik örneği')
                self.assertFalse(read(1, '/api/meta')['homography']['available'])
                self.assertNotIn('homography', read(1, '/api/frames?start=0&count=1'))
            finally:
                for server in servers: server.shutdown(); server.server_close()
                for worker in workers: worker.join(timeout=2)
