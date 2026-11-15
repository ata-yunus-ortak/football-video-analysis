"""Freeze possession-v2.14 after the registered gates passed: checks that the files in the repository copy are the
registered ones (pooling module, network modules, the three six-match members inside the merged weight file) and writes
possession-v214-release.json. Refuses unless possession-v214-results.json says that the candidate was selected.
Usage: /usr/bin/python3 freeze_v214.py REPO_DIR"""
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np

REPO = Path(sys.argv[1]).resolve()
V = Path('/home/claude/work/v214')
sys.path.insert(0, str(REPO))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return subprocess.check_output(['date', '-Iseconds']).decode().strip()


def main():
    from possession import run214, run211
    res_path, plan_path = REPO / 'possession-v214-results.json', REPO / 'possession-v214-plan.json'
    res, plan = json.loads(res_path.read_text()), json.loads(plan_path.read_text())
    if not res['selected'] or not all(res['gates'].values()):
        raise SystemExit('possession-v2.14 was not selected; nothing is frozen')
    if res['plan_sha256'] != sha(plan_path):
        raise SystemExit('the plan changed after the results were written')
    h = plan['hashes']
    assert sha(REPO / 'possession/fuse2.py') == h['validation_scripts']['fuse2.py'], 'fuse2.py is not the validated file'
    for f in ('__init__.py', 'infer.py', 'features.py', 'decode.py'):
        assert sha(REPO / 'possession/tcn' / f) == h['tcn_modules_sha256'][f], f
    members = ['dfl6_both_s0.npz', 'dfl6_both_s1.npz', 'dfl6_both_s2.npz']
    merged = np.load(run214.TCN_MODEL)
    for i, f in enumerate(members):                      # the merged file holds exactly the registered members, in this order
        assert sha(V / 'tcn_weights' / f) == h['tcn_weights_sha256'][f], f
        blob = np.load(V / 'tcn_weights' / f)
        for k in blob.files:
            a, b = blob[k], merged['m%d/%s' % (i, k.split('/', 1)[1])]
            assert a.dtype == b.dtype and a.shape == b.shape and np.array_equal(a, b), (f, k)
    assert len(merged.files) == sum(len(np.load(V / 'tcn_weights' / f).files) for f in members)
    for name in run214.SOURCES:
        assert b'\r' not in (REPO / 'possession' / name).read_bytes(), name
    v211 = json.loads((REPO / 'possession-v211-release.json').read_text())
    v211k = json.loads((REPO / 'possession-v211k-release.json').read_text())
    assert all(v211['source_sha256'][n] == sha(REPO / 'possession' / n) for n in run211.SOURCES)      # the v2.11 files are untouched
    assert all(v211k['source_sha256'][n] == sha(REPO / 'possession' / n) for n in v211k['source_sha256'])
    comp = {k: v for k, v in v211['components'].items() if k != 'second_half_kickoff'}
    comp['second_half_kickoff'] = ('play blocks = the organisers\' graded windows (as possession-v2.11g); then the Smart Tagging kick-off '
                                   'rule of possession-v2.11k (possession/kickoff.py); the kick-off frame published in FAQ.md is not used')
    comp['second_model'] = ('possession-v2.14: on the v2.1 path the second-stage probabilities of the v2 models are pooled '
                            f"({plan['fusion_rule_fixed_before_any_score']['pool']} pool, weight {plan['fusion_rule_fixed_before_any_score']['weight']}; "
                            'possession/fuse2.py) with a temporal convolution network (possession/tcn/, models/possession-tcn-v214.npz, three '
                            'members) and decoded by the unchanged v2 decoder; on the v2.3 path nothing is pooled')
    rel = {
        'version': 'possession-v2.14',
        'frozen_at': now(),
        'entry_point': 'python -m possession.run214',
        'components': comp,
        'selection': {'plan': plan_path.name, 'plan_sha256': sha(plan_path), 'results': res_path.name, 'results_sha256': sha(res_path),
                      'rule': 'all seven registered gates passed on 16 new corrupted copies of four external validation matches (tactical camera, '
                              'simulated broadcast fill, copies of the second simulator)',
                      'earlier_candidate': 'possession-v2.13 (possession-v213-plan.json, possession-v213-results.json): the same v2 probabilities '
                                           'averaged 50/50 with the team member\'s committed weights and decoded by one single-cost Viterbi pass; '
                                           'three of six gates failed, not released'},
        'evidence_limits': 'validation matches and simulators had been used before; only the copies were new. The second model saw the two '
                           'corruption simulators of the team and nothing of the provided match. Without the pooling (v2.3 path) the output is '
                           'the output of possession-v2.11k',
        'source_sha256': {n: sha(REPO / 'possession' / n) for n in run214.SOURCES},
        'bundle_sha256': dict(v211['bundle_sha256'], tcn=sha(run214.TCN_MODEL)),
        'tcn_members_sha256': {f: h['tcn_weights_sha256'][f] for f in members},
        'tcn_training': {'script': 'experiments/possession_v2/v214/tcn_jax.py', 'data': 'six open DFL matches (CC BY 4.0), replicas of both '
                         'corruption simulators', 'runs': {f: plan['tcn']['training_runs'][f] for f in members}},
        'plans': v211['plans'] + ['possession-v213-plan.json', 'possession-v214-plan.json'],
        'previous_release': {'name': 'possession-v2.11k', 'manifest': 'possession-v211k-release.json',
                             'manifest_sha256': sha(REPO / 'possession-v211k-release.json')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-v214-release.json').write_text(json.dumps(rel, indent=1) + '\n', encoding='utf-8')
    run214.check_release()
    print(json.dumps({'v2.14': sha(REPO / 'possession-v214-release.json'), 'tcn': rel['bundle_sha256']['tcn'],
                      'sources': len(rel['source_sha256'])}, indent=1))


if __name__ == '__main__':
    main()
