import io
from pathlib import Path
import unittest
import zipfile
from tools.vision_gallery_build import member_payload
from tools.soccernet_video import image_members


class GalleryAcquisitionTests(unittest.TestCase):
    def test_random_access_zip_member_matches_zipfile(self):
        for compression in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED):
            data = io.BytesIO()
            with zipfile.ZipFile(data, 'w', compression=compression) as writer:
                writer.writestr('SNGS-060/img1/000001.jpg', b'first' * 1000)
                writer.writestr('SNGS-060/img1/000002.jpg', b'second' * 1000)
            with zipfile.ZipFile(data) as archive:
                info = archive.getinfo('SNGS-060/img1/000002.jpg')
                raw = data.getvalue()[info.header_offset:]
                self.assertEqual(member_payload(info, raw), archive.read(info))
                corrupted = bytearray(raw)
                corrupted[30] ^= 1
                with self.assertRaises(ValueError): member_payload(info, corrupted)
                with self.assertRaises(ValueError): member_payload(info, raw[:31])

    def test_registered_nonzero_range_preserves_source_frame_numbers(self):
        manifest = {'complete': True, 'provided_fixture_used': False, 'frame_range': [75, 150],
                    'acquired_files': [{'member': f'SNGS-068/img1/{n:06}.jpg', 'zip_crc_verified': True}
                                       for n in range(76, 151)]}
        self.assertEqual(len(image_members(manifest)), 75)
        manifest['acquired_files'][2]['member'] = 'SNGS-068/img1/000075.jpg'
        with self.assertRaises(ValueError): image_members(manifest)
