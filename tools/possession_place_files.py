"""Put the match files into the bundle folder that the delivery chain reads (step 1 of TESLIM-TEK-TIK.cmd).

    python -m tools.possession_place_files [--data-dir DIR] [--search DIR ...] [--only] [--status-file FILE] [--dry-run]

Looks for the nine files the organisers ship (DATA.md: tactical/ and broadcast/, names as they arrive, also with a
" (1)" that a browser adds to a second download) in the usual folders of this computer (Downloads, Desktop, Documents,
Videos, OneDrive, FootballPrivate, the top levels of other drives) and in the folders given with --search, also inside
.zip archives, and copies every missing one into the bundle folder (default as tools/possession_deliver.py:
MTAH_DATA_DIR, else MTAH_PRIVATE_DIR/mtah2027/bundle, else ~/FootballPrivate/mtah2027/bundle).

A file that is already in the bundle is never replaced (an empty one is). When several copies are found the largest is
taken. Only names, folders and status words are printed and written to --status-file; the files are opened only to copy
them. Runs on the team's computer only; standard library only.

Exit code: 0 all nine files are in the bundle; 2 all except one or both videos (the chain then skips the clock reading);
1 a tracking, homography or Smart Tagging file is still missing or could not be copied.
"""
import argparse
import os
import re
import shutil
import string
import sys
import zipfile
from pathlib import Path

GAME = 'BAR-ATH'
FILES = [('tactical', 'tactical_atd.xml'), ('tactical', 'tactical_atd.txt'), ('tactical', 'tactical_homography.csv'),
         ('tactical', 'tactical_smart_tagging.xml'), ('tactical', 'tactical.mp4'),
         ('broadcast', 'broadcast_atd.xml'), ('broadcast', 'broadcast_atd.txt'), ('broadcast', 'broadcast_homography.csv'),
         ('broadcast', 'broadcast.mp4')]
VIDEOS = {'tactical.mp4', 'broadcast.mp4'}
SKIP = {'.git', 'node_modules', '__pycache__', 'site-packages', 'appdata', '$recycle.bin', 'windows', 'program files',
        'program files (x86)', 'programdata', 'system volume information'}
OTHER_ARCHIVES = ('.7z', '.rar', '.tar', '.tgz', '.tar.gz')
HINTS = ('bar-ath', 'bar_ath', 'barath', 'mtah', 'hack', 'metrica', 'barcelona', 'athletic', 'bundle')   # archive names reported
SPARE = 200 * 1024 * 1024          # free space kept on the target drive beyond the file itself


def default_data_dir():
    if os.environ.get('MTAH_DATA_DIR'):
        return Path(os.environ['MTAH_DATA_DIR'])
    private = Path(os.environ.get('MTAH_PRIVATE_DIR') or Path.home() / 'FootballPrivate')
    return private / 'mtah2027' / 'bundle'


def pattern(name):
    stem, ext = os.path.splitext(name)
    return re.compile(re.escape(stem) + r'(?: \(\d+\))?' + re.escape(ext), re.I)


def search_roots(extra, only):
    roots = [(Path(x), 99) for x in extra]
    if not only:
        home = Path.home()
        roots += [(home / n, 99) for n in ('Downloads', 'Desktop', 'Documents', 'Videos', 'FootballPrivate')]
        roots += [(p, 99) for p in sorted(home.glob('OneDrive*')) if p.is_dir()]
        if os.name == 'nt':
            sysdrive = os.environ.get('SystemDrive', 'C:').upper()
            roots += [(Path(f'{d}:\\'), 3) for d in string.ascii_uppercase if f'{d}:' != sysdrive and os.path.isdir(f'{d}:\\')]
    out = []
    for p, depth in roots:
        try:
            p = p.resolve()
        except OSError:
            continue
        if p.is_dir() and not any(_inside(p, q) for q, _ in out):
            out = [(q, dq) for q, dq in out if not _inside(q, p)] + [(p, depth)]
    return out


def _inside(p, q):
    try:
        p.relative_to(q)
        return True
    except ValueError:
        return False


def _norm(p):
    return os.path.normcase(os.path.abspath(str(p)))


def scan(roots, exclude):
    """loose files whose name matches, .zip archives, other archives with a name that looks related"""
    pats = {(cam, suf): pattern(f'{GAME}_{suf}') for cam, suf in FILES}
    loose = {k: [] for k in pats}
    zips, others = [], []
    ex = [_norm(e) for e in exclude]
    for root, maxdepth in roots:
        base = len(root.parts)
        for d, dirs, files in os.walk(root, onerror=lambda e: None):
            dp = Path(d)
            keep = []
            for x in dirs:
                n = _norm(dp / x)
                if x.lower() in SKIP or x.lower().startswith(('.venv', 'venv')) or any(n == e or n.startswith(e + os.sep) for e in ex):
                    continue
                keep.append(x)
            dirs[:] = keep
            if len(dp.parts) - base >= maxdepth:
                dirs[:] = []
            for f in files:
                low = f.lower()
                for k, pat in pats.items():
                    if pat.fullmatch(f):
                        loose[k].append(dp / f)
                if low.endswith('.zip'):
                    zips.append(dp / f)
                elif low.endswith(OTHER_ARCHIVES) and any(h in low for h in HINTS):
                    others.append(dp / f)
    return loose, zips, others


def candidates(key, loose, zips):
    """[(size, is_zip, source, member)] for one wanted file; loose files before zip members of the same size"""
    pat = pattern(f'{GAME}_{key[1]}')
    out = []
    for p in loose[key]:
        try:
            out.append((p.stat().st_size, 0, p, None))
        except OSError:
            pass
    for z in zips:
        try:
            with zipfile.ZipFile(z) as zf:
                for info in zf.infolist():
                    if not info.is_dir() and pat.fullmatch(info.filename.replace('\\', '/').rsplit('/', 1)[-1]):
                        out.append((info.file_size, 1, z, info.filename))
        except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError):
            pass
    out = [c for c in out if c[0] > 0]
    out.sort(key=lambda c: (-c[0], c[1], str(c[2])))
    return out


class Problem(Exception):
    pass


def place(size, source, member, dst, say_progress):
    dst.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(dst.parent).free
    if free < size + SPARE:
        if member is None:
            try:
                os.link(source, dst)           # same drive: a second name for the same file, no extra space
                return 'baglanti'
            except OSError:
                pass
        raise Problem('YER YOK (diskte yeterli bos alan yok)')
    part = dst.with_name(dst.name + '.part')
    done, step, nxt = 0, max(size // 10, 1), max(size // 10, 1)
    big = size > 200 * 1024 * 1024
    try:
        zf = zipfile.ZipFile(source) if member is not None else None
        try:
            src = zf.open(member) if zf else open(source, 'rb')
            with src as fi, open(part, 'wb') as fo:
                while True:
                    block = fi.read(1 << 22)
                    if not block:
                        break
                    fo.write(block)
                    done += len(block)
                    if big and done >= nxt:
                        say_progress(f' %{min(100, round(100 * done / size))}')
                        nxt += step
        finally:
            if zf:
                zf.close()
        if part.stat().st_size != size:
            raise Problem('HATA (kopya eksik kaldi)')
        os.replace(part, dst)
    except Problem:
        part.unlink(missing_ok=True)
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError) as e:
        part.unlink(missing_ok=True)
        raise Problem(f'HATA (kopyalanamadi: {type(e).__name__})')
    return 'kopya'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--data-dir', help='bundle root with tactical/ and broadcast/ (default as tools/possession_deliver.py)')
    p.add_argument('--search', action='append', default=[], help='an extra folder to look in (may be repeated)')
    p.add_argument('--only', action='store_true', help='look only in the --search folders')
    p.add_argument('--status-file', help='also write the status lines to this file')
    p.add_argument('--dry-run', action='store_true', help='say what would be copied, copy nothing')
    a = p.parse_args(argv)
    data = Path(a.data_dir) if a.data_dir else default_data_dir()
    lines = []
    sep = '\\' if os.name == 'nt' else '/'

    def say(text):
        print(text, flush=True)
        lines.append(text)
        if a.status_file:
            try:
                Path(a.status_file).parent.mkdir(parents=True, exist_ok=True)
                Path(a.status_file).write_text('\n'.join(lines) + '\n', encoding='utf-8')
            except OSError:
                pass

    say(f'DOSYA YERLESTIRME  hedef: {data}')
    todo = []
    for cam, suf in FILES:
        t = data / cam / f'{GAME}_{suf}'
        try:
            present = t.is_file() and t.stat().st_size > 0
        except OSError:
            present = False
        if not present:
            todo.append((cam, suf))
    loose, zips, others = ({}, [], [])
    if todo:
        say('Dosyalar araniyor (birkac dakika surebilir)...')
        try:
            exclude = [data.resolve()]
        except OSError:
            exclude = []
        loose, zips, others = scan(search_roots(a.search, a.only), exclude)
    missing, failed = [], []
    for i, (cam, suf) in enumerate(FILES, 1):
        name = f'{cam}{sep}{GAME}_{suf}'
        head = f'[{i}] {name} ' + '.' * max(2, 44 - len(name))
        if (cam, suf) not in todo:
            say(f'{head} ZATEN VAR')
            continue
        cands = candidates((cam, suf), loose, zips)
        if not cands:
            say(f'{head} BULUNAMADI')
            missing.append(suf)
            continue
        size, _, source, member = cands[0]
        where = f'{source} icinden' if member is not None else str(source.parent)
        note = ' (birden fazla kopya vardi; en buyugu alindi)' if len({c[0] for c in cands}) > 1 else ''
        if a.dry_run:
            say(f'{head} KOPYALANACAK (kaynak: {where}){note}')
            continue
        print(f'{head} kopyalaniyor...', end='', flush=True)
        try:
            how = place(size, source, member, data / cam / f'{GAME}_{suf}', lambda s: print(s, end='', flush=True))
            print('', flush=True)
            say(f'{head} YERLESTIRILDI ({how}; kaynak: {where}){note}')
        except Problem as e:
            print('', flush=True)
            say(f'{head} {e}')
            failed.append(suf)
    required = [s for s in missing + failed if s not in VIDEOS]
    if missing and others:
        say('Acilmamis arsiv(ler) bulundu; icindeki dosyalari bu program acamiyor, elle acip tekrar calistirin:')
        for o in others[:10]:
            say(f'    {o}')
    if a.dry_run:
        say('SONUC: DENEME (hicbir sey kopyalanmadi)')
        return 0
    if required:
        say('SONUC: EKSIK (' + ', '.join(f'{GAME}_{s}' for s in required) + '). Organizatorun indirme baglantisindaki '
            'paketi indirin (Downloads klasorune) ve bu programi tekrar calistirin.')
        return 1
    if missing or failed:
        say('SONUC: VIDEO EKSIK (' + ', '.join(f'{GAME}_{s}' for s in missing + failed) + '). Teslim zinciri yine calisir; '
            'yalnizca videonun saatini okuma adimini atlar.')
        return 2
    say('SONUC: TAMAM. Dokuz dosyanin hepsi paket klasorunde.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
