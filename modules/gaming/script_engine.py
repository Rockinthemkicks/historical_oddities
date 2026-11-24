"""
Stages 2-3: chapter outline and the full documentary script, written one
chapter at a time.

Each chapter is generated from the approved dossier, the outline and a short
summary of earlier chapters (to keep continuity without resending everything),
validated, and saved to chapters/chNN.json before the next one starts. A
failed or interrupted run resumes from the first missing chapter.

Chapter JSON (what the model must return, and what a human may hand-edit):
{
  "chapter_id": "ch01",
  "summary": "two sentences for continuity",
  "segments": [
    {"narration": "...",
     "claim_ids": ["C1", "C4"],            -> every factual segment cites dossier claims
     "visuals": [
       {"kind": "illustration", "prompt": "..."},   -> illustration | map | timeline | evidence_board
       {"kind": "user_asset", "asset_id": "gp-007"},  -> footage or screenshot from assets/provenance.json
       {"kind": "chapter_card"}                       -> title card made locally, free
     ]}
  ]
}

The final script.json keeps the existing renderer schema (title, scenes with
scene_number/narration/image_prompt) and adds optional fields per scene:
chapter, claim_ids and visuals. The historical pipeline ignores them.
"""
import json
import math
import os
import re

from .config import word_budget
from .research import shingles

GENERATED_KINDS = ("illustration", "map", "timeline", "evidence_board")
VISUAL_KINDS = GENERATED_KINDS + ("user_asset", "chapter_card")
HEDGES = ("theory", "theories", "theorize", "speculat", "might", "may ", "may,", "perhaps", "possibly",
          "suggest", "rumor", "rumour", "some fans", "fans believe", "unconfirmed", "if true",
          "it's possible", "it is possible", "could have", "one reading", "interpret")
# Phrases that make narration sound machine-written. Warnings, not errors.
GENERIC_PHRASES = ("delve", "tapestry", "in conclusion", "let's dive in", "buckle up", "it's important to note",
                   "it is important to note", "rich history", "stands as a testament", "a testament to",
                   "in today's world", "ever-evolving", "embark on a journey", "unravel the mysteries",
                   "little did they know", "the rest is history", "game-changer", "navigate the complexities")
UNCITED_MAX_WORDS = 25   # short transitions (~10 s) may stand without a claim
WIKI_SHINGLE = 12        # words in a row that count as copied from a source excerpt
REPEAT_SHINGLE = 8


def words(text):
    return len(re.findall(r"[A-Za-z0-9']+", text))


# ---------- outline ----------

def outline_prompts(production, dossier, budget, n_chapters=None):
    n = n_chapters or max(4, min(12, round(budget["target_words"] / 450)))
    claims = [{k: c[k] for k in ("id", "text", "status", "continuity", "spoiler") if k in c}
              for c in dossier["claims"]]
    system = (
        "You are the head writer of a serious investigative documentary about a fictional game world. "
        "Plan chapters only from the research claims provided. Never add facts, sources or events that are "
        "not in the claims. Return JSON only.")
    user = json.dumps({
        "task": "Write a chapter outline.",
        "title": production["title"],
        "format": production.get("documentary_format", "fictional investigative history"),
        "continuities": production["_continuities"],
        "spoiler_level": production["spoiler_level"],
        "target_words_total": budget["target_words"],
        "chapters": n,
        "requirements": [
            "Chapter 1 opens with a compelling hook drawn from the claims.",
            "Give the context a newcomer needs, then progress chronologically or investigatively.",
            "Include original analysis; keep evidence and theories clearly separate.",
            "End on a satisfying conclusion, not a cliffhanger.",
            "Each chapter lists the claim ids it will use; target_words across chapters sums to the total.",
        ],
        "return_format": {"chapters": [{"id": "ch01", "title": "...", "purpose": "...",
                                        "target_words": 0, "claim_ids": ["C1"]}]},
        "claims": claims,
    }, indent=1)
    return system, user


def validate_outline(outline, dossier, budget):
    errors, warnings = [], []
    claim_ids = {c["id"] for c in dossier["claims"]}
    chapters = outline.get("chapters") or []
    if len(chapters) < 3:
        errors.append("outline needs at least 3 chapters (YouTube chapters need 3+ anyway)")
    seen = set()
    total = 0
    for i, ch in enumerate(chapters, start=1):
        cid = ch.get("id")
        if cid != f"ch{i:02d}":
            errors.append(f"chapter {i} must have id ch{i:02d} (got {cid!r})")
        if cid in seen:
            errors.append(f"duplicate chapter id {cid}")
        seen.add(cid)
        if not (ch.get("title") or "").strip():
            errors.append(f"{cid}: missing title")
        unknown = [c for c in ch.get("claim_ids", []) if c not in claim_ids]
        if unknown:
            errors.append(f"{cid}: uses claims not in the dossier: {unknown}")
        if not ch.get("claim_ids"):
            warnings.append(f"{cid}: plans no claims; a chapter with no evidence is likely padding")
        total += int(ch.get("target_words") or 0)
    if chapters and not (budget["min_words"] <= total <= budget["max_words"]):
        errors.append(f"chapter targets add up to {total} words; the duration needs "
                      f"{budget['min_words']}-{budget['max_words']}")
    return {"errors": errors, "warnings": warnings, "passed": not errors}


# ---------- chapters ----------

def chapter_prompts(production, dossier, outline, chapter, prior_summaries):
    by_id = {c["id"]: c for c in dossier["claims"]}
    claims = [by_id[c] for c in chapter.get("claim_ids", []) if c in by_id]
    system = (
        "You write narration for a serious investigative documentary about a fictional game world, read "
        "aloud by one narrator. Use ONLY the claims provided. Say plainly when something is confirmed in the "
        "games, when it is interpretation, and when it is a fan theory or speculation (use words like "
        "'theory', 'possibly', 'some fans believe'). Never invent quotes, dates, names, sources or events. "
        "Write original prose: do not copy wording from sources. No padding, no filler, no stock phrases "
        "like 'delve' or 'let's dive in'. Return JSON only.")
    user = json.dumps({
        "documentary": production["title"],
        "chapter": chapter,
        "chapter_number": int(chapter["id"][2:]),
        "chapters_total": len(outline["chapters"]),
        "previously": prior_summaries,
        "target_words": chapter.get("target_words"),
        "visual_guidance": {
            "seconds_per_visual": production["_settings"].get("seconds_per_visual", 12),
            "kinds": list(VISUAL_KINDS),
            "illustration_rules": "Describe original, unnamed people, places and objects. Never name game "
                                  "characters, brands or logos in a visual prompt; no on-image text.",
            "first_segment_of_chapter_starts_with": {"kind": "chapter_card"},
        },
        "return_format": {"chapter_id": chapter["id"], "summary": "...",
                          "segments": [{"narration": "...", "claim_ids": ["C1"],
                                        "visuals": [{"kind": "illustration", "prompt": "..."}]}]},
        "claims": claims,
    }, indent=1)
    return system, user


def _has_hedge(text):
    low = " " + text.lower() + " "
    return any(h in low for h in HEDGES)


def validate_chapter(ch, outline_ch, dossier, earlier_chapters=(), wpm=140):
    errors, warnings = [], []
    cid = outline_ch["id"]
    claims = {c["id"]: c for c in dossier["claims"]}
    excerpts = set()
    for s in dossier.get("sources", []):
        if s.get("excerpt"):
            excerpts |= shingles(s["excerpt"], WIKI_SHINGLE)
    if ch.get("chapter_id") != cid:
        errors.append(f"{cid}: chapter_id is {ch.get('chapter_id')!r}")
    segs = ch.get("segments") or []
    if not segs:
        errors.append(f"{cid}: no segments")
    total = 0
    earlier = set()
    for e in earlier_chapters:
        for s in e.get("segments", []):
            earlier |= shingles(s.get("narration", ""), REPEAT_SHINGLE)
    for i, seg in enumerate(segs, start=1):
        where = f"{cid} segment {i}"
        text = (seg.get("narration") or "").strip()
        n = words(text)
        total += n
        if not text:
            errors.append(f"{where}: empty narration")
            continue
        ids = seg.get("claim_ids") or []
        unknown = [c for c in ids if c not in claims]
        if unknown:
            errors.append(f"{where}: cites claims not in the dossier {unknown}")
        if not ids and n > UNCITED_MAX_WORDS:
            errors.append(f"{where}: {n} words of narration cite no claim; every factual passage must "
                          f"trace to the dossier")
        outside = [c for c in ids if c in claims and c not in outline_ch.get("claim_ids", [])]
        if outside:
            warnings.append(f"{where}: uses claims outside this chapter's outline {outside}")
        uncertain = [c for c in ids if c in claims and claims[c]["status"] in ("fan_theory", "speculation")]
        if uncertain and not _has_hedge(text):
            errors.append(f"{where}: presents {uncertain} (theory/speculation) without saying so")
        low = text.lower()
        for p in GENERIC_PHRASES:
            if p in low:
                warnings.append(f"{where}: stock phrase '{p}'")
        if excerpts and shingles(text, WIKI_SHINGLE) & excerpts:
            errors.append(f"{where}: copies {WIKI_SHINGLE}+ words in a row from a source excerpt; rewrite")
        rep = shingles(text, REPEAT_SHINGLE) & earlier
        if len(rep) >= 2:
            warnings.append(f"{where}: repeats passages from an earlier chapter")
        vis = seg.get("visuals") or []
        if not vis:
            errors.append(f"{where}: no visuals")
        for v in vis:
            kind = v.get("kind")
            if kind not in VISUAL_KINDS:
                errors.append(f"{where}: unknown visual kind {kind!r}")
            elif kind in GENERATED_KINDS and not (v.get("prompt") or "").strip():
                errors.append(f"{where}: {kind} visual needs a prompt")
            elif kind == "user_asset" and not v.get("asset_id"):
                errors.append(f"{where}: user_asset visual needs an asset_id")
        seconds = n / wpm * 60
        if seconds > 45 and len(vis) < 2:
            warnings.append(f"{where}: about {seconds:.0f}s on a single visual; consider another")
    target = outline_ch.get("target_words") or 0
    if target:
        ratio = total / target
        if ratio < 0.6 or ratio > 1.5:
            errors.append(f"{cid}: {total} words vs target {target}")
        elif ratio < 0.8 or ratio > 1.25:
            warnings.append(f"{cid}: {total} words vs target {target}")
    return {"errors": errors, "warnings": warnings, "passed": not errors, "words": total}


def chapter_path(prod_dir, cid):
    return os.path.join(prod_dir, "chapters", f"{cid}.json")


def write_chapters(llm, production, dossier, outline, log=print, max_output_tokens=12000):
    """Generates missing chapters in order; keeps valid existing ones. Returns reports."""
    os.makedirs(os.path.join(production["_dir"], "chapters"), exist_ok=True)
    done, reports = [], {}
    wpm = production["_settings"].get("words_per_minute", 140)
    for ch_meta in outline["chapters"]:
        path = chapter_path(production["_dir"], ch_meta["id"])
        if os.path.exists(path):
            with open(path) as f:
                ch = json.load(f)
            rep = validate_chapter(ch, ch_meta, dossier, done, wpm)
            if rep["passed"]:
                log(f"      {ch_meta['id']}: kept existing ({rep['words']} words)")
                reports[ch_meta["id"]] = rep
                done.append(ch)
                continue
        prior = [{"id": c["chapter_id"], "summary": c.get("summary", "")} for c in done]
        system, user = chapter_prompts(production, dossier, outline, ch_meta, prior)
        log(f"      {ch_meta['id']}: writing '{ch_meta.get('title', '')}'")
        ch = llm.complete_json(system, user, label=f"chapter:{ch_meta['id']}",
                               max_output_tokens=max_output_tokens)
        rep = validate_chapter(ch, ch_meta, dossier, done, wpm)
        reports[ch_meta["id"]] = rep
        target = path if rep["passed"] else path.replace(".json", ".rejected.json")
        with open(target, "w") as f:
            json.dump(ch, f, indent=2)
        if not rep["passed"]:
            raise ValueError(f"{ch_meta['id']} failed checks (saved to {target} for review): "
                             + "; ".join(rep["errors"][:5]))
        done.append(ch)
    return reports


def assemble_script(production, outline, chapters):
    """Chapters -> script.json in the existing schema, plus optional per-scene fields."""
    scenes, n, v = [], 0, 0
    titles = {c["id"]: c.get("title", "") for c in outline["chapters"]}
    for ch in chapters:
        for seg in ch["segments"]:
            n += 1
            visuals = []
            for vis in seg["visuals"]:
                v += 1
                visuals.append({"id": f"v{v:03d}", **vis})
            scenes.append({"scene_number": n, "narration": seg["narration"], "image_prompt": "",
                           "chapter": ch["chapter_id"], "chapter_title": titles.get(ch["chapter_id"], ""),
                           "claim_ids": seg.get("claim_ids", []), "visuals": visuals})
    return {"title": production["title"], "mode": "gaming-lore", "scenes": scenes}


def plan_estimate(production, outline_words=None):
    """Very rough planning numbers for a target duration (for estimates before writing)."""
    s = production["_settings"]
    b = word_budget(production["target_minutes"], s.get("words_per_minute", 140),
                    tuple(s.get("words_per_minute_range", (130, 150))))
    words_total = outline_words or b["target_words"]
    seconds = words_total / b["wpm"] * 60
    visuals = math.ceil(seconds / s.get("seconds_per_visual", 12))
    return {**b, "planned_words": words_total, "seconds": seconds, "visuals": visuals,
            "characters": int(words_total * 6.0)}
