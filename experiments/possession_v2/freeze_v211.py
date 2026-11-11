"""Freeze possession-v2.11 and its reserve entry point after the registered gates passed.
Writes the two manifests and the two release configurations. Refuses unless possession-v211-results.json says
that possession-v2.11 was selected and the registered files are unchanged. Usage: freeze.py"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path('/home/claude/sc')
sys.path.insert(0, str(REPO))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return subprocess.check_output(['date', '-Iseconds']).decode().strip()


def main():
    from possession import run211, run29
    res_path, plan_path = REPO / 'possession-v211-results.json', REPO / 'possession-v211-plan.json'
    res, plan = json.loads(res_path.read_text()), json.loads(plan_path.read_text())
    if res['selected'] != 'possession-v2.11' or not all(g['pass'] for g in res['gates'].values()):
        raise SystemExit('possession-v2.11 was not selected; nothing is frozen')
    if sha(REPO / 'possession/keeper2.py') != plan['hashes']['possession/keeper2.py'] or res['plan_sha256'] != sha(plan_path):
        raise SystemExit('a registered file changed')
    v29 = json.loads((REPO / 'possession-v29-release.json').read_text())
    for name in run211.SOURCES:
        b = (REPO / 'possession' / name).read_bytes()
        assert b'\r' not in b, name
    assert all(v29['source_sha256'][n] == sha(REPO / 'possession' / n) for n in run29.SOURCES)      # the v2.9 files are untouched
    rel = {
        'version': 'possession-v2.11',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run211',
        'components': dict(v29['components'], goalkeeper_team_correction=(
            'possession-v2.11 (possession/keeper2.py): goalkeeper track pieces found under the id of the team that does not defend '
            'their goal are moved to the defending team in the tracking the models see (whole half: most of the goal\'s evidence is under '
            'the other id; shorter: the piece continues a goalkeeper piece); noise gate, broadcast alignment, registration and accuracy '
            'gate use the ids as given')),
        'selection': {'plan': plan_path.name, 'plan_sha256': sha(plan_path), 'results': res_path.name, 'results_sha256': sha(res_path),
                      'rule': 'all six registered gates passed on 8 external validation copies: simulated goalkeeper id errors, and a simulated '
                              'camera that does not always show the far goalkeeper',
                      'earlier_candidate': 'possession-v2.10 (possession/keeper.py; possession-v210-plan.json, possession-v210-results.json) passed '
                                           'its four gates and was not released: it moved outfield players when the far goalkeeper was not tracked'},
        'evidence_limits': 'the errors and the camera window were simulated by us; whether the provided tracking has them was not looked at. '
                           'The output is the output of possession-v2.9 unless a goalkeeper track piece is found in a slot of the other team',
        'source_sha256': {n: sha(REPO / 'possession' / n) for n in run211.SOURCES},
        'bundle_sha256': v29['bundle_sha256'],
        'plans': v29['plans'] + ['possession-v29-amendment-plan.json', 'possession-v210-plan.json', 'possession-v211-plan.json'],
        'previous_release': {'name': 'possession-v2.9', 'manifest': 'possession-v29-release.json', 'manifest_sha256': sha(REPO / 'possession-v29-release.json')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v211-release.json').write_text(json.dumps(rel, indent=1) + '\n', encoding='utf-8')
    v29g = json.loads((REPO / 'possession-v29g-release.json').read_text())
    relg = {
        'version': 'possession-v2.11g',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run211g',
        'status': v29g['status'].replace('possession-v2.9 stays', 'possession-v2.11 stays'),
        'change': v29g['change'].replace('possession-v2.9', 'possession-v2.11'),
        'evidence': 'made of components selected on external matches (possession-v2.5b; registration of possession-v2.9; goalkeeper team '
                    'correction of possession-v2.11, plan possession-v211-plan.json). What the models predict on a period before a kick-off '
                    'is not measurable on external matches (their tracking starts at the kick-off)',
        'base_release': 'possession-v211-release.json',
        'base_release_sha256': sha(REPO / 'possession-v211-release.json'),
        'source_sha256': {'run211g.py': sha(REPO / 'possession/run211g.py')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v211g-release.json').write_text(json.dumps(relg, indent=1) + '\n', encoding='utf-8')
    # release configurations
    cfg = json.loads((REPO / 'possession-release.json').read_text())
    cfg['release'] = 'possession-v2.11'
    cfg['steps'] = [{'name': 'possession-v2.11', 'module': 'possession.run211', 'manifest': 'possession-v211-release.json', 'broadcast': True}] + \
                   [s for s in cfg['steps'] if s['module'] != 'possession.run211']
    for t in ('tests.test_possession_v211',):
        if t not in cfg['tests']:
            cfg['tests'].insert(cfg['tests'].index('tests.test_possession_v29') + 1, t)
    text = json.dumps(cfg, indent=2)
    (REPO / 'possession-release.json').write_text(text + '\n', encoding='utf-8')
    cfgg = json.loads((REPO / 'possession-release-graded-windows.json').read_text())
    cfgg['release'] = 'possession-v2.11g'
    cfgg['steps'] = [{'name': 'possession-v2.11g', 'module': 'possession.run211g', 'manifest': 'possession-v211g-release.json', 'broadcast': True}] + \
                    [s for s in cfgg['steps'] if s['module'] != 'possession.run211g']
    for t in ('tests.test_possession_v211', 'tests.test_possession_v211g'):
        if t not in cfgg['tests']:
            cfgg['tests'].append(t)
    (REPO / 'possession-release-graded-windows.json').write_text(json.dumps(cfgg, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'v2.11': sha(REPO / 'possession-v211-release.json'), 'v2.11g': sha(REPO / 'possession-v211g-release.json'),
                      'steps': [s['name'] for s in cfg['steps']], 'reserve_steps': [s['name'] for s in cfgg['steps']]}, indent=1))


if __name__ == '__main__':
    main()
