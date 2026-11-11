"""Write possession-final-test-plan.json (registration of the final test on the reserved external match).
Usage: register_final_test.py   (reads the clock; run when the tool is final and before any access to the match)"""
import hashlib, json, subprocess
from pathlib import Path
SC = Path('/home/claude/sc')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
data = json.loads((SC / 'sportec-data-plan.json').read_text())
files = [e for e in data['files'] if e['fixture_id'] == 'J03WMX']
assert len(files) == 2 and all(e['split'] == 'reserved_test' for e in files)
plan = {
    'plan': 'possession-final-test',
    'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
    'registered_before': ('any access to the match. DFL J03WMX was set aside on 2026-11-07 (sportec-data-plan.json, split reserved_test). The '
                          'assistant has never downloaded or read a file of it, and the cloud session that wrote this plan cannot reach the '
                          "source. The project records (handoff of the external-data stage: reserved_test_not_downloaded) and a listing of "
                          "the team's external-data folder made on 2026-11-11 show no file of it."),
    'purpose': ('One measurement of the frozen release on a match that was never used to train, tune, select or check anything. '
                'Reported, not a gate.'),
    'release': {'name': 'possession-v2.9', 'manifest': 'possession-v29-release.json', 'manifest_sha256': sha(SC / 'possession-v29-release.json'),
                'entry_point': 'possession.run29.run, in its own process, on tracking files written from each copy (possession/epts_export.py)'},
    'fixture': {'id': 'J03WMX', 'competition': 'Bundesliga (DFL / Sportec open data, CC BY 4.0)', 'data_plan': 'sportec-data-plan.json',
                'data_plan_sha256_with_lf_line_endings': hashlib.sha256((SC / 'sportec-data-plan.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
                'source_commit': data['commit'],
                'files': [{k: e[k] for k in ('path', 'bytes', 'sha256', 'git_blob_sha1')} for e in files],
                'labels': ("provider flags BallStatus / BallPossession converted by tools/sportec_prepare.convert (D, H, A; X where the provider "
                           "names no owner): the same kind of labels the models were trained on, not the competition's definition")},
    'design': {
        'tactical_copies': [{'profile': 'v2', 'seed': 9101}, {'profile': 'v2', 'seed': 9102},
                            {'profile': 'ext_players', 'seed': 9501}, {'profile': 'ext_players', 'seed': 9502}],
        'corruption': ("possession.degrade with sample_params(rng, RANGES) for 'v2' and RANGES with player_sigma_m = (0.3, 0.6) for "
                       "'ext_players', rng = numpy default_rng(seed): the two profiles of the validations since possession-v25-plan.json"),
        'tactical_slots': 46, 'broadcast_slots': 51,
        'file_layout': ('tracklets packed into anonymous slots (half per team; a track lost for at most 25 frames returns to its slot, otherwise '
                        'the slot free the longest), Metrica EPTS layout as documented for the provided ATD, coordinates written with 5 decimals'),
        'broadcast_regimes': ['good', 'medium', 'bad'],
        'broadcast': ('experiments/possession_v2/synth_broadcast3.simulate_warp on the clean match; quality = synth_broadcast.sample_quality '
                      "('default') with bias / ball / player error ranges of the regime (tools/possession_final_test.REGIMES, the ranges of "
                      'possession-v25-plan.json); rng = default_rng(stream_seed_base + 100 * regime_index + copy_index)'),
        'stream_seed_base': 79000,
        'clock': ('experiments/possession_v2/synth_clock.observations for both recordings, p_read ~ U(0.5, 0.95) and p_misread ~ U(0.01, 0.03) per '
                  'recording; rng = default_rng(clock_seed_base + 100 * regime_index + copy_index)'),
        'clock_seed_base': 89000,
        'systems': ["baseline logic: the organisers' starter/baseline.py rule (nearest tracked player, majority vote over +-50 frames) on the corrupted copy",
                    'tactical only: the release entry point without broadcast files',
                    'broadcast good / medium / bad: the release entry point with a simulated broadcast stream and clock readings'],
        'metric': "possession.evaluate.score = the organisers' possession_metrics on the play blocks: spellF1 (ranking metric) and macroF1",
        'runs': '4 copies x (1 + 3) entry-point runs; every row and the mean per system are reported',
    },
    'reporting': ['possession-final-test-results.json holds every row, the means, the hashes of raw and prepared data, release, tool and simulators.',
                  'The tool refuses to run when that file exists: the test is run once. A run that stops half-way is resumed with the same rows.',
                  'The numbers go into the technical document as "reserved match, run once after freezing", next to the earlier numbers, whatever they are.'],
    'decision_rule': ('none. The release is not changed, retrained, re-thresholded or replaced because of this result. '
                      'If the result is poor, that is reported as a limitation.'),
    'expectations_written_before_the_result': {
        'basis': ('validation copies of the two DFL validation matches, scored with models that had not seen them (K002 rows): tactical only 0.676 '
                  "(profile v2, 0.641-0.726) and 0.633 (ext_players, 0.550-0.695); with a good / medium simulated broadcast +0.016 / +0.013 "
                  '(v2) and +0.042 / +0.039 (ext_players); bad: gate closed'),
        'tactical only': 'mean of the four copies between 0.58 and 0.70 spellF1',
        'broadcast good and medium': 'gate open on most copies; mean above tactical only by 0.01 to 0.05',
        'broadcast bad': 'gate closed on every copy; identical to tactical only',
        'baseline logic': 'between 0.15 and 0.27'},
    'code_check_before_registration': ('the tool was run on the development match J03WN1 (which is part of the training set of the release, so '
                                       'its numbers mean nothing) to check that it works: once with copy 0 and the seeds of this plan (9101, '
                                       '79000, 89000) before rehearsals were given their own seeds (+100000), then through the unit tests on a '
                                       'synthetic match. The copies of the final test are J03WMX with these seeds; none exists yet.'),
    'what_it_cannot_show': ['accuracy on the provided match: other provider, corrected tracking corrupted by our own simulator, labels of another definition',
                            'anything about the real broadcast stream: the stream is simulated by us',
                            'one match: differences below about 0.04 spellF1 are within match-to-match noise (EVALUATION.md)'],
    'seeds_checked_unused': ('9101, 9102, 9501, 9502 and the twelve stream and twelve clock seeds (79000 + 100 * r + c, 89000 + 100 * r + c, '
                             'r = 0..2, c = 0..3) occur in no earlier plan, results file, document or experiment script of the repository '
                             '(each value searched on registration)'),
    'tool': {'path': 'tools/possession_final_test.py', 'sha256': sha(SC / 'tools' / 'possession_final_test.py'),
             'writer_sha256': sha(SC / 'possession' / 'epts_export.py'),
             'adapter': 'tools/sportec_prepare.convert', 'adapter_sha256': sha(SC / 'tools' / 'sportec_prepare.py')},
    'simulator_sha256': {n: sha(SC / 'experiments' / 'possession_v2' / n) for n in ('synth_broadcast.py', 'synth_broadcast3.py', 'synth_clock.py')},
    'provided_fixture_used': False,
}
(SC / 'possession-final-test-plan.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8')
print('registered', plan['registered_at'])
