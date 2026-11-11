"""Is this checkout the frozen release? (manifest hashes, release configuration, line-ending protection); no match data."""
import importlib
import json
import unittest
from pathlib import Path
try:
    from possession import run25, run25c, run29, run211
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
        run25.check_release()

    def test_v211_adds_two_files_and_leaves_every_v29_file_as_frozen(self):
        new = json.loads((REPO / 'possession-v211-release.json').read_text(encoding='utf-8'))
        old = json.loads((REPO / 'possession-v29-release.json').read_text(encoding='utf-8'))
        self.assertEqual(set(new['source_sha256']) - set(old['source_sha256']), {'keeper2.py', 'run211.py'})
        self.assertEqual({k: new['source_sha256'][k] for k in old['source_sha256']}, old['source_sha256'])
        self.assertEqual(new['bundle_sha256'], old['bundle_sha256'])                        # the same two model bundles
        steps = json.loads((REPO / 'possession-release.json').read_text(encoding='utf-8'))['steps']
        self.assertEqual([s['module'] for s in steps[:2]], ['possession.run211', 'possession.run29'])   # v2.9 is the next step of the ladder
        plan = json.loads((REPO / 'possession-v211-plan.json').read_text(encoding='utf-8'))
        results = json.loads((REPO / 'possession-v211-results.json').read_text(encoding='utf-8'))
        self.assertEqual(plan['hashes']['possession/keeper2.py'], new['source_sha256']['keeper2.py'])    # the file that was validated
        self.assertLess(plan['registered_at'], results['written_at'])
        self.assertTrue(all(g['pass'] for g in results['gates'].values()))
        self.assertEqual(results['selected'], 'possession-v2.11')

    def test_release_configurations_name_existing_entry_points_manifests_and_tests(self):
        for name, release in (('possession-release.json', 'possession-v2.11'), ('possession-release-graded-windows.json', 'possession-v2.11g')):
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
        reserve = json.loads((REPO / 'possession-release-graded-windows.json').read_text(encoding='utf-8'))
        self.assertFalse({'possession.run211', 'possession.run29', 'possession.run25c'} & {s['module'] for s in reserve['steps']})   # nothing with the kick-off frame

    def test_frozen_bytes_are_protected_from_line_ending_conversion(self):
        rules = [l.strip() for l in (REPO / '.gitattributes').read_text(encoding='utf-8').splitlines()]
        for line in ('possession/*.py -text', 'models/possession-v2.npz binary', 'models/possession-v23.npz binary'):
            self.assertIn(line, rules)
        for name in run211.SOURCES + ('run29g.py', 'run211g.py'):
            self.assertNotIn(b'\r', (REPO / 'possession' / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
