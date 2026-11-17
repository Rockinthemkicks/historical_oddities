"""
Clean-up presets for owner-recorded narration (issue #15).

The goal is "your voice, but sounding like a narrator": remove rumble and
steady background hiss, tame harsh "s" sounds, even out loud and quiet
words, and bring everything to a consistent loudness. Denoising is
deliberately gentle, since heavy noise reduction makes speech sound
metallic or underwater, which is worse than a little room tone.

Presets:
  raw    - untouched, just converted and level-matched for fair comparison
  light  - recommended default
  heavy  - stronger noise reduction and compression, for noisy rooms

Loudness target: -16 LUFS integrated, -1.5 dBTP peak, the common target for
spoken content on YouTube and mobile platforms.

Usage:
  python3 -m modules.voice my_recording.m4a --out-dir voice_test/
  -> voice_test/<name>_raw.mp3, _light.mp3, _heavy.mp3 (+ a loudness report)
"""
import argparse
import json
import os
import re
import subprocess

from .utils import run_ffmpeg

LOUDNESS = "loudnorm=I=-16:TP=-1.5:LRA=11"

PRESETS = {
    "raw": [LOUDNESS],
    "light": [
        "highpass=f=80",                                   # rumble, handling noise
        "afftdn=nr=10:nf=-45:tn=1",                        # gentle, adaptive hiss reduction
        "equalizer=f=250:t=q:w=1.2:g=-2",                  # less boxy/muddy room tone
        "equalizer=f=3500:t=q:w=1.0:g=2",                  # presence and clarity
        "deesser=i=0.3",                                   # soften harsh s sounds
        "acompressor=threshold=-20dB:ratio=2.5:attack=15:release=200:makeup=2",
        LOUDNESS,
    ],
    "heavy": [
        "highpass=f=100",
        "afftdn=nr=20:nf=-40:tn=1",
        "agate=threshold=0.015:ratio=2:attack=5:release=250",  # duck noise between phrases
        "equalizer=f=200:t=q:w=1.2:g=-3",
        "equalizer=f=120:t=q:w=1.0:g=1.5",                 # a little warmth back
        "equalizer=f=3500:t=q:w=1.0:g=3",
        "deesser=i=0.4",
        "acompressor=threshold=-24dB:ratio=4:attack=10:release=150:makeup=4",
        LOUDNESS,
    ],
}


def process(src, dst, preset="light", sample_rate=48000):
    """Applies a preset and writes a mono file (format from dst's extension)."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset {preset!r}; use one of {sorted(PRESETS)}")
    codec = ["-c:a", "libmp3lame", "-b:a", "192k"] if dst.lower().endswith(".mp3") else []
    run_ffmpeg(["-i", src, "-af", ",".join(PRESETS[preset]), "-ac", "1",
                "-ar", str(sample_rate), *codec, dst], description=f"voice preset {preset}")
    return dst


def measure(path):
    """Integrated loudness (LUFS) and true peak (dBTP) of a file."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return {}
    data = json.loads(m.group(0))
    return {"lufs": float(data["input_i"]), "true_peak": float(data["input_tp"]),
            "lra": float(data["input_lra"])}


def compare(src, out_dir):
    """Writes raw/light/heavy versions of `src` for side-by-side listening."""
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src))[0]
    results = {}
    for name in ("raw", "light", "heavy"):
        dst = os.path.join(out_dir, f"{stem}_{name}.mp3")
        process(src, dst, name)
        results[name] = {"path": dst, **measure(dst)}
    return results


def _main():
    p = argparse.ArgumentParser(description="Make raw/light/heavy versions of a voice recording.")
    p.add_argument("recording")
    p.add_argument("--out-dir", default="voice_test")
    a = p.parse_args()
    for name, info in compare(a.recording, a.out_dir).items():
        print(f"{name:6s} {info['path']}  {info.get('lufs', '?')} LUFS, peak {info.get('true_peak', '?')} dBTP")


if __name__ == "__main__":
    _main()
