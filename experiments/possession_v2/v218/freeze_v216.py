"""Freeze possession-v2.16 after the registered gates passed: checks that possession/playerfill.py is the validated file and
that no file of the v2.15 release changed, and writes possession-v216-release.json. Refuses unless
possession-v216-results.json says that the candidate was selected.
Usage: /usr/bin/python3 freeze_v216.py REPO_DIR"""
import hashlib, json, subprocess, sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return subprocess.check_output(['date', '-Iseconds']).decode().strip()


def main():
    from possession import run215, run216
    res_path, plan_path = REPO / 'possession-v216-results.json', REPO / 'possession-v216-plan.json'
    res, plan = json.loads(res_path.read_text()), json.loads(plan_path.read_text())
    if not res['selected'] or not all(g['passed'] for g in res['gates'].values()):
        raise SystemExit('possession-v2.16 was not selected; nothing is frozen')
    if res['plan_sha256'] != sha(plan_path):
        raise SystemExit('the plan changed after the results were written')
    assert sha(REPO / 'possession/playerfill.py') == plan['hashes']['possession/playerfill.py'] == res['sha256']['possession/playerfill.py'], \
        'playerfill.py is not the validated file'
    v215 = json.loads((REPO / 'possession-v215-release.json').read_text())
    assert sha(REPO / 'possession-v215-release.json') == plan['hashes']['possession-v215-release.json']
    assert all(v215['source_sha256'][n] == sha(REPO / 'possession' / n) for n in run215.SOURCES)          # the v2.15 files are untouched
    assert run216.SOURCES == run215.SOURCES + ('playerfill.py', 'run216.py')
    for name in run216.SOURCES:
        assert b'\r' not in (REPO / 'possession' / name).read_bytes(), name
    comp = dict(v215['components'])
    comp['added_players'] = ('possession-v2.16: when the accuracy gate of the broadcast fill is open, broadcast players that, after the alignment and the '
                             'player-based registration, have no tactical player of either team within 1.5 m are added to the tracking the models see '
                             '(possession/playerfill.py); the goalkeeper team check then runs on the tracking with the added players. Tactical positions '
                             'are never moved. Without broadcast files or with the gate closed nothing is added')
    s = res['summary']
    rel = {
        'version': 'possession-v2.16',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run216',
        'components': comp,
        'selection': {'plan': plan_path.name, 'plan_sha256': sha(plan_path), 'results': res_path.name, 'results_sha256': sha(res_path),
                      'rule': 'all seven registered gates passed on 16 new corrupted copies of four external validation matches with a simulated second '
                              f"camera: +{s['good']['mean_diff']:.4f} spellF1 over possession-v2.15 (DFL +{s['good']['dfl']:.4f}, Metrica +{s['good']['metrica']:.4f}; "
                              f"{s['good']['better']} better, {s['good']['worse']} worse, worst {s['good']['min']:+.4f}); medium stream +{s['medium']['mean_diff']:.4f}; stream that loses and "
                              f"invents players +{s['good_degraded']['mean_diff']:.4f}; copies of the other simulator +{s['sim2_good']['mean_diff']:.4f}"},
        'evidence_limits': 'the second camera is simulated; in three of the four conditions it never loses or invents a player inside its window. The gate on the '
                           'copies of the other simulator passed by 0.0004 (three of four copies lower). Validation matches and simulators had been used before; '
                           'only the copies were new. Without broadcast files or with the gate closed the output is that of possession-v2.15',
        'source_sha256': {n: sha(REPO / 'possession' / n) for n in run216.SOURCES},
        'bundle_sha256': dict(v215['bundle_sha256']),
        'tcn_members_sha256': v215['tcn_members_sha256'],
        'tcn_training': v215['tcn_training'],
        'plans': v215['plans'] + ['possession-v216-plan.json'],
        'previous_release': {'name': 'possession-v2.15', 'manifest': 'possession-v215-release.json',
                             'manifest_sha256': sha(REPO / 'possession-v215-release.json')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v216-release.json').write_text(json.dumps(rel, indent=1) + '\n', encoding='utf-8')
    run216.check_release()
    print(json.dumps({'v2.16': sha(REPO / 'possession-v216-release.json'), 'sources': len(rel['source_sha256']), 'frozen_at': rel['frozen_at']}, indent=1))


if __name__ == '__main__':
    main()
