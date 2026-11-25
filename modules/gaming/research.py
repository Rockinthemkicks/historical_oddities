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
                                                  | real_world_fact (release dates, sales: no continuity)
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
STATUSES = ("confirmed_canon", "interpretation", "fan_theory", "speculation", "real_world_fact")
# real_world_fact: facts about the real world (release dates, sales, inspirations), not
# in-universe canon. They need a non-community source and sit outside any continuity.
SPOILERS = ("none", "minor", "major")
# What a status needs as evidence.
CANON_SOURCE_TYPES = {"primary_game", "official"}


# Evidence ladder, weakest to strongest (ChatGPT editorial review, 2026-11-23).
EVIDENCE_STATUSES = ("discovered", "accessed", "matched", "primary_checked", "human_verified", "disputed")
_RANK = {s: i for i, s in enumerate(EVIDENCE_STATUSES[:-1])}
# Source families: sources in the same family are NOT independent corroboration
# (e.g. three fan wikis repeating each other count once).
FAMILIES = ("game", "official", "press", "encyclopedia", "fan_wiki", "community")
_DEFAULT_FAMILY = {"primary_game": "game", "official": "official", "community": "community"}


def source_family(src):
    return src.get("family") or _DEFAULT_FAMILY.get(src.get("type"), "fan_wiki")


def claim_evidence(claim, sources):
    """The claim's evidence records; claims without any get 'discovered'/'accessed' from source_ids."""
    if claim.get("evidence"):
        return claim["evidence"]
    out = []
    for sid in claim.get("source_ids", []):
        s = sources.get(sid, {})
        out.append({"source_id": sid, "status": "accessed" if s.get("read_by_assistant") else "discovered"})
    return out


def claim_readiness(claim, sources):
    """
    Factual standing of one claim, separate from structural validity:
      verified     - checked in the game, or verified by a human
      corroborated - supporting passages matched from 2+ independent families, or from an
                     official source (real-world facts) / the game itself
      matched      - a supporting passage matched, but from one family only
      unsupported  - found or opened, but nothing matched to the claim yet
      disputed     - some evidence contradicts it
    """
    ev = claim_evidence(claim, sources)
    if any(e.get("status") == "disputed" for e in ev):
        return "disputed"
    if any(e.get("status") in ("primary_checked", "human_verified") for e in ev):
        return "verified"
    matched = [e for e in ev if e.get("status") == "matched"]
    fams = {source_family(sources.get(e["source_id"], {})) for e in matched}
    if matched and (len(fams) >= 2 or fams & {"official", "game"}):
        return "corroborated"
    if matched:
        return "matched"
    return "unsupported"


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
        if s.get("family") and s["family"] not in FAMILIES:
            out.append(_finding("error", where, "source_family", f"family must be one of {FAMILIES}"))

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
        if status == "real_world_fact":
            cont = None
        elif cont not in continuities:
            out.append(_finding("error", where, "continuity",
                                f"continuity {cont!r} isn't in this production's scope {continuities}"))
        for gid in c.get("games", []):
            g = games.get(gid)
            if not g:
                out.append(_finding("error", where, "game", f"unknown game id {gid!r}"))
            elif cont is not None and g["continuity"] != cont:
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

        elif status == "real_world_fact" and not any(s.get("type") in ("official", "secondary") for s in cited):
            out.append(_finding("error", where, "missing_evidence",
                                "a real-world fact needs an official or reputable secondary source"))
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
        for e in c.get("evidence", []):
            if e.get("source_id") not in sources:
                out.append(_finding("error", where, "evidence_source", f"evidence cites unknown source {e.get('source_id')!r}"))
            if e.get("status") not in EVIDENCE_STATUSES:
                out.append(_finding("error", where, "evidence_status", f"status must be one of {EVIDENCE_STATUSES}"))
            elif e.get("status") in ("matched", "primary_checked", "human_verified", "disputed") \
                    and not (e.get("passage") or "").strip():
                out.append(_finding("error", where, "evidence_passage",
                                    "matched, checked or disputed evidence must record the passage (paraphrase)"))
        if cont is not None and c.get("event") is not None and c.get("year") is not None:
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

    # Factual standing is reported separately from structural validity.
    readiness = {cid: claim_readiness(c, sources) for cid, c in claims.items() if c.get("status") in STATUSES}
    escalate = []
    for cid, c in claims.items():
        r = readiness.get(cid)
        if r is None:
            continue
        if r == "disputed":
            escalate.append({"claim": cid, "reason": "evidence conflicts"})
        elif r == "unsupported" and c.get("status") != "speculation":
            escalate.append({"claim": cid, "reason": "no supporting passage matched yet"})
        elif c.get("risk") == "high" and r not in ("verified", "corroborated"):
            escalate.append({"claim": cid, "reason": "high-risk claim without independent or primary support"})
    errors = [f for f in out if f["level"] == "error"]
    warnings = [f for f in out if f["level"] == "warning"]
    by_status = {s: sum(1 for c in claims.values() if c.get("status") == s) for s in STATUSES}
    counts = {r: sum(1 for v in readiness.values() if v == r)
              for r in ("verified", "corroborated", "matched", "unsupported", "disputed")}
    factually_verified = bool(readiness) and all(
        v == "verified" or (v == "corroborated" and claims[k].get("risk") != "high")
        or claims[k].get("status") == "speculation" for k, v in readiness.items())
    return {"errors": errors, "warnings": warnings, "passed": not errors,
            "structurally_valid": not errors,
            "factually_verified": factually_verified,
            "readiness": readiness, "readiness_counts": counts, "escalate": escalate,
            "stats": {"sources": len(sources), "claims": len(claims), **by_status}}


def readiness_lines(report, approvals=None):
    """The four separate readiness levels. Passing one never implies the next."""
    approvals = approvals or {}
    counts = report.get("readiness_counts", {})
    return [
        "## Readiness",
        "",
        f"- Structural validation: {'PASSED' if report.get('structurally_valid', report['passed']) else 'FAILED'}"
        f" ({len(report['errors'])} error(s), {len(report['warnings'])} warning(s))",
        f"- Factual verification: {'COMPLETE' if report.get('factually_verified') else 'NOT COMPLETE'}"
        f" (verified {counts.get('verified', 0)}, corroborated {counts.get('corroborated', 0)},"
        f" single-family {counts.get('matched', 0)}, unsupported {counts.get('unsupported', 0)},"
        f" disputed {counts.get('disputed', 0)}; {len(report.get('escalate', []))} claim(s) need attention)",
        f"- Editorial approval: {'GIVEN' if approvals.get('editorial') else 'NOT GIVEN'}",
        f"- Production approval: {'GIVEN' if approvals.get('production') else 'NOT GIVEN'}",
    ]


def dossier_markdown(dossier, report, approvals=None):
    """Human-review version of the dossier (stage 1 approval)."""
    srcs = {s["id"]: s for s in dossier.get("sources", [])}
    readiness = report.get("readiness", {})
    lines = [f"# Research dossier: {dossier.get('topic', '')}", ""]
    if dossier.get("thesis"):
        lines += [f"Thesis: {dossier['thesis']}", ""]
    lines += readiness_lines(report, approvals) + ["", f"Stats: {report['stats']}"]
    for title, status in (("Real-world facts", "real_world_fact"), ("Confirmed canon", "confirmed_canon"),
                          ("Interpretation", "interpretation"), ("Fan theory", "fan_theory"),
                          ("Speculation", "speculation")):
        items = [c for c in dossier.get("claims", []) if c.get("status") == status]
        if not items:
            continue
        lines += ["", f"## {title}", ""]
        for c in items:
            ev = claim_evidence(c, srcs)
            cites = "; ".join(f"{e['source_id']} [{source_family(srcs.get(e['source_id'], {}))}] {e['status']}"
                              + (f": {e['passage']}" if e.get("passage") else "")
                              for e in ev) or "no source"
            scope = "real world" if status == "real_world_fact" else c.get("continuity")
            lines.append(f"- **{c['id']}** [{scope}, spoiler: {c.get('spoiler', 'none')}, "
                         f"standing: {readiness.get(c['id'], '-').upper()}"
                         + (f", risk: {c['risk']}" if c.get("risk") else "") + f"] "
                         f"{c.get('text', '')}  \n  Evidence: {cites}"
                         + (f"  \n  Note: {c['notes']}" if c.get("notes") else ""))
    lines += ["", "## Sources", ""]
    for s in dossier.get("sources", []):
        loc = s.get("url") or s.get("locator", "")
        state = "" if s.get("verified") else (" (READ BY ASSISTANT, not human-verified)"
                                              if s.get("read_by_assistant") else " (UNVERIFIED)")
        lines.append(f"- **{s['id']}** ({s.get('type')}, {source_family(s)}) {s.get('title', '')}: {loc}{state}"
                     + (f"  \n  Note: {s['notes']}" if s.get("notes") else ""))
    if report.get("escalate"):
        lines += ["", "## Claims needing attention before scripting", ""]
        for e in report["escalate"]:
            lines.append(f"- {e['claim']}: {e['reason']}")
    if report["errors"] or report["warnings"]:
        lines += ["", "## Flags for review", ""]
        for f in report["errors"] + report["warnings"]:
            lines.append(f"- [{f['level'].upper()}] {f['where']}: {f['rule']}: {f['detail']}")
    return "\n".join(lines) + "\n"


_WORD = re.compile(r"[a-z0-9']+")


def shingles(text, n=12):
    words = _WORD.findall(text.lower())
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}
