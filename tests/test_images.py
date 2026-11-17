"""Image generation with the OpenAI API faked out: no network, no cost."""
import base64
import io
import json

import pytest
from PIL import Image

from modules import images
from modules.costs import BudgetExceeded, CostLedger, ledger_total
from modules.image_prompts import parse_batch_prompts, resolve_scene_prompts

PNG = io.BytesIO()
Image.new("RGB", (8, 8), (255, 0, 0)).save(PNG, format="PNG")
PNG_B64 = base64.b64encode(PNG.getvalue()).decode()


class FakeResp:
    status_code = 200
    headers = {}
    text = ""

    def json(self):
        return {"data": [{"b64_json": PNG_B64}],
                "usage": {"input_tokens": 100, "output_tokens": 1000,
                          "input_tokens_details": {"text_tokens": 100, "image_tokens": 0}}}


@pytest.fixture
def fake_api(monkeypatch):
    calls = []

    def fake_post(url, **kw):
        calls.append({"url": url, **kw})
        return FakeResp()

    monkeypatch.setattr(images.requests, "post", fake_post)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return calls


SCENES = [{"scene_number": n, "narration": "x", "image_prompt": ""} for n in (1, 2, 3)]
PROMPTS = {1: "a flood", 2: "a street", 3: "a courtroom"}


def test_parse_prefixed_batch_prompts():
    text = "﻿scene01.png - First prompt\nwrapped line\n\nscene02.png - Second\n"
    assert parse_batch_prompts(text) == {1: "First prompt wrapped line", 2: "Second"}


def test_parse_character_block_layout():
    text = ("CHARACTER REFERENCE BLOCKS\n\nCITIZEN: round head\n\nSCENE PROMPTS\n\n"
            "Opening scene\n\nSecond scene\n")
    assert parse_batch_prompts(text) == {1: "Opening scene", 2: "Second scene"}


def test_real_episode_prompt_files_cover_every_scene():
    for ep in ["london-beer-flood", "boston-molasses-flood", "lake-peigneur",
               "niagara-falls-stopped", "kentucky-meat-shower"]:
        script = json.load(open(f"episodes/{ep}/script.json"))
        prompts = resolve_scene_prompts(script["scenes"], f"episodes/{ep}/batch_prompts.txt")
        assert len(prompts) == len(script["scenes"]), ep


def test_missing_prompt_is_caught_before_any_call(fake_api):
    with pytest.raises(ValueError, match=r"\[3\]"):
        images.generate_all_images(SCENES, "unused", prompts={1: "a", 2: "b", 3: ""})
    assert fake_api == []


def test_generates_reference_then_scenes_with_style(tmp_path, fake_api):
    out = tmp_path / "images"
    res = images.generate_all_images(SCENES, str(out), prompts=PROMPTS, style="BRIGHT STYLE",
                                     project_dir=str(tmp_path))
    assert [r["scene_number"] for r in res] == [1, 2, 3]
    assert (out / "reference.png").exists() and (out / "scene03.png").exists()
    assert fake_api[0]["url"] == images.OPENAI_GENERATE_URL
    assert all(c["url"] == images.OPENAI_EDIT_URL for c in fake_api[1:])
    assert fake_api[1]["data"]["prompt"].startswith("BRIGHT STYLE")
    assert fake_api[1]["data"]["size"] == "1536x1024"
    assert fake_api[1]["data"]["quality"] == "medium"
    log = [json.loads(l) for l in open(tmp_path / "costs.jsonl")]
    done = [e for e in log if e["status"] == "done"]
    assert len(done) == 4 and all(e["actual_usd"] > 0 for e in done)
    assert len([e for e in log if e["status"] == "pending"]) == 4  # written before each call


def test_rerun_skips_finished_images(tmp_path, fake_api):
    out = tmp_path / "images"
    images.generate_all_images(SCENES, str(out), prompts=PROMPTS, project_dir=str(tmp_path))
    (out / "scene02.png").unlink()
    fake_api.clear()
    images.generate_all_images(SCENES, str(out), prompts=PROMPTS, project_dir=str(tmp_path))
    assert len(fake_api) == 1  # only scene 2; reference and the rest reused


def test_user_reference_image_is_used(tmp_path, fake_api):
    ref = tmp_path / "my_ref.png"
    ref.write_bytes(PNG.getvalue())
    images.generate_all_images(SCENES, str(tmp_path / "img"), prompts=PROMPTS,
                               reference_image=str(ref), project_dir=str(tmp_path))
    assert all(c["url"] == images.OPENAI_EDIT_URL for c in fake_api)
    assert len(fake_api) == 3


def test_estimate_over_cap_refuses_before_spending(tmp_path, fake_api):
    with pytest.raises(BudgetExceeded):
        images.generate_all_images(SCENES, str(tmp_path / "img"), prompts=PROMPTS,
                                   quality="high", max_cost=0.10, project_dir=str(tmp_path))
    assert fake_api == []


def test_ledger_stops_mid_run(tmp_path):
    ledger = CostLedger(str(tmp_path), run_cap=0.10)
    cid = ledger.begin("x", "a", 0.06)
    ledger.finish(cid, 0.06, 0.05)
    with pytest.raises(BudgetExceeded):
        ledger.check_room(0.06)


def test_api_error_message_is_readable(tmp_path, monkeypatch):
    class Bad(FakeResp):
        status_code = 400

        def json(self):
            return {"error": {"message": "Your request was rejected by the safety system"}}

    monkeypatch.setattr(images.requests, "post", lambda url, **kw: Bad())
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with pytest.raises(RuntimeError, match="safety system"):
        images.generate_all_images(SCENES, str(tmp_path / "img"), prompts=PROMPTS,
                                   use_reference=False, project_dir=str(tmp_path))
    assert not list((tmp_path / "img").glob("*.png"))


def test_main_estimate_only_spends_nothing(tmp_path):
    import subprocess, sys, os
    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    env["ELEVENLABS_VOICE_ID"] = "test-voice"
    r = subprocess.run([sys.executable, "main.py", "--project", str(tmp_path / "p"),
                        "--skip-script", "--script-file", "episodes/london-beer-flood/script.json",
                        "--prompts-file", "episodes/london-beer-flood/batch_prompts.txt", "--ignore-lint",
                        "--estimate-only"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert "estimated $" in r.stdout and "nothing was generated" in r.stdout.lower()
    assert not (tmp_path / "p" / "costs.jsonl").exists()


def test_main_refuses_over_cap(tmp_path):
    import subprocess, sys
    r = subprocess.run([sys.executable, "main.py", "--project", str(tmp_path / "p"),
                        "--skip-script", "--script-file", "episodes/london-beer-flood/script.json",
                        "--prompts-file", "episodes/london-beer-flood/batch_prompts.txt", "--ignore-lint",
                        "--image-quality", "high", "--max-image-cost", "1"],
                       capture_output=True, text=True,
                       env={**__import__("os").environ, "ELEVENLABS_VOICE_ID": "test-voice"})
    assert r.returncode != 0 and "over its $1.00 limit" in r.stderr
    assert not (tmp_path / "p" / "audio").exists()  # narration never started
