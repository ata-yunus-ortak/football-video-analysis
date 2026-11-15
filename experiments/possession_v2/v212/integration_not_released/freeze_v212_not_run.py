"""Freeze possession-v2.12 and its reserve entry point v2.12g after the registered gates passed and the release bundle
was trained. Writes the two manifests and updates the two release configurations of tools/possession_deliver.py.
Refuses unless possession-v212-results.json says that v2.12 was selected, the registered files are unchanged and the
bundle card names the registered touch.py. Usage: /usr/bin/python3 freeze_v212.py"""
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
    from possession import run212, run211
    from possession.bundle import load
    res_path, plan_path = REPO / 'possession-v212-results.json', REPO / 'possession-v212-plan.json'
    res, plan = json.loads(res_path.read_text()), json.loads(plan_path.read_text())
    if not res['selected'] or not all(res['gates'].values()):
        raise SystemExit('possession-v2.12 was not selected; nothing is frozen')
    if res['plan_sha256'] != sha(plan_path):
        raise SystemExit('the plan changed after the results')
    for k in ('possession/touch.py', 'possession/keeper2.py', 'possession/features.py'):
        if sha(REPO / k) != plan['hashes'][k]:
            raise SystemExit(f'a registered file changed: {k}')
    b = load(run212.V212_MODEL)
    if b['card']['source_sha256'].get('touch.py') != plan['hashes']['possession/touch.py']:
        raise SystemExit('the release bundle was not trained with the registered touch.py')
    v211 = json.loads((REPO / 'possession-v211-release.json').read_text())
    assert all(v211['source_sha256'][n] == sha(REPO / 'possession' / n) for n in run211.SOURCES)      # the v2.11 files are untouched
    for name in run212.SOURCES:
        assert b'\r' not in (REPO / 'possession' / name).read_bytes(), name
    s = res['summary']
    rel = {
        'version': 'possession-v2.12',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run212',
        'components': dict(v211['components'], touch_columns=(
            'possession-v2.12 (possession/touch.py, possession/pipeline212.py): on the v2.1 path the stage-1 models also see 36 columns '
            'of evidence of ball touches and control changes, computed on the goalkeeper-corrected tactical tracking before the '
            'broadcast fill; new stage-1 and second-stage models (models/possession-v212.npz, possession/train212.py, '
            'possession-v212-config.json); the v2.3 path for noisy inputs is unchanged')),
        'selection': {'plan': plan_path.name, 'plan_sha256': sha(plan_path), 'results': res_path.name, 'results_sha256': sha(res_path),
                      'rule': 'all six registered gates passed on 16 new corrupted copies of the four validation matches '
                              '(tactical camera), plus two simulated broadcast regimes on 8 of them',
                      'measured': {'tactical_mean_spell_f1_difference': s['tactical']['diff_spell_f1_mean'],
                                   'dfl': s['tactical_DFL']['diff_spell_f1_mean'], 'metrica': s['tactical_Metrica']['diff_spell_f1_mean'],
                                   'fill_good': s['fill_good']['diff_spell_f1_mean'], 'fill_medium': s['fill_medium']['diff_spell_f1_mean']}},
        'evidence_limits': 'validation matches used for every earlier selection (new corrupted copies only); corruption, slot packing, '
                           'camera window and broadcast camera simulated; DFL provider flags and Metrica event-derived proxy labels; if the '
                           'measured noise of the provided tracking exceeds 0.30 m the output is the possession-v2.11 output',
        'source_sha256': {n: sha(REPO / 'possession' / n) for n in run212.SOURCES},
        'bundle_sha256': {'v2.12': sha(run212.V212_MODEL), 'v2.3': v211['bundle_sha256']['v2.3']},
        'training_config': {'file': 'possession-v212-config.json', 'sha256': sha(REPO / 'possession-v212-config.json')},
        'plans': v211['plans'] + ['possession-v212-plan.json'],
        'previous_release': {'name': 'possession-v2.11', 'manifest': 'possession-v211-release.json',
                             'manifest_sha256': sha(REPO / 'possession-v211-release.json')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v212-release.json').write_text(json.dumps(rel, indent=1) + '\n', encoding='utf-8')
    v211g = json.loads((REPO / 'possession-v211g-release.json').read_text())
    relg = {
        'version': 'possession-v2.12g',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run212g',
        'status': v211g['status'].replace('possession-v2.11 stays', 'possession-v2.12 stays'),
        'change': v211g['change'].replace('possession-v2.11', 'possession-v2.12'),
        'evidence': v211g['evidence'] + '; touch columns of possession-v2.12, plan possession-v212-plan.json',
        'base_release': 'possession-v212-release.json',
        'base_release_sha256': sha(REPO / 'possession-v212-release.json'),
        'source_sha256': {'run212g.py': sha(REPO / 'possession/run212g.py')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v212g-release.json').write_text(json.dumps(relg, indent=1) + '\n', encoding='utf-8')
    cfg = json.loads((REPO / 'possession-release.json').read_text())
    cfg['release'] = 'possession-v2.12'
    cfg['steps'] = [{'name': 'possession-v2.12', 'module': 'possession.run212', 'manifest': 'possession-v212-release.json', 'broadcast': True}] + \
                   [s for s in cfg['steps'] if s['module'] != 'possession.run212']
    for t in ('tests.test_possession_v212', 'tests.test_possession_touch'):
        if t not in cfg['tests']:
            cfg['tests'].insert(cfg['tests'].index('tests.test_possession_v211') + 1, t)
    (REPO / 'possession-release.json').write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
    cfgg = json.loads((REPO / 'possession-release-graded-windows.json').read_text())
    cfgg['release'] = 'possession-v2.12g'
    cfgg['steps'] = [{'name': 'possession-v2.12g', 'module': 'possession.run212g', 'manifest': 'possession-v212g-release.json', 'broadcast': True}] + \
                    [s for s in cfgg['steps'] if s['module'] != 'possession.run212g']
    for t in ('tests.test_possession_v212', 'tests.test_possession_touch', 'tests.test_possession_v212g'):
        if t not in cfgg['tests']:
            cfgg['tests'].append(t)
    (REPO / 'possession-release-graded-windows.json').write_text(json.dumps(cfgg, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'v2.12': sha(REPO / 'possession-v212-release.json'), 'v2.12g': sha(REPO / 'possession-v212g-release.json'),
                      'steps': [s['name'] for s in cfg['steps']], 'reserve_steps': [s['name'] for s in cfgg['steps']]}, indent=1))


if __name__ == '__main__':
    main()
