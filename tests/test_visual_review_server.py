import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tools.visual_review_server import server


class ProgressiveReviewServerTests(unittest.TestCase):
    def test_status_range_and_nonpublic_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'registration.json').write_text('{"private_receipt":true}')
            (root/'part-000.mp4').write_bytes(b'0123456789')
            service=server(root,port=0)
            thread=threading.Thread(target=service.serve_forever,daemon=True);thread.start()
            address=f'http://127.0.0.1:{service.server_port}'
            try:
                with urlopen(address+'/api/status') as response:
                    self.assertTrue(json.load(response)['preparing'])
                (root/'status.json').write_text(json.dumps({'complete':False,'ready_seconds':10,'chunks':[{'file':'part-000.mp4'}]}))
                with urlopen(address+'/api/status') as response:
                    self.assertEqual(json.load(response)['ready_seconds'],10)
                with urlopen(Request(address+'/media/part-000.mp4',headers={'Range':'bytes=2-5'})) as response:
                    self.assertEqual(response.status,206);self.assertEqual(response.read(),b'2345')
                for path in ('/registration.json','/media/registration.json','/media/../registration.json'):
                    with self.subTest(path=path),self.assertRaises(HTTPError) as error:urlopen(address+path)
                    self.assertEqual(error.exception.code,404)
                with self.assertRaises(HTTPError) as error:urlopen(Request(address+'/',headers={'Host':'external.example'}))
                self.assertEqual(error.exception.code,403)
            finally:
                service.shutdown();service.server_close();thread.join()
