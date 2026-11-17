"""Small shared helpers used across the pipeline."""
import json
import os
import subprocess
import time

# Common bold font locations to try, in order, across macOS/Linux/Windows.
# Used for rendering caption text with Pillow (see modules/caption_images.py).
_FONT_CANDIDATES = [
    os.environ.get("FONT_PATH"),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",       # macOS
    "/System/Library/Fonts/Supplemental/Arial.ttf",             # macOS fallback
    "/System/Library/Fonts/Helvetica.ttc",                      # macOS fallback
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",     # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux
    "C:\\Windows\\Fonts\\arialbd.ttf",                          # Windows
]


def find_font():
    """Returns the first existing font file path from _FONT_CANDIDATES, or None."""
    for path in _FONT_CANDIDATES:
        if path and os.path.exists(path):
            return path
    return None


def load_env():
    """Load key=value pairs from a .env file in the project root, if present."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


RETRY_STATUS = {429, 500, 502, 503, 504}


def post_with_retry(post_fn, max_retries=5, base_delay=8):
    """
    Calls post_fn() (a zero-arg callable that performs one requests.post and
    returns the Response) and retries with backoff on rate limits (429),
    temporary server errors (5xx) and dropped connections/timeouts, honoring a
    Retry-After header when the API provides one. Retries are capped at
    max_retries, so a persistent failure can't loop (or bill) forever.
    """
    import requests  # local import keeps utils usable without requests installed

    resp = None
    for attempt in range(max_retries + 1):
        try:
            resp = post_fn()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"      Network error ({type(e).__name__}), retrying in {delay:.0f}s "
                  f"(attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)
            continue
        if resp.status_code not in RETRY_STATUS or attempt == max_retries:
            return resp
        retry_after = resp.headers.get("retry-after")
        try:
            delay = float(retry_after) if retry_after else base_delay * (2 ** attempt)
        except ValueError:
            delay = base_delay * (2 ** attempt)
        print(f"      HTTP {resp.status_code}, retrying in {delay:.0f}s "
              f"(attempt {attempt + 1}/{max_retries})...")
        time.sleep(delay)
    return resp


def get_duration(path):
    """Return duration in seconds of an audio/video/image-loop file via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True
    )
    return float(out.stdout.strip())


def run_ffmpeg(args, description=""):
    """Run an ffmpeg command, raising with stderr output on failure."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({description}):\n{result.stderr}\n\nCommand: {' '.join(cmd)}")
    return result


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def load_json(path):
    with open(path) as f:
        return json.load(f)
