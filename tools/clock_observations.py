"""Local-only automatic scoreboard readings with immutable input/config provenance.

Video crops are consumed in memory and never saved or uploaded. Synthetic tests
and configuration freeze must precede provided-fixture review inference. No
threshold selection, training, human anchors or possession predictions occur.
"""
import argparse
from dataclasses import dataclass
import importlib.metadata
import json
import math
from pathlib import Path
import time
from development.clock_alignment import observe_tokens
from .metrica_data import external_output, sha256


@dataclass(frozen=True)
class ClockOCRConfig:
    sample_interval_s: float
    roi: list
    min_confidence: float
    threads: int

    def __post_init__(self):
        if (not math.isfinite(self.sample_interval_s) or self.sample_interval_s <= 0
                or not math.isfinite(self.min_confidence) or not 0 < self.min_confidence <= 1
                or type(self.threads) is not int or self.threads < 1
                or len(self.roi) != 4 or not all(math.isfinite(v) for v in self.roi)
                or not 0 <= self.roi[0] < self.roi[2] <= 1
                or not 0 <= self.roi[1] < self.roi[3] <= 1):
            raise ValueError('Explicit normalized ROI, clock confidence and sampling required')


class LocalClockOCR:
    def __init__(self, cfg):
        from rapidocr_onnxruntime import RapidOCR
        self.engine = RapidOCR(intra_op_num_threads=cfg.threads, inter_op_num_threads=1,
                               det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False,
                               det_limit_type='max', det_limit_side_len=960)
        self.cfg = cfg

    def __call__(self, bgr):
        height, width = bgr.shape[:2]
        x0, y0, x1, y1 = self.cfg.roi
        crop = bgr[math.floor(y0 * height):math.ceil(y1 * height),
                   math.floor(x0 * width):math.ceil(x1 * width)]
        result, _ = self.engine(crop, use_cls=False)
        return [{'text': text, 'confidence': float(score)} for _, text, score in (result or [])]


def keyframe_samples(video, interval):
    import av
    with av.open(str(video)) as container:
        stream = container.streams.video[0]
        fps = float(stream.average_rate or 0)
        if not math.isfinite(fps) or fps <= 0 or stream.start_time is None:
            raise ValueError('Video FPS and presentation-time origin are required')
        origin = float(stream.start_time * stream.time_base)
        stream.thread_type = 'AUTO'
        stream.codec_context.skip_frame = 'NONKEY'
        next_time, previous = 0., -math.inf
        for frame in container.decode(stream):
            if frame.pts is None:
                raise ValueError('Missing frame presentation timestamp')
            timestamp = float(frame.pts * frame.time_base) - origin
            if timestamp <= previous:
                raise ValueError('Non-increasing frame presentation timestamps')
            previous = timestamp
            if timestamp + 1e-6 < next_time:
                continue
            index = round(timestamp * fps)
            if abs(index - timestamp * fps) > .25:
                raise ValueError('CFR frame/time contract not satisfied; no invented ATD frame')
            yield index, timestamp, fps, frame.to_ndarray(format='bgr24')
            next_time = timestamp + interval


def runtime_provenance():
    import rapidocr_onnxruntime
    root = Path(rapidocr_onnxruntime.__file__).parent
    return {'packages': {name: importlib.metadata.version(name) for name in
                         ('rapidocr-onnxruntime', 'onnxruntime', 'opencv-python', 'numpy', 'av')},
            'bundled_model_sha256': {p.name: sha256(p) for p in root.rglob('*.onnx')},
            'engine_license': 'Apache-2.0',
            'source_url': 'https://github.com/RapidAI/RapidOCR',
            'distribution_url': 'https://pypi.org/project/rapidocr-onnxruntime/1.4.4/'}


def run(video, config_path, out, *, factory=LocalClockOCR, frame_reader=keyframe_samples,
        provenance=runtime_provenance):
    video, config_path = Path(video).resolve(), Path(config_path).resolve()
    spec = json.loads(config_path.read_text(encoding='utf-8'))
    if (spec.get('purpose') != 'automatic_read_only_synchronization'
            or spec.get('parameters_selected_on_provided_fixture') is not False
            or spec.get('human_anchors_used') is not False
            or not spec.get('source_provenance')
            or spec.get('fixture_kind') not in ('synthetic_fixture', 'permitted_external_video', 'provided_fixture_review')):
        raise ValueError('Registered automatic review inference without supplied-fixture selection required')
    cfg = ClockOCRConfig(**spec['parameters'])
    if sha256(video) != spec.get('video_sha256'):
        raise ValueError('Video content does not match registration')
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[1]
    sources = [Path(__file__), repo / 'development' / 'clock_alignment.py']
    source_hashes = {p.relative_to(repo).as_posix(): sha256(p) for p in sources}
    registration = {**spec, 'config_sha256': sha256(config_path), 'source_sha256': source_hashes,
                    'video_path': str(video), 'video_bytes': video.stat().st_size,
                    'video_mtime_ns': video.stat().st_mtime_ns,
                    'runtime': provenance(), 'selected_release': False,
                    'frames_uploaded': 0, 'images_saved': 0, 'before_decode': True}
    (out / 'registration.json').write_text(json.dumps(registration, indent=2), encoding='utf-8')
    engine = factory(cfg)
    started, count, accepted, fps_seen = time.monotonic(), 0, 0, None
    previous_time, previous_index = -math.inf, -1
    with (out / 'observations.jsonl').open('x', encoding='utf-8') as target:
        for index, timestamp, fps, bgr in frame_reader(video, cfg.sample_interval_s):
            if (not math.isfinite(timestamp) or timestamp < 0 or not math.isfinite(fps) or fps <= 0
                    or timestamp <= previous_time or type(index) is not int or index <= previous_index
                    or fps_seen is not None and fps != fps_seen):
                raise ValueError('Invalid/changing source clock')
            fps_seen = fps
            previous_time, previous_index = timestamp, index
            tokens = engine(bgr)
            observed = observe_tokens(tokens, cfg.min_confidence)
            row = {**observed, 'video_time_s': timestamp, 'source_frame': index,
                   'source_kind': 'automatic_clock_observation', 'fps': fps,
                   'tokens': tokens, 'human_annotated': False}
            target.write(json.dumps(row, allow_nan=False) + '\n')
            count += 1
            accepted += observed['clock_s'] is not None
            if count % 100 == 0:
                target.flush()
                print(json.dumps({'samples': count, 'video_time_s': timestamp,
                                  'elapsed_s': round(time.monotonic() - started, 1)}), flush=True)
    if count == 0:
        raise ValueError('No video keyframes sampled')
    if any(sha256(repo / name) != digest for name, digest in source_hashes.items()):
        raise ValueError('Clock source changed during observation; no complete result')
    if video.stat().st_size != registration['video_bytes'] or video.stat().st_mtime_ns != registration['video_mtime_ns']:
        raise ValueError('Video changed during automatic reading; no complete result')
    summary = {'samples': count, 'observed_clock_samples': accepted, 'fps': fps_seen,
               'elapsed_s': time.monotonic() - started, 'source_read_complete': True,
               'accuracy_evaluated': False, 'possession_inferred': False, 'images_saved': 0}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.video, args.config, args.out), indent=2), flush=True)
