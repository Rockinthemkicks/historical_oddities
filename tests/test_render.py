"""
End-to-end render tests: build tiny 3-scene videos in both formats with
ffmpeg and verify them with the QC module. No API keys or network needed.
Regression coverage for: invalid MP4 (missing moov), missing audio, wrong
dimensions, and silently short renders.
"""
import json
import shutil
import subprocess
import sys

import pytest
from PIL import Image

from modules.qc import check_video

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))


def make_inputs(tmp_path):
    images = tmp_path / "images"
    audio = tmp_path / "audio"
    images.mkdir()
    audio.mkdir()
    colors = [(200, 80, 60), (60, 120, 200), (90, 160, 90)]
    for i, color in enumerate(colors, start=1):
        Image.new("RGB", (640, 360), color).save(images / f"scene{i:02d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "sine=frequency=440:sample_rate=44100", "-t", "1.5",
                        "-c:a", "libmp3lame", str(audio / f"scene{i:02d}.mp3")], check=True)
    # Scene 2 gets two illustrations to exercise the multi-image path.
    (images / "scene02.png").rename(images / "scene02_1.png")
    Image.new("RGB", (640, 360), (230, 200, 90)).save(images / "scene02_2.png")
    script = {"title": "Test Episode", "scenes": [
        {"scene_number": i, "narration": f"This is scene number {i} of the test.", "image_prompt": ""}
        for i in (1, 2, 3)]}
    (tmp_path / "script.json").write_text(json.dumps(script))
    return images, audio


@pytest.mark.parametrize("fmt,expect", [
    ("vertical", [("final_video.mp4", (360, 640))]),
    ("landscape", [("final_video_landscape.mp4", (640, 360))]),
    ("both", [("final_video.mp4", (360, 640)), ("final_video_landscape.mp4", (640, 360))]),
])
def test_render_formats(tmp_path, fmt, expect):
    images, audio = make_inputs(tmp_path)
    project = tmp_path / "project"
    cmd = [sys.executable, "main.py", "--project", str(project),
           "--skip-script", "--script-file", str(tmp_path / "script.json"),
           "--skip-audio", "--audio-dir", str(audio),
           "--skip-images", "--images-dir", str(images),
           "--format", fmt, "--fps", "15",
           "--width", "360", "--height", "640",
           "--landscape-width", "640", "--landscape-height", "360"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    # 3 x 1.5s narration + 2 x 0.3s pauses
    for name, size in expect:
        report = check_video(str(project / name), expected_size=size, expected_duration=5.1,
                             duration_tolerance=0.5)
        assert report["passed"], report
        assert (project / name.replace(".mp4", "_qc.json")).exists()


def test_qc_flags_truncated_mp4(tmp_path):
    images, audio = make_inputs(tmp_path)
    project = tmp_path / "project"
    subprocess.run([sys.executable, "main.py", "--project", str(project),
                    "--skip-script", "--script-file", str(tmp_path / "script.json"),
                    "--skip-audio", "--audio-dir", str(audio),
                    "--skip-images", "--images-dir", str(images),
                    "--width", "360", "--height", "640", "--fps", "15"],
                   cwd=ROOT, check=True, capture_output=True)
    good = project / "final_video.mp4"
    broken = tmp_path / "broken.mp4"
    data = good.read_bytes()
    broken.write_bytes(data[: len(data) // 3])  # chop the file, like an interrupted write
    report = check_video(str(broken))
    assert not report["passed"]
    assert any(c["name"] == "decodes_to_end" and not c["passed"] for c in report["checks"])

    # Classic "moov atom not found": a non-faststart MP4 cut off before its index.
    plain = tmp_path / "plain.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(good), "-c", "copy",
                    "-movflags", "-faststart", str(plain)], check=True)
    no_moov = tmp_path / "no_moov.mp4"
    no_moov.write_bytes(plain.read_bytes()[:-2000])
    report = check_video(str(no_moov))
    assert not report["passed"]


def test_qc_flags_wrong_size_and_duration(tmp_path):
    images, audio = make_inputs(tmp_path)
    project = tmp_path / "project"
    subprocess.run([sys.executable, "main.py", "--project", str(project),
                    "--skip-script", "--script-file", str(tmp_path / "script.json"),
                    "--skip-audio", "--audio-dir", str(audio),
                    "--skip-images", "--images-dir", str(images),
                    "--width", "360", "--height", "640", "--fps", "15", "--skip-qc"],
                   cwd=ROOT, check=True, capture_output=True)
    report = check_video(str(project / "final_video.mp4"), expected_size=(1080, 1920),
                         expected_duration=60)
    failed = {c["name"] for c in report["checks"] if not c["passed"]}
    assert failed == {"dimensions", "duration_matches"}
