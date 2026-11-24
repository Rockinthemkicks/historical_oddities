"""
Stage 1: the research dossier and its canon checks.

research.json is the single source of truth the script may draw on. Nothing
reaches narration unless it's a claim here, and every claim carries its
evidence and how certain it is:

{
  "topic": "...",
  "sources": [
    {"id": "S1", "type": "primary_game",       -> primary_game | official | secondary | community
     "title": "Vice City: mission 'X' dialogue",
     "url": "https://...",                     -> required for official/secondary/community
     "locator": "mission name / dialogue line / timestamp",  -> required for primary_game
     "accessed": "2026-11-23",
     "verified": true,                         -> a human opened it and it says what's claimed
     "excerpt": "short quote, for wiki-copy detection (optional)"}
  ],
  "claims": [
    {"id": "C1",
     "text": "...",
     "status": "confirmed_canon",              -> confirmed_canon | interpretation | fan_theory | speculation
     "continuity": "3D",
     "games": ["gtavc"],
     "source_ids": ["S1"],
     "spoiler": "none",                        -> none | minor | major
     "event": "optional-event-key", "year": 1986}   -> optional, for timeline checks
  ],
  "open_questions": ["..."]
}

The checks never invent or "fill in" evidence. A claim without enough
support is flagged for a human, never silently upgraded or dropped.
"""
import re
from urllib.parse import urlparse

from .config import SPOILER_ALLOWED

SOURCE_TYPES = ("primary_game", "official", "secondary", "community")
STATUSES = ("confirmed_canon", "interpretation", "fan_theory", "speculation")
SPOILERS = ("none", "minor", "major")
# What a status needs as evidence.
CANON_SOURCE_TYPES = {"primary_game", "official"}


def _finding(level, where, rule, detail):
    return {"level": level, "where": where, "rule": rule, "detail": detail}


def validate_dossier(dossier, production):
    """
    Returns {"errors": [...], "warnings": [...], "passed": bool, "stats": {...}}.
    errors block script generation; warnings go to the human reviewer.
    """
    franchise = production["_franchise"]
    continuities = production["_continuities"]
    games = {g["id"]: g for g in franchise["games"]}
    allowed_spoilers = SPOILER_ALLOWED[production["spoiler_level"]]
    out = []

    sources = {}
    for s in dossier.get("sources", []):
        sid = s.get("id")
        where = f"source {sid}"
        if not sid or sid in sources:
            out.append(_finding("error", where, "source_id", "missing or duplicate source id"))
            continue
        sources[sid] = s
        if s.get("type") not in SOURCE_TYPES:
            out.append(_finding("error", where, "source_type", f"type must be one of {SOURCE_TYPES}"))
        url = s.get("url")
        if url:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                out.append(_finding("error", where, "source_url", f"not a usable URL: {url!r}"))
        elif s.get("type") != "primary_game":
            out.append(_finding("error", where, "source_url", "non-game sources need a URL"))
        if s.get("type") == "primary_game" and not s.get("locator"):
            out.append(_finding("error", where, "source_locator",
                                "game sources need a locator (mission, dialogue line, location or timestamp)"))
        if not s.get("verified"):
            out.append(_finding("warning", where, "source_unverified",
                                "not yet opened and checked by a human"))

    claims = {}
    events = {}
    for c in dossier.get("claims", []):
        cid = c.get("id")
        where = f"claim {cid}"
        if not cid or cid in claims:
            out.append(_finding("error", where, "claim_id", "missing or duplicate claim id"))
            continue
        claims[cid] = c
        status = c.get("status")
        if status not in STATUSES:
            out.append(_finding("error", where, "claim_status", f"status must be one of {STATUSES}"))
            continue
        if not (c.get("text") or "").strip():
            out.append(_finding("error", where, "claim_text", "empty claim"))
        cont = c.get("continuity")
        if cont not in continuities:
            out.append(_finding("error", where, "continuity",
                                f"continuity {cont!r} isn't in this production's scope {continuities}"))
        for gid in c.get("games", []):
            g = games.get(gid)
            if not g:
                out.append(_finding("error", where, "game", f"unknown game id {gid!r}"))
            elif g["continuity"] != cont:
                out.append(_finding("error", where, "continuity_mix",
                                    f"{g['title']} is {g['continuity']} universe but the claim is {cont}; "
                                    f"cross-universe statements must be split per universe"))
        src_ids = c.get("source_ids", [])
        missing = [s for s in src_ids if s not in sources]
        if missing:
            out.append(_finding("error", where, "unknown_source", f"cites unknown source(s) {missing}"))
        cited = [sources[s] for s in src_ids if s in sources]
        if status == "confirmed_canon":
            if not any(s.get("type") in CANON_SOURCE_TYPES for s in cited):
                out.append(_finding("error", where, "canon_evidence",
                                    "confirmed canon needs a game or official source; downgrade it to "
                                    "interpretation or find primary evidence"))
            elif not any(s.get("type") in CANON_SOURCE_TYPES and s.get("verified") for s in cited):
                out.append(_finding("warning", where, "canon_unverified",
                                    "its game/official source hasn't been verified by a human yet"))
        elif status == "interpretation" and not cited:
            out.append(_finding("error", where, "missing_evidence",
                                "an interpretation must point at the evidence it interprets"))
        elif status == "fan_theory" and not cited:
            out.append(_finding("warning", where, "theory_unsourced",
                                "fan theory with no source: cite where the theory comes from"))
        spoiler = c.get("spoiler", "none")
        if spoiler not in SPOILERS:
            out.append(_finding("error", where, "spoiler", f"spoiler must be one of {SPOILERS}"))
        elif spoiler not in allowed_spoilers:
            out.append(_finding("error", where, "spoiler_level",
                                f"{spoiler} spoiler exceeds this production's '{production['spoiler_level']}' "
                                f"spoiler level; cut it or raise the level and add a warning"))
        if c.get("event") is not None and c.get("year") is not None:
            key = (cont, c["event"])
            if key in events and events[key][1] != c["year"]:
                out.append(_finding("error", where, "timeline_conflict",
                                    f"event {c['event']!r} dated {c['year']} here but {events[key][1]} "
                                    f"in claim {events[key][0]} (same {cont} continuity)"))
            events.setdefault(key, (cid, c["year"]))

    if not claims:
        out.append(_finding("error", "dossier", "empty", "no claims: research hasn't been done yet"))
    for q in dossier.get("open_questions", []):
        out.append(_finding("warning", "dossier", "open_question", q))

    errors = [f for f in out if f["level"] == "error"]
    warnings = [f for f in out if f["level"] == "warning"]
    by_status = {s: sum(1 for c in claims.values() if c.get("status") == s) for s in STATUSES}
    return {"errors": errors, "warnings": warnings, "passed": not errors,
            "stats": {"sources": len(sources), "claims": len(claims), **by_status}}


def dossier_markdown(dossier, report):
    """Human-review version of the dossier (stage 1 approval)."""
    srcs = {s["id"]: s for s in dossier.get("sources", [])}
    lines = [f"# Research dossier: {dossier.get('topic', '')}", ""]
    lines.append(f"Check: {'PASSED' if report['passed'] else 'FAILED'} - "
                 f"{len(report['errors'])} error(s), {len(report['warnings'])} warning(s). "
                 f"{report['stats']}")
    for title, status in (("Confirmed canon", "confirmed_canon"), ("Interpretation", "interpretation"),
                          ("Fan theory", "fan_theory"), ("Speculation", "speculation")):
        items = [c for c in dossier.get("claims", []) if c.get("status") == status]
        if not items:
            continue
        lines += ["", f"## {title}", ""]
        for c in items:
            cites = ", ".join(f"{s} ({srcs[s]['type']}{'' if srcs[s].get('verified') else ', UNVERIFIED'})"
                              for s in c.get("source_ids", []) if s in srcs) or "no source"
            lines.append(f"- **{c['id']}** [{c.get('continuity')}, spoiler: {c.get('spoiler', 'none')}] "
                         f"{c.get('text', '')}  \n  Evidence: {cites}")
    lines += ["", "## Sources", ""]
    for s in dossier.get("sources", []):
        loc = s.get("url") or s.get("locator", "")
        lines.append(f"- **{s['id']}** ({s.get('type')}) {s.get('title', '')}: {loc}"
                     f"{'' if s.get('verified') else ' (UNVERIFIED)'}")
    if report["errors"] or report["warnings"]:
        lines += ["", "## Flags for review", ""]
        for f in report["errors"] + report["warnings"]:
            lines.append(f"- [{f['level'].upper()}] {f['where']}: {f['rule']}: {f['detail']}")
    return "\n".join(lines) + "\n"


_WORD = re.compile(r"[a-z0-9']+")


def shingles(text, n=12):
    words = _WORD.findall(text.lower())
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}
