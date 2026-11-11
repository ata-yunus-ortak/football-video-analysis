"""One command for the whole local delivery chain of the possession release (team computer only).

    python -m tools.possession_deliver [--team NAME] [--data-dir DIR] [--private DIR] [--quick] [--no-ocr]
    Windows: double-click TESLIM-HAZIRLA.cmd

The provided match may be processed only on the team's own computer, and nothing about it may be given
to an AI service. This tool therefore runs every step itself, sends all program output to a private log
outside the repository and prints status words only (OK, FAIL, AYNI, FARKLI, ATLANDI, VAR, YOK, UYARI).
The printed lines and PAYLASILABILIR-durum.txt can be shared. The log, run.json, OZEL-kayit.json, the
CSV and the run record appended to the document copy must not be given to an AI service.

Steps (possession-release.json names the release, its technical fall-backs and the tests):
  ORTAM      Python 3.10-3.12, .venv-possession with the pinned packages
  SURUM      every frozen source and both model bundles equal the release manifest
  TESTLER    synthetic unit tests of the release (no match data)
  PLATFORM   does this computer reproduce the recorded bytes of the pipeline on a synthetic bundle?
  VERI       are the provided files where the entry point expects them?
  GIRDI OKUMA  do the release's readers reproduce the aggregate facts DATA.md publishes about the files
             (record counts, track slots, frames with a ball, usable homography rows), and do they agree, frame
             by frame, with a second reading done the way the organisers' starter code reads the tracking files?
             names of failed checks only
  URETIM     the release entry point; a lower step of the ladder is used only when the step above
             ends with an error, never because of its output
  BICIM      the organisers' format rules (possession.validate) and an independent plain-text check
  MAKULLUK   aggregate plausibility ranges (possession.plausibility); names of failed checks only
  TESLIM     <private>/teslim/<team>.csv and <team>.md (technical document + run record)
  SAAT       automatic clock readings of both videos (separate OCR environment), then the entry point
             again with the clock anchor; SAATSIZ says whether the file without the clock is the same
  TEKRAR     the delivered variant once more: are the bytes the same?
  TEMIZ KLON a fresh clone of the pushed branch regenerates the file: are the bytes the same?
             (only when the local commit is the head of the branch on GitHub)
  ORGANIZATOR / ACIK PENCERE   the organisers' validate_submission.py and the pass/fail-only check on the
             public five minutes (possession-final-check-plan.json), when their repository is found

Nothing here selects a model or a parameter: the release is fixed by possession-release.json before the
tool is run, and no step compares two outputs to choose the better one.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / 'possession-release.json'
CAMS = ('tactical', 'broadcast')
LABELS = set('HADX')


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def error_class(text, code):
    """'ValueError @ possession/data.py:102 read_epts' from a traceback: class and code location, never the message."""
    if 'Traceback (most recent call last)' not in text:
        return f'cikis kodu {code}'
    tb = text[text.rindex('Traceback (most recent call last)'):]
    lines = [l for l in tb.strip().splitlines() if l.strip()]
    m = re.match(r'^([A-Za-z_][\w.]*)\s*(:|$)', lines[-1]) if lines else None
    name = m.group(1) if m else 'hata'
    where = ''
    for f, ln, fn in reversed(re.findall(r'File "([^"]+)", line (\d+), in (\S+)', tb)):
        try:
            rel = Path(f).resolve().relative_to(REPO)
        except (ValueError, OSError):
            continue
        if any(part.startswith('.venv') or part == 'site-packages' for part in rel.parts):
            continue
        where = f' @ {rel.as_posix()}:{ln} {fn}'
        break
    return name + where


def release_detail(text):
    """What a failed release check names: the changed source file or bundle, or a missing package.
    The release check reads no match data, so this part of its message cannot carry any."""
    m = re.search(r"^(?:ValueError: ((?:frozen (?:source|bundle) changed|the v2\.\d\w? release manifest changed)[\w .:\-]{0,60})"
                  r"|ModuleNotFoundError: (No module named '[\w.]+'))\s*$", text, re.M)
    return (m.group(1) or m.group(2)) if m else ''


def plain_csv_check(path, rows):
    """The submission contract checked without any package: header, row count, frame order, alphabet, line ends."""
    raw = Path(path).read_bytes()
    if b'\r' in raw or not raw.endswith(b'\n'):
        return False
    try:
        lines = raw.decode('utf-8').split('\n')[:-1]
    except UnicodeDecodeError:
        return False
    if len(lines) != rows + 1 or lines[0] != 'frame,label':
        return False
    for i, line in enumerate(lines[1:]):
        f, _, lab = line.partition(',')
        if f != str(i) or lab not in LABELS:
            return False
    return True


def keeper_fact(rep):
    """What the goalkeeper team correction of possession-v2.11 did, as a category (no counts)."""
    k = rep.get('goalkeeper_correction')
    if not isinstance(k, dict):
        return 'not part of the entry point that produced the file'
    if not k.get('moved_pieces'):
        return 'nothing moved (no goalkeeper track found under the other team\'s id)'
    whole = any((h.get(f'{side}_evidence_frames') or {}).get('other_id_dominant') for h in k.get('halves', []) for side in ('left', 'right'))
    if whole:
        return ('a goalkeeper\'s tracks carried the other team\'s id for most of a half and were moved to the team that defends '
                'that goal')
    return ('short goalkeeper track pieces under the other team\'s id were moved to the team that defends that goal; '
            'no goalkeeper carried the other id for most of a half')


def run_record(rep, facts):
    """Markdown appendix with categorical facts of the delivered run (no per-frame content, no measured values)."""
    fus = rep.get('fusion') or {}
    if fus.get('reason'):
        cam = 'broadcast files not found: tactical camera only'
    else:
        cam = (f"files present; alignment: {fus.get('alignment_mode', 'n/a')}; accuracy gate "
               f"{'open (missing tactical balls filled)' if rep.get('broadcast_fill_used') else 'closed (tactical ball only)'}")
    rows = [('File', f"`{facts['file']}`, {rep.get('rows')} rows, SHA-256 `{facts['sha256']}`"),
            ('Generated', facts['when']),
            ('Command', f"`{facts['command']}`"),
            ('System', str(rep.get('system'))),
            ('Repository state', facts['repo']),
            ('Platform', facts['platform']),
            ('Input files against DATA.md', facts.get('inputs', 'not run')),
            ('Model path chosen by the noise gate', str(rep.get('path'))),
            ('Goalkeeper team correction', keeper_fact(rep)),
            ('Broadcast camera', cam),
            ('Play blocks', str(rep.get('period_source'))),
            ('Format (organisers\' rules)', facts['format']),
            ('Plausibility ranges', facts['plausibility']),
            ('Same bytes on a second run', facts['repeat']),
            ('Fresh clone of the public repository', facts['clone']),
            ('Same bytes without the clock readings', facts['noclock']),
            ('Synthetic cross-platform check', facts['platform_check']),
            ("Organisers' validate_submission.py", facts['organiser']),
            ('Public five minutes, pass/fail only', facts['public'])]
    out = ['', '', '## Appendix R. Run record of the submitted file',
           '', 'Written automatically by `tools/possession_deliver.py` on the team\'s computer when the file was generated.',
           'It lists decisions of the pipeline, not scores.', '', '| Item | Value |', '|---|---|']
    out += [f'| {k} | {v} |' for k, v in rows]
    return '\n'.join(out) + '\n'


class Chain:
    def __init__(self, a):
        self.a = a
        self.cfg = json.loads(Path(a.release_config).read_text(encoding='utf-8'))
        self.private = Path(a.private or os.environ.get('MTAH_PRIVATE_DIR') or Path.home() / 'FootballPrivate')
        self.data = Path(a.data_dir or os.environ.get('MTAH_DATA_DIR') or self.private / 'mtah2027' / 'bundle')
        self.rows = a.rows or int(self.cfg['rows'])
        self.game = self.cfg['game']
        self.stamp = time.strftime('%Y%m%d-%H%M%S')
        self.deliver = self.private / 'teslim'
        self.deliver.mkdir(parents=True, exist_ok=True)
        self.log = self.deliver / f'OZEL-log-{self.stamp}.txt'
        self.clk = self.private / 'possession-clock'
        self.lines, self.warn, self.n, self.k = [], [], 0, 0
        self.py = None
        self.facts = {}
        self.repo = REPO          # the checkout whose code is run (tests point this at a temporary checkout)

    # ---- output -------------------------------------------------------------------------------
    def say(self, text):
        print(text, flush=True)
        self.lines.append(text)
        (self.deliver / 'PAYLASILABILIR-durum.txt').write_text('\n'.join(self.lines) + '\n', encoding='utf-8')

    def step(self, name, status, warn=False):
        self.n += 1
        self.say(f'[{self.n:2d}] {name + " " + "." * max(2, 26 - len(name))} {status}')
        if warn:
            self.warn.append(name)

    def call(self, cmd, cwd=None, quiet=False):
        """Run a program with all of its output in the private log. Returns (exit code, its output)."""
        cmd = [str(c) for c in cmd]
        cwd = cwd or self.repo
        with open(self.log, 'ab') as fh:
            fh.write(f'\n===== {time.strftime("%H:%M:%S")} {" ".join(cmd)}\n'.encode('utf-8', 'replace'))
            fh.flush()
            start = fh.tell()
            t0, nxt = time.time(), 60
            try:
                proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            except OSError as e:
                return 127, type(e).__name__
            while True:
                try:
                    code = proc.wait(timeout=1)
                    break
                except subprocess.TimeoutExpired:
                    el = time.time() - t0
                    if el >= nxt and not quiet:
                        print(f'       ... calisiyor ({int(el // 60)} dk)', flush=True)
                        nxt += 60
                    if el > self.a.timeout_min * 60:
                        proc.kill(); proc.wait()
                        code = -999
                        break
        with open(self.log, 'rb') as fh:
            fh.seek(start)
            return code, fh.read().decode('utf-8', 'replace')

    # ---- environment --------------------------------------------------------------------------
    def versions(self, py):
        code = ('import json, platform, sys\n'
                'out = {"python": platform.python_version(), "platform": platform.platform()}\n'
                'for m in ("numpy", "scipy", "pandas"):\n'
                '    try: out[m] = __import__(m).__version__\n'
                '    except Exception: out[m] = None\n'
                'print(json.dumps(out))')
        try:
            r = subprocess.run([str(py), '-c', code], capture_output=True, text=True, timeout=300)
            return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            return None

    def env(self):
        pins = dict(l.strip().split('==') for l in (self.repo / 'requirements-possession.txt').read_text().splitlines()
                    if '==' in l and not l.startswith('#'))
        if self.a.python:
            py = Path(self.a.python)
        else:
            vdir = self.repo / '.venv-possession'
            py = vdir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            if not py.exists():
                if not (3, 10) <= sys.version_info[:2] <= (3, 12):
                    self.step('ORTAM', 'FAIL (Python 3.10, 3.11 veya 3.12 ile baslatin)')
                    return False
                code, text = self.call([sys.executable, '-m', 'venv', vdir])
                if code or not py.exists():
                    self.step('ORTAM', f'FAIL (sanal ortam kurulamadi: {error_class(text, code)})')
                    return False
        v = self.versions(py)
        if not self.a.python and (v is None or any(v.get(k) != pins[k] for k in pins)):
            self.call([py, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', self.repo / 'requirements-possession.txt'])
            v = self.versions(py)
        if v is None or any(v.get(k) is None for k in pins):
            self.step('ORTAM', 'FAIL (numpy/scipy/pandas kurulamadi; internet baglantisini kontrol edin)')
            return False
        self.py = py
        desc = f"{v['platform']}, Python {v['python']}, " + ', '.join(f'{k} {v[k]}' for k in pins)
        self.facts['platform'] = desc
        pinned = all(v.get(k) == pins[k] for k in pins)
        self.step('ORTAM', f'OK ({desc})' if pinned else f'UYARI: paket surumleri sabitlenenlerden farkli ({desc})', warn=not pinned)
        return True

    def repo_state(self):
        try:
            head = self.git('rev-parse', 'HEAD')
            # content differences of tracked files against HEAD (line-ending-only differences of a working copy do not count)
            n = len([l for l in self.git('diff', 'HEAD', '--name-only').splitlines() if l.strip()])
            self.facts['repo'] = f'commit {head}' + ('' if not n else f' with {n} locally modified tracked file(s)')
            self.step('DEPO', f'commit {head[:12]}, ' + ('temiz' if not n else f'{n} dosya commit edilmemis'), warn=bool(n))
        except Exception:
            self.facts['repo'] = 'not a git checkout'
            self.step('DEPO', 'ATLANDI (git bilgisi okunamadi)')

    def git(self, *args, timeout=600):
        r = subprocess.run(['git'] + [str(x) for x in args], cwd=str(self.repo), capture_output=True, text=True, timeout=timeout)
        if r.returncode:
            raise OSError('git')
        return r.stdout.strip()

    def clone_check(self):
        """Does a fresh clone of the pushed branch regenerate the delivered file? (what SUBMISSION.md asks for)"""
        name = 'TEMIZ KLON'
        self.facts['clone'] = 'not checked'
        if self.a.no_clone_check:
            return self.step(name, 'ATLANDI')
        try:
            local, branch, url = self.git('rev-parse', 'HEAD'), self.git('rev-parse', '--abbrev-ref', 'HEAD'), self.git('remote', 'get-url', 'origin')
            remote = (self.git('ls-remote', url, f'refs/heads/{branch}').split() or [''])[0]
        except Exception:
            return self.step(name, 'ATLANDI (git ya da ag erisimi yok)')
        if remote != local:
            return self.step(name, "ATLANDI (yerel commit GitHub'daki dal ile ayni degil; once GIT-YUKLE, sonra bu adim)", warn=True)
        if self.a.quick:
            return self.step(name, "ATLANDI (--quick; yerel commit GitHub'daki dal ile ayni)")
        dest = self.private / f'possession-clone-{self.stamp}'
        code, text = self.call(['git', 'clone', '--quiet', '--branch', branch, '--single-branch', url, dest], quiet=True)
        if code:
            return self.step(name, f'FAIL (git clone: {error_class(text, code)})', warn=True)
        r, err = self.attempt(self.final['step'], self.final['clock'], cwd=dest)
        if r is None:
            return self.step(name, f'FAIL ({err})', warn=True)
        same = r['sha256'] == self.final['sha256']
        self.facts['clone'] = (f'a fresh clone of commit {local} regenerates the same bytes' if same
                               else f'a fresh clone of commit {local} gives DIFFERENT bytes')
        self.step(name, f"{'AYNI' if same else 'FARKLI'} (commit {local[:12]})", warn=not same)

    def release(self):
        ok = []
        for s in self.cfg['steps']:
            code, text = self.call([self.py, '-c', f"import importlib; importlib.import_module('{s['module']}').check_release()"], quiet=True)
            if code == 0:
                ok.append(s)
            elif s is self.cfg['steps'][0]:
                detail = release_detail(text)
                self.step('SURUM', f"FAIL ({s['name']}: {error_class(text, code)}{'; ' + detail if detail else ''})")
                return False
        self.steps = [s for s in self.cfg['steps'] if s in ok]
        self.step('SURUM', f"OK ({self.cfg['release']})")
        return True

    def tests(self):
        code, text = self.call([self.py, '-m', 'unittest'] + list(self.cfg['tests']))
        if code == 0:
            return self.step('TESTLER', 'OK')
        bad = re.findall(r'^(?:FAIL|ERROR): (\S+) \((\S+?)\)', text, re.M)
        names = ', '.join(sorted({b if b.endswith('.' + a) else f'{b}.{a}' for a, b in bad})[:6]) or error_class(text, code)
        self.step('TESTLER', f'FAIL ({names})', warn=True)

    def platform_check(self):
        code, text = self.call([self.py, '-m', 'tests.test_possession_crossplatform', '--status'])
        last = (text.strip().splitlines() or [''])[-1].split()
        word = last[0] if last else ''
        if code == 0 and word == 'SAME':
            self.facts['platform_check'] = 'same bytes as recorded on Linux x86-64 (seven synthetic variants)'
            return self.step('PLATFORM', 'AYNI')
        if code == 2 and word == 'DIFFERENT':
            self.facts['platform_check'] = 'DIFFERENT from the bytes recorded on Linux x86-64 for: ' + ', '.join(last[1:])
            return self.step('PLATFORM', 'FARKLI (' + ', '.join(last[1:]) + ')', warn=True)
        if code == 3 and word == 'INPUT_DIFFERS' and last[1:] == ['keepers']:
            self.facts['platform_check'] = ('same bytes as recorded on Linux x86-64 for five synthetic variants; not conclusive for the two '
                                            'goalkeeper variants (their synthetic input differs on this computer)')
            return self.step('PLATFORM', 'BELIRSIZ (kaleci varyantlarinin sentetik girdisi bu bilgisayarda farkli; diger bes varyant AYNI)', warn=True)
        if code == 3 and word == 'INPUT_DIFFERS':
            self.facts['platform_check'] = 'not conclusive (the synthetic input differs on this computer)'
            return self.step('PLATFORM', 'BELIRSIZ (sentetik girdi bu bilgisayarda farkli)', warn=True)
        self.facts['platform_check'] = 'not run'
        self.step('PLATFORM', f'FAIL ({error_class(text, code)})', warn=True)

    # ---- data ---------------------------------------------------------------------------------
    def files(self):
        g, d = self.game, self.data
        tac = [d / 'tactical' / f'{g}_tactical_atd.xml', d / 'tactical' / f'{g}_tactical_atd.txt']
        bro = [d / 'broadcast' / f'{g}_broadcast_atd.xml', d / 'broadcast' / f'{g}_broadcast_atd.txt',
               d / 'broadcast' / f'{g}_broadcast_homography.csv']
        self.video = {c: d / c / f'{g}_{c}.mp4' for c in CAMS}
        self.has_bro = all(p.exists() for p in bro)
        self.has_video = all(p.exists() for p in self.video.values())
        if not all(p.exists() for p in tac):
            self.step('VERI', 'FAIL (taktik ATD dosyalari bulunamadi; viewer-local.cmd icindeki MTAH_DATA_DIR yolunu kontrol edin)')
            return False
        self.step('VERI', f"OK (taktik VAR, yayin {'VAR' if self.has_bro else 'YOK'}, videolar {'VAR' if self.has_video else 'YOK'})",
                  warn=not self.has_bro)
        return True

    def inputs(self):
        """Do the release's readers see what DATA.md says the files contain? (possession/inputs_check.py)"""
        code, text = self.call([self.py, '-m', 'possession.inputs_check', '--data-dir', self.data])
        bad = re.findall(r'^FAIL (\w+)', text, re.M)
        if code == 0:
            self.facts['inputs'] = ('the readers reproduce every aggregate fact that DATA.md publishes about the files and agree '
                                    'frame by frame with a second reading done the way the organisers\' starter code reads them')
            return self.step('GIRDI OKUMA', 'OK')
        if code == 2 and bad:
            self.facts['inputs'] = 'input checks that did not pass: ' + ', '.join(bad)
            return self.step('GIRDI OKUMA', 'FAIL (' + ', '.join(bad) + ')', warn=True)
        self.facts['inputs'] = 'not run'
        self.step('GIRDI OKUMA', f'FAIL ({error_class(text, code)})', warn=True)

    def clock_ready(self):
        return all((self.clk / c / n).exists() for c in CAMS for n in ('observations.jsonl', 'summary.json'))

    def sync_python(self):
        vdir = self.repo / '.venv-sync'
        py = vdir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if py.exists():
            return py
        base = [sys.executable]
        if sys.version_info[:2] != (3, 10):
            for cand in (['py', '-3.10'], ['python3.10']):
                try:
                    if subprocess.run(cand + ['-c', 'import sys'], capture_output=True, timeout=60).returncode == 0:
                        base = cand
                        break
                except Exception:
                    pass
        code, _ = self.call(base + ['-m', 'venv', vdir])
        if code or not py.exists():
            return None
        code, _ = self.call([py, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', self.repo / 'requirements-sync-lock.txt'])
        return py if code == 0 else None

    def ocr(self):
        py = Path(self.a.sync_python) if self.a.sync_python else self.sync_python()
        if py is None:
            self.step('SAAT OKUMA', 'FAIL (OCR ortami kurulamadi)', warn=True)
            return False
        for cam in CAMS:
            out = self.clk / cam
            if (out / 'summary.json').exists() and (out / 'observations.jsonl').exists():
                continue
            if out.exists():
                out.rename(self.clk / f'{cam}-yarim-{self.stamp}')     # an unfinished earlier reading is kept aside
            self.clk.mkdir(parents=True, exist_ok=True)
            print(f'       {cam} videosunun saati okunuyor (uzun surebilir)', flush=True)
            code, text = self.call([py, '-m', self.cfg.get('clock_module', 'tools.possession_clock'), '--video', self.video[cam], '--out', out])
            if code or not ((out / 'summary.json').exists() and (out / 'observations.jsonl').exists()):
                self.step('SAAT OKUMA', f'FAIL ({cam}: {error_class(text, code)})', warn=True)
                return False
        self.step('SAAT OKUMA', 'OK')
        return True

    # ---- generation ---------------------------------------------------------------------------
    def tactical_view(self):
        """A folder that shows the entry point only the tactical camera (junction, link or copy; never deleted here)."""
        view = self.private / f'possession-tactical-only-{self.stamp}'
        link, src = view / 'tactical', self.data / 'tactical'
        if link.exists():
            return view
        view.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == 'nt':
                r = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(src)], capture_output=True, timeout=60)
                if r.returncode or not link.exists():
                    raise OSError('junction')
            else:
                os.symlink(src, link, target_is_directory=True)
        except Exception:
            link.mkdir(exist_ok=True)
            for name in (f'{self.game}_tactical_atd.xml', f'{self.game}_tactical_atd.txt'):
                shutil.copy2(src / name, link / name)
        return view

    def attempt(self, s, clock, cwd=None):
        self.k += 1
        out = self.private / f'possession-run-{self.stamp}-{self.k}'
        data = self.data if s['broadcast'] else self.tactical_view()
        cmd = [self.py, '-m', s['module'], '--data-dir', data, '--out', out]
        shown = f"python -m {s['module']} --data-dir <bundle> --out <new folder>"
        if clock:
            cmd += ['--tactical-clock', self.clk / 'tactical', '--broadcast-clock', self.clk / 'broadcast']
            shown += ' --tactical-clock <clock readings> --broadcast-clock <clock readings>'
        code, text = self.call(cmd, cwd=cwd)
        csv = out / 'submission.csv'
        if code == 0 and csv.exists():
            return {'step': s, 'clock': clock, 'out': out, 'csv': csv, 'sha256': sha256(csv), 'command': shown}, None
        return None, error_class(text, code)

    def label(self, r):
        return f"{r['step']['name']}, " + ('saatli' if r['clock'] else 'saatsiz')

    def generate(self, clock):
        """Walk the ladder. Returns the first run that ends without an error and passes the format rules."""
        plan = []
        for s in self.steps:
            if s['broadcast'] and clock:
                plan.append((s, True))
            plan.append((s, False))
        errors = []
        for i, (s, c) in enumerate(plan):
            r, err = self.attempt(s, c)
            if r is None:
                errors.append(f"{s['name']}{' saatli' if c else ''}: {err}")
                continue
            if not self.format_ok(r['csv']):
                errors.append(f"{s['name']}{' saatli' if c else ''}: bicim FAIL")
                continue
            r['rung'] = i + 1
            if errors:
                self.step('URETIM', f"OK ({self.label(r)}; basamak {i + 1}; ust basamak hatalari: {'; '.join(errors)})", warn=True)
            else:
                self.step('URETIM', f'OK ({self.label(r)})')
            return r
        self.step('URETIM', 'FAIL (' + '; '.join(errors) + ')')
        return None

    def format_ok(self, csv):
        code, _ = self.call([self.py, '-m', 'possession.validate', csv, '--rows', self.rows], quiet=True)
        return code == 0 and plain_csv_check(csv, self.rows)

    def plausibility(self, csv):
        code, text = self.call([self.py, '-m', 'possession.plausibility', csv], quiet=True)
        bad = re.findall(r'^FAIL (\w+)', text, re.M)
        if code == 0:
            self.facts['plausibility'] = 'all checks pass'
            return self.step('MAKULLUK', 'OK')
        if code == 2 and bad:
            self.facts['plausibility'] = 'outside the expected range: ' + ', '.join(bad)
            return self.step('MAKULLUK', 'FAIL (' + ', '.join(bad) + ')', warn=True)
        self.facts['plausibility'] = 'not run'
        self.step('MAKULLUK', f'FAIL ({error_class(text, code)})', warn=True)

    def hand_over(self, r, name='TESLIM'):
        target = self.deliver / f'{self.team}.csv'
        note = ''
        if target.exists() and not hasattr(self, 'final'):          # a file of an earlier chain
            if sha256(target) == r['sha256']:
                note = '; onceki teslim dosyasi ile AYNI'
            else:
                target.replace(self.deliver / f'{self.team}.csv.onceki-{self.stamp}')
                note = '; onceki teslim dosyasindan FARKLI (eskisi .onceki olarak saklandi)'
        tmp = self.deliver / f'{self.team}.csv.tmp'
        shutil.copyfile(r['csv'], tmp)
        tmp.replace(target)
        self.final = dict(r, target=target)
        self.step(name, f'OK ({self.label(r)}{note})')

    # ---- organisers' tools --------------------------------------------------------------------
    def organiser_repo(self):
        cands = [self.a.organiser_repo, os.environ.get('MTAH_ORG_REPO'), self.repo.parent / 'official-20261020',
                 self.repo.parent / 'upstream', self.repo.parent / 'more-than-a-hack-2027', self.private / 'more-than-a-hack-2027']
        for c in cands:
            if c and (Path(c) / 'evaluation' / 'validate_submission.py').exists():
                return Path(c)
        return None

    def organiser_checks(self, csv):
        org = self.organiser_repo()
        self.facts['organiser'] = self.facts['public'] = 'not run'
        if org is None:
            self.step('ORGANIZATOR DOGRULAYICI', 'ATLANDI (organizator deposu bulunamadi)')
            self.step('ACIK PENCERE', 'ATLANDI')
            return
        code, text = self.call([self.py, org / 'evaluation' / 'validate_submission.py', csv, '--rows', self.rows], cwd=org, quiet=True)
        self.facts['organiser'] = 'OK' if code == 0 else 'FAIL'
        self.step('ORGANIZATOR DOGRULAYICI', 'OK' if code == 0 else 'FAIL', warn=bool(code))
        gt = org / 'evaluation' / 'gt' / f'{self.game}_possession_gt_public.csv'
        if self.a.no_public_check or not gt.exists():
            return self.step('ACIK PENCERE', 'ATLANDI')
        code, text = self.call([self.py, '-m', 'possession.public_check', csv, gt], quiet=True)
        bad = re.findall(r'^FAIL (\w+)', text, re.M)
        if code == 0:
            self.facts['public'] = 'pass'
            return self.step('ACIK PENCERE', 'OK')
        if code == 2 and bad:
            self.facts['public'] = 'FAIL: ' + ', '.join(bad)
            return self.step('ACIK PENCERE', 'FAIL (' + ', '.join(bad) + ')', warn=True)
        self.step('ACIK PENCERE', f'FAIL ({error_class(text, code)})', warn=True)

    # ---- documents ----------------------------------------------------------------------------
    def documents(self):
        r = self.final
        rep = json.loads((r['out'] / 'run.json').read_text(encoding='utf-8'))
        self.facts.update(file=f'{self.team}.csv', sha256=r['sha256'], command=r['command'], format='OK',
                          when=time.strftime('%Y-%m-%d %H:%M (UTC%z)'))
        record = {'delivered': str(r['target']), 'sha256': r['sha256'], 'run_folder': str(r['out']), 'step': r['step']['name'],
                  'clock': r['clock'], 'rung': r.get('rung'), 'facts': self.facts, 'warnings': self.warn, 'log': str(self.log)}
        (self.deliver / 'OZEL-kayit.json').write_text(json.dumps(record, indent=1), encoding='utf-8')
        doc = self.repo / self.cfg.get('document', 'TECHNICAL_DOCUMENT.md')
        if doc.exists():
            (self.deliver / f'{self.team}.md').write_text(doc.read_text(encoding='utf-8').rstrip('\n') + run_record(rep, self.facts),
                                                          encoding='utf-8', newline='\n')
            self.step('BELGE', f'OK ({self.team}.md = teknik belge + calisma kaydi)')
        else:
            self.step('BELGE', 'ATLANDI (teknik belge bulunamadi)', warn=True)

    # ---- the chain ----------------------------------------------------------------------------
    def team_name(self):
        f = self.deliver / 'takim-adi.txt'
        name = self.a.team or (f.read_text(encoding='utf-8').strip() if f.exists() else '')
        if not name and sys.stdin is not None and sys.stdin.isatty():
            name = input('Takim adi (Google Form ile ayni yazim): ').strip()
        name = re.sub(r'[\\/:*?"<>|\s]+', '_', name).strip('._')
        self.named = bool(name)
        self.team = name or 'TAKIM-ADI'
        if name:
            f.write_text(name, encoding='utf-8')

    def run(self):
        self.team_name()
        self.say(f'POSSESSION TESLIM ZINCIRI  {time.strftime("%Y-%m-%d %H:%M")}  ({self.cfg["release"]})')
        self.say('Bu satirlar paylasilabilir. Log, run.json, OZEL-kayit.json, CSV ve belge eki paylasilmaz.')
        if not self.env():
            return self.end(False)
        self.repo_state()
        if not self.release():
            return self.end(False)
        if not self.a.no_tests:
            self.tests()
            self.platform_check()
        else:
            self.facts['platform_check'] = 'not run'
        if not self.files():
            return self.end(False)
        self.inputs()
        had_clock = self.clock_ready()
        first = self.generate(clock=had_clock)
        if first is None:
            return self.end(False)
        self.step('BICIM', 'OK')
        self.plausibility(first['csv'])
        will_read = first['step']['broadcast'] and self.has_bro and self.has_video and not had_clock and not self.a.no_ocr
        self.hand_over(first, 'ON TESLIM' if will_read else 'TESLIM')
        self.facts['noclock'] = self.facts['repeat'] = 'not checked'
        other = None
        if not first['step']['broadcast'] or not self.has_bro:
            self.step('SAAT', 'ATLANDI (yayin kamerasi kullanilmiyor)')
        elif had_clock:
            self.step('SAAT', 'VAR (onceki okuma kullanildi)' if first['clock'] else 'VAR (saatli uretim hata verdi; saatsiz uretim kullanildi)',
                      warn=not first['clock'])
            if first['clock'] and not self.a.quick:
                other, err = self.attempt(first['step'], False)
                if other is None:
                    self.step('SAATSIZ URETIM', f'FAIL ({err})', warn=True)
        elif self.a.no_ocr or not self.has_video:
            self.step('SAAT', 'ATLANDI (' + ('--no-ocr' if self.a.no_ocr else 'video dosyalari bulunamadi') + ')', warn=True)
        elif self.ocr():
            withclock, err = self.attempt(first['step'], True)
            if withclock is None or not self.format_ok(withclock['csv']):
                self.step('SAATLI URETIM', f"FAIL ({err or 'bicim'}); teslim dosyasi saatsiz uretim olarak kaldi", warn=True)
            else:
                withclock['rung'] = first.get('rung')
                self.step('SAATLI URETIM', f'OK ({self.label(withclock)})')
                other = first
                self.plausibility(withclock['csv'])
                self.hand_over(withclock)
        if other is not None:
            same = other['sha256'] == self.final['sha256']
            self.facts['noclock'] = 'yes' if same else 'NO (the clock readings change the file)'
            self.step('SAATSIZ KARSILASTIRMA', 'AYNI' if same else 'FARKLI', warn=not same)
        if not self.a.quick:
            again, err = self.attempt(self.final['step'], self.final['clock'])
            if again is None:
                self.step('TEKRAR URETIM', f'FAIL ({err})', warn=True)
            else:
                same = again['sha256'] == self.final['sha256']
                self.facts['repeat'] = 'yes' if same else 'NO'
                self.step('TEKRAR URETIM', 'AYNI' if same else 'FARKLI', warn=not same)
        self.clone_check()
        self.organiser_checks(self.final['target'])
        self.documents()
        return self.end(True)

    def end(self, ready):
        if not ready:
            self.say('SONUC: TESLIM HAZIR DEGIL. Yukaridaki FAIL satirini (yalnizca bu satirlari) paylasin.')
            return 1
        extra = '' if self.named else ' (takim adi verilmedi: dosyayi <takim_adi>.csv olarak yeniden adlandirin)'
        if self.warn:
            self.say(f'SONUC: TESLIM DOSYASI HAZIR, UYARILAR VAR ({", ".join(dict.fromkeys(self.warn))}){extra}')
        else:
            self.say('SONUC: TESLIM HAZIR' + extra)
        self.say(f'Dosyalar: {self.deliver}')
        return 2 if self.warn else 0


def parse(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--team', help='team name as written in the Google Form (file name of the CSV and the document)')
    p.add_argument('--data-dir', help='bundle root with tactical/ and broadcast/ (default: MTAH_DATA_DIR or <private>/mtah2027/bundle)')
    p.add_argument('--private', help='private folder outside the repository (default: MTAH_PRIVATE_DIR or ~/FootballPrivate)')
    p.add_argument('--python', help='interpreter with the pinned packages (default: .venv-possession, created when missing)')
    p.add_argument('--sync-python', help='interpreter of the OCR environment (default: .venv-sync, created when missing)')
    p.add_argument('--rows', type=int, help='expected number of rows (default: possession-release.json)')
    p.add_argument('--release-config', default=str(CONFIG))
    p.add_argument('--organiser-repo', help="clone of the organisers' repository (validator and public five minutes)")
    p.add_argument('--no-ocr', action='store_true', help='do not read the video clocks')
    p.add_argument('--no-tests', action='store_true', help='skip the synthetic tests and the cross-platform check')
    p.add_argument('--no-public-check', action='store_true')
    p.add_argument('--no-clone-check', action='store_true', help='do not regenerate the file from a fresh clone of the pushed branch')
    p.add_argument('--quick', action='store_true', help='skip the repeat run and the run without the clock')
    p.add_argument('--timeout-min', type=float, default=240.0, help='limit for a single program')
    return p.parse_args(argv)


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors='replace')
    except Exception:
        pass
    return Chain(parse(argv)).run()


if __name__ == '__main__':
    sys.exit(main())
