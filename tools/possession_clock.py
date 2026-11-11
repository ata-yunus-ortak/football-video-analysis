"""Automatic clock readings of one video for possession v2.5 (run in the separate OCR environment).

    python -m tools.possession_clock --video <bundle>/tactical/BAR-ATH_tactical.mp4 --out <new folder outside the repo>
    python -m tools.possession_clock --video <bundle>/broadcast/BAR-ATH_broadcast.mp4 --out <new folder>

Wraps tools/clock_observations.py (experiment S002) with the parameters registered in
sync-review-plan.json (one key frame every 5 s, top-left 45% x 22% of the picture, confidence 0.8).
Nothing is tuned on the video; frames are read in memory only and never saved. The output folder
(observations.jsonl, registration.json, summary.json) is passed to possession.run25.
Environment: python -m pip install -r requirements-sync-lock.txt (separate from the possession env).
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from .clock_observations import run as observe

REPO = Path(__file__).resolve().parents[1]


def file_sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                return h.hexdigest()
            h.update(block)


def main(video, out):
    plan = json.loads((REPO / 'sync-review-plan.json').read_text(encoding='utf-8'))
    spec = {'purpose': 'automatic_read_only_synchronization',
            'parameters_selected_on_provided_fixture': False, 'human_anchors_used': False,
            'fixture_kind': 'provided_fixture_review',
            'source_provenance': {'plan': 'sync-review-plan.json', 'plan_version': plan['version'],
                                  'used_by': 'possession.run25 (clock-anchored broadcast alignment)'},
            'parameters': plan['clock_ocr'], 'video_sha256': file_sha256(video)}
    with tempfile.TemporaryDirectory() as d:
        spec_path = Path(d) / 'clock-spec.json'
        spec_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
        return observe(video, spec_path, out)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--video', required=True)
    p.add_argument('--out', required=True, help='new folder outside the repository')
    a = p.parse_args()
    print(json.dumps(main(a.video, a.out), indent=2))
