"""
Generates per-scene images via the OpenAI image API, using a reference image
to keep the character/style consistent across scenes.

There's no "seed" or "GenID" parameter in OpenAI's API for this (that term refers
to a ChatGPT-app-only feature, not something the API exposes). The actual
mechanism is the image *edit* endpoint: you pass one or more existing images
alongside a new prompt, and the model uses them as a visual reference for the
new image. So the flow here is:

  1. Generate ONE reference image from a "character sheet" style prompt.
  2. For every scene, call the edit endpoint with that reference image + the
     scene's own prompt, so each new image is generated "in reference to" the
     established look rather than from scratch.

This helps a lot but isn't perfect -- OpenAI's own docs note the model can still
occasionally drift on recurring characters across many generations. Reviewing
scene images before final assembly is still worth doing for a long script.
"""
import base64
import os
import requests

from .utils import post_with_retry

OPENAI_GENERATE_URL = "https://api.openai.com/v1/images/generations"
OPENAI_EDIT_URL = "https://api.openai.com/v1/images/edits"


def _save_b64_or_url(payload, out_path):
    if "b64_json" in payload:
        img_bytes = base64.b64decode(payload["b64_json"])
    else:
        img_resp = requests.get(payload["url"], timeout=60)
        img_resp.raise_for_status()
        img_bytes = img_resp.content
    with open(out_path, "wb") as f:
        f.write(img_bytes)


def generate_reference_image(prompt, out_path, api_key=None, model="gpt-image-2", size="1024x1536"):
    """
    Generates the initial 'character sheet' / style-anchor image that every
    scene image will be generated in reference to. `prompt` should describe
    the recurring character and the overall visual style clearly, e.g.
    "A simple black-and-white stick figure character, thick clean lines,
    minimal flat background, neutral standing pose, reference character sheet."
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No OpenAI API key found (set OPENAI_API_KEY in your .env)")

    resp = post_with_retry(lambda: requests.post(
        OPENAI_GENERATE_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "prompt": prompt, "size": size, "n": 1},
        timeout=180,
    ))
    resp.raise_for_status()
    _save_b64_or_url(resp.json()["data"][0], out_path)
    return out_path


def generate_scene_image(prompt, reference_paths, out_path, api_key=None, model="gpt-image-2", size="1024x1536"):
    """
    Generates one scene image via the edit endpoint, using `reference_paths`
    (a list of one or more image file paths) as visual reference so the
    character/style stays consistent with earlier scenes.
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No OpenAI API key found (set OPENAI_API_KEY in your .env)")

    def do_post():
        files = []
        opened = []
        try:
            for path in reference_paths:
                fh = open(path, "rb")
                opened.append(fh)
                files.append(("image[]", (os.path.basename(path), fh, "image/png")))
            return requests.post(
                OPENAI_EDIT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                data={"model": model, "prompt": prompt, "size": size, "n": 1},
                files=files,
                timeout=180,
            )
        finally:
            for fh in opened:
                fh.close()

    resp = post_with_retry(do_post)
    resp.raise_for_status()
    _save_b64_or_url(resp.json()["data"][0], out_path)
    return out_path


def generate_all_images(scenes, out_dir, api_key=None, size="1024x1536",
                         reference_prompt=None, use_reference=True):
    """
    scenes: list of dicts with at least {"scene_number": int, "image_prompt": str}
    Writes sceneNN.png files to out_dir, plus reference.png (the style anchor),
    and returns a list of {"scene_number", "image_path"}.

    reference_prompt: prompt for the initial character/style sheet. If not given,
    it's built from the first scene's image_prompt.
    use_reference: if False, falls back to independent generation per scene
    (faster/cheaper, but no consistency mechanism between scenes).
    """
    os.makedirs(out_dir, exist_ok=True)
    results = []

    reference_path = None
    if use_reference:
        reference_path = os.path.join(out_dir, "reference.png")
        prompt = reference_prompt or (
            f"Character reference sheet, neutral standing pose, plain background. "
            f"{scenes[0]['image_prompt']}"
        )
        print("      Generating reference/style image...")
        generate_reference_image(prompt, reference_path, api_key=api_key, size=size)

    for scene in scenes:
        n = scene["scene_number"]
        out_path = os.path.join(out_dir, f"scene{n:02d}.png")
        print(f"      Generating image {n}/{len(scenes)}...")
        if use_reference:
            generate_scene_image(scene["image_prompt"], [reference_path], out_path,
                                  api_key=api_key, size=size)
        else:
            generate_reference_image(scene["image_prompt"], out_path, api_key=api_key, size=size)
        results.append({"scene_number": n, "image_path": out_path})

    return results
