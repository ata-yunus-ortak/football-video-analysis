"""Update GIT-YUKLE-V2.cmd for the release possession-v2.15: the weight file in the path list and in the data-type guard,
and the message of the first commit (K012, K013 added in front of the unchanged K007-K011 paragraphs).
The file stays ASCII with CRLF line ends. Usage: gityukle215.py REPO_DIR"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
r4 = json.loads((REPO / 'possession-v214-results.json').read_text())
r5 = json.loads((REPO / 'possession-v215-results.json').read_text())
assert r5['selected'] and not r4['selected']
T4, T5 = r4['summary']['tactical'], r5['summary']['tactical']
p = REPO / 'GIT-YUKLE-V2.cmd'
s = p.read_bytes().decode('ascii')
assert s.count('\r\n') == s.count('\n')


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


rep('git add -- possession models/possession-v2.npz models/possession-v23.npz ',
    'git add -- possession models/possession-v2.npz models/possession-v23.npz models/possession-tcn-v215.npz ')
rep('git diff --cached --name-only -- "*.npz" ":(exclude)models/possession-v2.npz" ":(exclude)models/possession-v23.npz" | findstr /r "." >nul',
    'git diff --cached --name-only -- "*.npz" ":(exclude)models/possession-v2.npz" ":(exclude)models/possession-v23.npz" ":(exclude)models/possession-tcn-v215.npz" | findstr /r "." >nul')
rep('rem Commits the possession release (source, model bundles, plans, results, documents, tests, launchers, experiment scripts)',
    'rem Commits the possession release (source, model bundles and network weights, plans, results, documents, tests, launchers, experiment scripts)')
old_head = ('> "%POSSESSION_MSG1%" echo Release possession-v2.11k (Smart Tagging kick-off rule); records K007-K011\r\n'
            '>> "%POSSESSION_MSG1%" echo.\r\n')
new_lines = [
 'Release possession-v2.15 (second model pooled with the v2 models); records K007-K013',
 '',
 'K013: the submission system is now possession-v2.15 = v2.11k plus a second model family on the core',
 'model path. The second-stage probabilities of the tree models are averaged with those of a temporal',
 'convolution network, weight 0.2 for the network, and decoded by the unchanged v2 decoder, see',
 'possession/pooling.py, possession/tcn and models/possession-tcn-v215.npz. The network was designed',
 'by a team member, branch mtah-possession, commit 167dc7b; its weights were trained by us on the six',
 'open DFL matches with both corruption simulators, experiments/possession_v2/v214/tcn_jax.py.',
 'Registered before any new result, possession-v215-plan.json: on 16 new copies spellF1 %+.4f,' % T5['diff_spell_f1_mean'],
 'better on %d copies and worse on %d, all seven gates passed, possession-v215-results.json.' % (T5['copies_better'], T5['copies_worse']),
 'It is the third attempt with the same gates and the documents say so. Nothing is pooled on the',
 'noisier v2.3 path. The next step of the technical ladder is v2.11k.',
 '',
 'K012: candidate possession-v2.14, the same pooled system with equal weights: %+.4f on 16 new' % T4['diff_spell_f1_mean'],
 'copies and better on %d, but one copy was %.3f worse, so the gate on single copies failed and it' % (T4['copies_better'], abs(T4['diff_spell_f1_min'])),
 'is not released, see possession-v214-plan.json and possession-v214-results.json.',
 '',
 'K011: possession-v2.11k = v2.11g plus one rule (possession/kickoff.py):',
]
new_head = '> "%POSSESSION_MSG1%" echo ' + new_lines[0] + '\r\n' + ''.join(
    ('>> "%POSSESSION_MSG1%" echo.\r\n' if not x else '>> "%POSSESSION_MSG1%" echo ' + x + '\r\n') for x in new_lines[1:])
rep(old_head + '>> "%POSSESSION_MSG1%" echo K011: the submission system is now possession-v2.11k = v2.11g plus one rule (possession/kickoff.py):\r\n', new_head)
rep('>> "%POSSESSION_MSG1%" echo DATA.md (28 checks), and the final-test plan was re-registered for v2.11k.\r\n',
    '>> "%POSSESSION_MSG1%" echo DATA.md (28 checks), and the final-test plan was re-registered for v2.11k and stays there.\r\n')
b = s.encode('ascii')
lines = s.split('\r\n')
msg = [l.split(' echo ', 1)[1] for l in lines if l.startswith(('> "%POSSESSION_MSG1%" echo ', '>> "%POSSESSION_MSG1%" echo '))]
assert all(not m.startswith('(') for m in msg), [m for m in msg if m.startswith('(')]
assert "'" not in ''.join(msg) and all(len(m) <= 110 for m in msg), [m for m in msg if len(m) > 110]
for m in msg:      # characters that cmd.exe would interpret in an echo line
    t = m.replace('^<', '').replace('^>', '').replace('%%', '')
    assert not any(c in t for c in '<>|&%^"'), m
assert s.count('\n') == s.count('\r\n') and all(c < 128 for c in b)
p.write_bytes(b)
print('GIT-YUKLE-V2.cmd updated;', len(msg), 'message lines')
print('\n'.join(msg[:22]))
