"""Re-register possession-final-test-plan.json for the release possession-v2.11 (the reserved match has not been
accessed). Design, copies, seeds, simulators and expectations are kept; only the release under test, the tool hash
and the registration time change. Usage: register_final_test_v211.py   (after the v2.11 manifest is frozen)"""
import hashlib, json, subprocess
from pathlib import Path
SC = Path('/home/claude/sc')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = SC / 'possession-final-test-plan.json'
plan = json.loads(path.read_text(encoding='utf-8'))
assert plan['release']['name'] == 'possession-v2.9' and not (SC / 'possession-final-test-results.json').exists()
first = {'registered_at': plan['registered_at'], 'release': plan['release']['name'], 'manifest_sha256': plan['release']['manifest_sha256'],
         'tool_sha256': plan['tool']['sha256'], 'plan_file_sha256': sha(path)}
now = subprocess.check_output(['date', '-Iseconds']).decode().strip()
out = {}
for k, v in plan.items():
    if k == 'registered_at':
        out[k] = now
        out['registration_history'] = [
            dict(first, note='first registration, for possession-v2.9; the match had not been accessed'),
            {'registered_at': now, 'release': 'possession-v2.11',
             'note': 'the release changed before the match was accessed (goalkeeper team check, possession-v211-plan.json and '
                     'possession-v211-results.json). Unchanged: design, copies, seeds, simulators, metric, reporting, decision rule and '
                     'expectations. Changed: the release under test, and the tool (it calls the entry point named in this plan and records '
                     'what the goalkeeper check moved on each copy).'}]
    elif k == 'release':
        out[k] = {'name': 'possession-v2.11', 'module': 'possession.run211', 'manifest': 'possession-v211-release.json',
                  'manifest_sha256': sha(SC / 'possession-v211-release.json'),
                  'entry_point': 'possession.run211.run, in its own process, on tracking files written from each copy (possession/epts_export.py)'}
    elif k == 'expectations_written_before_the_result':
        out[k] = dict(v, **{'goalkeeper team check': 'the provider\'s team ids are correct, so the check should move only goalkeeper pieces that our corruption '
                            'put under the other id for 1-6 s; the expectations above (written for possession-v2.9) are kept unchanged, because on '
                            'the validation copies with ids as corrupted possession-v2.11 scored the same as possession-v2.9'})
    elif k == 'tool':
        out[k] = dict(v, sha256=sha(SC / 'tools/possession_final_test.py'))
        assert out[k]['writer_sha256'] == sha(SC / 'possession/epts_export.py') and out[k]['adapter_sha256'] == sha(SC / 'tools/sportec_prepare.py')
    else:
        out[k] = v
assert out['simulator_sha256'] == {n: sha(SC / 'experiments/possession_v2' / n) for n in out['simulator_sha256']}
path.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(now, out['release']['manifest_sha256'][:16], out['tool']['sha256'][:16])
