"""Run when requirements-video.txt is installed; otherwise cleanly skipped."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest

from football_video_analysis.analysis import analyze
from football_video_analysis.demo import demo_config, sample_tracks
from football_video_analysis.tracks import file_sha256
from football_video_analysis.video import render_video


@unittest.skipUnless(importlib.util.find_spec("cv2") and importlib.util.find_spec("numpy"), "optional OpenCV runtime is not installed")
class VideoTests(unittest.TestCase):
    def test_synthetic_video_round_trip_preserves_source_fps_frame_count_and_dimensions(self):
        import cv2
        data = sample_tracks()
        with tempfile.TemporaryDirectory() as temp:
            path, preview = Path(temp) / "synthetic.avi", Path(temp) / "preview.png"
            render_video(path, data, analyze(data, demo_config()), preview=preview)
            cap = cv2.VideoCapture(str(path))
            try:
                self.assertTrue(cap.isOpened())
                self.assertAlmostEqual(cap.get(cv2.CAP_PROP_FPS), 25)
                self.assertEqual(cap.get(cv2.CAP_PROP_FRAME_WIDTH), 960)
                self.assertEqual(cap.get(cv2.CAP_PROP_FRAME_HEIGHT), 640)
                actual = 0
                while cap.read()[0]:
                    actual += 1
                self.assertEqual(actual, 100)
            finally:
                cap.release()
            self.assertIsNotNone(cv2.imread(str(preview)))

    def test_video_fingerprint_mismatch_rejected(self):
        data = sample_tracks()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.avi"
            render_video(source, data, analyze(data, demo_config()))
            data["source"] = {"kind": "video", "sha256": "0" * 64}
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                render_video(Path(temp) / "output.avi", data, analyze(data, demo_config()), source_video=source)
            data["source"]["sha256"] = file_sha256(source)
            render_video(Path(temp) / "output.avi", data, analyze(data, demo_config()), source_video=source)

    def test_featureless_camera_motion_fails_safely(self):
        import numpy as np
        from football_video_analysis.inference import estimate_translation
        blank = np.zeros((100, 150, 3), dtype=np.uint8)
        shift, valid = estimate_translation(blank, blank)
        self.assertFalse(valid)
        self.assertEqual(shift, [0.0, 0.0])
