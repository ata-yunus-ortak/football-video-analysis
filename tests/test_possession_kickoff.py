"""Synthetic tests of possession/kickoff.py (dead ball before a half's Smart Tagging kick-off tag).
No match data: the tagging files and submissions are generated here."""
import csv
import hashlib
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from possession import kickoff

BLOCKS = [(1000, 8999), (12000, 19999)]
N = 21000


def tagging(instances):
    """instances: (start, end, code, [(group, text), ...]); start None omits the element."""
    parts = ['<?xml version="1.0" encoding="utf-8"?>', '<file><ALL_INSTANCES>']
    for i, (start, end, code, labels) in enumerate(instances):
        parts.append(f'<instance><ID>{i}</ID>')
        if start is not None:
            parts.append(f'<start>{start}</start>')
        parts.append(f'<end>{end}</end><code>{code}</code>')
        parts += [f'<label><group>{g}</group><text>{t}</text></label>' for g, t in labels]
        parts.append('</instance>')
    parts.append('</ALL_INSTANCES></file>')
    return '\n'.join(parts)


def kick(start, text='Kick Off (Start)', code='SET PIECES', team='N/A'):
    return (start, start + 5 if isinstance(start, (int, float)) else 0, code, [('Team', team), ('Type', text)])


def reference(labels, blocks, path):
    """The rule as committed on branch mtah-possession (commit 4b32747, possession/predict.py), kept verbatim."""
    FPS = 25
    starts = []
    for instance in ET.parse(path).iter("instance"):
        tags = {label.findtext("group"): (label.findtext("text") or "")
                for label in instance.findall("label")}
        if ((instance.findtext("code") or "").strip().lower() == "set pieces"
                and tags.get("Type", "").strip().lower() == "kick off (start)"):
            starts.append(int(round(float(instance.findtext("start")) * FPS)))
    kickoffs = sorted(starts)
    out = labels.copy()
    for first, last in blocks:
        block = out[first:last + 1]
        inside = [k for k in kickoffs if first <= k <= last]
        if inside and inside[0] - first < 10 * 60 * FPS:
            block[:inside[0] - first] = "D"
    return out


def random_labels(rng, n=N):
    out = np.empty(n, '<U1')
    i = 0
    while i < n:
        length = int(rng.integers(5, 400))
        out[i:i + length] = rng.choice(['H', 'A', 'D'])
        i += length
    return out


def write_run(folder, labels):
    folder = Path(folder)
    with open(folder / 'submission.csv', 'x', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['frame', 'label'])
        w.writerows(zip(range(len(labels)), labels.tolist()))
    (folder / 'run.json').write_text(json.dumps({'rows': len(labels), 'submission_sha256': 'before',
                                                 'label_counts_in_play_blocks': {}, 'possession_spells_in_play_blocks': -1}))


def read_labels(folder):
    with open(Path(folder) / 'submission.csv', encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f))
    return rows[0], np.array([r[1] for r in rows[1:]], dtype='<U1')


class KickoffTags(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def xml(self, instances, name='tags.xml'):
        p = self.dir / name
        p.write_text(tagging(instances), encoding='utf-8')
        return p

    def test_reads_only_kickoff_start_set_pieces(self):
        p = self.xml([kick(40.0), kick(480.04, text=' kick off (start) ', code=' Set Pieces '),
                      kick(100.0, text='Kick Off'), kick(120.0, text='Free Kick'),
                      (130.0, 135.0, 'BUILD UP', [('Type', 'Kick Off (Start)')]),
                      (140.0, 145.0, 'SET PIECES', [('Team', 'Kick Off (Start)')]),
                      kick(None), kick('abc'), kick('nan')])
        self.assertEqual(kickoff.kickoff_tag_starts(p, 25), [1000, 12001])

    def test_start_frame_rounding(self):
        p = self.xml([kick(4000.04), kick(1234.56), kick(0.02), kick(0.06)])
        self.assertEqual(kickoff.kickoff_tag_starts(p, 25), [0, 2, 30864, 100001])   # round half to even, as int(round(x))

    def test_rule_equals_the_committed_reference(self):
        rng = np.random.default_rng(20261113)
        for case in range(300):
            inst = []
            for _ in range(int(rng.integers(0, 6))):
                t = float(np.round(rng.uniform(0, N / 25), int(rng.integers(0, 4))))
                inst.append(kick(t, text=str(rng.choice(['Kick Off (Start)', 'kick off (start)', 'Kick Off', 'Corner Kick'])),
                                 code=str(rng.choice(['SET PIECES', 'Set Pieces', 'BUILD UP']))))
            p = self.xml(inst, f'case{case}.xml')
            labels = random_labels(rng)
            blocks = BLOCKS if case % 3 else [(0, 16000), (16500, N - 1)]      # second layout: blocks longer than ten minutes
            new, changed, used = kickoff.dead_before_kickoff(labels, blocks, kickoff.kickoff_tag_starts(p, 25), 25)
            ref = reference(labels, blocks, p)
            self.assertTrue(np.array_equal(new, ref), case)
            self.assertEqual(sum(changed), int(np.sum(labels != ref)), case)

    def test_first_tag_inside_the_block_and_the_ten_minute_bound(self):
        labels = np.full(40000, 'H', '<U1')
        blocks = [(1000, 30000)]
        for k, expect in ((1000, 0), (1001, 1), (15999, 14999), (16000, None), (20000, None), (999, None), (30001, None)):
            new, changed, used = kickoff.dead_before_kickoff(labels, blocks, [k], 25)
            if expect is None:
                self.assertEqual((used, changed), ([False], [0]), k)
                self.assertTrue(np.array_equal(new, labels), k)
            else:
                self.assertEqual((used, changed), ([True], [expect]), k)
                self.assertTrue((new[1000:k] == 'D').all() and (new[k:] == 'H').all() and (new[:1000] == 'H').all(), k)
        # several tags: only the first one inside the block counts, even if a later one is closer to ten minutes
        new, changed, used = kickoff.dead_before_kickoff(labels, blocks, [500, 3000, 9000], 25)
        self.assertEqual(changed, [2000])
        # a first tag beyond the bound is not replaced by nothing else
        new, changed, used = kickoff.dead_before_kickoff(labels, blocks, [500, 17000, 29000], 25)
        self.assertEqual((used, changed), ([False], [0]))

    def test_input_labels_are_not_modified(self):
        labels = np.full(5000, 'A', '<U1')
        before = labels.copy()
        kickoff.dead_before_kickoff(labels, [(100, 4000)], [900], 25)
        self.assertTrue(np.array_equal(labels, before))

    def test_submission_rewritten_and_recorded(self):
        rng = np.random.default_rng(7)
        labels = random_labels(rng)
        labels[12000:12600] = 'H'
        write_run(self.dir, labels)
        p = self.xml([kick(40.0), kick(504.0)])                # frames 1000 (block start: nothing to change) and 12600
        rec = kickoff.apply_to_submission(self.dir, p, BLOCKS, 25)
        header, new = read_labels(self.dir)
        self.assertEqual(header, ['frame', 'label'])
        self.assertEqual(len(new), N)
        self.assertTrue((new[12000:12600] == 'D').all())
        keep = np.r_[0:12000, 12600:N]
        self.assertTrue(np.array_equal(new[keep], labels[keep]))
        self.assertEqual(rec['used_in_block'], [True, True])
        self.assertEqual(rec['frames_changed_in_block'], [0, 600])
        self.assertEqual(rec['status'], 'applied')
        raw = (self.dir / 'submission.csv').read_bytes()
        self.assertNotIn(b'\r', raw)
        self.assertTrue(raw.endswith(b'\n') and not raw.endswith(b'\n\n'))
        report = json.loads((self.dir / 'run.json').read_text())
        self.assertEqual(report['submission_sha256'], hashlib.sha256(raw).hexdigest())
        graded = np.zeros(N, bool)
        graded[1000:9000] = True
        graded[12000:20000] = True
        self.assertEqual(report['label_counts_in_play_blocks'], {k: int(np.sum(new[graded] == k)) for k in 'HADX'})
        spells = sum(int(np.sum(np.r_[True, new[a:b + 1][1:] != new[a:b + 1][:-1]] & np.isin(new[a:b + 1], ('H', 'A')))) for a, b in BLOCKS)
        self.assertEqual(report['possession_spells_in_play_blocks'], spells)
        self.assertEqual(report['kickoff_rule'], rec)
        self.assertEqual(report['rows'], N)

    def test_without_a_usable_file_the_submission_is_untouched(self):
        labels = random_labels(np.random.default_rng(3))
        cases = {'missing': self.dir / 'absent.xml'}
        broken = self.dir / 'broken.xml'
        broken.write_text('<file><ALL_INSTANCES><instance>', encoding='utf-8')
        cases['broken'] = broken
        cases['no tag'] = self.xml([kick(100.0, text='Corner Kick')], 'none.xml')
        cases['late tag'] = self.xml([kick(12000 / 25 + 601)], 'late.xml')
        for name, path in cases.items():
            folder = self.dir / name.replace(' ', '_')
            folder.mkdir()
            write_run(folder, labels)
            before = (folder / 'submission.csv').read_bytes()
            rec = kickoff.apply_to_submission(folder, path, BLOCKS, 25)
            self.assertEqual((folder / 'submission.csv').read_bytes(), before, name)
            self.assertEqual(rec['used_in_block'], [False, False], name)
            self.assertIn('not applied', rec['status'], name)
            report = json.loads((folder / 'run.json').read_text())
            self.assertEqual(report['submission_sha256'], 'before', name)
            self.assertEqual(report['kickoff_rule'], rec, name)

    def test_unexpected_submission_layout_is_refused(self):
        (self.dir / 'submission.csv').write_text('frame,label\n0,H\n2,A\n', encoding='utf-8')
        (self.dir / 'run.json').write_text('{}')
        with self.assertRaises(ValueError):
            kickoff.apply_to_submission(self.dir, self.xml([kick(0.0)]), [(0, 1)], 25)

    def test_no_frame_number_of_a_match_in_the_source(self):
        source = Path(kickoff.__file__).read_text(encoding='utf-8')
        self.assertEqual(re.findall(r'\d{4,}', source.replace('4b32747', '')), ['2026'])


if __name__ == '__main__':
    unittest.main()
