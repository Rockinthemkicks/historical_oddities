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
    from .brand import load_brand
    _accent = load_brand()["colors"]["accent"]
    draw.rectangle([int(w * 0.08), int(h * 0.62), int(w * 0.92), int(h * 0.625)], fill=_accent)
    small, big = _load_font(int(h * 0.045)), _load_font(int(h * 0.085))
    draw.text((int(w * 0.08), int(h * 0.36)), f"CHAPTER {number}", font=small, fill=_accent)
    y = int(h * 0.43)
    for line in textwrap.wrap(title, 34)[:2]:
        draw.text((int(w * 0.08), y), line, font=big, fill=(240, 240, 240))
        y += int(h * 0.095)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path)
    return out_path


def _card_background(bg_path, size, plain=(12, 13, 18)):
    """Plain near-black, or a blurred and darkened version of an illustration (so typography
    sits inside the film's world instead of on a slide)."""
    from PIL import ImageEnhance, ImageFilter
    w, h = size
    if not bg_path or not os.path.exists(bg_path):
        return Image.new("RGB", size, tuple(plain))
    bg = Image.open(bg_path).convert("RGB")
    sc = max(w / bg.width, h / bg.height)
    bg = bg.resize((int(bg.width * sc) + 1, int(bg.height * sc) + 1))
    left, top = (bg.width - w) // 2, (bg.height - h) // 2
    bg = bg.crop((left, top, left + w, top + h)).filter(ImageFilter.GaussianBlur(w * 0.012))
    bg = ImageEnhance.Brightness(bg).enhance(0.58)
    shade = Image.linear_gradient("L").rotate(90, expand=True).resize(size)   # darker on the left
    return Image.composite(Image.new("RGB", size, (6, 6, 10)), bg, shade.point(lambda v: int(v * 0.5)))


def reveal_steps(spec):
    """A progressive reveal: the card with 0..N rows (or lines) shown, in order."""
    key = "rows" if spec.get("rows") else "lines"
    items = spec.get(key, [])
    return [{**spec, key: items[:k]} for k in range(0, len(items) + 1)]


def text_card(spec, out_path, size=(1920, 1080)):
    """Documentary typography made locally (no paid call). spec:
      {"style": "title"|"stamp"|"rows", "heading": str, "lines": [str], "rows": [[label, text], ...],
       "note": small grey footnote (e.g. an illustration disclosure)}"""
    w, h = size
    from .brand import load_brand, paste_logo
    brand = load_brand()
    img = _card_background(spec.get("_bg_path"), size, brand["colors"]["background"])
    draw = ImageDraw.Draw(img)
    gold, white, grey = brand["colors"]["accent"], brand["colors"]["text"], (170, 170, 180)
    style = spec.get("style", "title")
    if style == "stamp":
        text = spec.get("heading", "")
        fs = int(h * 0.16)
        font = _load_font(fs)
        while draw.textlength(text, font=font) > w * 0.9 and fs > int(h * 0.05):
            fs = int(fs * 0.92)  # long quotes shrink to fit the frame instead of running off it
            font = _load_font(fs)
        tw = draw.textlength(text, font=font)
        draw.text(((w - tw) / 2, h * 0.38), text, font=font, fill=white)
        sub = _load_font(int(h * 0.04))
        for i, line in enumerate(spec.get("lines", [])[:2]):
            lw = draw.textlength(line, font=sub)
            draw.text(((w - lw) / 2, h * (0.60 + 0.06 * i)), line, font=sub, fill=gold)
    elif style == "rows":
        head = _load_font(int(h * 0.05))
        draw.text((w * 0.08, h * 0.16), spec.get("heading", ""), font=head, fill=gold)
        lab, txt = _load_font(int(h * 0.06)), _load_font(int(h * 0.045))
        rows = spec.get("rows", [])[:5]
        col = w * 0.08 + max([draw.textlength(r[0], font=lab) for r in rows] or [0]) + w * 0.03
        y = h * 0.30
        for row in rows:
            label, text = row[0], row[1]
            draw.text((w * 0.08, y), label, font=lab, fill=white)
            draw.rectangle([col, y + h * 0.012, col + w * 0.004, y + h * 0.065], fill=gold)
            draw.text((col + w * 0.025, y + h * 0.012), text, font=txt, fill=(205, 205, 210))
            y += h * 0.12
    else:
        big = _load_font(int(h * 0.085))
        y = h * 0.40 - 0.05 * h * len(spec.get("lines", []))
        for line in textwrap.wrap(spec.get("heading", ""), 22)[:2]:
            draw.text((w * 0.08, y), line, font=big, fill=white)
            y += h * 0.10
        draw.rectangle([w * 0.08, y + h * 0.02, w * 0.30, y + h * 0.026], fill=gold)
        sub = _load_font(int(h * 0.045))
        for line in spec.get("lines", [])[:3]:
            y += h * 0.07
            draw.text((w * 0.08, y), line, font=sub, fill=(205, 205, 210))
    if style == "title":
        paste_logo(img, brand)
        draw = ImageDraw.Draw(img)
    if spec.get("note"):
        draw.text((w * 0.08, h * 0.06), spec["note"], font=_load_font(int(h * 0.026)), fill=grey)
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


MONETIZATION_CHECKLIST = """# Before you upload: monetization checklist

Based on YouTube and Rockstar policies as checked on 2026-11-23. Policies change, so re-check them.
This is not legal advice.

## YouTube ads (advertiser-friendly guidelines)
- [ ] Thumbnail shows no graphic violence (blood, injury, gore) and no sexualized imagery.
- [ ] The first 7 seconds contain no graphic violence (that earns no ads); seconds 8-15 earn limited ads.
- [ ] Title and thumbnail have no profanity or shock wording.

## Reused / inauthentic content (YPP)
- [ ] The video is original research, writing and narration, not a re-read of a wiki or another video.
- [ ] The channel description says how the videos are made (researched scripts, original illustrations,
      AI narration voice, human fact-check).
- [ ] This episode differs clearly from earlier ones (topic, structure, hook, visuals).

## Copyright
- [ ] No game music or radio audio anywhere (Content ID claims; the songs are licensed, not Rockstar's).
      The renderer drops the audio of every gameplay clip, and ambient audio must be licensed.
- [ ] No isolated cutscene runs and no ending footage (Rockstar removes these).
- [ ] Every asset in assets/provenance.json is resolved, and the owner has accepted any
      "publisher_policy" footage (Rockstar's policy covers occasional, non-commercial use only).

## Disclosure
- [ ] YouTube "altered or synthetic content": not required for clearly animated or illustrated content.
      Re-check if any realistic-looking imagery is used.
"""


DESCRIPTION_LIMIT = 5000      # YouTube's description limit (characters)
DESCRIPTION_RESERVE = 900     # room kept for credits, disclosure and the brand footer


def sources_markdown(production, script, dossier):
    """Public claim-by-claim source list (for the description link when the list is too long)."""
    claims = {c["id"]: c for c in dossier.get("claims", [])}
    sources = {s["id"]: s for s in dossier.get("sources", [])}
    out = [f"# Sources: {production['title']}", "",
           "Every factual claim in the video, in order, with the sources it rests on. Lines marked "
           "*interpretation* are the documentary's reading of the evidence, not facts stated by the games.", ""]
    seen = []
    for sc in script["scenes"]:
        for cid in sc.get("claim_ids", []):
            if cid in claims and cid not in seen:
                seen.append(cid)
    chapter = None
    for sc in script["scenes"]:
        if sc.get("chapter_title") != chapter:
            chapter = sc.get("chapter_title")
            out += [f"## {chapter}", ""]
        for cid in sc.get("claim_ids", []):
            if cid not in seen:
                continue
            seen.remove(cid)
            c = claims[cid]
            tag = " *(interpretation)*" if c.get("status") == "interpretation" else ""
            out.append(f"- **{cid}**{tag}: {c['text']}")
            for sid in c.get("source_ids", []):
                if sid in sources:
                    s = sources[sid]
                    where = s.get("url") or s.get("locator", "")
                    out.append(f"  - {s.get('title', sid)}" + (f": {where}" if where else ""))
    out.append("")
    return "\n".join(out)


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
    from .brand import load_brand
    brand = load_brand()
    lines = [production["title"], ""]
    if production.get("description"):
        lines += [production["description"], ""]
    note = SPOILER_NOTES[production["spoiler_level"]]
    if note:
        lines += [note, ""]
    lines += ["Chapters", chapters_txt, ""]
    def src_line(sid):
        s = sources[sid]
        return f"- {s.get('title', sid)}: {s.get('url') or s.get('locator', '')}"
    source_lines = [src_line(sid) for sid in used_sources]
    sources_url = production.get("sources_url")
    if used_sources and sources_url:
        # Full list on a public page; the description keeps the most primary sources that fit
        # YouTube's limit (game > official > press > encyclopedia > wikis/community).
        from .research import source_family
        order = ["game", "official", "press", "encyclopedia", "fan_wiki", "community"]
        ranked = sorted(used_sources, key=lambda sid: (order.index(source_family(sources[sid]))
                                                        if source_family(sources[sid]) in order else 9,
                                                        used_sources.index(sid)))
        source_lines = [f"Every claim and its sources ({len(used_sources)} in all): {sources_url}", "",
                        "Key sources"]
        budget = DESCRIPTION_LIMIT - DESCRIPTION_RESERVE - len("\n".join(lines))
        for sid in ranked:
            line = src_line(sid)
            if len("\n".join(source_lines)) + len(line) + 1 > budget:
                break
            source_lines.append(line)
    if used_sources:
        lines.append("Sources")
        lines += source_lines
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
        "is an AI voice and illustrations are AI-generated original artwork, not game footage. Facts are "
        "researched against the sources listed above; interpretations are presented as interpretations.",
        f"Not affiliated with or endorsed by the makers of {franchise['name']}. "
        f"All game names and trademarks belong to their owners.",
        "",
        brand["name"] + (f": {brand['tagline']}" if brand.get("tagline") else ""),
    ]
    description = "\n".join(lines) + "\n"
    with open(os.path.join(out_dir, "description.txt"), "w") as f:
        f.write(description)
    with open(os.path.join(out_dir, "monetization_checklist.md"), "w") as f:
        f.write(MONETIZATION_CHECKLIST)
    with open(os.path.join(out_dir, "chapters.txt"), "w") as f:
        f.write(chapters_txt + "\n")
    with open(os.path.join(out_dir, "sources.json"), "w") as f:
        json.dump({"claims": [claims[c] for c in used_claims],
                   "sources": [sources[s] for s in used_sources]}, f, indent=2)
    return description
