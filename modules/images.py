"""
Generates per-scene images via the OpenAI image API, using a reference image
to keep the character/style consistent across scenes.

There's no "seed" or "GenID" parameter in OpenAI's API for this (that term refers
to a ChatGPT-app-only feature, not something the API exposes). The actual
mechanism is the image *edit* endpoint: you pass one or more existing images
alongside a new prompt, and the model uses them as a visual reference for the
new image. So the flow here is:

  1. Generate ONE reference image from a "character sheet" style prompt
     (or use a master reference you already made, via reference_image=).
  2. For every scene, call the edit endpoint with that reference image + the
     scene's own prompt, so each new image is generated "in reference to" the
     established look rather than from scratch.

Safeguards for unattended runs:
  - Images already on disk are reused, never regenerated, so a re-run after a
    failure only pays for what's missing.
  - The whole run's cost is estimated up front and refused if it's over the
    cap; spending is also checked before every single call.
  - Every paid call is logged to <project>/costs.jsonl.

This helps a lot but isn't perfect -- OpenAI's own docs note the model can still
occasionally drift on recurring characters across many generations. Reviewing
scene images before final assembly is still worth doing for a long script.
"""
import base64
import os
import requests

from .costs import BudgetExceeded, CostLedger, cost_from_usage, image_unit_cost
from .utils import post_with_retry

OPENAI_GENERATE_URL = "https://api.openai.com/v1/images/generations"
OPENAI_EDIT_URL = "https://api.openai.com/v1/images/edits"

DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1536x1024"   # 16:9-ish landscape, matching the scene format
DEFAULT_QUALITY = "medium"

# Image calls are slow and billed; a couple of retries is plenty.
IMAGE_MAX_RETRIES = 2


def _save_b64_or_url(payload, out_path):
    if "b64_json" in payload:
        img_bytes = base64.b64decode(payload["b64_json"])
    else:
        img_resp = requests.get(payload["url"], timeout=60)
        img_resp.raise_for_status()
        img_bytes = img_resp.content
    tmp = out_path + ".part"
    with open(tmp, "wb") as f:
        f.write(img_bytes)
    os.replace(tmp, out_path)  # never leave a half-written image that looks finished


def _api_key(api_key):
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No OpenAI API key found (set OPENAI_API_KEY in your .env)")
    return api_key


def _raise_for_status(resp):
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("error", {}).get("message", resp.text[:300])
        except ValueError:
            msg = resp.text[:300]
        raise RuntimeError(f"OpenAI image API error {resp.status_code}: {msg}")


def _generate(prompt, out_path, api_key, model, size, quality):
    key = _api_key(api_key)
    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    if quality:
        payload["quality"] = quality
    resp = post_with_retry(lambda: requests.post(
        OPENAI_GENERATE_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=300,
    ), max_retries=IMAGE_MAX_RETRIES)
    _raise_for_status(resp)
    data = resp.json()
    _save_b64_or_url(data["data"][0], out_path)
    return data.get("usage")


def _edit(prompt, reference_paths, out_path, api_key, model, size, quality):
    key = _api_key(api_key)

    def do_post():
        files = []
        opened = []
        try:
            for path in reference_paths:
                fh = open(path, "rb")
                opened.append(fh)
                files.append(("image[]", (os.path.basename(path), fh, "image/png")))
            data = {"model": model, "prompt": prompt, "size": size, "n": 1}
            if quality:
                data["quality"] = quality
            return requests.post(
                OPENAI_EDIT_URL,
                headers={"Authorization": f"Bearer {key}"},
                data=data,
                files=files,
                timeout=300,
            )
        finally:
            for fh in opened:
                fh.close()

    resp = post_with_retry(do_post, max_retries=IMAGE_MAX_RETRIES)
    _raise_for_status(resp)
    data = resp.json()
    _save_b64_or_url(data["data"][0], out_path)
    return data.get("usage")


def generate_reference_image(prompt, out_path, api_key=None, model=DEFAULT_MODEL, size=DEFAULT_SIZE,
                             quality=None):
    """
    Generates the initial 'character sheet' / style-anchor image that every
    scene image will be generated in reference to.
    """
    _generate(prompt, out_path, api_key, model, size, quality)
    return out_path


def generate_scene_image(prompt, reference_paths, out_path, api_key=None, model=DEFAULT_MODEL,
                         size=DEFAULT_SIZE, quality=None):
    """
    Generates one scene image via the edit endpoint, using `reference_paths`
    (a list of one or more image file paths) as visual reference so the
    character/style stays consistent with earlier scenes.
    """
    _edit(prompt, reference_paths, out_path, api_key, model, size, quality)
    return out_path


def _with_style(style, prompt):
    return f"{style.strip()}\n\n{prompt.strip()}" if style else prompt


def plan_images(scenes, out_dir, prompts=None, use_reference=True, reference_image=None,
                model=DEFAULT_MODEL, size=DEFAULT_SIZE, quality=DEFAULT_QUALITY):
    """
    Works out what a run would generate and cost without calling anything.
    Returns {"to_generate": [...labels], "existing": [...], "estimate_usd": float}.
    """
    to_generate, existing = [], []
    need_reference = use_reference and not reference_image and \
        not os.path.exists(os.path.join(out_dir, "reference.png"))
    if need_reference:
        to_generate.append("reference")
    for s in scenes:
        n = s["scene_number"]
        label = f"scene{n:02d}"
        (existing if os.path.exists(os.path.join(out_dir, f"{label}.png")) else to_generate).append(label)
    estimate = 0.0
    for label in to_generate:
        estimate += image_unit_cost(model, quality, size,
                                    with_reference=use_reference and label != "reference")
    return {"to_generate": to_generate, "existing": existing, "estimate_usd": round(estimate, 4)}


def generate_all_images(scenes, out_dir, api_key=None, size=DEFAULT_SIZE,
                        reference_prompt=None, use_reference=True, *,
                        prompts=None, style="", quality=DEFAULT_QUALITY, model=DEFAULT_MODEL,
                        reference_image=None, project_dir=None, max_cost=None):
    """
    scenes: list of dicts with at least {"scene_number": int} and, unless
        `prompts` is given, a non-empty "image_prompt".
    prompts: optional {scene_number: prompt} (e.g. from a batch_prompts.txt).
    style: text prepended to every prompt (e.g. config/style_prompt.txt).
    reference_image: path to your own master reference to use instead of
        generating one.
    max_cost: USD cap for this run; None = no cap.

    Writes sceneNN.png files to out_dir, plus reference.png (the style anchor),
    and returns a list of {"scene_number", "image_path"}.
    """
    os.makedirs(out_dir, exist_ok=True)
    prompts = prompts or {s["scene_number"]: s.get("image_prompt", "") for s in scenes}
    missing = [n for n, p in prompts.items() if not (p or "").strip()]
    if missing:
        raise ValueError(f"No image prompt for scene(s) {missing}")

    plan = plan_images(scenes, out_dir, prompts, use_reference, reference_image, model, size, quality)
    print(f"      Images: {len(plan['to_generate'])} to generate, {len(plan['existing'])} already done, "
          f"estimated ${plan['estimate_usd']:.2f} ({model}, {quality}, {size})")
    if max_cost is not None and plan["estimate_usd"] > max_cost + 1e-9:
        raise BudgetExceeded(
            f"Estimated image cost ${plan['estimate_usd']:.2f} is over the ${max_cost:.2f} cap. "
            f"Raise --max-image-cost or lower --image-quality.")

    ledger = CostLedger(project_dir or os.path.dirname(os.path.abspath(out_dir)), cap_usd=max_cost)

    def paid_call(label, unit, fn):
        ledger.check_room(unit)
        usage = fn()
        actual = cost_from_usage(model, usage)
        ledger.record("openai-image", label, unit, actual,
                      extra={"model": model, "quality": quality, "size": size, "usage": usage})

    reference_path = None
    if use_reference:
        if reference_image:
            reference_path = reference_image
            print(f"      Using your reference image: {reference_path}")
        else:
            reference_path = os.path.join(out_dir, "reference.png")
            if os.path.exists(reference_path):
                print("      Reusing existing reference.png")
            else:
                first = prompts[sorted(prompts)[0]]
                prompt = reference_prompt or (
                    "Character and style reference sheet: the recurring characters in clear neutral "
                    "standing poses, with a small palette strip, on a plain background. "
                    f"Setting and characters for this video: {first}")
                print("      Generating reference/style image...")
                paid_call("reference", image_unit_cost(model, quality, size, False),
                          lambda: _generate(_with_style(style, prompt), reference_path,
                                            api_key, model, size, quality))

    results = []
    for scene in scenes:
        n = scene["scene_number"]
        out_path = os.path.join(out_dir, f"scene{n:02d}.png")
        if os.path.exists(out_path):
            results.append({"scene_number": n, "image_path": out_path})
            continue
        print(f"      Generating image {n}/{len(scenes)}...")
        prompt = _with_style(style, prompts[n])
        if use_reference:
            paid_call(f"scene{n:02d}", image_unit_cost(model, quality, size, True),
                      lambda: _edit(prompt, [reference_path], out_path, api_key, model, size, quality))
        else:
            paid_call(f"scene{n:02d}", image_unit_cost(model, quality, size, False),
                      lambda: _generate(prompt, out_path, api_key, model, size, quality))
        results.append({"scene_number": n, "image_path": out_path})

    print(f"      Image spend this run: ~${ledger.spent:.2f}")
    return results
