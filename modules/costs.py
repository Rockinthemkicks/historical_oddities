"""
Cost estimates and spend tracking for paid API calls.

PRICES ARE ESTIMATES. Figures below are OpenAI's published per-image output
prices for gpt-image-2 as listed in its image-generation guide, checked
2026-11-16. Reference-image edits also bill the input image tokens, covered
here by EDIT_INPUT_ALLOWANCE. Re-check https://platform.openai.com/docs/pricing
before relying on these, and update the table if they've changed.
"""
import json
import os
from datetime import datetime, timezone

# USD per generated image, by model -> quality -> size.
IMAGE_PRICES = {
    "gpt-image-2": {
        "low":    {"1024x1024": 0.006, "1536x1024": 0.005, "1024x1536": 0.005},
        "medium": {"1024x1024": 0.053, "1536x1024": 0.041, "1024x1536": 0.041},
        "high":   {"1024x1024": 0.211, "1536x1024": 0.165, "1024x1536": 0.165},
    },
}

# Extra allowance per image when a reference image is sent to the edit
# endpoint (input image tokens). Deliberately generous.
EDIT_INPUT_ALLOWANCE = 0.015

# Per-1M-token rates used to price the actual `usage` OpenAI returns.
TOKEN_RATES = {
    "gpt-image-2": {"text_input": 8.00, "image_input": 8.00, "image_output": 30.00},
}


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
    """Actual cost from an OpenAI image response's `usage` dict, or None."""
    rates = TOKEN_RATES.get(model)
    if not rates or not usage:
        return None
    details = usage.get("input_tokens_details") or {}
    text_in = details.get("text_tokens", usage.get("input_tokens", 0) - details.get("image_tokens", 0))
    image_in = details.get("image_tokens", 0)
    out = usage.get("output_tokens", 0)
    return (text_in * rates["text_input"] + image_in * rates["image_input"]
            + out * rates["image_output"]) / 1_000_000


class CostLedger:
    """
    Appends one line per paid call to <project>/costs.jsonl and enforces a
    per-run cap. Each call is charged at max(estimate, actual) so an
    under-estimate can't let a run blow past the cap.
    """

    def __init__(self, project_dir, cap_usd=None):
        self.path = os.path.join(project_dir, "costs.jsonl")
        self.cap = cap_usd
        self.spent = 0.0
        os.makedirs(project_dir, exist_ok=True)

    def check_room(self, next_cost):
        if self.cap is not None and self.spent + next_cost > self.cap + 1e-9:
            raise BudgetExceeded(
                f"Stopping: next call (~${next_cost:.3f}) would take this run past its "
                f"${self.cap:.2f} cap (spent so far ~${self.spent:.3f}). Raise --max-image-cost to continue; "
                f"finished images are kept and won't be regenerated.")

    def record(self, service, item, estimate, actual=None, extra=None):
        charged = max(estimate, actual or 0.0)
        self.spent += charged
        entry = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "service": service, "item": item, "estimate_usd": round(estimate, 5),
                 "actual_usd": None if actual is None else round(actual, 5)}
        if extra:
            entry.update(extra)
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return charged

    @staticmethod
    def total(project_dir):
        path = os.path.join(project_dir, "costs.jsonl")
        if not os.path.exists(path):
            return 0.0
        total = 0.0
        with open(path) as f:
            for line in f:
                e = json.loads(line)
                total += e["actual_usd"] if e.get("actual_usd") is not None else e["estimate_usd"]
        return total
