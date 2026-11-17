"""
Generates per-scene narration audio via ElevenLabs, with word-level timing for captions.

Narration is cached by content: each clip is stored under a hash of
(text, voice ID, model, speed, seed) in <audio_dir>/cache/, together with its
word timings. Rebuilding an episode whose text and voice settings haven't
changed makes no ElevenLabs calls and costs nothing; changing any of those
inputs for a scene regenerates just that scene. Reordering or renumbering
scenes still reuses the cache, since the key is the content, not the number.
"""
import base64
import hashlib
import json
import os
import shutil
import requests

from .costs import narration_unit_cost
from .utils import post_with_retry

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"

DEFAULT_MODEL_ID = "eleven_multilingual_v2"


class NarrationApiError(RuntimeError):
    """ElevenLabs answered with an error status: no audio produced (not billed)."""


def resolve_voice_id(voice_id=None):
    """
    The voice must be chosen explicitly (--voice-id or ELEVENLABS_VOICE_ID).
    There is deliberately no fallback: a silent switch to a stock voice is how
    episodes ended up with inconsistent narration before.
    """
    voice_id = (voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or "").strip()
    if not voice_id:
        raise RuntimeError(
            "No ElevenLabs voice set. Put ELEVENLABS_VOICE_ID=<your voice id> in .env "
            "or pass --voice-id, so every episode uses the same narrator.")
    return voice_id


def cache_key(text, voice_id, model_id=DEFAULT_MODEL_ID, speed=1.0, seed=None):
    h = hashlib.sha256()
    for part in ("v1", text, voice_id, model_id, f"{float(speed):.4f}", "" if seed is None else str(seed)):
        h.update(str(part).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:32]


def generate_scene_narration(text, out_path, voice_id=None, api_key=None, model_id=DEFAULT_MODEL_ID,
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
    voice_id = resolve_voice_id(voice_id)

    payload = {"text": text, "model_id": model_id, "voice_settings": {"speed": speed}}
    if seed is not None:
        payload["seed"] = seed

    resp = post_with_retry(lambda: requests.post(
        ELEVENLABS_URL.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    ))
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text[:300])
        except ValueError:
            detail = resp.text[:300]
        raise NarrationApiError(f"ElevenLabs error {resp.status_code}: {detail}")
    data = resp.json()

    audio_bytes = base64.b64decode(data["audio_base64"])
    tmp = out_path + ".part"
    with open(tmp, "wb") as f:
        f.write(audio_bytes)
    os.replace(tmp, out_path)

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


def plan_narration(scenes, out_dir, voice_id, model_id=DEFAULT_MODEL_ID, speed=1.0, seed=None):
    """Which scenes need a paid call, and the estimated cost. Makes no calls."""
    cache_dir = os.path.join(out_dir, "cache")
    to_generate, cached, chars = [], [], 0
    for s in scenes:
        key = cache_key(s["narration"], voice_id, model_id, speed, seed)
        if os.path.exists(os.path.join(cache_dir, f"{key}.mp3")) and \
                os.path.exists(os.path.join(cache_dir, f"{key}.json")):
            cached.append(s["scene_number"])
        else:
            to_generate.append(s["scene_number"])
            chars += len(s["narration"])
    return {"to_generate": to_generate, "cached": cached, "characters": chars,
            "estimate_usd": round(narration_unit_cost(chars, model_id), 4)}


def generate_all_narration(scenes, out_dir, voice_id=None, api_key=None, speed=1.0, seed=None,
                           model_id=DEFAULT_MODEL_ID, ledger=None):
    """
    scenes: list of dicts with at least {"scene_number": int, "narration": str}
    Writes sceneNN.mp3 files to out_dir and returns a list of per-scene dicts:
      {"scene_number", "audio_path", "duration", "words", "cached"}
    ledger: optional modules.costs.CostLedger; every paid call goes through it.
    """
    voice_id = resolve_voice_id(voice_id)
    os.makedirs(out_dir, exist_ok=True)
    cache_dir = os.path.join(out_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    results = []
    for scene in scenes:
        n = scene["scene_number"]
        text = scene["narration"]
        key = cache_key(text, voice_id, model_id, speed, seed)
        cached_mp3 = os.path.join(cache_dir, f"{key}.mp3")
        cached_json = os.path.join(cache_dir, f"{key}.json")
        out_path = os.path.join(out_dir, f"scene{n:02d}.mp3")

        was_cached = os.path.exists(cached_mp3) and os.path.exists(cached_json)
        if was_cached:
            with open(cached_json) as f:
                timing = json.load(f)
        else:
            print(f"      Generating narration {n}/{len(scenes)}...")
            unit = narration_unit_cost(len(text), model_id)
            call_id = ledger.begin("elevenlabs-tts", f"scene{n:02d}", unit,
                                   extra={"characters": len(text), "voice_id": voice_id,
                                          "model": model_id}) if ledger else None
            try:
                timing = generate_scene_narration(text, cached_mp3, voice_id=voice_id, api_key=api_key,
                                                  model_id=model_id, speed=speed, seed=seed)
            except NarrationApiError as e:
                if ledger:
                    ledger.not_billed(call_id, unit, str(e))
                raise
            if ledger:
                ledger.finish(call_id, unit)
            timing.update({"text": text, "voice_id": voice_id, "model_id": model_id,
                           "speed": speed, "seed": seed})
            tmp = cached_json + ".part"
            with open(tmp, "w") as f:
                json.dump(timing, f, indent=2)
            os.replace(tmp, cached_json)

        shutil.copyfile(cached_mp3, out_path)
        results.append({
            "scene_number": n,
            "audio_path": out_path,
            "duration": timing["duration"],
            "words": timing["words"],
            "cached": was_cached,
        })
    reused = sum(r["cached"] for r in results)
    if reused:
        print(f"      Reused {reused} cached narration clip(s) at no cost")
    return results
