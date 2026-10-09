"""Command-line entry point. Offline commands do not import inference libraries."""

import argparse
from pathlib import Path
import sys
from .analysis import analyze
from .config import load_config
from .demo import demo_config, sample_tracks
from .report import write_reports
from .tracks import load_tracks, write_json


def protect_inputs(output_directory, inputs):
    output = Path(output_directory).resolve()
    if output.exists() and not output.is_dir():
        raise ValueError("Output must be a directory")
    generated = {output / name for name in ("tracks.json", "config.json", "summary.json", "control.csv", "movement.csv", "report.svg", "annotated.avi", "synthetic.avi", "preview.png", "dashboard.png")}
    for value in inputs:
        if value and Path(value).resolve() in generated:
            raise ValueError("An output file would overwrite an input; choose another output directory")


def parser():
    root = argparse.ArgumentParser(description="Football video analysis: safe JSON replay and a synthetic offline demo")
    sub = root.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run deterministic synthetic tracking without weights or footage")
    demo.add_argument("--out", default="outputs/demo")
    demo.add_argument("--render-video", action="store_true", help="Also write an OpenCV MJPG AVI and preview PNG")
    cached = sub.add_parser("analyze", help="Analyze a validated JSON tracking cache, without loading a model")
    cached.add_argument("--tracks", required=True)
    cached.add_argument("--config")
    cached.add_argument("--out", default="outputs/analysis")
    cached.add_argument("--video", help="Optional source video for rendering; SHA-256 must match the cache")
    inference = sub.add_parser("infer", help="Run optional YOLO + ByteTrack on a trusted local video and model")
    inference.add_argument("--video", required=True)
    inference.add_argument("--model", required=True)
    inference.add_argument("--config")
    inference.add_argument("--out", default="outputs/inference")
    inference.add_argument("--max-frames", type=int, default=300)
    inference.add_argument("--camera-motion", action="store_true", help="Estimate cumulative translation; no zoom/rotation/cut support")
    inference.add_argument("--device", default="cpu")
    inference.add_argument("--render-video", action="store_true")
    return root


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        protect_inputs(arguments.out, [getattr(arguments, name, None) for name in ("tracks", "config", "video", "model")])
        if arguments.command == "demo":
            data, settings = sample_tracks(), demo_config()
        else:
            settings = load_config(arguments.config)
            if arguments.command == "analyze":
                data = load_tracks(arguments.tracks)
            else:
                from .inference import infer_tracks
                data = infer_tracks(arguments.video, arguments.model, settings, arguments.max_frames, arguments.camera_motion, arguments.device)
        result = analyze(data, settings)
        out = Path(arguments.out)
        # Rendering validates metadata/fingerprints before report files are written.
        if getattr(arguments, "render_video", False) or (arguments.command == "analyze" and arguments.video):
            from .video import render_dashboard, render_video
            render_video(out / ("synthetic.avi" if data["source"]["kind"] == "synthetic" else "annotated.avi"),
                         data, result, getattr(arguments, "video", None), out / "preview.png")
            render_dashboard(out / "dashboard.png", data, result)
        write_reports(out, data, result)
        if arguments.command != "analyze":
            write_json(out / "tracks.json", data)
            write_json(out / "config.json", settings.to_dict())
        summary = result["summary"]
        print(f"Analyzed {summary['frame_count']} {summary['source_kind']} frames at {summary['fps']:g} FPS; {summary['duration_seconds']:.2f} s")
        print(f"Known heuristic control coverage: {summary['control']['known_coverage_percent']:.1f}%")
        print(f"Reports: {out.resolve()}")
        return 0
    except (ValueError, OSError, RuntimeError, TypeError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
