"""
Gaming-lore mode: configuration, research/canon checks, script schema, chapter
timing, provenance, costs, approvals, dry-run and rendering. Fully offline:
any attempt at a network call fails the test.
"""
import copy
import json
import os
import shutil
import subprocess
import sys

import pytest

from modules.gaming import pipeline, provenance, workflow
from modules.gaming.config import ConfigError, load_franchise, load_production, word_budget
from modules.gaming.packaging import chapter_markers, fmt_ts, validate_youtube_chapters
from modules.gaming.research import validate_dossier
from modules.gaming.script_engine import (assemble_script, validate_chapter, validate_outline)
from modules.costs import text_unit_cost
from modules.qc import check_video

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures", "gaming_synthetic")
PILOT = os.path.join(ROOT, "episodes", "gaming", "vice-city-dark-history", "production.json")
ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import requests

    def boom(*a, **k):
        raise AssertionError("network call attempted in an offline test")
    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setattr(requests, "get", boom)


@pytest.fixture
def prod_dir(tmp_path):
    d = tmp_path / "prod"
    shutil.copytree(FIX, d)
    return d


def run(prod_dir, *args):
    return pipeline.main(["--production", str(prod_dir / "production.json"), *args])


def fixtures(prod_dir):
    return json.load(open(prod_dir / "fixtures" / "llm.json"))


# ---------- configuration & backwards compatibility ----------

def test_historical_mode_is_default_and_unchanged():
    import main
    assert main._requested_mode([]) == "historical"
    assert main._requested_mode(["--mode", "gaming-lore"]) == "gaming-lore"
    r = subprocess.run([sys.executable, "main.py", "--mode", "banana"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode != 0 and "Unknown --mode" in r.stderr


def test_gta_franchise_continuities():
    gta = load_franchise("gta")
    assert set(gta["continuities"]) == {"2D", "3D", "HD"}
    by = {g["id"]: g["continuity"] for g in gta["games"]}
    assert by["gtavc"] == "3D" and by["gta6"] == "HD" and by["gta1"] == "2D"
    assert all("release" not in g for g in gta["games"])  # dates are verified, never hardcoded


def test_pilot_production_loads_with_landscape_defaults():
    prod = load_production(PILOT)
    assert prod["_continuities"] == ["2D", "3D", "HD"]
    assert prod["_settings"]["format"] == "landscape"
    assert prod["_settings"]["motion"] == "kenburns"
    b = word_budget(prod["target_minutes"])
    assert b["target_words"] == 3150 and b["min_words"] == 2600 and b["max_words"] == 3750


def test_production_rejects_game_outside_continuity(tmp_path):
    p = json.load(open(PILOT))
    p["continuity"] = "3D"  # but games include gta1 (2D) and gta6 (HD)
    path = tmp_path / "production.json"
    path.write_text(json.dumps(p))
    with pytest.raises(ConfigError, match="production doesn.t cover"):
        load_production(str(path))


def test_production_rejects_out_of_range_duration(tmp_path):
    p = json.load(open(PILOT))
    p["target_minutes"] = 5
    path = tmp_path / "production.json"
    path.write_text(json.dumps(p))
    with pytest.raises(ConfigError, match="outside"):
        load_production(str(path))


# ---------- research & canon ----------

def dossier_and_prod(prod_dir):
    return (json.load(open(prod_dir / "research.json")),
            load_production(str(prod_dir / "production.json")))


def test_fixture_dossier_passes(prod_dir):
    d, p = dossier_and_prod(prod_dir)
    rep = validate_dossier(d, p)
    assert rep["passed"], rep["errors"]
    assert rep["stats"]["confirmed_canon"] == 2 and rep["stats"]["fan_theory"] == 1


@pytest.mark.parametrize("mutate,rule", [
    (lambda d: d["claims"][0].update(source_ids=["S3"]), "canon_evidence"),        # canon from a forum
    (lambda d: d["claims"][0].update(continuity="remake"), "continuity_mix"),       # nh1 is classic
    (lambda d: d["claims"][3].update(spoiler="major"), "spoiler_level"),            # over 'light'
    (lambda d: d["claims"][1].update(event="blackout", year=1988), "timeline_conflict"),
    (lambda d: d["claims"][2].update(source_ids=["S9"]), "unknown_source"),
    (lambda d: d["claims"][2].update(source_ids=[]), "missing_evidence"),
    (lambda d: d["sources"][1].update(url="not a url"), "source_url"),
    (lambda d: d["sources"][0].pop("locator"), "source_locator"),
    (lambda d: d.update(claims=[]), "empty"),
])
def test_dossier_flags(prod_dir, mutate, rule):
    d, p = dossier_and_prod(prod_dir)
    mutate(d)
    rep = validate_dossier(d, p)
    assert not rep["passed"] and rule in {e["rule"] for e in rep["errors"]}


def test_pilot_dossier_is_valid_but_flags_every_unverified_source():
    p = load_production(PILOT)
    d = json.load(open(os.path.join(os.path.dirname(PILOT), "research.json")))
    rep = validate_dossier(d, p)
    assert rep["passed"], rep["errors"]
    unverified = [w for w in rep["warnings"] if w["rule"] == "source_unverified"]
    assert len(unverified) == len(d["sources"])          # nothing is marked verified by the assistant
    hd = [c for c in d["claims"] if c.get("continuity") == "HD"]
    assert hd and all(c["spoiler"] == "none" for c in hd)  # GTA VI stays setting-level


# ---------- outline & script schema ----------

def test_outline_budget_and_ids(prod_dir):
    d, p = dossier_and_prod(prod_dir)
    b = word_budget(p["target_minutes"])
    o = fixtures(prod_dir)["outline"]
    assert validate_outline(o, d, b)["passed"]
    bad = copy.deepcopy(o)
    bad["chapters"][0]["target_words"] = 500
    assert any("add up" in e for e in validate_outline(bad, d, b)["errors"])
    bad = copy.deepcopy(o)
    bad["chapters"][1]["id"] = "chapter2"
    assert not validate_outline(bad, d, b)["passed"]


def chapter_check(prod_dir, edit):
    d, _ = dossier_and_prod(prod_dir)
    fx = fixtures(prod_dir)
    ch = copy.deepcopy(fx["chapter:ch03"])
    edit(ch, d)
    return validate_chapter(ch, fx["outline"]["chapters"][2], d)


def test_valid_chapter_passes(prod_dir):
    assert chapter_check(prod_dir, lambda ch, d: None)["passed"]


def test_theory_without_hedging_fails(prod_dir):
    def edit(ch, d):
        ch["segments"][0]["narration"] = ("The Syndicate staged the blackout itself. It planned the outage "
                                          "for weeks and then moved everything under cover of darkness, "
                                          "which is why the docks went quiet that night.")
    rep = chapter_check(prod_dir, edit)
    assert any("without saying so" in e for e in rep["errors"])


def test_uncited_narration_fails(prod_dir):
    def edit(ch, d):
        ch["segments"][0]["claim_ids"] = []
    assert any("cite no claim" in e for e in chapter_check(prod_dir, edit)["errors"])


def test_copying_a_source_excerpt_fails(prod_dir):
    def edit(ch, d):
        ch["segments"][0]["narration"] += (" Some say the Saltworks Syndicate ran every night shipment that left "
                                           "the harbor and answered to no one on the waterfront, perhaps.")
    assert any("copies" in e for e in chapter_check(prod_dir, edit)["errors"])


def test_unknown_claim_and_bad_visual_fail(prod_dir):
    def edit(ch, d):
        ch["segments"][0]["claim_ids"].append("C99")
        ch["segments"][0]["visuals"].append({"kind": "illustration"})
    errs = chapter_check(prod_dir, edit)["errors"]
    assert any("C99" in e for e in errs) and any("needs a prompt" in e for e in errs)


def test_stock_phrases_warn(prod_dir):
    def edit(ch, d):
        ch["segments"][0]["narration"] = ch["segments"][0]["narration"].replace(
            "Some players go further.", "Let's dive in. Some players go further.")
    assert any("let's dive in" in w for w in chapter_check(prod_dir, edit)["warnings"])


def test_assembled_script_keeps_renderer_schema(prod_dir):
    _, p = dossier_and_prod(prod_dir)
    fx = fixtures(prod_dir)
    chapters = [fx[f"chapter:ch0{i}"] for i in (1, 2, 3)]
    s = assemble_script(p, fx["outline"], chapters)
    for i, sc in enumerate(s["scenes"], start=1):
        assert sc["scene_number"] == i and sc["narration"] and sc["image_prompt"] == ""
        assert sc["chapter"].startswith("ch") and sc["visuals"]
    ids = [v["id"] for sc in s["scenes"] for v in sc["visuals"]]
    assert len(ids) == len(set(ids))


# ---------- chapter timing ----------

def test_chapter_markers_and_youtube_rules():
    script = {"scenes": [{"chapter": "ch01", "chapter_title": "A"}, {"chapter": "ch01"},
                         {"chapter": "ch02", "chapter_title": "B"}, {"chapter": "ch03", "chapter_title": "C"}]}
    m = chapter_markers(script, [0.0, 12.0, 30.5, 61.0], 90.0)
    assert [x["start"] for x in m] == [0.0, 30.5, 61.0] and m[-1]["end"] == 90.0
    assert validate_youtube_chapters(m) == []
    assert validate_youtube_chapters(m[:2])                     # fewer than 3
    short = chapter_markers(script, [0.0, 1.0, 2.0, 5.0], 90.0)
    assert any("under 10" in p for p in validate_youtube_chapters(short))
    assert fmt_ts(61) == "1:01" and fmt_ts(3725) == "1:02:05"


# ---------- provenance ----------

def test_provenance_rules(tmp_path):
    d = tmp_path
    (d / "assets").mkdir()
    clip = d / "assets" / "clip.mp4"
    clip.write_bytes(b"x")
    song = d / "assets" / "bed.mp3"
    song.write_bytes(b"y")
    m = {"assets": []}
    provenance.register(str(d), m, "gp1", str(clip), "user_gameplay_video", "owner capture",
                        "unverified", "b-roll")
    provenance.register(str(d), m, "mus1", str(song), "licensed_music", "a library", "licensed", "ambient bed")
    rep = provenance.check(str(d), m, used_ids=["gp1", "ghost"], for_publication=True)
    errs = " ".join(rep["errors"])
    assert "gp1: rights unverified" in errs and "ghost" in errs and "mus1: licensed audio needs" in errs
    m["assets"][0]["permission_status"] = "publisher_policy"
    rep = provenance.check(str(d), m, used_ids=["gp1"])
    assert any("owner must accept" in w for w in rep["warnings"])
    clip.write_bytes(b"changed")
    assert any("file changed" in w for w in provenance.check(str(d), m)["warnings"])


# ---------- costs, estimate-only and approvals ----------

def test_text_costs():
    assert text_unit_cost("gpt-5.4", 1_000_000, 0) == 2.50
    assert text_unit_cost("gpt-5.4", 0, 1_000_000) == 15.00
    with pytest.raises(ValueError):
        text_unit_cost("unknown-model", 1, 1)


def test_paid_commands_need_approvals(prod_dir):
    for cmd in ("outline", "write", "produce", "package"):
        with pytest.raises(SystemExit, match="approval"):
            run(prod_dir, cmd)


def test_estimate_only_never_calls_paid_apis(prod_dir, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    assert run(prod_dir, "check-research") == 0
    workflow.approve(str(prod_dir), "research")
    assert run(prod_dir, "outline", "--estimate-only") == 0     # real client built, never called
    assert not (prod_dir / "costs.jsonl").exists()


def test_approval_is_invalidated_by_edits(prod_dir):
    workflow.approve(str(prod_dir), "research")
    assert workflow.is_approved(str(prod_dir), "research")
    d = json.load(open(prod_dir / "research.json"))
    d["claims"][0]["text"] += " (edited)"
    (prod_dir / "research.json").write_text(json.dumps(d))
    assert not workflow.is_approved(str(prod_dir), "research")


def test_storyboard_blocks_protected_ip_and_missing_assets(prod_dir):
    assert run(prod_dir, "outline", "--dry-run") == 0
    assert run(prod_dir, "write", "--dry-run") == 0
    s = json.load(open(prod_dir / "script.json"))
    s["scenes"][0]["visuals"][1]["prompt"] = "Atmospheric documentary portrait of Captain Vex on the docks"
    s["scenes"][1]["visuals"].append({"id": "v099", "kind": "user_asset", "asset_id": "gp-missing"})
    (prod_dir / "script.json").write_text(json.dumps(s))
    assert run(prod_dir, "storyboard") == 1
    sb = json.load(open(prod_dir / "storyboard.json"))
    errs = " ".join(sb["errors"])
    assert "protected_ip" in errs and "gp-missing" in errs
    with pytest.raises(SystemExit, match="storyboard"):
        run(prod_dir, "produce", "--dry-run")


# ---------- full dry run + rendering ----------

@ffmpeg
def test_full_dry_run_pipeline(prod_dir):
    for cmd in ("check-research", "outline", "write", "storyboard", "estimate", "produce", "package"):
        args = [cmd] if cmd in ("check-research", "storyboard", "estimate") else [cmd, "--dry-run"]
        assert run(prod_dir, *args) == 0, cmd
    rep = json.load(open(prod_dir / "out" / "qc_report.json"))
    assert rep["dry_run"] and rep["qc"]["passed"] and rep["spent_this_run_usd"] == 0
    assert len(rep["chapters"]) == 3 and rep["chapters"][0]["start"] == 0
    assert rep["chapter_problems"] == []
    assert check_video(str(prod_dir / "out" / "documentary.mp4"), expected_size=(640, 360))["passed"]
    desc = open(prod_dir / "publish" / "description.txt").read()
    assert "0:00 Three Dark Days" in desc and "example.com/neon-harbor/manual" in desc
    assert "Not affiliated" in desc
    assert not (prod_dir / "costs.jsonl").exists()               # nothing was ever spent
    # re-running is free and reuses every rendered scene
    assert run(prod_dir, "produce", "--dry-run") == 0


@ffmpeg
def test_mixed_still_and_video_with_ambient_bed(tmp_path):
    from PIL import Image
    from modules.render import render_episode
    img = tmp_path / "a.png"
    Image.new("RGB", (640, 360), (200, 60, 60)).save(img)
    clip = tmp_path / "gameplay.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25",
                    "-t", "0.8", "-pix_fmt", "yuv420p", str(clip)], check=True)  # shorter than its slot: loops
    voice = tmp_path / "v.m4a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=300:d=3",
                    "-c:a", "aac", str(voice)], check=True)
    bed = tmp_path / "bed.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=90:d=1",
                    "-c:a", "libmp3lame", str(bed)], check=True)
    scenes = [{"image_paths": [str(img), {"path": str(clip)}], "duration": 2.0},
              {"image_paths": [{"path": str(img), "motion": "none"}], "duration": 1.0}]
    res = render_episode(scenes, str(voice), [], str(tmp_path / "out.mp4"), str(tmp_path / "cache"),
                         size=(640, 360), fps=15, motion="kenburns",
                         ambient={"path": str(bed), "gain_db": -20})
    assert res["scene_starts"] == [0.0, 2.0]
    assert check_video(res["path"], expected_size=(640, 360), expected_duration=3.0,
                       duration_tolerance=0.2)["passed"]
