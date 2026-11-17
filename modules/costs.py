"""
Cost estimates, spend tracking and budget limits for paid API calls.

Spending is recorded in two append-only ledgers:
  - <project>/costs.jsonl            -> this episode's spend
  - the global ledger (see GLOBAL_LEDGER_PATH) -> spend across ALL projects

Both are read back at the start of every run, so restarting the pipeline (or
re-running an episode) can't reset a budget. Deleting a ledger file does
reset it; that is the only way, and it's deliberate.

Accounting is conservative:
  - Each call is written as "pending" BEFORE it is made, then closed as
    "done" (with the actual cost from the API's `usage`, when given) or
    "not_billed" (the API answered with an error, so no image was produced).
  - A pending entry that never got closed (crash, timeout, killed process) is
    counted at its estimate, because the provider may have billed it.
  - A done entry counts at max(estimate, actual) toward budgets, so a low
    estimate can't let spending creep past a cap. Reports show both.

PRICES ARE ESTIMATES. The gpt-image-2 figures for 1024x1024, 1536x1024 and
1024x1536 are the per-image output prices OpenAI's image-generation guide
lists, as quoted by two independent sources on 2026-11-16 (OpenAI's own page
couldn't be fetched from the build environment). 2048x1152 (true 16:9) is a
third-party figure only, marked UNVERIFIED. Re-check OpenAI's pricing page and
update this table before relying on it.
"""
import json
import os
import uuid
from datetime import datetime, timezone

# USD per generated image, by model -> quality -> size.
IMAGE_PRICES = {
    "gpt-image-2": {
        "low":    {"1024x1024": 0.006, "1536x1024": 0.005, "1024x1536": 0.005},
        "medium": {"1024x1024": 0.053, "1536x1024": 0.041, "1024x1536": 0.041,
                   "2048x1152": 0.0424},   # 2048x1152: UNVERIFIED third-party figure
        "high":   {"1024x1024": 0.211, "1536x1024": 0.165, "1024x1536": 0.165},
    },
}
UNVERIFIED_PRICES = {("gpt-image-2", "medium", "2048x1152")}

# Extra allowance per image when a reference image is sent to the edit
# endpoint (input image tokens). Deliberately generous.
EDIT_INPUT_ALLOWANCE = 0.015

# Per-1M-token rates used to price the actual `usage` OpenAI returns.
TOKEN_RATES = {
    "gpt-image-2": {"text_input": 5.00, "image_input": 8.00, "image_output": 30.00},
}

# ElevenLabs bills by character, at a rate that depends on your plan
# (published figures in 2026 range from about $0.08 to $0.30 per 1,000
# characters for Multilingual v2). The default is the conservative top of
# that range so budgets err on the safe side; set ELEVENLABS_USD_PER_1K_CHARS
# in .env to your plan's real effective rate.
NARRATION_USD_PER_1K_CHARS_DEFAULT = 0.30
# Credits per character by model (Flash/Turbo bill half).
NARRATION_CREDIT_MULTIPLIER = {"eleven_flash_v2_5": 0.5, "eleven_turbo_v2_5": 0.5}


def narration_unit_cost(characters, model_id="eleven_multilingual_v2"):
    rate = float(os.environ.get("ELEVENLABS_USD_PER_1K_CHARS", NARRATION_USD_PER_1K_CHARS_DEFAULT))
    return characters / 1000 * rate * NARRATION_CREDIT_MULTIPLIER.get(model_id, 1.0)


GLOBAL_LEDGER_PATH = os.environ.get(
    "HO_SPEND_LEDGER",
    os.path.join(os.path.expanduser("~"), ".historical_oddities", "spend_ledger.jsonl"),
)


class BudgetExceeded(RuntimeError):
    pass


def image_unit_cost(model, quality, size, with_reference):
    try:
        base = IMAGE_PRICES[model][quality][size]
    except KeyError:
        raise ValueError(f"No price on file for {model} / {quality} / {size}; add it to "
                         f"modules/costs.py IMAGE_PRICES before generating")
    return base + (EDIT_INPUT_ALLOWANCE if with_reference else 0.0)


def cost_from_usage(model, usage):
    """Actual cost from an OpenAI image response's `usage` dict, or None if unknown."""
    rates = TOKEN_RATES.get(model)
    if not rates or not usage or "output_tokens" not in usage:
        return None
    details = usage.get("input_tokens_details") or {}
    image_in = details.get("image_tokens", 0)
    text_in = details.get("text_tokens", max(0, usage.get("input_tokens", 0) - image_in))
    out = usage.get("output_tokens", 0)
    return (text_in * rates["text_input"] + image_in * rates["image_input"]
            + out * rates["image_output"]) / 1_000_000


def _read(path):
    entries = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries


def ledger_total(path):
    """
    Budget total for one ledger file: done -> max(estimate, actual),
    not_billed -> 0, pending with no close -> estimate.
    """
    calls = {}
    for e in _read(path):
        calls.setdefault(e["call_id"], {}).update(e)
    total = 0.0
    for c in calls.values():
        status = c.get("status")
        if status == "not_billed":
            continue
        est = c.get("estimate_usd") or 0.0
        act = c.get("actual_usd")
        total += max(est, act) if (status == "done" and act is not None) else est
    return total


def ledger_actual_total(path):
    """Best-known actual spend (actual where reported, else estimate) for reports."""
    calls = {}
    for e in _read(path):
        calls.setdefault(e["call_id"], {}).update(e)
    total = 0.0
    for c in calls.values():
        if c.get("status") == "not_billed":
            continue
        act = c.get("actual_usd")
        total += act if act is not None else (c.get("estimate_usd") or 0.0)
    return total


class CostLedger:
    """
    Enforces three limits, all checked before every paid call:
      run_cap     - this invocation only
      episode_cap - everything ever recorded in <project>/costs.jsonl
      total_cap   - everything ever recorded in the global ledger
    Any cap may be None (no limit).
    """

    def __init__(self, project_dir, run_cap=None, episode_cap=None, total_cap=None,
                 global_path=None):
        os.makedirs(project_dir, exist_ok=True)
        self.project_path = os.path.join(project_dir, "costs.jsonl")
        self.global_path = global_path or GLOBAL_LEDGER_PATH
        os.makedirs(os.path.dirname(self.global_path) or ".", exist_ok=True)
        self.project_name = os.path.basename(os.path.abspath(project_dir))
        self.run_cap, self.episode_cap, self.total_cap = run_cap, episode_cap, total_cap
        self.run_spent = 0.0

    # -- totals --
    def episode_spent(self):
        return ledger_total(self.project_path)

    def total_spent(self):
        return ledger_total(self.global_path)

    def check_room(self, next_cost):
        """Raises BudgetExceeded if spending `next_cost` more would break any cap."""
        checks = [
            ("this run's", self.run_cap, self.run_spent, "--max-run-cost"),
            ("this episode's", self.episode_cap, self.episode_spent(), "--episode-budget"),
            ("the overall", self.total_cap, self.total_spent(), "--total-budget"),
        ]
        for label, cap, spent, flag in checks:
            if cap is not None and spent + next_cost > cap + 1e-9:
                raise BudgetExceeded(
                    f"Stopping: ~${next_cost:.2f} more would take {label} spending to "
                    f"~${spent + next_cost:.2f}, over its ${cap:.2f} limit (already ~${spent:.2f}). "
                    f"Raise {flag} to continue; finished files are kept.")

    # -- recording --
    def _append(self, entry):
        line = json.dumps(entry) + "\n"
        for path in (self.project_path, self.global_path):
            with open(path, "a") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())

    def begin(self, service, item, estimate, extra=None):
        """Records a call as pending before it's made. Returns its call_id."""
        self.check_room(estimate)
        call_id = uuid.uuid4().hex
        entry = {"call_id": call_id, "status": "pending",
                 "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "project": self.project_name, "service": service, "item": item,
                 "estimate_usd": round(estimate, 5)}
        if extra:
            entry.update(extra)
        self._append(entry)
        self.run_spent += estimate  # provisional until closed
        return call_id

    def finish(self, call_id, estimate, actual=None, usage=None):
        self._append({"call_id": call_id, "status": "done",
                      "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "actual_usd": None if actual is None else round(actual, 5),
                      "usage": usage})
        if actual is not None and actual > estimate:
            self.run_spent += actual - estimate

    def not_billed(self, call_id, estimate, reason=""):
        self._append({"call_id": call_id, "status": "not_billed",
                      "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "reason": reason[:300]})
        self.run_spent -= estimate
