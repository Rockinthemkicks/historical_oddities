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
  - images/manifest.json records a hash of everything that went into each
    image (prompt, style, model, size, quality, reference). An image is reused
    only when its hash still matches; otherwise it's moved to images/_replaced/
    and regenerated. Files the pipeline didn't make are treated the same way.
  - The run's cost is estimated up front and refused if it would break the
    per-run, per-episode or overall budget (see modules/costs.py); every
    single call is checked again before it's made.
  - Every paid call is logged, pending before and closed after.

This helps a lot but isn't perfect -- OpenAI's own docs note the model can still
occasionally drift on recurring characters across many generations. Reviewing
scene images before final assembly is still worth doing for a long script.
"""
import base64
import hashlib
import json
import os
import shutil
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


class ImageApiError(RuntimeError):
    """The API answered with an error status: no image was produced (not billed)."""


def _raise_for_status(resp):
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("error", {}).get("message", resp.text[:300])
        except ValueError:
            msg = resp.text[:300]
        raise ImageApiError(f"OpenAI image API error {resp.status_code}: {msg}")


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


MANIFEST_NAME = "manifest.json"


def _sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update((p if isinstance(p, bytes) else str(p).encode("utf-8")))
        h.update(b"\x00")
    return h.hexdigest()


def _file_sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _load_manifest(out_dir):
    path = os.path.join(out_dir, MANIFEST_NAME)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save_manifest(out_dir, manifest):
    path = os.path.join(out_dir, MANIFEST_NAME)
    tmp = path + ".part"
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _default_reference_prompt(prompts):
    first = prompts[sorted(prompts)[0]]
    return ("Character and style reference sheet: the recurring characters in clear neutral "
            "standing poses, with a small palette strip, on a plain background. "
            f"Setting and characters for this video: {first}")


def _input_hashes(scenes, prompts, style, model, size, quality, use_reference,
                  reference_image, reference_prompt):
    """
    Returns {"reference": hash or None, "scene01": hash, ...}: what each image
    should have been made from. Scene hashes include the reference's hash, so
    a new reference invalidates every scene.
    """
    settings = (model, size, quality)
    hashes = {"reference": None}
    ref_key = "none"
    if use_reference:
        if reference_image:
            ref_key = "user:" + _file_sha(reference_image)
        else:
            rp = reference_prompt or _default_reference_prompt(prompts)
            hashes["reference"] = _sha("reference", *settings, _with_style(style, rp))
            ref_key = hashes["reference"]
    for s in scenes:
        n = s["scene_number"]
        hashes[f"scene{n:02d}"] = _sha("scene", *settings, use_reference, ref_key,
                                       _with_style(style, prompts[n]))
    return hashes


def _is_current(out_dir, manifest, label, want_hash):
    path = os.path.join(out_dir, f"{label}.png")
    entry = manifest.get(label)
    return (os.path.exists(path) and entry is not None and entry.get("input_hash") == want_hash
            and entry.get("file_sha256") == _file_sha(path))


def _retire(out_dir, label):
    """Moves a stale image aside instead of overwriting it."""
    path = os.path.join(out_dir, f"{label}.png")
    if os.path.exists(path):
        dest_dir = os.path.join(out_dir, "_replaced")
        os.makedirs(dest_dir, exist_ok=True)
        i = 1
        while os.path.exists(os.path.join(dest_dir, f"{label}_{i}.png")):
            i += 1
        shutil.move(path, os.path.join(dest_dir, f"{label}_{i}.png"))


def seed_from(src_dir, out_dir, hashes):
    """Copies already-paid images from another production's images folder when their input hash
    (prompt, style, model, size, quality, reference) is identical, whatever their label. Only files
    whose bytes still match the source manifest are copied. Returns the labels seeded. Free."""
    src = _load_manifest(src_dir)
    by_hash = {}
    for label, e in src.items():
        path = os.path.join(src_dir, f"{label}.png")
        if os.path.exists(path) and e.get("file_sha256") == _file_sha(path):
            by_hash.setdefault(e.get("input_hash"), (label, e))
    os.makedirs(out_dir, exist_ok=True)
    manifest = _load_manifest(out_dir)
    seeded = []
    for label, want in hashes.items():
        if not want or _is_current(out_dir, manifest, label, want) or want not in by_hash:
            continue
        src_label, entry = by_hash[want]
        _retire(out_dir, label)
        shutil.copyfile(os.path.join(src_dir, f"{src_label}.png"), os.path.join(out_dir, f"{label}.png"))
        manifest[label] = dict(entry, seeded_from=f"{src_dir}:{src_label}")
        seeded.append(label)
    if seeded:
        _save_manifest(out_dir, manifest)
    return seeded


def plan_images(scenes, out_dir, prompts=None, use_reference=True, reference_image=None,
                model=DEFAULT_MODEL, size=DEFAULT_SIZE, quality=DEFAULT_QUALITY,
                style="", reference_prompt=None):
    """
    Works out what a run would generate and cost without calling anything.
    Returns {"to_generate": [labels], "stale": [labels with an outdated file],
             "existing": [labels reused], "estimate_usd": float}.
    """
    prompts = prompts or {s["scene_number"]: s.get("image_prompt", "") for s in scenes}
    hashes = _input_hashes(scenes, prompts, style, model, size, quality, use_reference,
                           reference_image, reference_prompt)
    manifest = _load_manifest(out_dir)
    to_generate, stale, existing = [], [], []
    labels = (["reference"] if hashes["reference"] else []) + \
        [f"scene{s['scene_number']:02d}" for s in scenes]
    for label in labels:
        if _is_current(out_dir, manifest, label, hashes[label]):
            existing.append(label)
        else:
            to_generate.append(label)
            if os.path.exists(os.path.join(out_dir, f"{label}.png")):
                stale.append(label)
    estimate = sum(image_unit_cost(model, quality, size,
                                   with_reference=use_reference and label != "reference")
                   for label in to_generate)
    return {"to_generate": to_generate, "stale": stale, "existing": existing,
            "estimate_usd": round(estimate, 4), "hashes": hashes}


def generate_all_images(scenes, out_dir, api_key=None, size=DEFAULT_SIZE,
                        reference_prompt=None, use_reference=True, *,
                        prompts=None, style="", quality=DEFAULT_QUALITY, model=DEFAULT_MODEL,
                        reference_image=None, project_dir=None, max_cost=None,
                        episode_budget=None, total_budget=None, ledger=None):
    """
    scenes: list of dicts with at least {"scene_number": int} and, unless
        `prompts` is given, a non-empty "image_prompt".
    prompts: optional {scene_number: prompt} (e.g. from a batch_prompts.txt).
    style: text prepended to every prompt (e.g. config/style_prompt.txt).
    reference_image: path to your own master reference to use instead of
        generating one.
    max_cost / episode_budget / total_budget: USD limits (None = no limit).

    Writes sceneNN.png files to out_dir, plus reference.png (the style anchor)
    and manifest.json, and returns a list of {"scene_number", "image_path"}.
    """
    os.makedirs(out_dir, exist_ok=True)
    prompts = prompts or {s["scene_number"]: s.get("image_prompt", "") for s in scenes}
    missing = [s["scene_number"] for s in scenes if not (prompts.get(s["scene_number"]) or "").strip()]
    if missing:
        raise ValueError(f"No image prompt for scene(s) {missing}")

    plan = plan_images(scenes, out_dir, prompts, use_reference, reference_image, model, size,
                       quality, style, reference_prompt)
    hashes = plan["hashes"]
    print(f"      Images: {len(plan['to_generate'])} to generate "
          f"({len(plan['stale'])} replacing outdated files), {len(plan['existing'])} reused, "
          f"estimated ${plan['estimate_usd']:.2f} ({model}, {quality}, {size})")

    ledger = ledger or CostLedger(project_dir or os.path.dirname(os.path.abspath(out_dir)),
                                  run_cap=max_cost, episode_cap=episode_budget,
                                  total_cap=total_budget)
    ledger.check_room(plan["estimate_usd"])  # whole plan must fit before anything is spent

    manifest = _load_manifest(out_dir)

    def paid_call(label, unit, prompt, fn):
        _retire(out_dir, label)
        call_id = ledger.begin("openai-image", label, unit,
                               extra={"model": model, "quality": quality, "size": size})
        try:
            usage = fn()
        except ImageApiError as e:
            ledger.not_billed(call_id, unit, str(e))
            raise
        # Any other exception (timeout, crash) leaves the entry pending, which
        # is counted at its estimate: the provider may have billed it.
        ledger.finish(call_id, unit, cost_from_usage(model, usage), usage)
        path = os.path.join(out_dir, f"{label}.png")
        manifest[label] = {"input_hash": hashes[label], "file_sha256": _file_sha(path),
                           "prompt": prompt, "model": model, "size": size, "quality": quality}
        _save_manifest(out_dir, manifest)

    reference_path = None
    if use_reference:
        if reference_image:
            reference_path = reference_image
            print(f"      Using your reference image: {reference_path}")
        else:
            reference_path = os.path.join(out_dir, "reference.png")
            if "reference" in plan["existing"]:
                print("      Reusing reference.png (inputs unchanged)")
            else:
                prompt = _with_style(style, reference_prompt or _default_reference_prompt(prompts))
                print("      Generating reference/style image...")
                paid_call("reference", image_unit_cost(model, quality, size, False), prompt,
                          lambda: _generate(prompt, reference_path, api_key, model, size, quality))

    results = []
    for scene in scenes:
        n = scene["scene_number"]
        label = f"scene{n:02d}"
        out_path = os.path.join(out_dir, f"{label}.png")
        if label in plan["existing"]:
            results.append({"scene_number": n, "image_path": out_path})
            continue
        print(f"      Generating image {n}/{len(scenes)}...")
        prompt = _with_style(style, prompts[n])
        if use_reference:
            paid_call(label, image_unit_cost(model, quality, size, True), prompt,
                      lambda: _edit(prompt, [reference_path], out_path, api_key, model, size, quality))
        else:
            paid_call(label, image_unit_cost(model, quality, size, False), prompt,
                      lambda: _generate(prompt, out_path, api_key, model, size, quality))
        results.append({"scene_number": n, "image_path": out_path})

    print(f"      Image spend this run: ~${ledger.run_spent:.2f} "
          f"(episode ~${ledger.episode_spent():.2f}, overall ~${ledger.total_spent():.2f})")
    return results
