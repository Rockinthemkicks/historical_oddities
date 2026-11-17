"""
Automated technical checks on a rendered MP4, using ffprobe.

Catches the failure modes this pipeline has hit before: unplayable files
(missing "moov" atom), missing audio, wrong dimensions/aspect ratio, and
renders that silently came out much shorter or longer than the narration.

Usage from Python:
    report = check_video("out/x/final_video.mp4", expected_size=(1080, 1920),
                         expected_duration=92.4)
    if not report["passed"]: ...

Or from the command line:
    python3 -m modules.qc out/x/final_video.mp4 --size 1080x1920 --duration 92.4
"""
import argparse
import json
import os
import subprocess
import sys


def probe(path):
    """Returns ffprobe's JSON (format + streams) for `path`, or raises RuntimeError."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)


def check_video(path, expected_size=None, expected_duration=None,
                duration_tolerance=1.0, require_audio=True):
    """
    Runs every check and returns:
      {"path", "passed": bool, "checks": [{"name", "passed", "detail"}], "info": {...}}
    Never raises for a bad video -- failures are reported in the result.
    """
    checks = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "passed": bool(ok), "detail": detail})

    info = {}
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        add("file_exists", False, "missing or empty file")
        return {"path": path, "passed": False, "checks": checks, "info": info}
    add("file_exists", True, f"{os.path.getsize(path)} bytes")

    try:
        data = probe(path)
    except RuntimeError as e:
        # This is what a missing moov atom / truncated MP4 looks like.
        add("readable", False, str(e)[:300])
        return {"path": path, "passed": False, "checks": checks, "info": info}
    add("readable", True)

    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    info["duration"] = duration

    add("has_video", video is not None)
    if video:
        w, h = int(video["width"]), int(video["height"])
        info.update({"width": w, "height": h, "video_codec": video.get("codec_name"),
                     "pix_fmt": video.get("pix_fmt")})
        add("video_codec_h264", video.get("codec_name") == "h264", video.get("codec_name", ""))
        add("pix_fmt_yuv420p", video.get("pix_fmt") == "yuv420p", video.get("pix_fmt", ""))
        if expected_size:
            add("dimensions", (w, h) == tuple(expected_size), f"got {w}x{h}, want "
                f"{expected_size[0]}x{expected_size[1]}")

    if require_audio:
        add("has_audio", audio is not None)
        if audio:
            info["audio_codec"] = audio.get("codec_name")

    add("duration_positive", duration > 0, f"{duration:.2f}s")

    # A file whose header is fine but whose data was cut off (interrupted write
    # or copy) still probes OK, so actually decode the final second and require
    # real video frames to come out of it.
    if duration > 0 and video:
        tail = subprocess.run(
            ["ffmpeg", "-v", "error", "-sseof", "-1", "-i", path, "-map", "0:v:0",
             "-f", "framemd5", "-"],
            capture_output=True, text=True,
        )
        decoded = sum(1 for line in tail.stdout.splitlines() if line and not line.startswith("#"))
        tail_err = tail.stderr.strip()
        ok = tail.returncode == 0 and not tail_err and decoded > 0
        add("decodes_to_end", ok, tail_err[:200] or f"{decoded} frame(s) decoded from the last second")

    if expected_duration is not None:
        diff = abs(duration - expected_duration)
        add("duration_matches", diff <= duration_tolerance,
            f"got {duration:.2f}s, want {expected_duration:.2f}s ±{duration_tolerance}s")

    return {"path": path, "passed": all(c["passed"] for c in checks),
            "checks": checks, "info": info}


def format_report(report):
    lines = [f"QC {'PASSED' if report['passed'] else 'FAILED'}: {report['path']}"]
    for c in report["checks"]:
        mark = "ok " if c["passed"] else "FAIL"
        lines.append(f"  [{mark}] {c['name']}" + (f" — {c['detail']}" if c["detail"] else ""))
    return "\n".join(lines)


def _main():
    p = argparse.ArgumentParser(description="Check a rendered MP4 with ffprobe.")
    p.add_argument("video")
    p.add_argument("--size", help="Expected WIDTHxHEIGHT, e.g. 1920x1080")
    p.add_argument("--duration", type=float, help="Expected duration in seconds")
    p.add_argument("--tolerance", type=float, default=1.0)
    a = p.parse_args()
    size = tuple(int(x) for x in a.size.lower().split("x")) if a.size else None
    report = check_video(a.video, expected_size=size, expected_duration=a.duration,
                         duration_tolerance=a.tolerance)
    print(format_report(report))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    _main()
