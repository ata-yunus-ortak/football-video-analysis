"""Status snapshot (CLAUDE.md) and launchers for possession-v2.16: the upload launcher no longer opens git's pager
(the team lead's window stopped at "(END)" on 15 Nov), asks for no key when started from TESLIM-TEK-TIK.cmd, and its commit
message describes this commit. Run once, after docs_v216_more.py. Usage: docs_v216_status.py REPO_DIR"""
import json, sys
from pathlib import Path
REPO = Path(sys.argv[1])
R = json.loads((REPO / 'possession-v216-results.json').read_text())
H = json.loads((REPO / 'possession-v216-rehearsal.json').read_text())
REL = json.loads((REPO / 'possession-v216-release.json').read_text())
PLAN = json.loads((REPO / 'possession-v216-plan.json').read_text())
K = json.loads((REPO / 'possession-k016-camera-priority.json').read_text())
S, G = R['summary'], R['gates']
T = K['spell_f1_difference_to_the_release_by_stream_regime']
g = S['good']
en = lambda x: f'{x:+.4f}'
new, old, dif = H['delivered_file_against_the_bundle_labels'], H['for_comparison_the_v2.15_chain_file'], H['against_the_v2.15_file']


def edit(name, pairs, binary=False):
    p = REPO / name
    s = p.read_bytes().decode('ascii') if binary else p.read_text(encoding='utf-8')
    for a, b, *n in pairs:
        n = n[0] if n else 1
        assert s.count(a) == n, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    if binary:
        assert s.count('\n') == s.count('\r\n')
        p.write_bytes(s.encode('ascii'))
    else:
        p.write_text(s, encoding='utf-8')
    return s


# ------------------------------------------------------------------ CLAUDE.md
SNAP = f'''## Status snapshot (15 Nov 2026, evening — verify before relying on it)

- **Submission system: `possession-v2.16`** (`python -m possession.run216`, manifest `possession-v216-release.json`,
  frozen {REL['frozen_at'][:16].replace('T', ' ')}) = v2.15 + one step (`possession/playerfill.py`): when the broadcast files are present and
  the accuracy gate of the ball fill is open, a registered broadcast player with no tactical player of either team
  within 1.5 m is added to the tracking the models see (one extra slot per broadcast track, team of that track); the
  goalkeeper check then runs on tactical + added players. Tactical positions are never moved. Without broadcast files,
  with the gate closed or with `add_players=False` (test switch) `run216` writes the bytes of `run215` (tested).
  `run216.py` is derived from `run215.py` by exact text replacements (`experiments/possession_v2/v218/port/make_run216.py`).
  Ladder in `possession-release.json`: v2.16 -> v2.15 -> v2.11k -> v2.11g -> v2.9g -> v2.5b -> v2.5b tactical only.
  Do not edit `playerfill.py` or `run216.py` (hash-frozen); a change needs a new version and a new plan.
- **Where it came from (K016, exploration):** the team lead asked whether the broadcast camera should take priority where
  it agrees with the tactical one. On development copies with a simulated second camera, taking the ball or the players
  from the broadcast stream where both agree changed the score by -0.005 to +0.002, even with a stream five times as
  precise (`possession-k016-camera-priority.json`); without the second camera the score is 0.036-0.043 lower. Adding the
  players the tactical copy has lost was the one variant with a gain ({en(T['sharp']['F']['mean'])} / {en(T['good']['F']['mean'])} on four copies).
- **Validation (K017):** `possession-v216-plan.json` registered {PLAN['registered_at'][11:19]} before the first validation row; 16 new
  copies with a simulated second camera, both arms on the same copy and stream: {g['v2_15_mean']:.4f} -> {g['candidate_mean']:.4f} ({en(g['mean_diff'])};
  DFL {en(g['dfl'])}, Metrica {en(g['metrica'])}; {g['better']} better, {g['worse']} worse, worst {en(g['min'])}); medium stream {en(S['medium']['mean_diff'])}; stream that loses and
  invents players {en(S['good_degraded']['mean_diff'])} (one copy {en(S['good_degraded']['min'])}); copies of the other simulator {en(S['sim2_good']['mean_diff'])} (3 of 4 lower). All seven
  gates (the thresholds of the earlier plans) passed; G7 by {G['G7 other simulator']['value']:.4f}. **Say these margins whenever the result is quoted.**
  The plan says no further candidate that takes players from the broadcast tracking is registered before the deadline.
- **Conditions of the registered decision rule** (otherwise v2.15 stays), to be met by 16 Nov 23:59 Istanbul: runs under
  Python 3.10 / numpy 1.26.4 (done); eleven synthetic bundles byte-identical under 3.10 / 1.26.4 and 3.13 / 2.5.3 (done; two
  new variants with added players, one per model path); full test suite (done: 467 tests, 15 skipped under 3.10 with the
  pins; 467, 4 skipped under 3.13); full-size chain rehearsal (done: `possession-v216-rehearsal.json`, all steps OK in
  {H['seconds']} s, peak {H['peak_child_rss_gb']} GB; {H['added_players_in_this_synthetic_run']['player_positions_added']:,} positions added on that synthetic bundle; spellF1 {new['graded windows']['spell_f1_mean']:.4f} against {old['graded windows']['spell_f1_mean']:.4f} for
  the v2.15 chain file; a wiring check, not an accuracy claim); documents (done). **Still open: the delivery chain must
  run OK on the team's computer** with `URETIM` and `TESLIM` naming `possession-v2.16`; if they name a lower step, that
  step is what is delivered and the documents must be brought in line before the Form is filled.
- **Limits to keep in every description:** the second camera is simulated and its players come from clean positions;
  the provided broadcast tracking was not examined (a referee it carries under a team and the tactical tracking lacks
  would be added as a player); the step was picked among seven variants on four development copies on a day on which
  three other ideas were examined on the same matches.
- **Delivery chain:** `PLATFORM` compares eleven synthetic variants; Appendix R has a "Players added from the broadcast
  camera" row (category only). `GIT-YUKLE-V2.cmd` now calls git with `--no-pager` (on 15 Nov the team lead's window
  stopped for hours at the pager's "(END)" until he pressed q) and asks for no key when `TESLIM-TEK-TIK.cmd` starts it
  (`POSSESSION_NO_PAUSE`); the data-type guard is unchanged.
- **The team lead's runs on 15 Nov:** `TESLIM-TEK-TIK.cmd` started 11:34 (all nine files placed), the upload went through
  at 16:28 (commit 668fc04: v2.15, records K007-K014), after which the chain ran with v2.15 as the first step. Read
  `Desktop\\logs\\PAYLASILABILIR-durum.txt` for its result. The v2.16 files and the K015-K017 records are copied to the PC
  only when no launcher is running there (never overwrite a `.cmd` file that may be running), and reach GitHub with
  the next run of `TESLIM-TEK-TIK.cmd` or `GIT-YUKLE-V2.cmd`.
- **Asked and refused on 15 Nov 14:06:** integrating a ready-made video model and judging it by eye on the provided
  video. Checking output against the provided video is forbidden by the organisers' clarification of 3 Nov; ready-made
  "possession from video" tools use the nearest-player rule on weaker detections than the provided tracking, and
  action-spotting models could not be measured together with our system on any external match in the time left.
- Everything in the snapshot below still holds except the name of the release and what is listed here.

'''
if '## Status snapshot (15 Nov 2026, evening' not in (REPO / 'CLAUDE.md').read_text(encoding='utf-8'):      # a first run stopped after this edit
  edit('CLAUDE.md', [
    ('## Status snapshot (15 Nov 2026, early morning — verify before relying on it)\n',
     SNAP + '## Earlier status (15 Nov 2026, early morning to afternoon)\n'),
    ('''  `possession-v215-release.json` adds `run215.py`, `pooling.py`, `tcn/*.py` and the network weights. Lower ladder steps''',
     '''  `possession-v215-release.json` adds `run215.py`, `pooling.py`, `tcn/*.py` and the network weights;
  `possession-v216-release.json` adds `playerfill.py` and `run216.py`. Lower ladder steps'''),
    ('python -m possession.run215 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local',
     'python -m possession.run216 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local'),
])

# ------------------------------------------------------------------ GIT-YUKLE-V2.cmd
p = REPO / 'GIT-YUKLE-V2.cmd'
s = p.read_bytes().decode('ascii')
assert s.count('\n') == s.count('\r\n')
lines = s.split('\r\n')
a = next(i for i, l in enumerate(lines) if l.startswith('> "%POSSESSION_MSG1%" echo '))
b = next(i for i, l in enumerate(lines) if l.startswith('>> "%POSSESSION_MSG1%" echo Co-Authored-By'))
msg = [
    'Release possession-v2.16: lost players added from the broadcast tracking; records K015-K018',
    '',
    'K017: the submission system is now possession-v2.16 = v2.15 plus one step, possession/playerfill.py. When the',
    'broadcast files are present and the accuracy gate of the ball fill is open, a registered broadcast player with',
    'no tactical player of either team within 1.5 m is added to the tracking the models see. Tactical positions',
    'are never moved; without broadcast files or with the gate closed the output is that of v2.15.',
    f'Registered before any validation row, possession-v216-plan.json: on 16 new copies with a simulated second',
    f'camera spellF1 {g["mean_diff"]:+.4f}, better on {g["better"]} copies and worse on {g["worse"]}, worst copy {g["min"]:+.4f}; medium stream {S["medium"]["mean_diff"]:+.4f},',
    f'stream that loses and invents players {S["good_degraded"]["mean_diff"]:+.4f}, copies of the other simulator {S["sim2_good"]["mean_diff"]:+.4f}. All seven gates',
    'passed, the last one by a hair, possession-v216-results.json. The second camera is simulated and the',
    'provided broadcast tracking was not examined; the documents say so. The next step of the ladder is v2.15.',
    'Eleven synthetic variants give the same bytes under Python 3.10 with numpy 1.26.4 and Python 3.13 with numpy 2.5.3.',
    '',
    'K016: asked by the team lead, whether the broadcast camera should take priority where it agrees with the',
    'tactical one. Simulated second camera on development copies, reporting only, possession-k016-camera-priority.json',
    'and experiments/possession_v2/v218: taking the ball or the players from the broadcast stream where both',
    'agree changed the score by -0.005 to +0.002, also with a stream five times as precise. Not adopted.',
    '',
    'K015: asked by the team lead, whether a Smart Tagging set-piece tag without a dead-ball stretch of ours',
    'around it should force one. Simulated tags on the 42 development copies, reporting only, see',
    'possession-k015-tag-rescue.json and experiments/possession_v2/v217. The decision already has a dead-ball',
    'stretch before 93 per cent of the restarts and the published tag counts cover about half of them, so the',
    'ceiling is 0.003 and the rule gained about 0.001. Not registered.',
    '',
    'K018: on 15 Nov the delivery chain ran end to end on the team lead computer with v2.15, every step OK,',
    'same bytes as recorded on Linux for the synthetic variants. v2.16 needs one more run of the chain there.',
    '',
    'Launchers: this script calls git without its pager and asks for no key when TESLIM-TEK-TIK.cmd starts it.',
    '',
    'No provided match data and no frame-level output are in the repository. External numbers are',
    'agreement with other providers labels, not competition scores.',
    '',
]
for m in msg:
    assert len(m) <= 118 and not m.startswith('(') and "'" not in m and not any(ch in m for ch in '<>|&%^"'), m
block = [('> ' if i == 0 else '>> ') + '"%POSSESSION_MSG1%" echo' + ('.' if not m else ' ' + m) for i, m in enumerate(msg)]
lines[a:b] = block
s = '\r\n'.join(lines)


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old)
    s = s.replace(old, new)


rep('git diff --cached --stat\r\n', 'git --no-pager diff --cached --stat\r\n', 2)
rep('git diff HEAD --name-only\r\n', 'git --no-pager diff HEAD --name-only\r\n')
rep('echo HATA: eklenecek dosyalar arasinda veri turu bir dosya var. Hicbir sey commit edilmedi.\r\ngit diff --cached --name-only\r\n',
    'echo HATA: eklenecek dosyalar arasinda veri turu bir dosya var. Hicbir sey commit edilmedi.\r\ngit --no-pager diff --cached --name-only\r\n')
rep('\r\npause >nul\r\n', '\r\nif not defined POSSESSION_NO_PAUSE pause >nul\r\n', 3)
rep('echo GitHub Actions sekmesinde testlerin sonucunu kontrol edin, sonra TESLIM-HAZIRLA.cmd calistirin.\r\npause\r\n',
    'echo GitHub Actions sekmesinde testlerin sonucunu kontrol edin, sonra TESLIM-HAZIRLA.cmd calistirin.\r\nif not defined POSSESSION_NO_PAUSE pause\r\n')
rep('rem Every path is named below; nothing else is added. Data file types are refused even if they were listed by mistake.\r\n',
    'rem Every path is named below; nothing else is added. Data file types are refused even if they were listed by mistake.\r\n'
    'rem git is called with --no-pager: a long list must not stop the window at the pager. With POSSESSION_NO_PAUSE set\r\n'
    'rem (TESLIM-TEK-TIK.cmd sets it) the script asks for no key unless something fails.\r\n')
assert s.count('\n') == s.count('\r\n') and 'git diff --cached --stat' not in s.replace('--no-pager diff --cached --stat', '')
p.write_bytes(s.encode('ascii'))
edit('TESLIM-TEK-TIK.cmd', [
    ('rem   2. GIT-YUKLE-V2.cmd commits and pushes the release (it asks for a key a few times),\r\n',
     'rem   2. GIT-YUKLE-V2.cmd commits and pushes the release (started from here it asks for no key unless something fails),\r\n'),
    ('echo ===== 2/3 GitHub\'a yukleniyor =====\r\ncall "%~dp0GIT-YUKLE-V2.cmd"\r\n',
     'echo ===== 2/3 GitHub\'a yukleniyor =====\r\nset "POSSESSION_NO_PAUSE=1"\r\ncall "%~dp0GIT-YUKLE-V2.cmd"\r\n'),
    ('echo Ekranda "bir tusa basin" yazdikca bir tusa basin.\r\n',
     'echo Bir sorun olmazsa hicbir tusa basmaniz gerekmez. Ekranda "bir tusa basin" yazarsa bir tusa basin.\r\n'),
], binary=True)
print('status snapshot and launchers written;', len(msg), 'message lines')
