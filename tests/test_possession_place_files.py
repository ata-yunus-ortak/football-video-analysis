"""tools/possession_place_files.py on synthetic folders (no match data): finds the bundle files where a download put them,
also inside a .zip, copies only the missing ones, never replaces a file that is already in the bundle, and prints only
names, folders and status words."""
import contextlib
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tools import possession_place_files as P

NAMES = [f'{cam}/{P.GAME}_{suf}' for cam, suf in P.FILES]
SECRET = 'icerik-satiri-12345'          # a marker inside every synthetic file; it must never appear in the output


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def run(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = P.main(args)
    return code, buf.getvalue()


class PlaceFilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bundle = self.root / 'FootballPrivate' / 'mtah2027' / 'bundle'
        self.down = self.root / 'Downloads'
        self.status = self.root / 'logs' / 'durum.txt'

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, *extra):
        return ['--data-dir', str(self.bundle), '--only', '--search', str(self.down), '--status-file', str(self.status)] + list(extra)

    def test_copies_every_missing_file_from_nested_download_folders(self):
        for n in NAMES:
            write(self.down / 'BAR-ATH-data' / n, f'{SECRET} {n}')
        code, out = run(self.args())
        self.assertEqual(code, 0)
        for n in NAMES:
            self.assertEqual((self.bundle / n).read_text(encoding='utf-8'), f'{SECRET} {n}')
            self.assertTrue((self.down / 'BAR-ATH-data' / n).exists())             # the original stays where it was
        self.assertIn('SONUC: TAMAM', out)
        self.assertEqual(out.count('YERLESTIRILDI'), 9)
        self.assertNotIn(SECRET, out)
        self.assertNotIn(SECRET, self.status.read_text(encoding='utf-8'))
        self.assertIn('SONUC: TAMAM', self.status.read_text(encoding='utf-8'))
        self.assertFalse(list(self.bundle.rglob('*.part')))

    def test_existing_files_are_kept_and_empty_ones_replaced(self):
        for n in NAMES:
            write(self.down / n.split('/')[1], f'{SECRET} new {n}')               # loose in Downloads, without folders
        write(self.bundle / NAMES[0], 'already here')
        write(self.bundle / NAMES[1], '')
        code, out = run(self.args())
        self.assertEqual(code, 0)
        self.assertEqual((self.bundle / NAMES[0]).read_text(encoding='utf-8'), 'already here')
        self.assertEqual((self.bundle / NAMES[1]).read_text(encoding='utf-8'), f'{SECRET} new {NAMES[1]}')
        self.assertEqual(out.count('ZATEN VAR'), 1)

    def test_files_inside_a_zip_and_browser_suffixes(self):
        z = self.down / 'mtah-2027-data.zip'
        z.parent.mkdir(parents=True)
        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
            for n in NAMES[:-1]:
                zf.writestr('data/' + n, f'{SECRET} zip {n}')
        write(self.down / f'{P.GAME}_broadcast (1).mp4', f'{SECRET} second download')
        code, out = run(self.args())
        self.assertEqual(code, 0)
        self.assertEqual((self.bundle / NAMES[3]).read_text(encoding='utf-8'), f'{SECRET} zip {NAMES[3]}')
        self.assertEqual((self.bundle / NAMES[-1]).read_text(encoding='utf-8'), f'{SECRET} second download')
        self.assertIn('icinden', out)
        self.assertNotIn(SECRET, out)

    def test_largest_copy_wins(self):
        for n in NAMES:
            write(self.down / 'a' / n, f'{SECRET} {n}')
        write(self.down / 'b' / NAMES[4], f'{SECRET} {NAMES[4]} the complete one, longer')
        code, out = run(self.args())
        self.assertEqual(code, 0)
        self.assertIn('longer', (self.bundle / NAMES[4]).read_text(encoding='utf-8'))
        self.assertIn('en buyugu', out)

    def test_exit_codes_for_missing_videos_and_missing_required_files(self):
        for n in NAMES:
            if not n.endswith('.mp4'):
                write(self.down / n, f'{SECRET} {n}')
        code, out = run(self.args())
        self.assertEqual(code, 2)
        self.assertIn('SONUC: VIDEO EKSIK', out)
        (self.bundle / 'tactical' / f'{P.GAME}_tactical_smart_tagging.xml').unlink()
        (self.down / 'tactical' / f'{P.GAME}_tactical_smart_tagging.xml').unlink()
        code, out = run(self.args())
        self.assertEqual(code, 1)
        self.assertIn('SONUC: EKSIK', out)
        self.assertIn('smart_tagging', out.splitlines()[-1])

    def test_the_bundle_itself_is_not_a_source_and_dry_run_copies_nothing(self):
        for n in NAMES:
            write(self.down / n, f'{SECRET} {n}')
        code, out = run(self.args('--dry-run'))
        self.assertEqual(code, 0)
        self.assertEqual(out.count('KOPYALANACAK'), 9)
        self.assertFalse(self.bundle.exists() and any(self.bundle.rglob('*.*')))
        # the bundle sits inside a searched folder: its own (empty) files are not taken as sources
        inner = self.down / 'bundle'
        write(inner / NAMES[0], '')
        code, out = run(['--data-dir', str(inner), '--only', '--search', str(self.down)])
        self.assertEqual(code, 0)
        self.assertEqual((inner / NAMES[0]).read_text(encoding='utf-8'), f'{SECRET} {NAMES[0]}')

    def test_no_space_uses_a_hard_link_for_loose_files_and_reports_zip_members(self):
        for n in NAMES:
            write(self.down / n, f'{SECRET} {n}')
        full = mock.patch.object(P.shutil, 'disk_usage', return_value=mock.Mock(free=0))
        with full:
            code, out = run(self.args())
        self.assertEqual(code, 0)
        self.assertIn('baglanti', out)
        self.assertEqual((self.bundle / NAMES[2]).read_text(encoding='utf-8'), f'{SECRET} {NAMES[2]}')
        other = self.root / 'other'
        z = self.root / 'zips' / 'bundle.zip'
        z.parent.mkdir(parents=True)
        with zipfile.ZipFile(z, 'w') as zf:
            zf.writestr(NAMES[0], f'{SECRET} zip')
        with full:
            code, out = run(['--data-dir', str(other), '--only', '--search', str(z.parent)])
        self.assertEqual(code, 1)
        self.assertIn('YER YOK', out)
        self.assertFalse(list(other.rglob('*.part')))

    def test_default_folder_follows_the_delivery_tool(self):
        with mock.patch.dict(os.environ, {'MTAH_DATA_DIR': str(self.root / 'x')}, clear=False):
            self.assertEqual(P.default_data_dir(), self.root / 'x')
        env = {k: v for k, v in os.environ.items() if k not in ('MTAH_DATA_DIR',)}
        env['MTAH_PRIVATE_DIR'] = str(self.root / 'priv')
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(P.default_data_dir(), self.root / 'priv' / 'mtah2027' / 'bundle')


if __name__ == '__main__':
    unittest.main()
