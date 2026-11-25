"""Builds the 60-second production test (review 5) as its own small production, so it runs through the
real pipeline: episodes/gaming/vice-city-60s-test/. Free and offline; it writes:
  production.json  (copy of the pilot's settings + the Corporal reference sheet + ambient bed)
  script.json      (the opening + continuity scenes from the draft, via assemble_script)
  assets/ambient_pad.mp3 (original pad made with ffmpeg here; registered as owned audio, not committed)
Paid generation still needs the owner's approval of each stage and an explicit run cap."""
import json, os, subprocess, sys
sys.path.insert(0, os.getcwd())
from build_draft import build, REFERENCE_PROMPT, PILOT
from modules.gaming.script_engine import assemble_script
from modules.gaming import provenance

TEST = os.path.join(os.path.dirname(PILOT), "vice-city-60s-test")
prod, dossier, rep, outline, chapters, results, orep, deps = build()
os.makedirs(os.path.join(TEST, "assets"), exist_ok=True)

pilot = json.load(open(os.path.join(PILOT, "production.json")))
test = {k: pilot[k] for k in ("mode", "franchise", "games", "continuity", "spoiler_level", "thesis")}
test.update({
    "title": pilot["title"] + " - 60-second test",
    "target_minutes": [1, 2],
    # Speed comparison (review 8): this run renders at 0.8. The 0.9 version is in run 45547596599's results.
    # Narration is cached per speed, so switching back to 0.9 later costs nothing.
    "overrides": {"target_minutes_range": [1, 60], "words_per_minute": 150, "narration_speed": 0.8},
    "description": "Production test of the opening (review 5). Not for publication.",
    "reference_prompt": REFERENCE_PROMPT,
    "ambient_asset_id": "ambient_pad",
    "extra_visuals": [{"id": "thumbnail_bg", "prompt":
        "Somber, dramatic, non-graphic. Dramatic low-angle composition: an old, generic badge with no insignia or lettering lies cracked "
        "on a wet seawall railing in the foreground, sharp focus; behind it, out of focus, a neon-lit 1980s coastal skyline at dusk in "
        "magenta and teal, palm silhouettes. Strong rim light on the badge's crack. Large empty area of sky on the left for title text."}],
    "owner_decisions": {"2026-11-24 (review 5)": "60-second production test approved in principle by the editorial review; "
                                                 "paid generation waits for the owner's explicit authorization ($2 test cap)."},
})
json.dump(test, open(os.path.join(TEST, "production.json"), "w"), indent=2, ensure_ascii=False)

script = assemble_script(test, {"chapters": outline["chapters"][:1]}, chapters[:1])
json.dump(script, open(os.path.join(TEST, "script.json"), "w"), indent=2, ensure_ascii=False)
json.dump(dossier, open(os.path.join(TEST, "research.json"), "w"), indent=2, ensure_ascii=False)
json.dump({"chapters": outline["chapters"][:1]}, open(os.path.join(TEST, "outline.json"), "w"), indent=2)

# Original ambient pad: two detuned low sines + soft filtered noise with a slow swell (ours, no third-party audio).
pad = os.path.join(TEST, "assets", "ambient_pad.mp3")
if not os.path.exists(pad):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=frequency=55:duration=120",
        "-f", "lavfi", "-i", "sine=frequency=82.6:duration=120",
        "-f", "lavfi", "-i", "anoisesrc=color=brown:amplitude=0.25:duration=120",
        "-filter_complex",
        "[0]volume=0.5[a];[1]volume=0.3[b];[2]lowpass=f=400,volume=0.4[c];"
        "[a][b][c]amix=inputs=3:normalize=0,tremolo=f=0.12:d=0.3,lowpass=f=900,afade=t=in:d=3,afade=t=out:st=115:d=5[o]",
        "-map", "[o]", "-ar", "44100", "-b:a", "128k", pad], check=True)
m = provenance.load(TEST)
provenance.register(TEST, m, "ambient_pad", pad, "licensed_music", "original pad generated locally with ffmpeg (draft/make_test.py)",
                    "owned", "ambient bed under narration", license_ref="own work: synthesized tones and noise, no samples")
provenance.save(TEST, m)
words = sum(len(sc["narration"].split()) for sc in script["scenes"])
gen = [v for sc in script["scenes"] for v in sc["visuals"] if v["kind"] == "illustration"]
print(f"test: {len(script['scenes'])} scenes, {words} words, {len(gen)} illustrations + 1 reference sheet")
