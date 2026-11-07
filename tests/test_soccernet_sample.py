import io
import unittest

from tools.soccernet_sample import RangeReader


class Response(io.BytesIO):
    status = 206


class RangeReaderTests(unittest.TestCase):
    def test_zip_style_seeks_and_budget(self):
        def opener(request, timeout):
            begin, end = map(int, request.headers['Range'].split('=')[1].split('-'))
            result = Response(b'0123456789'[begin:end + 1])
            result.headers = {'Content-Range': f'bytes {begin}-{end}/10'}
            return result
        reader = RangeReader('https://example.invalid/train.zip', 10, 5, opener)
        reader.seek(-2, 2)
        self.assertEqual(reader.read(), b'89')
        reader.seek(0)
        self.assertEqual(reader.read(3), b'012')
        with self.assertRaises(ValueError): reader.read(1)
        self.assertEqual(reader.downloaded, 5)

    def test_full_response_wrong_range_and_partial_response_rejected(self):
        for status, header, content in [(200, 'bytes 0-1/10', b'01'),
                                        (206, 'bytes 1-2/10', b'12'),
                                        (206, 'bytes 0-1/10', b'0')]:
            def opener(request, timeout):
                result = Response(content)
                result.status = status
                result.headers = {'Content-Range': header}
                return result
            with self.subTest(status=status, header=header, content=content):
                with self.assertRaises(ValueError):
                    RangeReader('https://example.invalid/train.zip', 10, 10, opener).read(2)
