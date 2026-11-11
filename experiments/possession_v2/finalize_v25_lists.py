"""After finalize_v25.py: launchers' file lists, setup tests, README / CLAUDE.md / AGENTS.md text."""
import json
from pathlib import Path
S = Path('/home/claude/sc')
use_clock = json.loads((S / 'possession-v25b-results.json').read_text())['selected']


def edit(path, old, new, raw=False):
    p = S / path
    t = p.read_bytes().decode('utf-8')
    assert t.count(old) == 1, (path, old[:70])
    p.write_bytes(t.replace(old, new).encode('utf-8'))


# GIT-YUKLE-V2.cmd: add the new files and update the message
extra = ('possession-v25-plan.json possession-v25-results.json possession-v25b-plan.json possession-v25b-results.json '
         'possession-v26-plan.json possession-v26-results.json possession-v25-release.json tests/test_possession_v25.py '
         'tests/test_possession_v26.py SAHIPLIK-V25-URET.cmd ' + ('tools/possession_clock.py SAAT-OKU.cmd ' if use_clock else ''))
edit('GIT-YUKLE-V2.cmd', 'possession-v24-plan.json possession-v24-results.json ', 'possession-v24-plan.json possession-v24-results.json ' + extra)
edit('GIT-YUKLE-V2.cmd', 'rem Commits ONLY the possession source, model bundles and documents (v2.4 release), then pushes the working branch.',
     'rem Commits ONLY the possession source, model bundles and documents (v2.5 release), then pushes the working branch.')
edit('GIT-YUKLE-V2.cmd', '  echo Add possession v2.4: noise-gated v2.1 / v2.3 H/A/D system\r\n',
     '  echo Add possession v2.5: noise-gated H/A/D system with gated broadcast ball fill\r\n')
edit('GIT-YUKLE-V2.cmd', 'wider noise^) when the noise exceeds 0.30 m. Frozen bundles models/possession-v2.npz and\r\n',
     'wider noise^) when the noise exceeds 0.30 m; v2.5 fills missing tactical balls with the aligned\r\n'
     '  echo broadcast ball only when both cameras agree within 0.50 m' + (' ^(alignment anchored on the match clock^)' if use_clock else '') + '. Frozen bundles models/possession-v2.npz and\r\n')
edit('GIT-YUKLE-V2.cmd', '  echo and v2.3 alone; plans, results and code are included. Plan clock times were corrected\r\n',
     '  echo v2.3 alone and a learned switch hazard ^(v2.6^); plans, results and code are included. Plan clock times were corrected\r\n')
# setup: run the new test modules too
edit('SAHIPLIK-V2-KURULUM.cmd', 'tests.test_possession_v2 tests.test_possession_v23 tests.test_possession_v24 -v',
     'tests.test_possession_v2 tests.test_possession_v23 tests.test_possession_v24 tests.test_possession_v25 tests.test_possession_v26 -v')
edit('SAHIPLIK-V2-KURULUM.cmd', 'echo KURULUM VE TESTLER TAMAM. Simdi SAHIPLIK-V24-URET.cmd calistirilabilir.',
     'echo KURULUM VE TESTLER TAMAM. Simdi ' + ('SAAT-OKU.cmd, ardindan ' if use_clock else '') + 'SAHIPLIK-V25-URET.cmd calistirilabilir.')
# README
edit('README.md', '## Possession v2.4 (submission candidate)', '## Possession v2.5 (submission candidate)')
edit('README.md', '`possession/` (version `possession-v2.4`) is the H/A/D system intended for the Initial Challenge',
     '`possession/` (version `possession-v2.5`) is the H/A/D system intended for the Initial Challenge')
edit('README.md', '''(v2.3 path), otherwise v2.1 unchanged. On corrupted external validation copies v2.1 reaches''',
     '''(v2.3 path), otherwise v2.1 unchanged. v2.5 also aligns the broadcast tracking to the tactical
frames''' + (''' (anchored on the match clock read by OCR in both videos)''' if use_clock else '') + ''' and fills missing tactical balls with
the broadcast ball when both cameras agree within 0.50 m. On corrupted external validation copies v2.1 reaches''')
edit('README.md', '''providers' labels, not competition scores). See [TECHNICAL_DOCUMENT_V2.md](TECHNICAL_DOCUMENT_V2.md)''',
     '''providers' labels, not competition scores); with simulated accurate broadcast streams v2.5 adds
+0.024 and otherwise changes nothing. See [TECHNICAL_DOCUMENT_V2.md](TECHNICAL_DOCUMENT_V2.md)''')
edit('README.md', '''guide), the registered plans `possession-v2-plan.json` ... `possession-v24-plan.json` and their''',
     '''guide), the registered plans `possession-v2-plan.json` ... `possession-v26-plan.json` and their''')
edit('README.md', '''python -m possession.run24 --data-dir <bundle root containing tactical/> --out <new folder>''',
     ('''# optional, separate OCR environment (requirements-sync-lock.txt):
python -m tools.possession_clock --video <bundle>/tactical/BAR-ATH_tactical.mp4 --out <clock>/tactical
python -m tools.possession_clock --video <bundle>/broadcast/BAR-ATH_broadcast.mp4 --out <clock>/broadcast
''' if use_clock else '') + '''python -m possession.run25 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder>''' +
     (''' --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast''' if use_clock else ''))
edit('README.md', '''On Windows, `SAHIPLIK-V2-KURULUM.cmd` sets up the environment and runs the tests, and
`SAHIPLIK-V24-URET.cmd` generates the file using `MTAH_DATA_DIR`.''',
     '''On Windows, `SAHIPLIK-V2-KURULUM.cmd` sets up the environment and runs the tests, ''' +
     ('''`SAAT-OKU.cmd` reads the clocks once, ''' if use_clock else '') + '''and
`SAHIPLIK-V25-URET.cmd` generates the file using `MTAH_DATA_DIR`.''')
# AGENTS.md
edit('AGENTS.md', '''- Possession (`possession/`, version `possession-v2.4` = frozen v2.1 core + noise gate + v2.3 path,
  entry point `python -m possession.run24`) is the current submission candidate.''',
     '''- Possession (`possession/`, version `possession-v2.5` = frozen v2.1 core + noise gate + v2.3 path +
  gated broadcast ball fill''' + (''' with clock-anchored alignment''' if use_clock else '') + ''', entry point `python -m possession.run25`, release
  manifest `possession-v25-release.json`) is the current submission candidate.''')
edit('AGENTS.md', '''  above: external-only training/selection (`possession-v2-plan.json` ... `possession-v24-plan.json`),''',
     '''  above: external-only training/selection (`possession-v2-plan.json` ... `possession-v26-plan.json`),''')
print('lists and readme updated; use_clock =', use_clock)
