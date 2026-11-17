"""Generates per-scene narration audio via ElevenLabs, with word-level timing for captions."""
import base64
import os
import requests

from .utils import post_with_retry

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"

# A generic default voice; override with your own voice_id from your ElevenLabs account.
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


def generate_scene_narration(text, out_path, voice_id=None, api_key=None, model_id="eleven_multilingual_v2",
                              speed=1.0, seed=None):
    """
    Synthesizes one scene's narration audio and returns word-level timing:
      {"duration": float, "words": [{"word": str, "start": float, "end": float}, ...]}
    Timing is relative to the start of this scene's own clip (starts at 0).

    speed: 0.7-1.2 (ElevenLabs' supported range), 1.0 = normal. Below 1.0 slows
    the voice down, above 1.0 speeds it up. Not supported on the eleven_v3 model.

    seed: optional int (0 to 4294967295). ElevenLabs generation is non-deterministic
    by default -- the same text/voice/settings can still sound slightly different
    (inflection, pacing) on every call. Passing the same seed on every request makes
    the output much more consistent across re-runs (not perfectly guaranteed, but
    close), which is useful when you're re-generating after only changing something
    unrelated (e.g. re-running assembly, or comparing two speed values fairly).
    """
    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("No ElevenLabs API key found (set ELEVENLABS_API_KEY in your .env)")
    voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE_ID

    payload = {"text": text, "model_id": model_id, "voice_settings": {"speed": speed}}
    if seed is not None:
        payload["seed"] = seed

    resp = post_with_retry(lambda: requests.post(
        ELEVENLABS_URL.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    ))
    resp.raise_for_status()
    data = resp.json()

    audio_bytes = base64.b64decode(data["audio_base64"])
    with open(out_path, "wb") as f:
        f.write(audio_bytes)

    words = _chars_to_words(data["alignment"])
    duration = data["alignment"]["character_end_times_seconds"][-1] if data["alignment"]["character_end_times_seconds"] else 0.0

    return {"duration": duration, "words": words}


def _chars_to_words(alignment):
    """Collapse ElevenLabs' character-level alignment into word-level timing."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words = []
    current = ""
    w_start = None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if current:
                words.append({"word": current, "start": w_start, "end": prev_end})
                current = ""
                w_start = None
        else:
            if current == "":
                w_start = s
            current += ch
            prev_end = e
    if current:
        words.append({"word": current, "start": w_start, "end": prev_end})
    return words


def generate_all_narration(scenes, out_dir, voice_id=None, api_key=None, speed=1.0, seed=None):
    """
    scenes: list of dicts with at least {"scene_number": int, "narration": str}
    Writes sceneNN.mp3 files to out_dir and returns a list of per-scene dicts:
      {"scene_number", "audio_path", "duration", "words"}
    """
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for scene in scenes:
        n = scene["scene_number"]
        out_path = os.path.join(out_dir, f"scene{n:02d}.mp3")
        print(f"      Generating narration {n}/{len(scenes)}...")
        timing = generate_scene_narration(scene["narration"], out_path, voice_id=voice_id, api_key=api_key,
                                           speed=speed, seed=seed)
        results.append({
            "scene_number": n,
            "audio_path": out_path,
            "duration": timing["duration"],
            "words": timing["words"],
        })
    return results
