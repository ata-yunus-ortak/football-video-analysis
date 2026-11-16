"""Apply the code-side integration of possession-v2.17 to a copy of the repository (every replacement must match
exactly once). The frozen release files are not touched: new files are added and configuration, tests and tools are
edited. Usage: python3 apply_v217.py REPO_DIR [XPLAT_JSON]
XPLAT_JSON: {'lost_added_eight_clock': {...}, 'keepers_eight_tactical_only': {...}} as recorded by
tests.test_possession_crossplatform --record; without it the two new variants get a placeholder hash."""
import json, shutil, subprocess, sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
V = Path('/home/claude/work/v219')
XPLAT = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else None


def edit(rel, pairs, crlf=False):
    p = REPO / rel
    s = p.read_bytes().decode('utf-8')
    if crlf:
        assert '\r\n' in s and '\n' not in s.replace('\r\n', ''), rel
        s = s.replace('\r\n', '\n')
    else:
        assert '\r' not in s, rel
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:90])
        s = s.replace(old, new)
    if crlf:
        s = s.replace('\n', '\r\n')
    p.write_bytes(s.encode('utf-8'))


# --- new files: byte copies of commit 74bedbf, the generated entry point, the eight members
(REPO / 'models' / 'possession-tcn-v217').mkdir(exist_ok=True)
for f in sorted((V / 'weights').glob('d6_*.npz')):
    shutil.copyfile(f, REPO / 'models' / 'possession-tcn-v217' / f.name)
shutil.copyfile(V / 'tcn2' / 'features2.py', REPO / 'possession' / 'tcn' / 'features2.py')
shutil.copyfile(V / 'tcn2' / 'infer.py', REPO / 'possession' / 'tcn' / 'infer2.py')
subprocess.check_call([sys.executable, str(V / 'port' / 'make_run217.py'), str(REPO / 'possession' / 'run217.py')])
shutil.copyfile(V / 'port' / 'test_possession_v217.py', REPO / 'tests' / 'test_possession_v217.py')

# --- .gitignore / .gitattributes
edit('.gitignore', [("!models/possession-tcn-v215.npz\n",
                     "!models/possession-tcn-v215.npz\n"
                     "# Second model of possession-v2.17: eight network members trained by a team member on the same external DFL data only (CC-BY 4.0), no match data\n"
                     "!models/possession-tcn-v217/\n!models/possession-tcn-v217/*.npz\n")])
edit('.gitattributes', [("models/possession-tcn-v215.npz binary\n", "models/possession-tcn-v215.npz binary\nmodels/possession-tcn-v217/*.npz binary\n")])

# --- release ladder
cfg = json.loads((REPO / 'possession-release.json').read_text(encoding='utf-8'))
assert cfg['release'] == 'possession-v2.16' and cfg['steps'][0]['module'] == 'possession.run216'
cfg['release'] = 'possession-v2.17'
old_note = ("The first step is the second with one addition: players the tactical tracking has lost are added from the broadcast tracking when the accuracy gate is open "
            "(possession-v216-plan.json). The second step pools the v2 models with a second model family (possession-v215-plan.json); every lower step is the v2 models alone.")
assert cfg['note'].count(old_note) == 1
cfg['note'] = cfg['note'].replace(old_note,
    "The first step is the second with another second model: eight network members instead of three, weight 0.4 instead of 0.2 (possession-v217-plan.json). "
    "The second step is the third with one addition: players the tactical tracking has lost are added from the broadcast tracking when the accuracy gate is open "
    "(possession-v216-plan.json). The third step pools the v2 models with a second model family (possession-v215-plan.json); every lower step is the v2 models alone.")
cfg['steps'].insert(0, {'name': 'possession-v2.17', 'module': 'possession.run217', 'manifest': 'possession-v217-release.json', 'broadcast': True, 'smart_tagging': True})
assert cfg['tests'][-1] == 'tests.test_possession_v216'
cfg['tests'].append('tests.test_possession_v217')
(REPO / 'possession-release.json').write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

# --- tests
edit('tests/test_possession_release.py', [
    ("    from possession import run25, run25c, run29, run29g, run211, run211g, run211k, run215, run216\n",
     "    from possession import run25, run25c, run29, run29g, run211, run211g, run211k, run215, run216, run217\n"),
    ("        self.assertEqual(run216.check_release()['version'], 'possession-v2.16')\n",
     "        self.assertEqual(run216.check_release()['version'], 'possession-v2.16')\n"
     "        self.assertEqual(run217.check_release()['version'], 'possession-v2.17')\n"),
    ("        self.assertEqual([s['module'] for s in steps[:5]],\n"
     "                         ['possession.run216', 'possession.run215', 'possession.run211k', 'possession.run211g', 'possession.run29g'])\n",
     "        self.assertEqual([s['module'] for s in steps[:6]],\n"
     "                         ['possession.run217', 'possession.run216', 'possession.run215', 'possession.run211k', 'possession.run211g', 'possession.run29g'])\n"),
    ("    def test_release_configurations_name_existing_entry_points_manifests_and_tests(self):\n"
     "        for name, release in (('possession-release.json', 'possession-v2.16'), ",
     "    def test_v217_adds_three_files_and_eight_members_and_leaves_every_v216_file_as_frozen(self):\n"
     "        new = json.loads((REPO / 'possession-v217-release.json').read_text(encoding='utf-8'))\n"
     "        old = json.loads((REPO / 'possession-v216-release.json').read_text(encoding='utf-8'))\n"
     "        self.assertEqual(set(new['source_sha256']) - set(old['source_sha256']), {'tcn/features2.py', 'tcn/infer2.py', 'run217.py'})\n"
     "        self.assertEqual({k: new['source_sha256'][k] for k in old['source_sha256']}, old['source_sha256'])\n"
     "        self.assertEqual(new['bundle_sha256'], {k: old['bundle_sha256'][k] for k in ('v2.1', 'v2.3')})     # the same two v2 bundles\n"
     "        self.assertEqual(new['previous_release']['manifest_sha256'], hashlib.sha256((REPO / 'possession-v216-release.json').read_bytes()).hexdigest())\n"
     "        plan = json.loads((REPO / 'possession-v217-plan.json').read_text(encoding='utf-8'))\n"
     "        results = json.loads((REPO / 'possession-v217-results.json').read_text(encoding='utf-8'))\n"
     "        self.assertEqual(list(new['tcn_members_sha256']), list(run217.TCN_MEMBERS))\n"
     "        for name, digest in new['tcn_members_sha256'].items():                                 # the files that were validated\n"
     "            self.assertEqual(digest, plan['hashes']['candidate_weights'][name])\n"
     "            self.assertEqual(digest, results['sha256']['candidate_weights'][name])\n"
     "            self.assertEqual(digest, hashlib.sha256((run217.TCN_DIR / name).read_bytes()).hexdigest())\n"
     "        self.assertEqual(new['source_sha256']['tcn/infer2.py'], plan['hashes']['tcn2']['infer.py'])            # byte copies of the validated inference\n"
     "        self.assertEqual(new['source_sha256']['tcn/features2.py'], plan['hashes']['tcn2']['features2.py'])\n"
     "        self.assertEqual(new['source_sha256']['tcn/features.py'], plan['hashes']['tcn2']['features.py'])\n"
     "        self.assertEqual(new['source_sha256']['pooling.py'], plan['hashes']['pooling.py'])\n"
     "        self.assertEqual(results['plan_sha256'], hashlib.sha256((REPO / 'possession-v217-plan.json').read_bytes()).hexdigest())\n"
     "        self.assertLess(plan['registered_at'], results['written_at'])\n"
     "        self.assertLess(results['written_at'], new['frozen_at'])\n"
     "        self.assertTrue(all(g['passed'] for g in results['gates'].values()) and results['selected'])\n"
     "        self.assertEqual(len(results['gates']), 7)\n"
     "        self.assertEqual(run217.TCN_WEIGHT, 0.4)\n\n"
     "    def test_release_configurations_name_existing_entry_points_manifests_and_tests(self):\n"
     "        for name, release in (('possession-release.json', 'possession-v2.17'), "),
    ("        self.assertEqual(default['steps'][3:], reserve['steps'])                             # the reserve is the ladder without the kick-off tag rule, the second model and the added players\n",
     "        self.assertEqual(default['steps'][4:], reserve['steps'])                             # the reserve is the ladder without the kick-off tag rule, the second model and the added players\n"),
    ("                     'possession/tcn/*.py -text', 'models/possession-tcn-v215.npz binary'):\n",
     "                     'possession/tcn/*.py -text', 'models/possession-tcn-v215.npz binary', 'models/possession-tcn-v217/*.npz binary'):\n"),
    ("        for name in run216.SOURCES + ('run29g.py',):\n", "        for name in run217.SOURCES + ('run29g.py',):\n"),
])
edit('tests/test_possession_final_test.py', [
    ("        # output of v2.16 is that of v2.15.\n"
     "        self.assertEqual((delivered['release'], delivered['steps'][0]['module']), ('possession-v2.16', 'possession.run216'))\n"
     "        self.assertEqual(delivered['steps'][1]['module'], 'possession.run215')\n"
     "        self.assertEqual((plan['release']['name'], plan['release']['module']),\n"
     "                         (delivered['steps'][2]['name'], delivered['steps'][2]['module']))\n",
     "        # output of v2.16 is that of v2.15. possession-v2.17 changes the members and the weight of the second model; for\n"
     "        # it the reserved match is as little untouched as for v2.15 (possession-v217-plan.json, limits).\n"
     "        self.assertEqual((delivered['release'], delivered['steps'][0]['module']), ('possession-v2.17', 'possession.run217'))\n"
     "        self.assertEqual([s['module'] for s in delivered['steps'][1:3]], ['possession.run216', 'possession.run215'])\n"
     "        self.assertEqual((plan['release']['name'], plan['release']['module']),\n"
     "                         (delivered['steps'][3]['name'], delivered['steps'][3]['module']))\n"),
])
edit('tests/test_possession_deliver.py', [
    ("[True, True, True, False, False, False, False])   # v2.16, v2.15 and v2.11k read it\n",
     "[True, True, True, True, False, False, False, False])   # v2.17, v2.16, v2.15 and v2.11k read it\n"),
])
new_variants = XPLAT or {'lost_added_eight_clock': {'sha256': 'TO-BE-RECORDED', 'path': 'v2.1', 'fill': True, 'mode': 'clock', 'moved_pieces': 8, 'pooled': True, 'added': 8771},
                         'keepers_eight_tactical_only': {'sha256': 'TO-BE-RECORDED', 'path': 'v2.1', 'fill': False, 'mode': None, 'moved_pieces': 4, 'pooled': True}}
def lit(d):
    return '{' + ', '.join(f"'{k}': {v!r}" for k, v in d.items()) + '}'
edit('tests/test_possession_crossplatform.py', [
    ("                         (possession/playerfill.py): the v2.1 path with the clock anchor and the v2.3 path\n"
     "                         without it.\n",
     "                         (possession/playerfill.py): the v2.1 path with the clock anchor and the v2.3 path\n"
     "                         without it.\n"
     "  possession.run217.run  two variants with the second model of eight networks, four of them on the extended\n"
     "                         features (possession/tcn/infer2.py, possession/tcn/features2.py): the bundle that\n"
     "                         loses players with broadcast and clock, and the goalkeeper bundle with the tactical\n"
     "                         camera only.\n"),
    ("    from possession import run29, run211, run215, run216\n", "    from possession import run29, run211, run215, run216, run217\n"),
    ("                                      'added': 4508},\n    },\n",
     "                                      'added': 4508},\n"
     "        # the two variants with the eight-member second model: recorded 2026-11-16 on Linux x86-64, identical under\n"
     "        # Python 3.10.20 / numpy 1.26.4 and Python 3.13.18 / numpy 2.5.3\n"
     f"        'lost_added_eight_clock': {lit(new_variants['lost_added_eight_clock'])},\n"
     f"        'keepers_eight_tactical_only': {lit(new_variants['keepers_eight_tactical_only'])},\n"
     "    },\n"),
    ("        if entry in (run215, run216):\n", "        if entry in (run215, run216, run217):\n"),
    ("        if entry is run216:\n", "        if entry is run216 or (entry is run217 and r['added_players'].get('used')):\n"),
    ("    one('keepers_pooled_tactical_only', keepers, False, run215, KEEPER_HALVES)\n",
     "    one('keepers_pooled_tactical_only', keepers, False, run215, KEEPER_HALVES)\n"
     "    one('keepers_eight_tactical_only', keepers, False, run217, KEEPER_HALVES)\n"),
    ("    one('lost_added_clock', lost, True, run216)\n",
     "    one('lost_added_clock', lost, True, run216)\n    one('lost_added_eight_clock', lost, True, run217)\n"),
])

# --- delivery tool: the number of synthetic variants
edit('tools/possession_deliver.py', [
    ("'same bytes as recorded on Linux x86-64 (eleven synthetic variants)'", "'same bytes as recorded on Linux x86-64 (thirteen synthetic variants)'"),
    ("('same bytes as recorded on Linux x86-64 for eight synthetic variants; not conclusive for the three '",
     "('same bytes as recorded on Linux x86-64 for nine synthetic variants; not conclusive for the four '"),
    ("diger sekiz varyant AYNI", "diger dokuz varyant AYNI"),
])
print('applied to', REPO)
