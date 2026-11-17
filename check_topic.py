#!/usr/bin/env python3
"""
Topic dedup checker for the video pipeline.

Keeps a small local log (topics_log.json) of every topic/title you've
already produced a video for, and lets you check a new candidate topic
against it before you start writing a new script.

This is intentionally NOT a semantic/embedding matcher -- it's a cheap
token-overlap heuristic meant to catch near-duplicates and flag them for
a human (or an LLM reading the --list output) to make the real judgment
call. It will have false positives and false negatives; treat its output
as "worth a second look," not a verdict.

Usage:
  # See everything logged so far (good to paste into a chat session
  # before drafting a new script, so an LLM can judge duplicates too)
  python3 check_topic.py --list

  # Check a candidate topic against the log
  python3 check_topic.py --check "The man who survived two atomic bombs"

  # Log a topic as soon as it's approved (right after Stage 0), before
  # writing the script -- not just on the ones you finish
  python3 check_topic.py --add "The Dancing Plague of 1518" \
      --topic "mass dancing mania in 16th century Strasbourg" \
      --project out/dancing_plague
"""
import argparse
import difflib
import json
import os
import re
import sys
from datetime import date

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topics_log.json")

STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "and", "or", "who",
    "that", "which", "is", "was", "were", "with", "for", "from", "as",
    "by", "it", "its", "this", "these", "those", "how", "why", "what",
    "when", "where", "did", "does", "do", "man", "woman", "people",
    "story", "history", "true", "real", "one", "two", "s",
}

FLAG_THRESHOLD = 0.30  # jaccard/sequence score above this gets flagged


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    return tokens


def load_log():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH) as f:
        return json.load(f)


def save_log(entries):
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def similarity(a_tokens, a_text, b_tokens, b_text):
    """Combine token-set overlap with a plain string-similarity ratio,
    and take the max -- catches both 'same words, different order' and
    'same phrase, mostly reworded' cases a bit better than either alone."""
    set_a, set_b = set(a_tokens), set(b_tokens)
    if set_a or set_b:
        jaccard = len(set_a & set_b) / len(set_a | set_b) if (set_a | set_b) else 0.0
    else:
        jaccard = 0.0
    ratio = difflib.SequenceMatcher(None, a_text, b_text).ratio()
    return max(jaccard, ratio)


def cmd_list(entries):
    if not entries:
        print("No topics logged yet.")
        return
    print(f"{len(entries)} topic(s) logged:\n")
    for e in entries:
        line = f"- {e['title']}"
        if e.get("topic"):
            line += f"  ({e['topic']})"
        if e.get("date"):
            line += f"  [{e['date']}]"
        print(line)


def cmd_check(entries, candidate):
    cand_norm = candidate.lower().strip()
    cand_tokens = normalize(candidate)

    scored = []
    for e in entries:
        combined_text = f"{e['title']} {e.get('topic', '')}".strip()
        combined_tokens = normalize(combined_text)
        score = similarity(cand_tokens, cand_norm, combined_tokens, combined_text.lower())
        scored.append((score, e))

    scored.sort(key=lambda x: x[0], reverse=True)

    flagged = [s for s in scored if s[0] >= FLAG_THRESHOLD]

    print(f"Checking: {candidate!r}\n")
    if not flagged:
        print("No likely duplicates found against the logged topics.")
    else:
        print("Possible overlap with existing topics (review before proceeding):\n")
        for score, e in flagged:
            marker = "!!" if score >= 0.6 else "! "
            print(f"  {marker} {score:.2f}  {e['title']}" + (f"  ({e['topic']})" if e.get("topic") else ""))

    if scored and not flagged:
        top_score, top_e = scored[0]
        print(f"\n(Closest existing topic was only {top_score:.2f}: {top_e['title']!r})")

    print(
        "\nNote: this is a keyword-overlap heuristic, not a meaning check. "
        "If you're running this inside a chat session, also paste the --list "
        "output and ask the model to judge whether the new topic overlaps "
        "with anything on it -- that catches reworded duplicates this script misses."
    )


def cmd_add(entries, title, topic, project):
    entries.append({
        "title": title,
        "topic": topic or "",
        "project": project or "",
        "date": date.today().isoformat(),
    })
    save_log(entries)
    print(f"Logged: {title!r}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="Print every logged topic/title")
    g.add_argument("--check", metavar="TOPIC", help="Check a candidate topic against the log")
    g.add_argument("--add", metavar="TITLE", help="Log a newly-approved title")
    p.add_argument("--topic", help="Short topic description (used with --add, improves matching)")
    p.add_argument("--project", help="Project folder name (used with --add, for your own reference)")
    args = p.parse_args()

    entries = load_log()

    if args.list:
        cmd_list(entries)
    elif args.check:
        cmd_check(entries, args.check)
    elif args.add:
        cmd_add(entries, args.add, args.topic, args.project)


if __name__ == "__main__":
    main()
