"""
Text-model calls for outline and chapter writing, routed through CostLedger.

OpenAIText calls the OpenAI Responses API. Every call is estimated, checked
against the run, episode and overall budgets, logged as pending before it
goes out and closed after with the tokens actually used. FixtureLLM returns
canned JSON for dry runs and tests and can never touch the network.
"""
import json
import os

import requests

from ..costs import text_unit_cost
from ..utils import post_with_retry

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class LLMError(RuntimeError):
    pass


def estimate_tokens(text):
    """Rough planning estimate: about 4 characters per token in English."""
    return max(1, len(text) // 4)


class OpenAIText:
    is_paid = True

    def __init__(self, model, ledger, api_key=None, max_retries=2):
        self.model = model
        self.ledger = ledger
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.max_retries = max_retries

    def estimate(self, system, user, max_output_tokens):
        return text_unit_cost(self.model, estimate_tokens(system + user), max_output_tokens)

    def complete_json(self, system, user, label, max_output_tokens=12000):
        if not self.api_key:
            raise LLMError("No OpenAI API key (OPENAI_API_KEY) for script generation")
        estimate = self.estimate(system, user, max_output_tokens)
        call_id = self.ledger.begin("openai-text", label, estimate,
                                    extra={"model": self.model, "max_output_tokens": max_output_tokens})
        payload = {"model": self.model, "instructions": system, "input": user,
                   "max_output_tokens": max_output_tokens,
                   "text": {"format": {"type": "json_object"}}}
        resp = post_with_retry(lambda: requests.post(
            OPENAI_RESPONSES_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload, timeout=600), max_retries=self.max_retries)
        if resp.status_code >= 400:
            self.ledger.not_billed(call_id, estimate, resp.text[:300])
            raise LLMError(f"OpenAI text API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        usage = data.get("usage") or {}
        actual = None
        if "input_tokens" in usage and "output_tokens" in usage:
            actual = text_unit_cost(self.model, usage["input_tokens"], usage["output_tokens"])
        self.ledger.finish(call_id, estimate, actual, usage)
        text = data.get("output_text") or "".join(
            part.get("text", "")
            for item in data.get("output", []) if item.get("type") == "message"
            for part in item.get("content", []) if part.get("type") == "output_text")
        if data.get("status") == "incomplete":
            raise LLMError(f"{label}: model stopped early ({data.get('incomplete_details')}); "
                           f"raise max_output_tokens or shorten the chapter")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"{label}: model didn't return valid JSON ({e})")


class FixtureLLM:
    """Offline stand-in: returns fixtures[label]. Used by --dry-run and tests."""
    is_paid = False

    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.calls = []

    def estimate(self, system, user, max_output_tokens):
        return 0.0

    def complete_json(self, system, user, label, max_output_tokens=12000):
        self.calls.append(label)
        if label not in self.fixtures:
            raise LLMError(f"dry run: no fixture for {label!r}")
        return json.loads(json.dumps(self.fixtures[label]))
