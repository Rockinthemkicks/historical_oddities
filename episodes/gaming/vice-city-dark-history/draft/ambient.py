"""Original ambient pad (ours: synthesized tones and filtered noise, no samples or third-party audio)."""
import subprocess


def make_pad(path, seconds=120):
    """Two detuned low sines + soft brown noise with a slow swell; fades in at the start and out at the end.
    Long enough for the whole video so the renderer never loops it (a loop would dip at every seam)."""
    fade_out = max(seconds - 5, 0)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=82.6:duration={seconds}",
        "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.25:duration={seconds}",
        "-filter_complex",
        "[0]volume=0.5[a];[1]volume=0.3[b];[2]lowpass=f=400,volume=0.4[c];"
        f"[a][b][c]amix=inputs=3:normalize=0,tremolo=f=0.12:d=0.3,lowpass=f=900,afade=t=in:d=3,afade=t=out:st={fade_out}:d=5[o]",
        "-map", "[o]", "-ar", "44100", "-b:a", "128k", path], check=True)
    return path
