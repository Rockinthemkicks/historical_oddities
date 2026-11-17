"""Voice clean-up presets (offline; synthetic noisy 'voice')."""
import re
import shutil
import subprocess

import pytest

from modules.voice import PRESETS, compare

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture
def noisy(tmp_path):
    out = tmp_path / "rec.m4a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", "sine=f=220:sample_rate=48000:d=4",
                    "-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.03:r=48000:d=4",
                    "-filter_complex", "[0]volume='if(lt(mod(t,2),1.2),0.6,0)':eval=frame[v];"
                    "[v][1]amix=inputs=2:normalize=0[o]",
                    "-map", "[o]", "-ac", "1", str(out)], check=True)
    return str(out)


def pause_level(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", "1.4", "-t", "0.5", "-i", path,
                        "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    return float(re.search(r"mean_volume: (\S+) dB", r.stderr).group(1))


def test_presets_level_match_and_reduce_noise(noisy, tmp_path):
    res = compare(noisy, str(tmp_path / "out"))
    assert set(res) == set(PRESETS) == {"raw", "light", "heavy"}
    for info in res.values():
        assert abs(info["lufs"] - (-16)) < 1.5          # fair, level-matched comparison
        assert info["true_peak"] <= -1.5               # limiter holds peaks under 0 dBTP
    raw, light, heavy = (pause_level(res[n]["path"]) for n in ("raw", "light", "heavy"))
    assert light < raw - 3 and heavy < light            # noise between phrases goes down
