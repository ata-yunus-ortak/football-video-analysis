import unittest
import importlib.util
import json
from pathlib import Path
import tempfile
from tools.metrica_data import sha256
from tools.soccernet_video import image_members


class SampleVideoTests(unittest.TestCase):
    def manifest(self):
        return {'complete': True, 'provided_fixture_used': False, 'acquired_files': [
            {'member': f'SNGS-060/img1/{index:06}.jpg', 'zip_crc_verified': True}
            for index in range(1, 26)]}

    def test_order_and_source_frame_mapping(self):
        files = image_members(self.manifest())
        self.assertEqual(files[0]['member'], 'SNGS-060/img1/000001.jpg')
        self.assertEqual(len(files), 25)

    def test_partial_wrong_sequence_and_unverified_images_rejected(self):
        for case in ('partial', 'sequence', 'crc', 'provided'):
            data = self.manifest()
            if case == 'partial': data['acquired_files'].pop()
            if case == 'sequence': data['acquired_files'][0]['member'] = 'SNGS-061/img1/000001.jpg'
            if case == 'crc': data['acquired_files'][0]['zip_crc_verified'] = False
            if case == 'provided': data['provided_fixture_used'] = True
            with self.subTest(case=case), self.assertRaises(ValueError): image_members(data)

    @unittest.skipUnless(importlib.util.find_spec('av'), 'Optional local vision environment required')
    def test_lossless_video_keeps_every_source_image(self):
        from PIL import Image
        from tools.soccernet_video import run
        with tempfile.TemporaryDirectory() as root:
            sample = Path(root) / 'input'
            sample.mkdir()
            manifest = self.manifest()
            for index, spec in enumerate(manifest['acquired_files']):
                path = sample / 'sample' / spec['member']
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new('RGB', (32, 24), (index * 8, 77, 150)).save(path)
                spec['sha256'] = sha256(path)
            (sample / 'manifest.json').write_text(json.dumps(manifest))
            out = Path(root) / 'output'
            run(sample, out, 25)
            result = json.loads((out / 'video-manifest.json').read_text())
            self.assertTrue(result['rgb_lossless_verified'])
            self.assertEqual(len(result['frames']), 25)
            self.assertEqual(result['frames'][-1]['source_frame'], 24)
            self.assertFalse(result['labels_used_as_input'])
