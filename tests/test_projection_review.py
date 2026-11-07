import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import numpy as np
from development.homography import FrameHomographies
from tools.source_clock_audit import check_clock, fingerprint
from tools.tracking_viewer import Tracking, projected_players, bound_clock_audit


class ProjectionReviewTests(unittest.TestCase):
    def info(self):
        return {'fps': 25., 'declared_frames': 3, 'packet_frames': 3,
                'packet_pts_present': True, 'packet_pts_regular': True, 'first_pts_s': 0.}

    def test_native_bases_and_extra_tracking_tail_never_shift_the_video(self):
        result = check_clock(self.info(), 25, 4, 4)
        self.assertTrue(result['structural_clock_compatible'])
        self.assertEqual(result['common_frames'], 3)
        self.assertEqual(result['unmatched_tracking_tail'], 1)
        self.assertFalse(result['independent_image_alignment_validated'])
        for name, value in [('fps', 30), ('packet_pts_regular', False), ('first_pts_s', .04), ('declared_frames', 2)]:
            info = dict(self.info(), **{name: value})
            with self.subTest(name=name): self.assertFalse(check_clock(info, 25, 3, 3)['structural_clock_compatible'])
        self.assertFalse(check_clock(self.info(), 25, 5, 5)['structural_clock_compatible'])

    def test_projection_preserves_frame_identity_and_never_projects_ball_or_invalid_matrix(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'homography.csv'
            with path.open('w', newline='') as stream:
                writer = csv.writer(stream);writer.writerow(FrameHomographies.COLUMNS)
                for frame, valid in enumerate((1, 0)):
                    writer.writerow([frame, 1000, 0, 0, 0, 500, 0, 0, 0, 1, 0, valid])
            tracking = Tracking.demo();tracking.data = tracking.data[:3]
            tracking.data[:, :, :2] = np.nan
            tracking.data[:, 0, :2] = [.5, .25]
            geometry = FrameHomographies(path)
            result = projected_players(tracking, geometry, 0)
            self.assertEqual(result['players_px'][0], [500., 125.])
            self.assertEqual(len(result['players_px']), len(tracking.objects) - 1)
            self.assertEqual(result['atd_record'], 1)
            self.assertFalse(result['ball_projected'])
            self.assertTrue(all(row == [None, None] for row in projected_players(tracking, geometry, 1)['players_px']))
            self.assertIsNone(projected_players(tracking, geometry, 2))

    def test_source_fingerprints_prevent_reusing_another_camera_clock(self):
        with tempfile.TemporaryDirectory() as root:
            files = {key: Path(root) / key for key in ('meta', 'tracking', 'homography', 'video')}
            for path in files.values(): path.write_bytes(b'synthetic')
            tracking = Tracking.demo();tracking.data = tracking.data[:3]
            tracking.source_paths = {key: str(files[key].resolve()) for key in ('meta', 'tracking')}
            report = check_clock(self.info(), tracking.fps, 3, 3)
            report['sources'] = {key: fingerprint(path) for key, path in files.items()}
            path = Path(root) / 'report.json';path.write_text(json.dumps(report))
            self.assertTrue(bound_clock_audit(path, tracking, files['video'], files['homography'])['available'])
            files['video'].write_bytes(b'other-source')
            with self.assertRaises(ValueError): bound_clock_audit(path, tracking, files['video'], files['homography'])

    @unittest.skipUnless(shutil.which('node'), 'Optional Node runtime for browser math')
    def test_letterboxing_dpr_and_outside_image_points(self):
        source = Path(__file__).resolve().parents[1] / 'viewer/tracking-projection.js'
        script = "const fs=require('fs'),vm=require('vm'),assert=require('assert');const scope={window:{}};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),scope);const p=scope.window.TrackingProjectionMath.contain;assert.deepStrictEqual(Array.from(p([960,540],1920,1080,1000,800)),[500,400]);assert.deepStrictEqual(Array.from(p([960,540],1920,1080,2000,1600)),[1000,800]);assert.strictEqual(p([1920,10],1920,1080,1000,800),null);assert.strictEqual(p([null,10],1920,1080,1000,800),null);assert.strictEqual(p([20,10],0,1080,1000,800),null);"
        subprocess.run([shutil.which('node'), '-e', script, str(source)], check=True, capture_output=True)
