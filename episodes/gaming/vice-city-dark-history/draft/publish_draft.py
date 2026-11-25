"""Draft YouTube package for owner review after the full-episode render (free, local).
Writes out/publish_draft/: description.txt, chapters.txt, sources.json, monetization_checklist.md and
cost.json. This is a DRAFT for review, not the approved publishing package: `package` stays gated on the
owner approving the finished cut (stage 'assembly'), and uploading always needs separate authorization.
Usage: python3 publish_draft.py <production.json>"""
import json, os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.gaming.config import load_production
from modules.gaming.packaging import build_package
from modules.gaming import provenance
from modules.costs import ledger_actual_total, ledger_total

YOUTUBE_DESCRIPTION_LIMIT = 5000


def main(path):
    prod = load_production(path)
    d = prod["_dir"]
    script = json.load(open(os.path.join(d, "script.json")))
    dossier = json.load(open(os.path.join(d, "research.json")))
    qc = json.load(open(os.path.join(d, "out", "qc_report.json")))
    out = os.path.join(d, "out", "publish_draft")
    desc = build_package(prod, script, dossier, qc["chapters"], provenance.load(d), out)
    problems = []
    if len(desc) > YOUTUBE_DESCRIPTION_LIMIT:
        problems.append(f"description is {len(desc)} characters; YouTube allows {YOUTUBE_DESCRIPTION_LIMIT}")
    import pilot_budget
    budget = pilot_budget.compute()
    cost = {"this_episode_actual_usd": round(ledger_actual_total(os.path.join(d, "costs.jsonl")), 4),
            "this_episode_budget_count_usd": round(ledger_total(os.path.join(d, "costs.jsonl")), 4),
            "test_spent_usd": budget["test_spent"], "cumulative_usd": budget["cumulative"],
            "ceiling_usd": budget["ceiling"], "description_chars": len(desc), "problems": problems}
    json.dump(cost, open(os.path.join(out, "cost.json"), "w"), indent=2)
    print(json.dumps(cost, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
