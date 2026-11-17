"""Narration caching and voice handling, with ElevenLabs faked (no network, no cost)."""
import base64
import json

import pytest

from modules import narration
from modules.costs import CostLedger, ledger_total

SCENES = [{"scene_number": 1, "narration": "In 1876, meat fell from the sky."},
          {"scene_number": 2, "narration": "Nobody knew why."},
          {"scene_number": 3, "narration": "Scientists had theories."}]


def alignment(text):
    chars = list(text)
    return {"characters": chars,
            "character_start_times_seconds": [i * 0.05 for i in range(len(chars))],
            "character_end_times_seconds": [(i + 1) * 0.05 for i in range(len(chars))]}


class FakeResp:
    status_code = 200
    headers = {}
    text = ""

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


@pytest.fixture
def fake_tts(monkeypatch):
    calls = []

    def fake_post(url, json=None, **kw):
        calls.append({"url": url, **json})
        return FakeResp({"audio_base64": base64.b64encode(b"ID3fake" + json["text"].encode()).decode(),
                         "alignment": alignment(json["text"])})

    monkeypatch.setattr(narration.requests, "post", fake_post)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice-A")
    return calls


def test_missing_voice_id_is_an_error(monkeypatch, tmp_path):
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    with pytest.raises(RuntimeError, match="No ElevenLabs voice set"):
        narration.generate_all_narration(SCENES, str(tmp_path))


def test_unchanged_rebuild_makes_no_calls(tmp_path, fake_tts):
    first = narration.generate_all_narration(SCENES, str(tmp_path / "audio"))
    assert len(fake_tts) == 3 and not any(r["cached"] for r in first)
    fake_tts.clear()
    again = narration.generate_all_narration(SCENES, str(tmp_path / "audio"))
    assert fake_tts == []
    assert all(r["cached"] for r in again)
    # word-level caption timing survives the cache
    assert [r["words"] for r in again] == [r["words"] for r in first]
    assert again[0]["words"][0]["word"] == "In"


def test_changed_text_regenerates_only_that_scene(tmp_path, fake_tts):
    narration.generate_all_narration(SCENES, str(tmp_path))
    fake_tts.clear()
    edited = [dict(s) for s in SCENES]
    edited[1]["narration"] = "Nobody could explain it."
    narration.generate_all_narration(edited, str(tmp_path))
    assert [c["text"] for c in fake_tts] == ["Nobody could explain it."]


@pytest.mark.parametrize("change", [{"voice_id": "voice-B"}, {"speed": 0.9}, {"seed": 7},
                                    {"model_id": "eleven_flash_v2_5"}])
def test_voice_settings_invalidate_cache(tmp_path, fake_tts, change):
    narration.generate_all_narration(SCENES, str(tmp_path))
    fake_tts.clear()
    narration.generate_all_narration(SCENES, str(tmp_path), **change)
    assert len(fake_tts) == 3


def test_renumbered_scenes_still_reuse_cache(tmp_path, fake_tts):
    narration.generate_all_narration(SCENES, str(tmp_path))
    fake_tts.clear()
    shifted = [{"scene_number": s["scene_number"] + 10, "narration": s["narration"]} for s in SCENES]
    out = narration.generate_all_narration(shifted, str(tmp_path))
    assert fake_tts == [] and (tmp_path / "scene11.mp3").exists() and out[0]["cached"]


def test_paid_calls_go_through_ledger(tmp_path, fake_tts, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_USD_PER_1K_CHARS", "0.30")
    ledger = CostLedger(str(tmp_path))
    narration.generate_all_narration(SCENES, str(tmp_path / "audio"), ledger=ledger)
    chars = sum(len(s["narration"]) for s in SCENES)
    assert ledger.episode_spent() == pytest.approx(chars / 1000 * 0.30)
    narration.generate_all_narration(SCENES, str(tmp_path / "audio"), ledger=ledger)
    assert ledger.episode_spent() == pytest.approx(chars / 1000 * 0.30)  # cache hit = $0


def test_api_error_not_billed_and_not_cached(tmp_path, monkeypatch):
    class Bad(FakeResp):
        status_code = 401

    monkeypatch.setattr(narration.requests, "post",
                        lambda url, **kw: Bad({"detail": "missing_permissions"}))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "v")
    ledger = CostLedger(str(tmp_path))
    with pytest.raises(narration.NarrationApiError, match="missing_permissions"):
        narration.generate_all_narration(SCENES, str(tmp_path / "audio"), ledger=ledger)
    assert ledger.episode_spent() == 0
    assert not list((tmp_path / "audio" / "cache").glob("*.mp3"))


def test_plan_reports_cached_and_cost(tmp_path, fake_tts):
    narration.generate_all_narration(SCENES[:2], str(tmp_path))
    plan = narration.plan_narration(SCENES, str(tmp_path), "voice-A")
    assert plan["cached"] == [1, 2] and plan["to_generate"] == [3]
    assert plan["characters"] == len(SCENES[2]["narration"])
