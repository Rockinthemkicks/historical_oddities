"""
Offline stand-ins for paid steps, used by --dry-run and tests.

Synthetic images are labelled placeholders showing the prompt; synthetic
narration is silence timed at the planning words-per-minute, with evenly
spaced word timings so captions, chapter timing and rendering all run
exactly as they would with real assets. Nothing here touches the network.
"""
import hashlib
import os
import re
import subprocess
import textwrap

from PIL import Image, ImageDraw

from ..caption_images import _load_font


def synthetic_image(prompt, out_path, size=(1536, 1024), label="DRY RUN"):
    h = hashlib.sha256(prompt.encode()).digest()
    top, bottom = (h[0] // 3, h[1] // 3, 60 + h[2] // 3), (20 + h[3] // 2, 20, 40 + h[4] // 2)
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):  # gradient so pan/zoom is visible in the dry-run video
        t = y / size[1]
        draw.line([(0, y), (size[0], y)],
                  fill=tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    for x in range(0, size[0], 96):
        draw.line([(x, 0), (x, size[1])], fill=(255, 255, 255), width=1)
    big, small = _load_font(64), _load_font(30)
    draw.text((60, 50), label, font=big, fill=(255, 220, 80))
    y = 160
    for line in textwrap.wrap(prompt, 80)[:14]:
        draw.text((60, y), line, font=small, fill=(235, 235, 235))
        y += 42
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path)
    return out_path


def synthetic_narration(scenes, out_dir, wpm=140, min_seconds=1.0):
    """Same result shape as modules.narration.generate_all_narration."""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for s in scenes:
        words = re.findall(r"\S+", s["narration"])
        duration = max(min_seconds, len(words) / wpm * 60)
        path = os.path.join(out_dir, f"scene{s['scene_number']:03d}.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=mono", "-t", f"{duration:.3f}",
                        "-c:a", "libmp3lame", "-b:a", "64k", path], check=True)
        step = duration / max(1, len(words))
        timed = [{"word": w, "start": i * step, "end": (i + 0.9) * step} for i, w in enumerate(words)]
        results.append({"scene_number": s["scene_number"], "audio_path": path,
                        "duration": duration, "words": timed, "cached": False})
    return results
