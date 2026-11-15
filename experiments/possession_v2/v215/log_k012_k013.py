"""Put the log entries K013 and K012 (bodies written by v215/k013.py and v214/k012.py) at the top of
docs/DENEY_KAYDI_TR.md of the given repository copy, K013 first. Refuses when either entry is already there.
Usage: log_k012_k013.py REPO_DIR"""
import sys
from pathlib import Path

REPO = Path(sys.argv[1])
k013 = Path('/home/claude/work/v215/k013_body.md').read_text(encoding='utf-8').rstrip('\n') + '\n\n'
k012 = Path('/home/claude/work/v214/k012_body.md').read_text(encoding='utf-8').rstrip('\n') + '\n\n'
assert k013.startswith('## K013 ') and k012.startswith('## K012 ')
p = REPO / 'docs' / 'DENEY_KAYDI_TR.md'
s = p.read_text(encoding='utf-8')
head = '# Deney kaydı\n\n'
assert s.startswith(head + '## K011 ') and '## K012 ' not in s and '## K013 ' not in s
p.write_text(head + k013 + k012 + s[len(head):], encoding='utf-8')
print('log: K013 and K012 inserted;', len(k013), '+', len(k012), 'characters')
