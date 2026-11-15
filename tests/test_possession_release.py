"""Is this checkout the frozen release? (manifest hashes, release configuration, line-ending protection); no match data."""
import importlib
import hashlib
import json
import unittest
from pathlib import Path
try:
    from possession import run25, run25c, run29, run29g, run211, run211g, run211k, run215, run216
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class ReleaseTests(unittest.TestCase):
    def test_every_frozen_source_and_bundle_equals_its_manifest(self):
        self.assertEqual(run211.check_release()['version'], 'possession-v2.11')
        self.assertEqual(run29.check_release()['version'], 'possession-v2.9')
        self.assertEqual(run25c.check_release()['version'], 'possession-v2.5c')
        self.assertEqual(run211k.check_release()['version'], 'possession-v2.11k')
        self.assertEqual(run215.check_release()['version'], 'possession-v2.15')
        self.assertEqual(run216.check_release()['version'], 'possession-v2.16')
        self.assertEqual(run211g.check_release()['version'], 'possession-v2.11g')
        self.assertEqual(run29g.check_release()['version'], 'possession-v2.9g')
        run25.check_release()

    def test_v211_adds_two_files_and_leaves_every_v29_file_as_frozen(self):
        new = json.loads((REPO / 'possession-v211-release.json').read_text(encoding='utf-8'))
        old = json.loads((REPO / 'possession-v29-release.json').read_text(encoding='utf-8'))
        self.assertEqual(set(new['source_sha256']) - set(old['source_sha256']), {'keeper2.py', 'run211.py'})
        self.assertEqual({k: new['source_sha256'][k] for k in old['source_sha256']}, old['source_sha256'])
        self.assertEqual(new['bundle_sha256'], old['bundle_sha256'])                        # the same two model bundles
        steps = json.loads((REPO / 'possession-release.json').read_text(encoding='utf-8'))['steps']
        self.assertEqual([s['module'] for s in steps[:5]],
                         ['possession.run216', 'possession.run215', 'possession.run211k', 'possession.run211g', 'possession.run29g'])
        k = json.loads((REPO / 'possession-v211k-release.json').read_text(encoding='utf-8'))    # v2.11k = v2.11g + two files, v2.11g = v2.11 + one
        g = json.loads((REPO / 'possession-v211g-release.json').read_text(encoding='utf-8'))
        self.assertEqual(set(k['source_sha256']), {'kickoff.py', 'run211k.py'})
        self.assertEqual(k['base_release_sha256'], hashlib.sha256((REPO / 'possession-v211g-release.json').read_bytes()).hexdigest())
        self.assertEqual(g['base_release_sha256'], hashlib.sha256((REPO / 'possession-v211-release.json').read_bytes()).hexdigest())
        plan = json.loads((REPO / 'possession-v211-plan.json').read_text(encoding='utf-8'))
        results = json.loads((REPO / 'possession-v211-results.json').read_text(encoding='utf-8'))
        self.assertEqual(plan['hashes']['possession/keeper2.py'], new['source_sha256']['keeper2.py'])    # the file that was validated
        self.assertLess(plan['registered_at'], results['written_at'])
        self.assertTrue(all(g['pass'] for g in results['gates'].values()))
        self.assertEqual(results['selected'], 'possession-v2.11')

    def test_v215_freezes_every_v211_file_the_kickoff_files_and_the_second_model(self):
        new = json.loads((REPO / 'possession-v215-release.json').read_text(encoding='utf-8'))
        old = json.loads((REPO / 'possession-v211-release.json').read_text(encoding='utf-8'))
        k = json.loads((REPO / 'possession-v211k-release.json').read_text(encoding='utf-8'))
        self.assertEqual({n: new['source_sha256'][n] for n in old['source_sha256']}, old['source_sha256'])
        self.assertEqual({n: new['source_sha256'][n] for n in k['source_sha256']}, k['source_sha256'])
        self.assertEqual(set(new['source_sha256']) - set(old['source_sha256']) - set(k['source_sha256']),
                         {'tcn/__init__.py', 'tcn/infer.py', 'tcn/features.py', 'tcn/decode.py', 'pooling.py', 'run211g.py', 'run215.py'})
        self.assertEqual({b: new['bundle_sha256'][b] for b in old['bundle_sha256']}, old['bundle_sha256'])   # the same two v2 bundles
        plan = json.loads((REPO / 'possession-v215-plan.json').read_text(encoding='utf-8'))
        results = json.loads((REPO / 'possession-v215-results.json').read_text(encoding='utf-8'))
        self.assertEqual(plan['hashes']['validation_scripts']['pooling.py'], new['source_sha256']['pooling.py'])   # the pooling that was validated
        for f in ('infer.py', 'features.py', 'decode.py'):
            self.assertEqual(plan['hashes']['tcn_modules_sha256'][f], new['source_sha256']['tcn/' + f])
        self.assertEqual(new['tcn_members_sha256'], {f: plan['hashes']['tcn_weights_sha256'][f] for f in new['tcn_members_sha256']})
        self.assertLess(plan['registered_at'], results['written_at'])
        self.assertTrue(all(results['gates'].values()) and results['selected'])

    def test_v216_adds_two_files_and_leaves_every_v215_file_as_frozen(self):
        new = json.loads((REPO / 'possession-v216-release.json').read_text(encoding='utf-8'))
        old = json.loads((REPO / 'possession-v215-release.json').read_text(encoding='utf-8'))
        self.assertEqual(set(new['source_sha256']) - set(old['source_sha256']), {'playerfill.py', 'run216.py'})
        self.assertEqual({k: new['source_sha256'][k] for k in old['source_sha256']}, old['source_sha256'])
        self.assertEqual(new['bundle_sha256'], old['bundle_sha256'])                        # the same three model files
        self.assertEqual(new['previous_release']['manifest_sha256'], hashlib.sha256((REPO / 'possession-v215-release.json').read_bytes()).hexdigest())
        plan = json.loads((REPO / 'possession-v216-plan.json').read_text(encoding='utf-8'))
        results = json.loads((REPO / 'possession-v216-results.json').read_text(encoding='utf-8'))
        self.assertEqual(plan['hashes']['possession/playerfill.py'], new['source_sha256']['playerfill.py'])    # the file that was validated
        self.assertEqual(results['sha256']['possession/playerfill.py'], new['source_sha256']['playerfill.py'])
        self.assertEqual(results['plan_sha256'], hashlib.sha256((REPO / 'possession-v216-plan.json').read_bytes()).hexdigest())
        self.assertLess(plan['registered_at'], results['written_at'])
        self.assertLess(results['written_at'], new['frozen_at'])
        self.assertTrue(all(g['passed'] for g in results['gates'].values()) and results['selected'])
        self.assertEqual(len(results['gates']), 7)

    def test_release_configurations_name_existing_entry_points_manifests_and_tests(self):
        for name, release in (('possession-release.json', 'possession-v2.16'), ('possession-release-graded-windows.json', 'possession-v2.11g')):
            cfg = json.loads((REPO / name).read_text(encoding='utf-8'))
            self.assertEqual((cfg['release'], cfg['rows'], cfg['game']), (release, 199319, 'BAR-ATH'))
            self.assertTrue(cfg['steps'][0]['broadcast'])
            for s in cfg['steps']:
                mod = importlib.import_module(s['module'])
                self.assertTrue(callable(mod.run) and callable(mod.check_release))
                mod.check_release()
                self.assertEqual(Path(mod.RELEASE).name, s['manifest'])
                self.assertEqual(json.loads((REPO / s['manifest']).read_text(encoding='utf-8'))['version'], s['name'].split(' ')[0])
            self.assertEqual(cfg['release'], cfg['steps'][0]['name'])
            for t in cfg['tests']:
                self.assertTrue((REPO / (t.replace('.', '/') + '.py')).exists(), t)
            self.assertTrue((REPO / cfg['document']).exists())
        default = json.loads((REPO / 'possession-release.json').read_text(encoding='utf-8'))
        reserve = json.loads((REPO / 'possession-release-graded-windows.json').read_text(encoding='utf-8'))
        for cfg in (default, reserve):                                                       # nothing with the published kick-off frame
            self.assertFalse({'possession.run211', 'possession.run29', 'possession.run25c'} & {s['module'] for s in cfg['steps']})
        self.assertEqual(default['steps'][3:], reserve['steps'])                             # the reserve is the ladder without the kick-off tag rule, the second model and the added players
        self.assertTrue(set(reserve['tests']) < set(default['tests']))

    def test_frozen_bytes_are_protected_from_line_ending_conversion(self):
        rules = [l.strip() for l in (REPO / '.gitattributes').read_text(encoding='utf-8').splitlines()]
        for line in ('possession/*.py -text', 'models/possession-v2.npz binary', 'models/possession-v23.npz binary',
                     'possession/tcn/*.py -text', 'models/possession-tcn-v215.npz binary'):
            self.assertIn(line, rules)
        for name in run216.SOURCES + ('run29g.py',):
            self.assertNotIn(b'\r', (REPO / 'possession' / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
