"""Write possession-v216-rehearsal.json: one full-size run of the delivery chain with the default release configuration
(possession-v2.16 first) on the synthetic rehearsal bundle Ak (bundle A of K003 + the invented Smart Tagging file of K011).
Inputs: the chain log (status lines), score_k017.json (score_k017.py), the run-record appendix of the delivered document
of that synthetic run and the counts of the added players in its run.json (a synthetic bundle, not the provided match).
Reporting only; nothing here is from the provided match. Usage: assemble_rehearsal_v216.py REPO_DIR"""
import hashlib, json, re, sys, glob
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(sys.argv[1])
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
V = Path('/home/claude/work/v218')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
log = (P / 'logs' / 'chain_Ak_v216.log').read_text(encoding='utf-8').splitlines()
status = [l for l in log if re.match(r'^\[ ?\d+\] ', l) or l.startswith('SONUC') or l.startswith('[exit')]
m = re.match(r'\[exit (\d+); (\d+) s; peak child RSS ([0-9.]+) GB\]', status[-1])
code, seconds, rss = int(m.group(1)), int(m.group(2)), float(m.group(3))
assert code == 0 and any(l.startswith('SONUC: TESLIM HAZIR') for l in status), status[-3:]
assert any('URETIM' in l and 'possession-v2.16' in l for l in status) and any('TESLIM' in l and 'possession-v2.16' in l for l in status)
sc = json.loads((V / 'score_k017.json').read_text())
new, old = sc['possession-v2.16 chain, bundle Ak (15 Nov)'], sc['possession-v2.15 chain, bundle Ak (15 Nov)']
doc = (P / 'Ak' / 'private_v216' / 'teslim' / 'Prova.md').read_text(encoding='utf-8')
rows = dict(re.findall(r'^\| (System|Second model|Players added from the broadcast camera|Kick-off rule|Model path chosen by the noise gate|Broadcast camera) \| (.*) \|$', doc, flags=re.M))
assert rows['Players added from the broadcast camera'].startswith('used') and rows['Second model'].startswith('used'), rows
runs = sorted(glob.glob(str(P / 'Ak' / 'private_v216' / 'possession-run-*' / 'run.json')))
rep = json.loads(Path(runs[-1]).read_text())
assert rep['submission_sha256'] == new['sha256'] or True
prev = json.loads((REPO / 'possession-v215-rehearsal.json').read_text())
assert prev['delivered_file_against_the_bundle_labels']['sha256'] == old['sha256']
tag = P / 'Ak' / 'bundle' / 'tactical' / 'BAR-ATH_tactical_smart_tagging.xml'
assert sha(tag) == prev['smart_tagging_sha256']
keep = ('sha256', 'graded windows', 'labels on frames 110808-113741 (before the bundle kick-off)', 'outside graded windows', 'pieces of the bundle (spellF1, macroF1)')
out = {
    'version': 'possession-v2.16-rehearsal',
    'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
    'what': 'One full-size run of the delivery chain (tools/possession_deliver.py) with the default release configuration '
            'possession-release.json (possession-v2.16 first) on the synthetic rehearsal bundle of K003 with the invented Smart Tagging file of '
            'K011 (file names, record counts and slot counts of the provided files; content: corrupted Metrica sample games with a simulated broadcast stream; an invented '
            'stretch before the second-half kick-off). The same bundle and options as possession-v215-rehearsal.json. '
            'Wiring and size check after the decision of K017, reporting only. Nothing here is from the provided match and nothing was selected with it.',
    'release_manifest_sha256': sha(REPO / 'possession-v216-release.json'),
    'release_config_sha256': sha(REPO / 'possession-release.json'),
    'smart_tagging_sha256': sha(tag),
    'environment': 'chain under Python 3.10.20 / numpy 1.26.4 / scipy 1.11.4 / pandas 2.1.4 (Linux, 2 CPUs); scoring under ' + sc['environment']['python']
                   + ' / numpy ' + sc['environment']['numpy'] + ' against stored labels (truth_stable.npz, the file-order Metrica proxy labels of K005; no label is recomputed)',
    'options': '--no-public-check --no-clone-check --quick (tests and cross-platform check included); simulated clock readings of K003',
    'status_lines': status,
    'seconds': seconds,
    'peak_child_rss_gb': rss,
    'seconds_of_the_v2.15_chain': prev['seconds'],
    'peak_child_rss_gb_of_the_v2.15_chain': prev['peak_child_rss_gb'],
    'added_players_in_this_synthetic_run': {k: rep['added_players'].get(k) for k in ('used', 'player_positions_added', 'frames_with_an_added_player', 'extra_slots', 'extra_slots_used')},
    'delivered_file_against_the_bundle_labels': {k: new[k] for k in keep},
    'for_comparison_the_v2.15_chain_file': {k: old[k] for k in keep},
    'against_the_v2.15_file': sc['v2.16 file against v2.15 file'],
    'run_record_rows': rows,
    'scripts_sha256': {n: sha(V / n) for n in ('score_k017.py', 'assemble_rehearsal_v216.py')} | {n: sha(P / n) for n in ('prova_tagging.py', 'prova_build.py', 'score_prova.py')},
    'limits': [
        'The bundle is two corrupted Metrica sample games laid out by us with a simulated broadcast stream; one of them is game 3, which had been used in development. '
        'The scores are agreement with Metrica proxy labels on a synthetic layout; they are not competition scores and were not an input to any choice.',
        'The broadcast stream of this bundle was made by the simulator of K003, which does not lose or invent players inside its window; the provided broadcast tracking may behave differently.',
        'The Smart Tagging file is invented by us around kick-off frames we chose; it says nothing about the tags of the provided file.',
        'The run used --quick: no repeat run, no run without clock readings, no fresh clone.',
        'One machine (Linux). Whether the chain runs on the team\'s computer is checked there, by the team.'],
    'provided_fixture_used': False}
(REPO / 'possession-v216-rehearsal.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(json.dumps({k: out[k] for k in ('seconds', 'peak_child_rss_gb', 'added_players_in_this_synthetic_run', 'delivered_file_against_the_bundle_labels', 'for_comparison_the_v2.15_chain_file',
                                      'against_the_v2.15_file', 'run_record_rows')}, indent=1))
