"""
Chapter cards, chapter timestamps and the publishing package.

Chapter timestamps come from the ACTUAL rendered scene times returned by the
renderer (whole frames), not from estimates, so YouTube chapter markers land
where the chapters really start.
"""
import json
import os
import textwrap

from PIL import Image, ImageDraw

from ..caption_images import _load_font


def chapter_card(number, title, out_path, size=(1920, 1080)):
    img = Image.new("RGB", size, (14, 14, 18))
    draw = ImageDraw.Draw(img)
    w, h = size
    draw.rectangle([int(w * 0.08), int(h * 0.62), int(w * 0.92), int(h * 0.625)], fill=(200, 160, 70))
    small, big = _load_font(int(h * 0.045)), _load_font(int(h * 0.085))
    draw.text((int(w * 0.08), int(h * 0.36)), f"CHAPTER {number}", font=small, fill=(200, 160, 70))
    y = int(h * 0.43)
    for line in textwrap.wrap(title, 34)[:2]:
        draw.text((int(w * 0.08), y), line, font=big, fill=(240, 240, 240))
        y += int(h * 0.095)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path)
    return out_path


def fmt_ts(seconds):
    s = int(seconds)
    hh, mm, ss = s // 3600, (s % 3600) // 60, s % 60
    return f"{hh}:{mm:02d}:{ss:02d}" if hh else f"{mm}:{ss:02d}"


def chapter_markers(script, scene_starts, total_seconds):
    """First scene of each chapter -> marker at that scene's rendered start time."""
    markers, seen = [], set()
    for scene, start in zip(script["scenes"], scene_starts):
        ch = scene.get("chapter")
        if ch and ch not in seen:
            seen.add(ch)
            markers.append({"chapter": ch, "title": scene.get("chapter_title") or ch, "start": start})
    for i, m in enumerate(markers):
        m["end"] = markers[i + 1]["start"] if i + 1 < len(markers) else total_seconds
    return markers


def validate_youtube_chapters(markers):
    """YouTube's chapter rules: first at 0:00, at least 3, each at least 10 seconds."""
    problems = []
    if len(markers) < 3:
        problems.append("YouTube needs at least 3 chapters")
    if markers and markers[0]["start"] > 0.001:
        problems.append("first chapter must start at 0:00")
    for m in markers:
        if m["end"] - m["start"] < 10:
            problems.append(f"{m['chapter']} is under 10 seconds")
    return problems


SPOILER_NOTES = {
    "none": "",
    "light": "Spoiler note: discusses setting and early-story details. No endings or major twists.",
    "full": "SPOILER WARNING: discusses major plot events and endings.",
}


def build_package(production, script, dossier, markers, manifest, out_dir):
    """Writes description.txt, chapters.txt and sources.json. Returns the description text."""
    os.makedirs(out_dir, exist_ok=True)
    franchise = production["_franchise"]
    claims = {c["id"]: c for c in dossier.get("claims", [])}
    sources = {s["id"]: s for s in dossier.get("sources", [])}
    used_claims = []
    for sc in script["scenes"]:
        for cid in sc.get("claim_ids", []):
            if cid in claims and cid not in used_claims:
                used_claims.append(cid)
    used_sources = []
    for cid in used_claims:
        for sid in claims[cid].get("source_ids", []):
            if sid in sources and sid not in used_sources:
                used_sources.append(sid)

    chapters_txt = "\n".join(f"{fmt_ts(m['start'])} {m['title']}" for m in markers)
    lines = [production["title"], ""]
    if production.get("description"):
        lines += [production["description"], ""]
    note = SPOILER_NOTES[production["spoiler_level"]]
    if note:
        lines += [note, ""]
    lines += ["Chapters", chapters_txt, ""]
    if used_sources:
        lines.append("Sources")
        for sid in used_sources:
            s = sources[sid]
            where = s.get("url") or s.get("locator", "")
            lines.append(f"- {s.get('title', sid)}: {where}")
        lines.append("")
    credits = [a for a in manifest.get("assets", [])
               if a.get("kind") in ("licensed_music", "licensed_sfx", "user_gameplay_video", "user_screenshot")]
    if credits:
        lines.append("Credits")
        for a in credits:
            lines.append(f"- {a['source']}" + (f" ({a['license_ref']})" if a.get("license_ref") else ""))
        lines.append("")
    lines += [
        "About this video: an independent fan documentary analysing a fictional game world. Narration "
        "is an AI voice and illustrations are AI-generated original artwork, written and fact-checked "
        "against the games and the sources above.",
        f"Not affiliated with or endorsed by the makers of {franchise['name']}. "
        f"All game names and trademarks belong to their owners.",
    ]
    description = "\n".join(lines) + "\n"
    with open(os.path.join(out_dir, "description.txt"), "w") as f:
        f.write(description)
    with open(os.path.join(out_dir, "chapters.txt"), "w") as f:
        f.write(chapters_txt + "\n")
    with open(os.path.join(out_dir, "sources.json"), "w") as f:
        json.dump({"claims": [claims[c] for c in used_claims],
                   "sources": [sources[s] for s in used_sources]}, f, indent=2)
    return description
