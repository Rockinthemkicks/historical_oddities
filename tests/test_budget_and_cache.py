"""Persistent budgets and manifest-based image reuse (API faked; no cost)."""
import json
import subprocess
import sys

import pytest

from modules import images
from modules.costs import BudgetExceeded, CostLedger, ledger_total
from tests.test_images import FakeResp, PROMPTS, SCENES  # noqa: F401  (fixture below re-declared)


@pytest.fixture
def fake_api(monkeypatch):
    calls = []

    def fake_post(url, **kw):
        calls.append(url)
        return FakeResp()

    monkeypatch.setattr(images.requests, "post", fake_post)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return calls


# ---- budgets ----

def test_restart_cannot_reset_overall_budget(tmp_path):
    first = CostLedger(str(tmp_path / "ep1"), total_cap=1.00)
    cid = first.begin("openai-image", "scene01", 0.60)
    first.finish(cid, 0.60, 0.60)
    # "Restart": brand-new ledger objects, even for a different episode.
    again = CostLedger(str(tmp_path / "ep2"), total_cap=1.00)
    assert again.total_spent() == pytest.approx(0.60)
    with pytest.raises(BudgetExceeded, match="overall"):
        again.check_room(0.50)


def test_episode_budget_persists_across_runs(tmp_path, fake_api):
    kw = dict(prompts=PROMPTS, project_dir=str(tmp_path), episode_budget=0.30)
    images.generate_all_images(SCENES, str(tmp_path / "images"), **kw)   # ~$0.21
    for f in (tmp_path / "images").glob("scene*.png"):
        f.unlink()  # force a second paid run of the same episode
    fake_api.clear()
    with pytest.raises(BudgetExceeded, match="episode"):
        images.generate_all_images(SCENES, str(tmp_path / "images"), **kw)
    assert fake_api == []  # refused before any call


def test_unfinished_call_counts_at_estimate(tmp_path):
    ledger = CostLedger(str(tmp_path))
    ledger.begin("openai-image", "scene01", 0.056)   # process "dies" here
    assert ledger_total(ledger.project_path) == pytest.approx(0.056)
    assert CostLedger(str(tmp_path)).total_spent() == pytest.approx(0.056)


def test_timeout_leaves_call_pending_and_charged(tmp_path, monkeypatch):
    import requests

    def boom(url, **kw):
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setattr(images.requests, "post", boom)
    monkeypatch.setattr(images, "IMAGE_MAX_RETRIES", 0)
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with pytest.raises(requests.exceptions.Timeout):
        images.generate_all_images(SCENES[:1], str(tmp_path / "img"), prompts=PROMPTS,
                                   use_reference=False, project_dir=str(tmp_path))
    assert ledger_total(str(tmp_path / "costs.jsonl")) > 0


def test_api_error_is_not_billed(tmp_path, monkeypatch):
    class Bad(FakeResp):
        status_code = 400

        def json(self):
            return {"error": {"message": "rejected"}}

    monkeypatch.setattr(images.requests, "post", lambda url, **kw: Bad())
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with pytest.raises(images.ImageApiError):
        images.generate_all_images(SCENES[:1], str(tmp_path / "img"), prompts=PROMPTS,
                                   use_reference=False, project_dir=str(tmp_path))
    assert ledger_total(str(tmp_path / "costs.jsonl")) == 0


def test_actual_above_estimate_counts_at_actual(tmp_path):
    ledger = CostLedger(str(tmp_path))
    cid = ledger.begin("openai-image", "scene01", 0.05)
    ledger.finish(cid, 0.05, 0.09)
    assert ledger.episode_spent() == pytest.approx(0.09)


# ---- manifest / cache invalidation ----

def run(tmp_path, **kw):
    args = dict(prompts=PROMPTS, project_dir=str(tmp_path))
    args.update(kw)
    return images.generate_all_images(SCENES, str(tmp_path / "images"), **args)


def test_unchanged_inputs_cost_nothing(tmp_path, fake_api):
    run(tmp_path)
    fake_api.clear()
    run(tmp_path)
    assert fake_api == []


def test_changed_prompt_regenerates_only_that_scene(tmp_path, fake_api):
    run(tmp_path)
    fake_api.clear()
    run(tmp_path, prompts={**PROMPTS, 2: "a different street"})
    assert len(fake_api) == 1
    assert (tmp_path / "images" / "_replaced" / "scene02_1.png").exists()


def test_changed_style_regenerates_everything(tmp_path, fake_api):
    run(tmp_path, style="A")
    fake_api.clear()
    run(tmp_path, style="B")
    assert len(fake_api) == 4  # reference + 3 scenes


def test_changed_quality_regenerates(tmp_path, fake_api):
    run(tmp_path)
    fake_api.clear()
    run(tmp_path, quality="low")
    assert len(fake_api) == 4


def test_unknown_or_edited_files_are_not_trusted(tmp_path, fake_api):
    img = tmp_path / "images"
    img.mkdir()
    (img / "scene01.png").write_bytes(b"not ours")      # no manifest entry
    run(tmp_path)
    assert (img / "_replaced" / "scene01_1.png").read_bytes() == b"not ours"
    fake_api.clear()
    (img / "scene03.png").write_bytes(b"edited by hand")  # sha no longer matches
    run(tmp_path)
    assert len(fake_api) == 1


def test_estimate_matches_plan_for_stale_files(tmp_path, fake_api):
    run(tmp_path)
    plan = images.plan_images(SCENES, str(tmp_path / "images"), {**PROMPTS, 3: "new"})
    assert plan["to_generate"] == ["scene03"] and plan["stale"] == ["scene03"]


# ---- main.py pre-flight ----

def test_main_refuses_when_overall_budget_nearly_used(tmp_path, isolated_global_ledger):
    with open(isolated_global_ledger, "w") as f:
        f.write(json.dumps({"call_id": "x", "status": "pending", "estimate_usd": 249.5}) + "\n")
    r = subprocess.run([sys.executable, "main.py", "--project", str(tmp_path / "p"),
                        "--skip-script", "--script-file", "episodes/london-beer-flood/script.json",
                        "--prompts-file", "episodes/london-beer-flood/batch_prompts.txt", "--ignore-lint"],
                       capture_output=True, text=True,
                       env={**__import__("os").environ, "ELEVENLABS_VOICE_ID": "test-voice"})
    assert r.returncode != 0 and "Not starting" in r.stderr and "overall" in r.stderr
