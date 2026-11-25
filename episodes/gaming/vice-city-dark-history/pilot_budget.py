"""Pilot spending ceiling for "The Dark History of Vice City" (production approval, 2026-11-25).

$15.00 covers EVERYTHING spent on this episode: the 60-second production test, retries and failed
requests (pending calls count at their estimate). It applies to this pilot only; default budgets in
the pipeline are unchanged.

Prints the --episode-budget to pass to the full-episode run (the ceiling minus what the test spent),
or exits non-zero without spending anything when the ledgers can't be trusted (fail closed).

Usage: python3 episodes/gaming/vice-city-dark-history/pilot_budget.py [--github-env FILE]
"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from modules.costs import GLOBAL_LEDGER_PATH, _read, ledger_total  # noqa: E402

CEILING = 15.00
# Test runs made before the episode ledger was carried between Actions runs (PR #24): runs
# 45521790385, 45547596599 and the first failed run. Recorded in REVIEW6/REVIEW7 packages.
PRE_LEDGER_TEST_SPEND = 1.03
HERE = os.path.dirname(os.path.abspath(__file__))
PILOT_NAME = os.path.basename(HERE)
TEST_DIR = os.path.join(os.path.dirname(HERE), "vice-city-60s-test")
TEST_NAME = os.path.basename(TEST_DIR)


class LedgerProblem(RuntimeError):
    pass


def project_totals(global_path):
    """Budget totals per project from the overall ledger (same counting rules as ledger_total)."""
    calls = {}
    for e in _read(global_path):
        calls.setdefault(e["call_id"], {}).update(e)
    out = {}
    for c in calls.values():
        if c.get("status") == "not_billed":
            continue
        est, act = c.get("estimate_usd") or 0.0, c.get("actual_usd")
        amount = max(est, act) if (c.get("status") == "done" and act is not None) else est
        out[c.get("project", "?")] = out.get(c.get("project", "?"), 0.0) + amount
    return out


def compute(global_path=None, test_ledger=None, pilot_ledger=None, ceiling=CEILING):
    global_path = global_path or os.environ.get("HO_SPEND_LEDGER") or GLOBAL_LEDGER_PATH
    test_ledger = test_ledger or os.path.join(TEST_DIR, "costs.jsonl")
    pilot_ledger = pilot_ledger or os.path.join(HERE, "costs.jsonl")
    if not os.path.exists(global_path):
        raise LedgerProblem(f"The overall spend ledger ({global_path}) wasn't restored, so earlier spending "
                            "can't be counted. Not starting; nothing was spent.")
    by_project = project_totals(global_path)
    test_spent = max(PRE_LEDGER_TEST_SPEND + ledger_total(test_ledger), by_project.get(TEST_NAME, 0.0))
    pilot_local = ledger_total(pilot_ledger)
    pilot_global = by_project.get(PILOT_NAME, 0.0)
    if pilot_global > pilot_local + 0.005:
        raise LedgerProblem(f"The overall ledger shows ${pilot_global:.2f} spent on this episode but its own "
                            f"ledger shows ${pilot_local:.2f}: the episode ledger was lost. Not starting; "
                            "nothing was spent.")
    remaining = round(ceiling - test_spent - pilot_local, 4)
    return {"ceiling": ceiling, "test_spent": round(test_spent, 4), "pilot_spent": round(pilot_local, 4),
            "cumulative": round(test_spent + pilot_local, 4), "remaining": remaining,
            # the pipeline's episode cap counts this episode's own ledger, so the cap is the ceiling
            # minus what the test spent
            "episode_budget": round(ceiling - test_spent, 4)}


def main(argv):
    try:
        r = compute()
    except LedgerProblem as e:
        print(f"::error::{e}")
        return 1
    print(json.dumps(r, indent=2))
    if r["remaining"] <= 0:
        print(f"::error::The ${r['ceiling']:.2f} pilot ceiling is used up (${r['cumulative']:.2f}). Nothing was spent.")
        return 1
    if "--github-env" in argv:
        with open(argv[argv.index("--github-env") + 1], "a") as f:
            f.write(f"EPISODE_BUDGET={r['episode_budget']:.2f}\nPILOT_SPENT_BEFORE={r['cumulative']:.2f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
