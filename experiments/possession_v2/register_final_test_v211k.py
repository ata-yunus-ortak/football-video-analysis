"""Re-register possession-final-test-plan.json for the release possession-v2.11k (the reserved match has not been
accessed by the release's process). Design, copies, seeds, simulators, tool and expectations are kept; only the release
under test and the registration time change. Usage: register_final_test_v211k.py   (after the v2.11k manifest is frozen)"""
import hashlib, json, subprocess
from pathlib import Path
SC = Path('/home/claude/sc')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = SC / 'possession-final-test-plan.json'
plan = json.loads(path.read_text(encoding='utf-8'))
assert plan['release']['name'] == 'possession-v2.11' and not (SC / 'possession-final-test-results.json').exists()
before = sha(path)
now = subprocess.check_output(['date', '-Iseconds']).decode().strip()
out = {}
for k, v in plan.items():
    if k == 'registered_at':
        out[k] = now
    elif k == 'registration_history':
        prev = dict(v[-1], manifest_sha256=plan['release']['manifest_sha256'], tool_sha256=plan['tool']['sha256'], plan_file_sha256=before)
        out[k] = v[:-1] + [prev, {
            'registered_at': now, 'release': 'possession-v2.11k',
            'note': 'the release changed before the match was accessed by the process that built it: the kick-off frame published in '
                    'FAQ.md is no longer used, the models run on the whole graded windows (possession-v2.11g) and the Smart Tagging '
                    'kick-off rule follows (possession/kickoff.py). On this external match neither change can act: its play blocks are '
                    'its two halves and it has no Smart Tagging file, so the entry point writes what possession-v2.11 would write. '
                    'Unchanged: design, copies, seeds, simulators, tool, metric, reporting, decision rule and expectations. Changed: '
                    'the release under test. Also recorded: a team member downloaded this match and used it while developing a '
                    'separate model (a temporal convolution network, possession-v213-plan.json); that model is not part of the '
                    'release, and no score or file of this match reached the process that built the release.'}]
    elif k == 'release':
        out[k] = {'name': 'possession-v2.11k', 'module': 'possession.run211k', 'manifest': 'possession-v211k-release.json',
                  'manifest_sha256': sha(SC / 'possession-v211k-release.json'),
                  'entry_point': 'possession.run211k.run, in its own process, on tracking files written from each copy (possession/epts_export.py)'}
    elif k == 'expectations_written_before_the_result':
        out[k] = dict(v, **{'kick-off rule': 'not applicable to this match (no Smart Tagging file, play blocks = the two halves): the output is '
                                             'that of possession-v2.11 on the same files, so the expectations above are kept unchanged'})
    else:
        out[k] = v
assert out['tool']['sha256'] == sha(SC / 'tools/possession_final_test.py') and out['tool']['writer_sha256'] == sha(SC / 'possession/epts_export.py')
assert out['simulator_sha256'] == {n: sha(SC / 'experiments/possession_v2' / n) for n in out['simulator_sha256']}
path.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(now, out['release']['manifest_sha256'][:16], out['tool']['sha256'][:16])
