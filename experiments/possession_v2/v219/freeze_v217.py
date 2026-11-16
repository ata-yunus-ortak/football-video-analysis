"""Freeze possession-v2.17 after the registered gates passed: checks that the eight network members and the inference
modules are the validated files and that no file of the v2.16 release changed, and writes possession-v217-release.json.
Refuses unless possession-v217-results.json says that the candidate was selected.
Usage: /usr/bin/python3 freeze_v217.py REPO_DIR"""
import hashlib, json, subprocess, sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return subprocess.check_output(['date', '-Iseconds']).decode().strip()


def main():
    from possession import run216, run217
    res_path, plan_path = REPO / 'possession-v217-results.json', REPO / 'possession-v217-plan.json'
    res, plan = json.loads(res_path.read_text()), json.loads(plan_path.read_text())
    if not res['selected'] or not all(g['passed'] for g in res['gates'].values()):
        raise SystemExit('possession-v2.17 was not selected; nothing is frozen')
    if res['plan_sha256'] != sha(plan_path):
        raise SystemExit('the plan changed after the results were written')
    members = {}
    for name in run217.TCN_MEMBERS:
        members[name] = sha(run217.TCN_DIR / name)
        assert members[name] == plan['hashes']['candidate_weights'][name] == res['sha256']['candidate_weights'][name], f'{name} is not the validated file'
    for ours, theirs in (('tcn/infer2.py', 'infer.py'), ('tcn/features2.py', 'features2.py'), ('tcn/features.py', 'features.py'), ('tcn/decode.py', 'decode.py'),
                         ('tcn/__init__.py', '__init__.py')):
        assert sha(REPO / 'possession' / ours) == plan['hashes']['tcn2'][theirs] == res['sha256']['tcn2'][theirs], f'{ours} is not the validated module'
    assert sha(REPO / 'possession' / 'pooling.py') == plan['hashes']['pooling.py'] == res['sha256']['pooling.py']
    v216 = json.loads((REPO / 'possession-v216-release.json').read_text())
    assert sha(REPO / 'possession-v216-release.json') == plan['hashes']['possession-v216-release.json']
    assert all(v216['source_sha256'][n] == sha(REPO / 'possession' / n) for n in run216.SOURCES)          # the v2.16 files are untouched
    assert run217.SOURCES == run216.SOURCES + ('tcn/features2.py', 'tcn/infer2.py', 'run217.py')
    for name in run217.SOURCES:
        assert b'\r' not in (REPO / 'possession' / name).read_bytes(), name
    comp = dict(v216['components'])
    comp['second_model'] = ('possession-v2.17: on the v2.1 path the second-stage probabilities of the v2 models are pooled (arithmetic pool, weight 0.4; possession/pooling.py) '
                            'with an ensemble of eight temporal convolution networks (models/possession-tcn-v217/: four on the 37 features of possession/tcn/features.py, four on '
                            'the 71 features of possession/tcn/features2.py; inference possession/tcn/infer2.py) and decoded by the unchanged v2 decoder; on the v2.3 path nothing '
                            'is pooled. Members and inference are byte copies of repository branch mtah-possession, commit 74bedbf. possession-v2.15 / v2.16 used three members '
                            '(models/possession-tcn-v215.npz) with weight 0.2')
    s = res['summary']
    t = s['tactical']
    rel = {
        'version': 'possession-v2.17',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run217',
        'components': comp,
        'selection': {'plan': plan_path.name, 'plan_sha256': sha(plan_path), 'results': res_path.name, 'results_sha256': sha(res_path),
                      'rule': 'all seven registered gates passed on 16 new corrupted copies of four external validation matches: '
                              f"{t['mean_diff']:+.4f} spellF1 over possession-v2.16 (DFL {t['dfl']:+.4f}, Metrica {t['metrica']:+.4f}; {t['better']} better, {t['worse']} worse, "
                              f"{t['equal']} equal, worst {t['min']:+.4f}); with a simulated second camera {s['fill_good']['mean_diff']:+.4f} (good stream) and "
                              f"{s['fill_medium']['mean_diff']:+.4f} (medium stream); copies of the other simulator {s['tactical_sim2']['mean_diff']:+.4f}"},
        'evidence_limits': 'fourth registered attempt with a second model, made after a written statement that there would be no further one and after the candidate\'s development '
                           'numbers were known; the members were trained, tuned and first checked by their author on his own computer, and that only external matches were used is his '
                           'statement; validation matches and simulators had been used before, only the copies were new; there is no untouched test for a pooled system. '
                           'On the v2.3 path the output is that of possession-v2.16',
        'source_sha256': {n: sha(REPO / 'possession' / n) for n in run217.SOURCES},
        'bundle_sha256': {k: v216['bundle_sha256'][k] for k in ('v2.1', 'v2.3')},
        'tcn_members_sha256': members,
        'tcn_training': {'by': 'the team member who wrote the network, on his own computer (PyTorch on Apple MPS); not observed and not repeated by the process that validated the files',
                         'source': 'repository branch mtah-possession, commit 74bedbf: experiments/v216u/train216.py, experiments/v216u/README.md, possession/train.py '
                                   '(byte copies under experiments/possession_v2/v219/author_74bedbf/)',
                         'data': 'six open DFL matches (CC BY 4.0): J03WOH, J03WOY, J03WPY, J03WQQ, J03WN1, J03WR9; per match 16 copies of the team\'s corruption simulator and 8 of his own, '
                                 'packed into 46 slots and goalkeeper-corrected with the team\'s code',
                         'recipes': {'d6_a_s0-3': '37 features, 3200 steps of AdamW, peak learning rate 1.5e-3, batch 16, seeds 0-3',
                                     'd6_f_s0-3': '71 features, 4800 steps, otherwise the same'},
                         'statement_of_the_author': 'external matches only; the provided match was not opened',
                         'reproducibility': 'a training run is not bit-reproducible; the released weights are the files with the SHA-256 above'},
        'plans': v216['plans'] + ['possession-v217-plan.json'],
        'previous_release': {'name': 'possession-v2.16', 'manifest': 'possession-v216-release.json',
                             'manifest_sha256': sha(REPO / 'possession-v216-release.json')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v217-release.json').write_text(json.dumps(rel, indent=1) + '\n', encoding='utf-8')
    run217.check_release()
    print(json.dumps({'v2.17': sha(REPO / 'possession-v217-release.json'), 'sources': len(rel['source_sha256']), 'members': len(members), 'frozen_at': rel['frozen_at']}, indent=1))


if __name__ == '__main__':
    main()
