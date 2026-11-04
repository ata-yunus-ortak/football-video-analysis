import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
import numpy as np
from tools.tracking_viewer import Tracking, server_for


class ViewerTests(unittest.TestCase):
    def test_schema_speed_units_velocity_and_missing_samples(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            meta, raw = root / 'meta.xml', root / 'raw.txt'
            meta.write_text('''<main><Team id="h"><Name>H</Name></Team><Team id="a"><Name>A</Name></Team>
            <Player id="1" teamId="h"/><Player id="2" teamId="a"/><FrameRate>25</FrameRate>
            <FieldSize><Width>100</Width><Height>60</Height></FieldSize>
            <Channel id="x"><Name>position_x</Name><Unit>normalized</Unit></Channel>
            <Channel id="y"><Name>position_y</Name><Unit>normalized</Unit></Channel>
            <Channel id="s"><Name>speed_kph</Name><Unit>kph</Unit></Channel>
            <BallChannelRef channelId="x"/><BallChannelRef channelId="y"/><BallChannelRef channelId="s"/></main>''')
            raw.write_text('1:0.2,0.3,36;0.7,0.5,0:0.3,0.4,72\n2:0.204,0.3,36;0.7,0.5,0:nan,nan,nan\n3:0.208,0.3,36;0.7,0.5,0:0.4,0.4,72\n')
            tracking = Tracking(meta, raw)
            rows = tracking.frames(0, 3)['frames']
            self.assertEqual(rows[0][0][2], 36.)
            self.assertEqual(rows[0][0][3:], [None, None])
            self.assertEqual(rows[1][0][3:], [10., 0.])
            self.assertEqual(rows[2][-1][3:], [None, None])
            self.assertEqual(tracking.frames(1, 1)['frames'][0][0][3:], [10., 0.])
            for start, count in [(-1, 1), (3, 1), (0, 501)]:
                with self.assertRaises(ValueError): tracking.frames(start, count)
            raw.write_text(raw.read_text().replace('2:', '4:'))
            with self.assertRaises(ValueError): Tracking(meta, raw)

    def test_loopback_routes_json_and_video_range_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / 'synthetic.mp4'
            video.write_bytes(bytes(range(100)))
            server = server_for(Tracking.demo(), video=video)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with urllib.request.urlopen(base + '/api/meta') as response:
                    meta = json.load(response)
                self.assertTrue(meta['synthetic'])
                self.assertTrue(meta['video_available'])
                with urllib.request.urlopen(base + '/api/frames?start=49&count=12') as response:
                    data = json.load(response)
                self.assertIsNone(data['frames'][1][-1][0])
                with urllib.request.urlopen(base) as response:
                    self.assertIn('Tracking Stüdyosu', response.read().decode())
                for header, expected in [('bytes=10-19', bytes(range(10, 20))), ('bytes=-5', bytes(range(95, 100)))]:
                    request = urllib.request.Request(base + '/video', headers={'Range': header})
                    with urllib.request.urlopen(request) as response:
                        self.assertEqual(response.status, 206)
                        self.assertEqual(response.read(), expected)
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(
                        urllib.request.Request(base + '/video', headers={'Range': 'bytes=1000-'}))
                self.assertEqual(caught.exception.code, 416)
                with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(base + '/api/frames?start=-1')
                with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(base + '/not-allowed')
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
