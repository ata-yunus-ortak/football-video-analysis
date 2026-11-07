import unittest
import json
import tempfile
from pathlib import Path
from tools.ball_detector_data import safe_member, usable_boxes, export
from tools.metrica_data import sha256


class BallDetectorDataTests(unittest.TestCase):
    def test_reject_traversal_and_absolute_paths(self):
        for p in ('../secret', '/secret', 'C:/secret', 'a\\secret'):
            with self.assertRaises(ValueError):
                safe_member(Path('.'), p)

    def test_missing_ball_is_not_negative(self):
        image = {'is_labeled': True, 'width': 100, 'height': 50}
        self.assertEqual(usable_boxes(image, [], 4), ([], 'unknown_ball'))

    def test_invalid_or_ignored_boxes_not_silently_clipped(self):
        image = {'is_labeled': True, 'width': 100, 'height': 50}
        a = {'category_id': 4, 'bbox_image': {'x': 95, 'y': 1, 'w': 10, 'h': 10}}
        self.assertEqual(usable_boxes(image, [a], 4)[1], 'invalid_box')
        a['bbox_image']['x'] = 5
        self.assertEqual(usable_boxes(image, [a], 4), ([[5,1,10,10]], 'included'))
        image['ignore_regions_x'] = [[1,2,3]]
        self.assertEqual(usable_boxes(image, [a], 4)[1], 'unknown_or_ignore')

    def test_export_keeps_games_separate_and_verifies_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); clips = []
            plan = {'version': 'synthetic', 'provided_fixture_used': False,
                    'dataset': 'SoccerNet/SN-GSR-2024', 'archive': 'train.zip',
                    'splits': {'train': ['4'], 'valid': ['6'], 'test': ['9']}}
            def write(p, r):
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(r))
            for game in ('4', '6', '9'):
                study = root/game; sample = study/'sample-v2'
                # Synthetic byte payload tests the copy/hash contract, not JPEG decoding.
                image = sample/'sample'/'clip'/'000001.jpg'
                image.parent.mkdir(parents=True); image.write_bytes(game.encode())
                label = image.parent/'Labels-GameState.json'
                write(label, {'images': [{'image_id': 1, 'file_name': image.name,
                    'is_labeled': True, 'width': 100, 'height': 100}],
                    'categories': [{'id': 4, 'name': 'ball'}],
                    'annotations': [{'image_id': 1, 'category_id': 4,
                        'bbox_image': {'x': 10, 'y': 10, 'w': 5, 'h': 5}}]})
                write(sample/'before-access.json', {'plan': plan})
                write(sample/'manifest.json', {'complete': True, 'acquired_files': [
                    {'member': 'clip/'+p.name, 'sha256': sha256(p)} for p in (image,label)]})
                clips.append({'id': game, 'source_game_id': game, 'study': str(study)})
            write(root/'plan.json', plan); write(root/'gallery.json', {'clips': clips})
            report = export(root/'gallery.json', root/'plan.json', root/'out')
            self.assertEqual([s['images'] for s in report['splits'].values()], [1,1,1])
            self.assertEqual({r['split']: r['game'] for r in report['images']},
                             {'train': '4', 'valid': '6', 'test': '9'})
            image.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Changed image'):
                export(root/'gallery.json', root/'plan.json', root/'bad-out')
