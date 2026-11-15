"""Add the one-double-click delivery (TESLIM-TEK-TIK.cmd, tools/possession_place_files.py) to GIT-YUKLE-V2.cmd: path list and
one paragraph of the first commit message. The file stays ASCII with CRLF line ends. Usage: gityukle_place.py REPO_DIR"""
import sys
from pathlib import Path
REPO = Path(sys.argv[1])
p = REPO / 'GIT-YUKLE-V2.cmd'
s = p.read_bytes().decode('ascii')
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
rep(' tools/possession_final_test.py ', ' tools/possession_final_test.py tools/possession_place_files.py ')
rep(' TESLIM-HAZIRLA.cmd SON-TEST.cmd ', ' TESLIM-HAZIRLA.cmd TESLIM-TEK-TIK.cmd SON-TEST.cmd ')
new = ['TESLIM-TEK-TIK.cmd: one double-click for the delivery on the team lead computer.',
       'tools/possession_place_files.py copies the files the organisers shipped from where a download put',
       'them into the bundle folder, on that computer only; then this script and the delivery chain run, and',
       'the shareable status lines are also copied to Desktop logs. Tests: tests/test_possession_place_files.py,',
       'synthetic folders only.',
       '']
anchor = '>> "%POSSESSION_MSG1%" echo K012: candidate possession-v2.14, the same pooled system with equal weights:'
assert s.count(anchor) == 1
s = s.replace(anchor, ''.join(('>> "%POSSESSION_MSG1%" echo.\r\n' if not x else '>> "%POSSESSION_MSG1%" echo ' + x + '\r\n') for x in new) + anchor)
lines = s.split('\r\n')
msg = [l.split(' echo ', 1)[1] for l in lines if l.startswith(('> "%POSSESSION_MSG1%" echo ', '>> "%POSSESSION_MSG1%" echo '))]
assert all(not m.startswith('(') for m in msg) and "'" not in ''.join(msg) and all(len(m) <= 110 for m in msg), [m for m in msg if len(m) > 110]
for m in msg:
    t = m.replace('^<', '').replace('^>', '').replace('%%', '')
    assert not any(c in t for c in '<>|&%^"'), m
assert s.count('\n') == s.count('\r\n') and all(ord(c) < 128 for c in s)
p.write_bytes(s.encode('ascii'))
print('GIT-YUKLE-V2.cmd updated;', len(msg), 'message lines')
