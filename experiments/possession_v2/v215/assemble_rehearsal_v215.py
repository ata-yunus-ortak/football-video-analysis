"""Write possession-v215-rehearsal.json: one full-size run of the delivery chain with the default release configuration
(possession-v2.15 first) on the synthetic rehearsal bundle Ak (bundle A of K003 + the invented Smart Tagging file of K011).
Inputs: the chain log (status lines), score_k013.json (score_k013.py) and the run-record appendix of the delivered
document of that synthetic run. Reporting only; nothing here is from the provided match.
Usage: assemble_rehearsal_v215.py REPO_DIR"""
import hashlib, json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(sys.argv[1])
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
V = Path('/home/claude/work/v215')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
log = (P / 'logs' / 'chain_Ak_v215.log').read_text(encoding='utf-8').splitlines()
status = [l for l in log if re.match(r'^\[ ?\d+\] ', l) or l.startswith('SONUC') or l.startswith('[exit')]
m = re.match(r'\[exit (\d+); (\d+) s; peak child RSS ([0-9.]+) GB\]', status[-1])
code, seconds, rss = int(m.group(1)), int(m.group(2)), float(m.group(3))
assert code == 0 and any(l.startswith('SONUC: TESLIM HAZIR') for l in status), status[-3:]
sc = json.loads((V / 'score_k013.json').read_text())
new, old = sc['possession-v2.15 chain, bundle Ak (15 Nov)'], sc['possession-v2.11k chain, bundle Ak (13 Nov)']
doc = (P / 'Ak' / 'private_v215' / 'teslim' / 'Prova.md').read_text(encoding='utf-8')
rows = dict(re.findall(r'^\| (System|Second model|Kick-off rule|Model path) \| (.*) \|$', doc, flags=re.M))
assert 'System' in rows and 'Second model' in rows, rows
prev = json.loads((REPO / 'possession-v211k-rehearsal.json').read_text())
assert prev['run_1_with_an_invented_smart_tagging_file']['delivered_file_against_the_bundle_labels']['sha256'] == old['sha256']
tag = P / 'Ak' / 'bundle' / 'tactical' / 'BAR-ATH_tactical_smart_tagging.xml'
assert sha(tag) == prev['run_1_with_an_invented_smart_tagging_file']['smart_tagging_sha256']
out = {
    'version': 'possession-v2.15-rehearsal',
    'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
    'what': 'One full-size run of the delivery chain (tools/possession_deliver.py) with the default release configuration '
            'possession-release.json (possession-v2.15 first) on the synthetic rehearsal bundle of K003 with the invented Smart Tagging file of '
            'K011 (file names, record counts and slot counts of the provided files; content: corrupted Metrica sample games; an invented '
            'stretch before the second-half kick-off). The same bundle and options as run 1 of possession-v211k-rehearsal.json. '
            'Wiring and size check after the decision of K013, reporting only. Nothing here is from the provided match and nothing was selected with it.',
    'release_manifest_sha256': sha(REPO / 'possession-v215-release.json'),
    'release_config_sha256': sha(REPO / 'possession-release.json'),
    'smart_tagging_sha256': sha(tag),
    'environment': 'chain under Python 3.10.20 / numpy 1.26.4 / scipy 1.11.4 / pandas 2.1.4 (Linux, 2 CPUs); scoring under ' + sc['environment']['python']
                   + ' / numpy ' + sc['environment']['numpy'] + ' against stored labels (truth_stable.npz, the file-order Metrica proxy labels of K005; no label is recomputed)',
    'options': '--no-public-check --no-clone-check --quick (tests and cross-platform check included); simulated clock readings of K003',
    'status_lines': status,
    'seconds': seconds,
    'peak_child_rss_gb': rss,
    'seconds_of_the_v2.11k_chain_13_Nov': prev['run_1_with_an_invented_smart_tagging_file']['seconds'],
    'delivered_file_against_the_bundle_labels': {k: new[k] for k in ('sha256', 'graded windows', 'labels on frames 110808-113741 (before the bundle kick-off)',
                                                                      'outside graded windows', 'pieces of the bundle (spellF1, macroF1)')},
    'for_comparison_the_v2.11k_chain_file_13_Nov': {k: old[k] for k in ('sha256', 'graded windows', 'labels on frames 110808-113741 (before the bundle kick-off)',
                                                                         'outside graded windows', 'pieces of the bundle (spellF1, macroF1)')},
    'against_the_v2.11k_file': sc['v2.15 file against v2.11k file'],
    'run_record_rows': rows,
    'scripts_sha256': {n: sha(V / n) for n in ('score_k013.py', 'assemble_rehearsal_v215.py')} | {n: sha(P / n) for n in ('prova_tagging.py', 'prova_build.py', 'score_prova.py')},
    'limits': [
        'The bundle is two corrupted Metrica sample games laid out by us; one of them is game 3, which had been used in the development of v2.14 and v2.15. '
        'The scores are agreement with Metrica proxy labels on a synthetic layout; they are not competition scores and were not an input to any choice.',
        'The Smart Tagging file is invented by us around kick-off frames we chose; it says nothing about the tags of the provided file.',
        'The run used --quick: no repeat run, no run without clock readings, no fresh clone.',
        'One machine (Linux). Whether the chain runs on the team\'s computer is checked there, by the team.'],
    'provided_fixture_used': False}
(REPO / 'possession-v215-rehearsal.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(json.dumps({k: out[k] for k in ('seconds', 'peak_child_rss_gb', 'delivered_file_against_the_bundle_labels', 'for_comparison_the_v2.11k_chain_file_13_Nov',
                                      'against_the_v2.11k_file', 'run_record_rows')}, indent=1))
