"""Acquire the registered external samples without accessing competition data."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path, spec):
    path = Path(path)
    size = path.stat().st_size
    if size != spec["bytes"]:
        raise ValueError(f"External file size differs: {path.name}")
    digest = hashlib.sha1(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != spec["git_blob_sha1"]:
        raise ValueError(f"Pinned Git blob differs: {path.name}")
    return sha256(path)


def validate_plan(plan):
    if (plan["repository"] != "https://github.com/metrica-sports/sample-data"
            or not re.fullmatch(r"[0-9a-f]{40}", plan["commit"])
            or plan["provided_fixture_used"] is not False):
        raise ValueError("A pinned external Metrica sample plan is required")
    if plan["fps"] != 25.0 or plan["pitch_m"] != [105.0, 68.0]:
        raise ValueError("Unsupported sample clock or pitch")
    fixtures = plan["fixtures"]
    if [(item["id"], item["split"]) for item in fixtures] != [
            ("metrica-sample-1", "train"), ("metrica-sample-2", "validation")]:
        raise ValueError("Registered fixture split differs")
    for game, fixture in enumerate(fixtures, 1):
        expected = {
            "events": f"Sample_Game_{game}_RawEventsData.csv",
            "home": f"Sample_Game_{game}_RawTrackingData_Home_Team.csv",
            "away": f"Sample_Game_{game}_RawTrackingData_Away_Team.csv",
        }
        if set(fixture["files"]) != set(expected):
            raise ValueError("Exactly events/home/away files are required")
        for role, spec in fixture["files"].items():
            path = PurePosixPath(spec["path"])
            if (str(path) != f"data/Sample_Game_{game}/{expected[role]}"
                    or not re.fullmatch(r"[0-9a-f]{40}", spec["git_blob_sha1"])
                    or type(spec["bytes"]) is not int or spec["bytes"] <= 0):
                raise ValueError("Invalid pinned sample file")


def external_output(path):
    path = Path(path).resolve()
    repo = Path(__file__).resolve().parents[1]
    if path == repo or repo in path.parents:
        raise ValueError("External data and generated outputs must stay outside the repository")
    return path


def run(plan_path, out):
    plan_path = Path(plan_path)
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    validate_plan(plan)
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "plan.json").write_bytes(plan_bytes)
    before = {
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "before_tracking_and_event_download": True,
        "provided_fixture_used": False,
        "purpose": "coverage audit only; no candidate selection",
    }
    (out / "before-access.json").write_text(json.dumps(before, indent=2), encoding="utf-8")

    def download(fixture, role, spec):
        url = ("https://raw.githubusercontent.com/metrica-sports/sample-data/"
               + plan["commit"] + "/" + spec["path"])
        path = out / "raw" / fixture["id"] / (role + ".csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".csv.part")
        request = urllib.request.Request(url, headers={"User-Agent": "Football-External-Data-Audit"})
        with urllib.request.urlopen(request, timeout=45) as response, temporary.open("xb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        content_hash = verify_file(temporary, spec)
        temporary.rename(path)
        print(json.dumps({"downloaded": fixture["id"], "role": role, "bytes": spec["bytes"]}), flush=True)
        return path.relative_to(out).as_posix(), {"url": url, "sha256": content_hash, **spec}

    records = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(download, fixture, role, spec)
                   for fixture in plan["fixtures"] for role, spec in fixture["files"].items()]
        for future in concurrent.futures.as_completed(futures):
            key, value = future.result()
            records[key] = value
    manifest = {"plan_sha256": before["plan_sha256"], "files": records}
    (out / "download-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="dead-ball-data-plan.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.plan, args.out)
