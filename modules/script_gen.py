"""Generates a scene-by-scene narration script from a topic using an LLM API."""
import json
import os
import re
import requests

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = """You write tight, punchy narration scripts for short-form vertical \
video (YouTube Shorts / TikTok / Reels style), broken into numbered scenes.

Rules:
- Return ONLY valid JSON, no markdown fences, no commentary.
- Structure: {{"title": "...", "scenes": [{{"scene_number": 1, "narration": "...", \
"image_prompt": "..."}}, ...]}}
- Produce exactly {num_scenes} scenes.
- Each "narration" is 1-2 short sentences (spoken aloud in 2-5 seconds), hooky, \
conversational, no filler.
- Each "image_prompt" is a vivid, concrete visual description of that scene, \
written for an image generation model, in this visual style: {style}.
- The first scene must be a strong hook. Scenes should flow as a continuous story/explainer.
"""


def generate_script(topic, num_scenes=10, style="simple stick-figure illustration, minimal flat color",
                     api_key=None, model="gpt-4o-mini"):
    """Calls an OpenAI-compatible chat completions endpoint and returns a parsed script dict."""
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No OpenAI API key found (set OPENAI_API_KEY in your .env)")

    resp = requests.post(
        OPENAI_CHAT_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(num_scenes=num_scenes, style=style)},
                {"role": "user", "content": f"Topic: {topic}"},
            ],
            "temperature": 0.9,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    data = _parse_json_loose(content)

    if "scenes" not in data or not isinstance(data["scenes"], list):
        raise RuntimeError(f"Unexpected script format from model: {content[:300]}")
    return data


def _parse_json_loose(text):
    """Strip markdown fences if the model added them anyway, then parse."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def save_script(script, path):
    with open(path, "w") as f:
        json.dump(script, f, indent=2)


def load_script(path):
    with open(path) as f:
        return json.load(f)
