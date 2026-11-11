"""Synthetic checks of the one-command delivery chain (tools/possession_deliver.py); no match data, no accuracy claims.

The chain is run on a small synthetic bundle that carries the file names of the provided match. The checks are
about the process: only status words reach the console, a lower ladder step is used only after an error, the
delivered file is the generated file, and the document copy receives the run record.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock
try:
    from possession import run29                                      # noqa: F401  (dependencies present?)
    from tests.test_possession_crossplatform import bundle, N
    from tools import possession_deliver as pd
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

REPO = Path(__file__).resolve().parents[1]
SECRET = 'SECRET-PROGRAM-OUTPUT'


def provided_like(root):
    """Synthetic bundle renamed to the file names of the provided match; returns (data dir, clock dirs)."""
    src = bundle(root / 'syn')
    data = root / 'bundle'
    for cam in ('tactical', 'broadcast'):
        (data / cam).mkdir(parents=True)
        for p in (src / cam).iterdir():
            shutil.copyfile(p, data / cam / p.name.replace('SYN_', 'BAR-ATH_'))
    return data, {'tactical': src / 'clock-tactical', 'broadcast': src / 'clock-broadcast'}


def put_clock(private, clocks):
    for cam, d in clocks.items():
        out = private / 'possession-clock' / cam
        out.mkdir(parents=True)
        shutil.copyfile(d / 'observations.jsonl', out / 'observations.jsonl')
        (out / 'summary.json').write_text('{}')


def config(root, steps, **extra):
    cfg = json.loads((REPO / 'possession-release.json').read_text(encoding='utf-8'))
    cfg.update(steps=steps, **extra)
    path = root / 'release.json'
    path.write_text(json.dumps(cfg))
    return path


def fake_modules(root, clocks):
    """A failing entry point and a clock reader that copies prepared readings (both print text that must stay private)."""
    fake = root / 'fake'
    fake.mkdir()
    (fake / 'fake_entry.py').write_text(textwrap.dedent(f'''
        import sys
        RELEASE = 'none'
        def check_release():
            return {{}}
        def run(*a, **k):
            raise ValueError('{SECRET} 42.5')
        if __name__ == '__main__':
            print('{SECRET} label_counts 123')
            print('{SECRET}', file=sys.stderr)
            run()
        '''))
    (fake / 'fake_clock.py').write_text(textwrap.dedent(f'''
        import argparse, shutil
        from pathlib import Path
        p = argparse.ArgumentParser(); p.add_argument('--video'); p.add_argument('--out'); a = p.parse_args()
        out = Path(a.out); out.mkdir(parents=True)
        src = {{'tactical': {str(clocks['tactical'])!r}, 'broadcast': {str(clocks['broadcast'])!r}}}[out.name]
        shutil.copyfile(Path(src) / 'observations.jsonl', out / 'observations.jsonl')
        (out / 'summary.json').write_text('{{}}')
        print('{SECRET} readings 77')
        '''))
    return fake


def chain(args, extra_path=None):
    env = dict(os.environ)
    if extra_path:
        env['PYTHONPATH'] = str(extra_path) + os.pathsep + env.get('PYTHONPATH', '')
    out = io.StringIO()
    with mock.patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(out):
        code = pd.main(['--python', sys.executable, '--no-tests', '--no-clone-check', '--rows', str(N)] + [str(a) for a in args])
    return code, out.getvalue()


def status(text, name):
    for line in text.splitlines():
        if line.startswith('[') and f'] {name} .' in line:
            return line.split('. ', 1)[1].strip() if '. ' in line else line
    return None


RUN29 = {'name': 'possession-v2.9', 'module': 'possession.run29', 'manifest': 'possession-v29-release.json', 'broadcast': True}
RUN29_TACTICAL = dict(RUN29, name='possession-v2.9 tactical camera only', broadcast=False)
FAKE = {'name': 'fake', 'module': 'fake_entry', 'manifest': 'none', 'broadcast': True}


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class HelperTests(unittest.TestCase):
    def test_error_class_gives_the_class_and_code_location_but_never_the_message(self):
        tb = ('noise\nTraceback (most recent call last):\n'
              f'  File "{REPO / "possession" / "run29.py"}", line 176, in <module>\n    run()\n'
              f'  File "{REPO / "possession" / "data.py"}", line 102, in read_epts\n    raise ValueError(x)\n'
              f'  File "{REPO / ".venv-possession" / "Lib" / "site-packages" / "numpy" / "x.py"}", line 5, in f\n    pass\n'
              'ValueError: line 17 has 3 fields: 0.4312,0.5521,1\n')
        got = pd.error_class(tb, 1)
        self.assertEqual(got, 'ValueError @ possession/data.py:102 read_epts')
        self.assertEqual(pd.error_class('killed', -9), 'cikis kodu -9')
        # block-buffered program output that reaches the log after the traceback (seen on GitHub runners)
        self.assertEqual(pd.error_class(tb + 'secret label_counts 123\n', 1), 'ValueError @ possession/data.py:102 read_epts')

    def test_a_failed_release_check_names_the_changed_file_and_nothing_else(self):
        tb = ('Traceback (most recent call last):\n  File "<string>", line 1, in <module>\n'
              f'  File "{REPO / "possession" / "run29.py"}", line 50, in check_release\n    raise ValueError(...)\n')
        self.assertEqual(pd.release_detail(tb + 'ValueError: frozen source changed: data.py\n'), 'frozen source changed: data.py')
        self.assertEqual(pd.release_detail(tb + 'ValueError: frozen bundle changed: v2.1\n'), 'frozen bundle changed: v2.1')
        self.assertEqual(pd.release_detail(tb + 'ValueError: the v2.9 release manifest changed\n'), 'the v2.9 release manifest changed')
        self.assertEqual(pd.release_detail(tb + 'ValueError: the v2.11 release manifest changed\n'), 'the v2.11 release manifest changed')
        self.assertEqual(pd.release_detail(tb + 'ValueError: frozen source changed: keeper2.py\n'), 'frozen source changed: keeper2.py')
        self.assertEqual(pd.release_detail(tb + "ModuleNotFoundError: No module named 'scipy'\n"), "No module named 'scipy'")
        self.assertEqual(pd.release_detail(tb + f'ValueError: {SECRET} 12.5\n'), '')            # any other message stays private
        self.assertEqual(pd.release_detail(tb + f'ValueError: frozen source changed: data.py {SECRET} ' + 'x' * 80 + '\n'), '')

    def test_the_run_record_says_whether_the_goalkeeper_check_moved_anything_without_a_count(self):
        facts = dict.fromkeys(('file', 'sha256', 'when', 'command', 'repo', 'platform', 'format', 'plausibility', 'repeat', 'clone',
                               'noclock', 'platform_check', 'organiser', 'public'), 'x')
        row = lambda rep: [l for l in pd.run_record(rep, facts).splitlines() if l.startswith('| Goalkeeper team correction')][0]
        base = {'rows': 5, 'system': 's', 'path': 'v2.1', 'fusion': {'reason': 'none'}}
        self.assertIn('not part of the entry point', row(base))                                  # a lower step of the ladder
        self.assertIn('nothing moved', row(dict(base, goalkeeper_correction={'moved_pieces': 0, 'moved_frames': 0})))
        short = row(dict(base, goalkeeper_correction={'moved_pieces': 37, 'moved_frames': 912, 'halves': [
            {'left_evidence_frames': {'defending_id': 30000, 'other_id': 80, 'other_id_dominant': False},
             'right_evidence_frames': {'defending_id': 28000, 'other_id': 0, 'other_id_dominant': False}}]}))
        self.assertIn('short goalkeeper track pieces', short)
        whole = row(dict(base, goalkeeper_correction={'moved_pieces': 300, 'moved_frames': 91234, 'halves': [
            {'left_evidence_frames': {'defending_id': 0, 'other_id': 30000, 'other_id_dominant': True},
             'right_evidence_frames': {'defending_id': 28000, 'other_id': 0, 'other_id_dominant': False}}]}))
        self.assertIn('for most of a half', whole)
        self.assertNotIn('short', whole)
        for text in (short, whole):
            self.assertIn('moved to the team that defends that goal', text)
            self.assertFalse(any(ch.isdigit() for ch in text))                                   # a category, never a number

    def test_plain_csv_check(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.csv'
            good = 'frame,label\n' + ''.join(f'{i},{"HADX"[i % 4]}\n' for i in range(8))
            for text, want in ((good, True), (good.replace('\n', '\r\n'), False), (good.replace('3,X', '3,'), False),
                               (good.replace('5,A', '6,A'), False), (good[:-1], False), (good.replace('frame,label', 'Frame,Label'), False),
                               (good + '8,H\n', False), (good.replace('2,D', '2,d'), False)):
                p.write_bytes(text.encode())
                self.assertEqual(pd.plain_csv_check(p, 8), want, text[:40])


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class ChainTests(unittest.TestCase):
    def test_chain_with_existing_clock_readings_delivers_the_generated_file_and_prints_status_words_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data, clocks = provided_like(root)
            private = root / 'private'
            put_clock(private, clocks)
            code, text = chain(['--team', 'Test Takimi', '--private', private, '--data-dir', data,
                                '--release-config', config(root, [RUN29])])
            self.assertIn(code, (0, 2), text)
            self.assertEqual(status(text, 'URETIM'), 'OK (possession-v2.9, saatli)')
            self.assertEqual(status(text, 'BICIM'), 'OK')
            self.assertTrue(status(text, 'GIRDI OKUMA').startswith('FAIL (tactical_records, '), text)   # a synthetic bundle is not the match
            self.assertEqual(status(text, 'SAAT'), 'VAR (onceki okuma kullanildi)')
            self.assertIn(status(text, 'SAATSIZ KARSILASTIRMA'), ('AYNI', 'FARKLI'))
            self.assertEqual(status(text, 'TEKRAR URETIM'), 'AYNI')
            self.assertTrue(status(text, 'MAKULLUK').startswith('FAIL ('))            # six minutes of synthetic play
            self.assertEqual(status(text, 'TEMIZ KLON'), 'ATLANDI')
            deliver = private / 'teslim'
            rec = json.loads((deliver / 'OZEL-kayit.json').read_text())
            run_csv = Path(rec['run_folder']) / 'submission.csv'
            self.assertEqual((deliver / 'Test_Takimi.csv').read_bytes(), run_csv.read_bytes())
            self.assertTrue(pd.plain_csv_check(deliver / 'Test_Takimi.csv', N))
            doc = (deliver / 'Test_Takimi.md').read_text(encoding='utf-8')
            self.assertIn('## Appendix R. Run record of the submitted file', doc)
            self.assertIn(rec['sha256'], doc)
            self.assertIn('alignment: clock', doc)
            # nothing the pipeline printed (aggregate JSON of the run) reaches the console or the shareable file
            shared = (deliver / 'PAYLASILABILIR-durum.txt').read_text(encoding='utf-8')
            for leaked in ('label_counts', 'submission_sha256', rec['sha256'], 'model_version'):
                self.assertNotIn(leaked, text)
                self.assertNotIn(leaked, shared)
            self.assertIn('label_counts', Path(rec['log']).read_text(encoding='utf-8', errors='replace'))   # it is in the private log

    def test_a_lower_step_is_used_only_after_an_error_and_the_error_message_stays_private(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data, clocks = provided_like(root)
            fake = fake_modules(root, clocks)
            private = root / 'private'
            code, text = chain(['--team', 'T', '--private', private, '--data-dir', data, '--no-ocr', '--quick',
                                '--release-config', config(root, [FAKE, RUN29_TACTICAL])], extra_path=fake)
            self.assertEqual(code, 2, text)
            got = status(text, 'URETIM')
            self.assertTrue(got.startswith('OK (possession-v2.9 tactical camera only, saatsiz; basamak 2;'), got)
            self.assertIn('fake: ValueError', got)
            self.assertNotIn(SECRET, text)
            self.assertNotIn('42.5', text)
            rec = json.loads((private / 'teslim' / 'OZEL-kayit.json').read_text())
            rep = json.loads((Path(rec['run_folder']) / 'run.json').read_text())
            self.assertFalse(rep['broadcast_fill_used'])
            self.assertIn('not found', rep['fusion']['reason'])
            self.assertTrue((data / 'broadcast').exists())                              # the provided folder is untouched
            self.assertIn('tactical camera only', (private / 'teslim' / 'T.md').read_text(encoding='utf-8'))
            # a top step that fails alone leaves no deliverable
            private2 = root / 'private2'
            code, text = chain(['--team', 'T', '--private', private2, '--data-dir', data, '--no-ocr', '--quick',
                                '--release-config', config(root, [FAKE])], extra_path=fake)
            self.assertEqual(code, 1)
            self.assertTrue(status(text, 'URETIM').startswith('FAIL (fake: ValueError'))
            self.assertFalse((private2 / 'teslim' / 'T.csv').exists())
            self.assertIn('TESLIM HAZIR DEGIL', text)
            self.assertNotIn(SECRET, text)

    def test_clock_reading_then_the_clock_run_replaces_the_first_delivery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data, clocks = provided_like(root)
            fake = fake_modules(root, clocks)
            for cam in ('tactical', 'broadcast'):
                (data / cam / f'BAR-ATH_{cam}.mp4').write_bytes(b'')                    # the reader is replaced by a fake
            private = root / 'private'
            (private / 'possession-clock' / 'tactical').mkdir(parents=True)             # an unfinished earlier reading
            code, text = chain(['--team', 'T', '--private', private, '--data-dir', data, '--sync-python', sys.executable,
                                '--release-config', config(root, [RUN29], clock_module='fake_clock')], extra_path=fake)
            self.assertIn(code, (0, 2), text)
            self.assertEqual(status(text, 'URETIM'), 'OK (possession-v2.9, saatsiz)')
            self.assertEqual(status(text, 'ON TESLIM'), 'OK (possession-v2.9, saatsiz)')
            self.assertEqual(status(text, 'SAAT OKUMA'), 'OK')
            self.assertEqual(status(text, 'SAATLI URETIM'), 'OK (possession-v2.9, saatli)')
            self.assertEqual(status(text, 'TESLIM'), 'OK (possession-v2.9, saatli)')
            self.assertEqual(status(text, 'TEKRAR URETIM'), 'AYNI')
            self.assertNotIn(SECRET, text)
            rec = json.loads((private / 'teslim' / 'OZEL-kayit.json').read_text())
            self.assertTrue(rec['clock'])
            rep = json.loads((Path(rec['run_folder']) / 'run.json').read_text())
            self.assertEqual(rep['fusion']['alignment_mode'], 'clock')
            self.assertEqual(len(list((private / 'possession-clock').glob('tactical-yarim-*'))), 1)

    @unittest.skipUnless(shutil.which('git'), 'git not installed')
    def test_fresh_clone_of_the_pushed_branch_regenerates_the_delivered_file(self):
        import subprocess

        def git(*args, cwd):
            subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false']
                           + [str(a) for a in args], cwd=str(cwd), check=True, capture_output=True)

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data, _ = provided_like(root)
            work = root / 'work'                                    # a checkout of the release code with a remote
            for rel in ('possession', 'models'):
                shutil.copytree(REPO / rel, work / rel, ignore=shutil.ignore_patterns('__pycache__'))
            for f in list(REPO.glob('possession-*.json')) + [REPO / n for n in ('requirements-possession.txt', 'TECHNICAL_DOCUMENT.md', '.gitattributes')]:
                shutil.copyfile(f, work / f.name)
            git('init', '--quiet', cwd=work); git('add', '-A', cwd=work); git('commit', '--quiet', '-m', 'release', cwd=work)
            git('clone', '--quiet', '--bare', work, root / 'origin.git', cwd=root)
            git('remote', 'add', 'origin', root / 'origin.git', cwd=work)

            def run(private, *more):
                a = pd.parse(['--python', sys.executable, '--no-tests', '--no-ocr', '--rows', str(N), '--team', 'T', '--private', str(private),
                              '--data-dir', str(data), '--release-config', str(config(root, [RUN29]))] + list(more))
                c = pd.Chain(a)
                c.repo = work
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = c.run()
                return code, out.getvalue()

            code, text = run(root / 'p1')
            self.assertIn(code, (0, 2), text)
            self.assertTrue(status(text, 'DEPO').endswith(', temiz'), text)
            self.assertTrue(status(text, 'TEMIZ KLON').startswith('AYNI (commit '), text)
            self.assertIn('regenerates the same bytes', (root / 'p1' / 'teslim' / 'T.md').read_text(encoding='utf-8'))
            # a commit that is not on the remote branch: the check is not run, and the reason is printed
            (work / 'TECHNICAL_DOCUMENT.md').write_text('changed', encoding='utf-8')
            code, text = run(root / 'p2', '--quick')
            self.assertTrue(status(text, 'DEPO').endswith('1 dosya commit edilmemis'), text)
            git('commit', '--quiet', '-am', 'local only', cwd=work)
            code, text = run(root / 'p3', '--quick')
            self.assertTrue(status(text, 'TEMIZ KLON').startswith('ATLANDI (yerel commit'), text)
            git('push', '--quiet', 'origin', 'HEAD', cwd=work)
            code, text = run(root / 'p4', '--quick')
            self.assertTrue(status(text, 'TEMIZ KLON').startswith('ATLANDI (--quick; yerel commit'), text)

    def test_missing_data_stops_the_chain_before_anything_is_generated(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            code, text = chain(['--team', 'T', '--private', root / 'private', '--data-dir', root / 'nothing',
                                '--release-config', config(root, [RUN29])])
            self.assertEqual(code, 1)
            self.assertTrue(status(text, 'VERI').startswith('FAIL'))
            self.assertIsNone(status(text, 'URETIM'))
            self.assertFalse(list((root / 'private').glob('possession-run-*')))


if __name__ == '__main__':
    unittest.main()
