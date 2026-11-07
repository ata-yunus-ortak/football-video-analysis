import json
from pathlib import Path
import tempfile
import unittest

from tools.vision_local_demo import external_settings


class LocalDemoSettingsTests(unittest.TestCase):
    def test_supplied_or_incomplete_runs_cannot_supply_settings(self):
        for supplied, processed in [(True, 50), (False, 49)]:
            with self.subTest(supplied=supplied, processed=processed), tempfile.TemporaryDirectory() as root:
                folder = Path(root)
                registration = {
                    'provided_fixture_used': supplied,
                    'config': {'fixture': {'source_kind': 'permitted_external_video',
                                          'provided_fixture_used': False}, 'max_frames': 50}}
                (folder / 'registration.json').write_text(json.dumps(registration))
                (folder / 'summary.json').write_text(json.dumps({'processed_frames': processed}))
                with self.assertRaises(ValueError):
                    external_settings(folder)
