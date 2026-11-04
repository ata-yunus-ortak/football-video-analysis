import tempfile
import unittest
from pathlib import Path
from tools.smart_tag_view import load_tags


class SmartTagTests(unittest.TestCase):
    def parse(self, xml, fps=25., frames=250):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'synthetic.xml'
            path.write_text(xml, encoding='utf-8')
            return load_tags(path, fps, frames)

    def test_overlapping_events_duplicate_fields_and_unrecognized_tags_preserved(self):
        result = self.parse('''<file><ALL_INSTANCES>
        <instance><ID>20</ID><start>3</start><end>5</end><code>SET PIECES</code>
        <label><group>Team</group><text>N/A</text></label></instance>
        <instance><ID>21</ID><start>1</start><end>4</end><code>BUILD UP</code>
        <label><group>Side</group><text>Left</text></label>
        <label><group>Side</group><text>Central</text></label>
        <label><group>Unknown Group</group><text>Örnek</text></label>
        <custom>retained</custom></instance></ALL_INSTANCES></file>''')
        self.assertEqual(result['count'], 2)
        first, second = result['events']
        self.assertEqual(first['id'], 1)
        self.assertEqual(first['source_id'], '21')
        self.assertEqual(first['tags']['Side'], ['Left', 'Central'])
        self.assertEqual(first['tags']['Unknown Group'], ['Örnek'])
        self.assertEqual(first['extras'], [{'name': 'custom', 'value': 'retained'}])
        self.assertEqual((first['start_frame'], first['end_frame']), (25, 100))
        self.assertLess(second['start_frame'], first['end_frame'])
        self.assertEqual(second['tags']['Team'], ['N/A'])
        self.assertFalse(result['human_accuracy_evaluated'])

    def test_original_out_of_bounds_and_zero_length_intervals_not_silently_rewritten(self):
        result = self.parse('''<file><instance><start>-1</start><end>11</end><code>X</code></instance>
        <instance><start>2</start><end>2</end><code>Z</code></instance></file>''')
        self.assertTrue(result['events'][0]['outside_reference'])
        self.assertEqual(result['events'][0]['start_s'], -1.)
        self.assertEqual(result['events'][1]['duration_s'], 0.)
        self.assertEqual(result['events'][1]['tags'], {})

    def test_invalid_clock_and_intervals_rejected_and_empty_file_supported(self):
        for xml in ('<file><instance><start>nan</start><end>3</end></instance></file>',
                    '<file><instance><start>5</start><end>3</end></instance></file>'):
            with self.assertRaises(ValueError): self.parse(xml)
        with self.assertRaises(ValueError): self.parse('<file/>', fps=0)
        self.assertEqual(self.parse('<file/>')['count'], 0)


if __name__ == '__main__':
    unittest.main()
