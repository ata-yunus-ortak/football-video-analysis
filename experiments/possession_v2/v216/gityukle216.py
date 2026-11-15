"""Update GIT-YUKLE-V2.cmd for the records of 15 Nov (K014): title and one paragraph of the first commit message.
The file stays ASCII with CRLF line ends. Usage: gityukle216.py REPO_DIR"""
import sys
from pathlib import Path
REPO = Path(sys.argv[1])
p = REPO / 'GIT-YUKLE-V2.cmd'
s = p.read_bytes().decode('ascii')
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
rep('echo Release possession-v2.15 (second model pooled with the v2 models); records K007-K013\r\n',
    'echo Release possession-v2.15 (second model pooled with the v2 models); records K007-K014\r\n')
new = ['K014: error-pattern study of v2.15 on 42 external development copies, reporting only, see',
       'possession-k014-error-patterns.json and experiments/possession_v2/v216. Possessions under 2 s carry',
       '38 per cent of the lost score and are not visible to either model family; 29 per cent is the timing',
       'of possessions that are found. Rules built on these patterns changed the score by at most 0.003,',
       'a learned combination of both families was explored and not registered. The release is unchanged.',
       '']
anchor = '>> "%POSSESSION_MSG1%" echo K012: candidate possession-v2.14, the same pooled system with equal weights:'
assert s.count(anchor) == 1
block = ''.join(('>> "%POSSESSION_MSG1%" echo.\r\n' if not x else '>> "%POSSESSION_MSG1%" echo ' + x + '\r\n') for x in new)
s = s.replace(anchor, block + anchor)
lines = s.split('\r\n')
msg = [l.split(' echo ', 1)[1] for l in lines if l.startswith(('> "%POSSESSION_MSG1%" echo ', '>> "%POSSESSION_MSG1%" echo '))]
assert all(not m.startswith('(') for m in msg) and "'" not in ''.join(msg) and all(len(m) <= 110 for m in msg)
for m in msg:
    t = m.replace('^<', '').replace('^>', '').replace('%%', '')
    assert not any(c in t for c in '<>|&%^"'), m
b = s.encode('ascii')
assert s.count('\n') == s.count('\r\n')
p.write_bytes(b)
print('GIT-YUKLE-V2.cmd updated;', len(msg), 'message lines'); print('\n'.join(msg[:20]))
