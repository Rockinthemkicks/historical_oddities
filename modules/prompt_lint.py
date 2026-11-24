"""
Quality gate 2: checks image prompts BEFORE any money is spent on them.

Encodes the rules from pipeline_prompt.md ("IMAGE-PROMPT PHRASING TO AVOID
GENERATION FAILURES", the character-block rule, the pre-flight scan) and the
style bible, so they're enforced by code instead of relying on a chat
session to remember them.

Severity:
  error   - would waste money or break consistency; blocks image generation
            (override with --ignore-lint)
  warning - worth a look, doesn't block

Usage:
  python3 -m modules.prompt_lint --script script.json --prompts batch_prompts.txt
"""
import argparse
import json
import re
import sys

from .image_prompts import _blocks, parse_batch_prompts

# Words the style bible says describe the OLD aged/sepia look. Any of these in
# a prompt fights config/style_prompt.txt. (docs/style_bible.md, "Color palette"
# and "Rendering technique".)
STYLE_CONFLICTS = [
    "sepia", "parchment", "aged paper", "textured paper", "paper texture", "notebook",
    "cross-hatch", "crosshatch", "pencil shading", "muted", "earthy", "earth tone",
    "earth-tone", "ochre", "soot", "cream", "restrained", "stick-figure", "stick figure",
]

# pipeline_prompt.md: conflict-coded and intensity words to avoid.
INTENSITY_WORDS = [
    "standoff", "aftermath", "battle", "clash", "violently", "brutal", "devastating",
    "massacre", "carnage", "slaughter", "horrific", "gruesome",
]

# Words that tend to trip safety filters even inside a negation list
# ("no blood, no gore..."). pipeline_prompt.md says to drop negations unless the
# scene literally shows something that needs them.
SENSITIVE_WORDS = [
    "blood", "bloody", "gore", "corpse", "corpses", "dead body", "dead bodies",
    "injury", "injuries", "wound", "wounds", "killed", "dying", "severed",
]

# Phrases that point back at a reference the API never sees.
REFERENCE_POINTERS = [
    "as established", "per reference", "the usual character", "same as before",
    "as in the reference", "master gen id", "gen id",
]

NON_GRAPHIC_FRAMES = ["non-graphic", "lighthearted", "light-hearted", "comedic",
                      "somber", "respectful", "playful", "whimsical", "atmospheric", "moody",
                      "documentary", "cinematic", "tense", "suspenseful"]

NON_ASCII_PUNCT = re.compile("[—–“”‘’…]")
CHAR_BLOCK = re.compile(r"^([A-Z][A-Z0-9 .'&-]{1,40}):\s+(.+)$", re.S)
MAX_PROMPT_CHARS = 3500


NEGATORS = ("no", "not", "without", "never", "avoid", "zero")


def _find(words, text, skip_negated=False):
    """
    Whole-word/phrase matches of `words` in `text`. With skip_negated, a match
    counts only if it isn't directly negated ("no paper texture", "without
    cross-hatching" are fine; style rules are allowed to forbid things).
    """
    low = text.lower()
    hits = []
    for w in words:
        for m in re.finditer(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            if skip_negated:
                before = re.findall(r"[a-z]+", low[max(0, m.start() - 40):m.start()])[-3:]
                if any(b in NEGATORS for b in before):
                    continue
            hits.append(w)
            break
    return hits


def character_blocks(prompts_text):
    """{LABEL: full block text} from the CHARACTER REFERENCE BLOCKS section, if any."""
    blocks = {}
    in_chars = False
    for b in _blocks(prompts_text):
        up = b.strip().upper().rstrip(":")
        if up == "CHARACTER REFERENCE BLOCKS":
            in_chars = True
            continue
        if up == "SCENE PROMPTS":
            break
        m = CHAR_BLOCK.match(b.strip())
        if in_chars and m:
            blocks[m.group(1).strip()] = b.strip()
    return blocks


def lint_prompt(n, p, errors, warnings, style_conflicts=STYLE_CONFLICTS, intensity_level="error",
                protected_terms=(), blocks=None):
    """Checks one prompt; appends findings. Shared by the historical and gaming checks."""
    def add(level, rule, detail):
        (errors if level == "error" else warnings).append({"scene": n, "rule": rule, "detail": detail})

    hits = _find(style_conflicts, p, skip_negated=True) if style_conflicts else []
    if hits:
        add("error", "style_conflict", f"old sepia/notebook-style words fight the locked style: {', '.join(hits)}")
    hits = _find(INTENSITY_WORDS, p)
    if hits:
        add(intensity_level, "intensity_words", f"conflict/intensity words (pipeline_prompt.md): {', '.join(hits)}")
    hits = _find(SENSITIVE_WORDS, p)
    if hits:
        add("warning", "sensitive_words", f"filter-sensitive words, even if negated: {', '.join(hits)}. "
            f"Keep only if the scene literally needs them")
    hits = _find(REFERENCE_POINTERS, p)
    if hits:
        add("error", "reference_pointer", f"points at something the image API never sees: {', '.join(hits)}")
    hits = _find([t.lower() for t in protected_terms], p, skip_negated=True)
    if hits:
        add("error", "protected_ip", f"names protected characters/brands ({', '.join(hits)}); describe an "
            f"original, unnamed figure or place instead")
    if NON_ASCII_PUNCT.search(p):
        add("error", "non_ascii", "em dash, en dash, curly quote or ellipsis character: use plain - and \" '")
    if not _find(NON_GRAPHIC_FRAMES, p[:250]):
        add("warning", "tone_frame", "doesn't state its tone up front (e.g. 'Lighthearted, non-graphic' "
            "or 'Somber, respectful, non-graphic') in the first sentence")
    if len(p) > MAX_PROMPT_CHARS:
        add("warning", "too_long", f"{len(p)} characters; long prompts drift and cost more input tokens")
    for label, block in (blocks or {}).items():
        if label.lower() in p.lower() and block not in p:
            add("error", "character_block", f"mentions {label} but doesn't include its reference block word for word")


def lint(scenes, prompts_text, style_text=""):
    """
    Returns {"errors": [...], "warnings": [...], "passed": bool}.
    Each finding: {"scene": n or None, "rule": str, "detail": str}.
    """
    errors, warnings = [], []

    def err(scene, rule, detail):
        errors.append({"scene": scene, "rule": rule, "detail": detail})

    def warn(scene, rule, detail):
        warnings.append({"scene": scene, "rule": rule, "detail": detail})

    numbers = [s["scene_number"] for s in scenes]
    if sorted(numbers) != list(range(1, len(numbers) + 1)):
        err(None, "scene_numbers", f"script scene numbers aren't 1..{len(numbers)} with no gaps: {numbers}")

    prompts = parse_batch_prompts(prompts_text) if prompts_text else {}
    own = {s["scene_number"]: (s.get("image_prompt") or "").strip() for s in scenes}
    effective = {n: own[n] or prompts.get(n, "") for n in numbers}

    missing = [n for n in numbers if not effective[n]]
    if missing:
        err(None, "prompt_count", f"no prompt for scene(s) {missing}")
    extra = sorted(set(prompts) - set(numbers))
    if extra:
        err(None, "prompt_count", f"prompt file has prompts for scene(s) {extra} that aren't in the script")

    blocks = character_blocks(prompts_text or "")

    for n in numbers:
        p = effective[n]
        if not p:
            continue
        lint_prompt(n, p, errors, warnings, blocks=blocks)

    if style_text:
        hits = _find(STYLE_CONFLICTS, style_text, skip_negated=True)
        if hits:
            err(None, "style_file", f"the style file itself contains old-style words: {', '.join(hits)}")

    return {"errors": errors, "warnings": warnings, "passed": not errors}


def format_report(report):
    lines = [f"Prompt check {'PASSED' if report['passed'] else 'FAILED'}: "
             f"{len(report['errors'])} error(s), {len(report['warnings'])} warning(s)"]
    for kind, items in (("ERROR", report["errors"]), ("warn ", report["warnings"])):
        for f in items:
            where = f"scene {f['scene']:02d}" if f["scene"] else "all     "
            lines.append(f"  [{kind}] {where} {f['rule']}: {f['detail']}")
    return "\n".join(lines)


def _main():
    p = argparse.ArgumentParser(description="Check image prompts before paying for them.")
    p.add_argument("--script", required=True)
    p.add_argument("--prompts", help="batch_prompts.txt (needed when image_prompt fields are empty)")
    p.add_argument("--style-file", help="Style text to check as well")
    a = p.parse_args()
    with open(a.script) as f:
        scenes = json.load(f)["scenes"]
    text = open(a.prompts, encoding="utf-8").read() if a.prompts else ""
    style = open(a.style_file, encoding="utf-8").read() if a.style_file else ""
    report = lint(scenes, text, style)
    print(format_report(report))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    _main()
