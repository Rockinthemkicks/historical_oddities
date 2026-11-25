"""Free, local prep for the full-episode run: makes the original ambient pad (13 minutes, so it never
loops under a ~9-10 minute episode) and registers it as owned audio in the pilot's assets/provenance.json.
The mp3 is generated on the machine that renders and is never committed. Run from the repo root."""
import os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_draft import PILOT
PILOT = sys.argv[1] if len(sys.argv) > 1 else PILOT  # optional: a copy of the production (dry runs)
from ambient import make_pad
from modules.gaming import provenance

pad = os.path.join(PILOT, "assets", "ambient_pad.mp3")
os.makedirs(os.path.dirname(pad), exist_ok=True)
if not os.path.exists(pad):
    make_pad(pad, 780)
m = provenance.load(PILOT)
provenance.register(PILOT, m, "ambient_pad", pad, "licensed_music",
                    "Ambient score: original, made for this video", "owned",
                    "ambient bed under narration", license_ref="own work: synthesized tones and noise, no samples")
provenance.save(PILOT, m)
print("ambient pad ready:", pad)
