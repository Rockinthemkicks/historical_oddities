"""Per-scene renderer: timing, motion, caching and selective re-render (offline)."""
import json
import os
import shutil
import subprocess
import sys

import pytest
from PIL import Image, ImageDraw

from modules.qc import check_video
from modules.render import frame_plan, render_episode

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def grid_image(path, color):
    """A detailed image so pan/zoom produces visibly different frames."""
    img = Image.new("RGB", (640, 360), color)
    d = ImageDraw.Draw(img)
    for x in range(0, 640, 40):
        d.line([(x, 0), (x, 360)], fill=(0, 0, 0), width=3)
    for y in range(0, 360, 40):
        d.line([(0, y), (640, y)], fill=(255, 255, 255), width=3)
    img.save(path)
    return str(path)


def silent(path, seconds):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", str(seconds), "-c:a", "aac", str(path)],
                   check=True)
    return str(path)


def frame_at(video, t, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(video),
                    "-frames:v", "1", str(out)], check=True)
    return Image.open(out).convert("L")


def diff(a, b):
    return sum(abs(x - y) for x, y in zip(a.tobytes(), b.tobytes())) / (a.width * a.height)


@pytest.fixture
def episode(tmp_path):
    imgs = [grid_image(tmp_path / f"s{i}.png", c) for i, c in
            enumerate([(200, 80, 60), (60, 120, 200), (90, 160, 90)], start=1)]
    scenes = [{"image_paths": [imgs[0]], "duration": 1.37},
              {"image_paths": [imgs[1]], "duration": 1.21},
              {"image_paths": [imgs[2]], "duration": 1.55}]
    audio = silent(tmp_path / "a.m4a", 4.13)
    return tmp_path, scenes, audio


def test_frame_plan_never_drifts():
    durs = [2.345] * 200          # 200 scenes with awkward lengths
    frames = frame_plan(durs, 30)
    assert sum(frames) == round(sum(durs) * 30)


def test_render_matches_audio_length_and_size(episode):
    tmp, scenes, audio = episode
    out = render_episode(scenes, audio, [], str(tmp / "v.mp4"), str(tmp / "cache"),
                         size=(640, 360), fps=15)
    report = check_video(out["path"], expected_size=(640, 360), expected_duration=4.13,
                         duration_tolerance=0.15)
    assert report["passed"], report


def test_kenburns_moves_and_none_is_static(episode):
    tmp, scenes, audio = episode
    for mode in ("none", "kenburns"):
        render_episode(scenes, audio, [], str(tmp / f"{mode}.mp4"), str(tmp / f"c_{mode}"),
                       size=(640, 360), fps=15, motion=mode)
    a = frame_at(tmp / "none.mp4", 0.05, tmp / "n0.png")
    b = frame_at(tmp / "none.mp4", 1.2, tmp / "n1.png")
    assert diff(a, b) < 1.0                      # static image: frames identical
    c = frame_at(tmp / "kenburns.mp4", 0.05, tmp / "k0.png")
    d = frame_at(tmp / "kenburns.mp4", 1.2, tmp / "k1.png")
    assert diff(c, d) > 5.0                      # zoom in over scene 1: frames differ


def test_unchanged_rebuild_reuses_every_clip(episode):
    tmp, scenes, audio = episode
    first = render_episode(scenes, audio, [], str(tmp / "v.mp4"), str(tmp / "cache"),
                           size=(640, 360), fps=15, motion="kenburns")
    assert first["rendered"] == [0, 1, 2]
    again = render_episode(scenes, audio, [], str(tmp / "v.mp4"), str(tmp / "cache"),
                           size=(640, 360), fps=15, motion="kenburns")
    assert again["rendered"] == [] and again["reused"] == [0, 1, 2]


def test_changing_one_scene_rerenders_only_it(episode):
    tmp, scenes, audio = episode
    render_episode(scenes, audio, [], str(tmp / "v.mp4"), str(tmp / "cache"),
                   size=(640, 360), fps=15)
    grid_image(scenes[1]["image_paths"][0], (250, 220, 40))   # new artwork for scene 2
    out = render_episode(scenes, audio, [], str(tmp / "v.mp4"), str(tmp / "cache"),
                         size=(640, 360), fps=15)
    assert out["rendered"] == [1] and out["reused"] == [0, 2]
    assert len([f for f in os.listdir(tmp / "cache") if f.startswith("scene002_")]) == 1


def test_multi_image_scene_and_captions(episode):
    tmp, scenes, audio = episode
    scenes[0]["image_paths"].append(grid_image(tmp / "s1b.png", (20, 20, 20)))
    cap = tmp / "cap.png"
    Image.new("RGBA", (200, 60), (255, 255, 255, 255)).save(cap)
    caps = [{"start": 0.2, "end": 1.0, "path": str(cap), "width": 200, "height": 60},
            {"start": 2.9, "end": 3.6, "path": str(cap), "width": 200, "height": 60}]
    out = render_episode(scenes, audio, caps, str(tmp / "v.mp4"), str(tmp / "cache"),
                         size=(360, 640), fps=15, motion="kenburns")
    assert check_video(out["path"], expected_size=(360, 640))["passed"]
    # caption shows during its window (white pill near the bottom), not outside it
    on = frame_at(tmp / "v.mp4", 0.5, tmp / "on.png").getpixel((180, 640 - int(640 * 0.18) + 30))
    off = frame_at(tmp / "v.mp4", 1.8, tmp / "off.png").getpixel((180, 640 - int(640 * 0.18) + 30))
    assert on > 200 and off < 50


def test_main_motion_and_legacy_paths(tmp_path):
    images = tmp_path / "images"
    audio = tmp_path / "audio"
    images.mkdir()
    audio.mkdir()
    for i in (1, 2, 3):
        grid_image(images / f"scene{i:02d}.png", (40 * i, 90, 150))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=mono", "-t", "1.2", "-c:a", "libmp3lame",
                        str(audio / f"scene{i:02d}.mp3")], check=True)
    (tmp_path / "s.json").write_text(json.dumps({"title": "T", "scenes": [
        {"scene_number": i, "narration": "one two three four", "image_prompt": ""} for i in (1, 2, 3)]}))
    base = [sys.executable, "main.py", "--skip-script", "--script-file", str(tmp_path / "s.json"),
            "--skip-audio", "--audio-dir", str(audio), "--skip-images", "--images-dir", str(images),
            "--width", "360", "--height", "640", "--landscape-width", "640",
            "--landscape-height", "360", "--fps", "15"]
    r = subprocess.run(base + ["--project", str(tmp_path / "p1"), "--format", "both",
                               "--motion", "kenburns"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "3 scene clip(s) rendered" in r.stdout
    r2 = subprocess.run(base + ["--project", str(tmp_path / "p1"), "--format", "both",
                                "--motion", "kenburns"], cwd=ROOT, capture_output=True, text=True)
    assert r2.stdout.count("0 scene clip(s) rendered, 3 reused") == 2
    r3 = subprocess.run(base + ["--project", str(tmp_path / "p2"), "--legacy-render"],
                        cwd=ROOT, capture_output=True, text=True)
    assert r3.returncode == 0, r3.stderr
    assert check_video(str(tmp_path / "p2" / "final_video.mp4"), expected_size=(360, 640))["passed"]


def test_two_line_caption_stays_inside_landscape_frame(episode):
    tmp, scenes, audio = episode
    cap = tmp / "tall.png"
    Image.new("RGBA", (300, 150), (255, 255, 255, 255)).save(cap)  # tall 2-line pill
    caps = [{"start": 0.1, "end": 1.2, "path": str(cap), "width": 300, "height": 150}]
    render_episode(scenes, audio, caps, str(tmp / "v.mp4"), str(tmp / "cache"),
                   size=(640, 360), fps=15, bottom_margin_frac=-0.06)
    f = frame_at(tmp / "v.mp4", 0.5, tmp / "f.png")
    bottom = 360 - int(360 * 0.06)
    assert f.getpixel((320, bottom - 5)) > 200      # pill's lower edge is visible
    assert f.getpixel((320, bottom + 8)) < 200      # and ends above the margin
