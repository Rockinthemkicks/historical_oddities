"""
Asset provenance: where every picture, clip and sound came from, and whether
we're allowed to use it the way we intend.

assets/provenance.json:
{
  "assets": [
    {"id": "gp-007",
     "path": "assets/user/vice_beach_drive.mp4",   -> relative to the production folder
     "kind": "user_gameplay_video",                -> see KINDS
     "source": "Owner's own capture, PS5, 2026-11-20",
     "permission_status": "publisher_policy",      -> see PERMISSIONS
     "license_ref": "https://support.rockstargames.com/...",
     "intended_usage": "B-roll behind chapter 3 narration; monetized YouTube",
     "notes": "",
     "sha256": "..."}                              -> filled in automatically
  ]
}

Nothing is downloaded automatically. Footage, screenshots, music and sound
effects are added by the owner, with their rights recorded here. Generated
images and chapter cards are registered by the pipeline itself.
"""
import hashlib
import json
import os

KINDS = ("generated_image", "chapter_card", "user_gameplay_video", "user_screenshot",
         "licensed_music", "licensed_sfx", "synthetic_test")
PERMISSIONS = ("generated", "owned", "licensed", "publisher_policy", "fair_use_claim", "unverified")
# Publishing is blocked until these are resolved by the owner.
BLOCKING = {"unverified"}
# Allowed, but the owner must explicitly accept the risk before publishing.
NEEDS_SIGNOFF = {"publisher_policy", "fair_use_claim"}


def manifest_path(prod_dir):
    return os.path.join(prod_dir, "assets", "provenance.json")


def load(prod_dir):
    path = manifest_path(prod_dir)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"assets": []}


def save(prod_dir, manifest):
    path = manifest_path(prod_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp, path)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def register(prod_dir, manifest, asset_id, path, kind, source, permission_status, intended_usage,
             license_ref="", notes=""):
    """Adds or updates an entry (used for generated images, chapter cards, test assets)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if permission_status not in PERMISSIONS:
        raise ValueError(f"permission_status must be one of {PERMISSIONS}")
    rel = os.path.relpath(path, prod_dir)
    entry = {"id": asset_id, "path": rel, "kind": kind, "source": source,
             "permission_status": permission_status, "license_ref": license_ref,
             "intended_usage": intended_usage, "notes": notes, "sha256": _sha(path)}
    manifest["assets"] = [a for a in manifest["assets"] if a["id"] != asset_id] + [entry]
    return entry


def check(prod_dir, manifest, used_ids=None, for_publication=False):
    """
    Returns {"errors", "warnings", "passed"}. used_ids: asset ids the script uses.
    for_publication adds the rights checks that block publishing.
    """
    errors, warnings = [], []
    by_id = {}
    for a in manifest.get("assets", []):
        aid = a.get("id")
        if not aid or aid in by_id:
            errors.append(f"asset {aid!r}: missing or duplicate id")
            continue
        by_id[aid] = a
        if a.get("kind") not in KINDS:
            errors.append(f"{aid}: unknown kind {a.get('kind')!r}")
        if a.get("permission_status") not in PERMISSIONS:
            errors.append(f"{aid}: unknown permission_status {a.get('permission_status')!r}")
        for field in ("source", "intended_usage"):
            if not (a.get(field) or "").strip():
                errors.append(f"{aid}: {field} is required")
        path = os.path.join(prod_dir, a.get("path", ""))
        if not os.path.exists(path):
            errors.append(f"{aid}: file not found at {a.get('path')}")
        elif a.get("sha256") and _sha(path) != a["sha256"]:
            warnings.append(f"{aid}: file changed since it was registered; re-check its rights")
        if a.get("kind") == "synthetic_test" and for_publication:
            errors.append(f"{aid}: synthetic test asset can't be published")
        status = a.get("permission_status")
        if for_publication and status in BLOCKING:
            errors.append(f"{aid}: rights unverified; resolve before publishing")
        elif status in NEEDS_SIGNOFF:
            warnings.append(f"{aid}: relies on {status.replace('_', ' ')} ({a.get('license_ref') or 'no reference'}); "
                            f"owner must accept this before publishing")
        if a.get("kind") in ("licensed_music", "licensed_sfx") and not a.get("license_ref"):
            errors.append(f"{aid}: licensed audio needs a license_ref")
    for aid in used_ids or []:
        if aid not in by_id:
            errors.append(f"script uses asset {aid!r}, which isn't in assets/provenance.json")
    return {"errors": errors, "warnings": warnings, "passed": not errors}
