import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from football_video_analysis.__main__ import protect_inputs
from football_video_analysis.tracks import load_tracks
from football_video_analysis.video import render_video


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        # -S removes site-packages: offline functionality must be standard-library only.
        return subprocess.run([sys.executable, "-S", "-m", "football_video_analysis", *map(str, arguments)], cwd=ROOT, capture_output=True, text=True)

    def test_demo_and_cached_analysis_work_without_site_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "first", Path(temp) / "second"
            demo = self.run_cli("demo", "--out", first)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            cached = self.run_cli("analyze", "--tracks", first / "tracks.json", "--config", first / "config.json", "--out", second)
            self.assertEqual(cached.returncode, 0, cached.stderr)
            initial = json.loads((first / "summary.json").read_text())
            replay = json.loads((second / "summary.json").read_text())
            self.assertEqual(initial, replay)
            self.assertEqual(initial["control"]["status_frames"], {"observed": 77, "interpolated": 2, "carried": 2, "unknown": 19})
            self.assertEqual(initial["control"]["known_coverage_percent"], 81)
            self.assertTrue((first / "report.svg").exists())

    def test_input_collision_is_rejected_without_touching_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "summary.json"
            path.write_text("preserve me")
            with self.assertRaises(ValueError):
                protect_inputs(temp, [path])
            self.assertEqual(path.read_text(), "preserve me")

    def test_video_collision_is_rejected_before_dependency_import_or_file_write(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.avi"
            source.write_bytes(b"source must survive")
            with self.assertRaises(ValueError):
                render_video(source, {}, {}, source_video=source)
            self.assertEqual(source.read_bytes(), b"source must survive")

    def test_pickle_and_nonfinite_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cache.pkl"
            path.write_bytes(b"not loaded")
            with self.assertRaises(ValueError):
                load_tracks(path)
            path = Path(temp) / "cache.json"
            path.write_text('{"schema_version": 1, "fps": NaN}')
            with self.assertRaises(ValueError):
                load_tracks(path)

    def test_bad_input_returns_actionable_error(self):
        result = self.run_cli("analyze", "--tracks", "absent.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
