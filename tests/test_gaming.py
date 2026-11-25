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
    assert b["target_words"] == 1960 and b["min_words"] == 1560 and b["max_words"] == 2400


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


def test_pilot_dossier_is_structurally_valid_but_not_factually_verified():
    p = load_production(PILOT)
    d = json.load(open(os.path.join(os.path.dirname(PILOT), "research.json")))
    rep = validate_dossier(d, p)
    assert rep["structurally_valid"], rep["errors"]
    assert not rep["factually_verified"]               # structure passing never implies facts are checked
    assert rep["readiness_counts"]["verified"] == 0    # nothing checked in-game or by a human yet
    flagged = {e["claim"] for e in rep["escalate"]}
    assert {"C24", "C32", "C36"} <= flagged            # still need a human or in-game check
    assert rep["readiness"]["C40"] == "disputed"       # Forbes's agency: sources disagree
    assert rep["readiness"]["C01"] == rep["readiness"]["C02"] == "corroborated"  # official sources
    fan = [c for c in d["claims"] if c["status"] == "fan_theory"]
    assert fan and all(c["id"] == "C26" for c in fan)
    hd = [c for c in d["claims"] if c.get("continuity") == "HD"]
    assert hd and all(c["spoiler"] == "none" for c in hd)  # GTA VI stays setting-level
    assert 12 <= p["target_minutes"][0] and p["target_minutes"][1] <= 16


def _ev_dossier(evidence, families):
    sources = [{"id": sid, "type": "secondary", "url": "https://example.org/" + sid, "family": fam}
               for sid, fam in families.items()]
    return {"sources": sources, "claims": [{"id": "C1", "text": "x", "status": "interpretation",
                                            "continuity": "3D", "games": [], "spoiler": "none",
                                            "source_ids": list(families), "evidence": evidence}]}


def test_wiki_repetition_is_not_independent_corroboration():
    from modules.gaming.research import claim_readiness
    d = _ev_dossier([{"source_id": "A", "status": "matched", "passage": "p"},
                     {"source_id": "B", "status": "matched", "passage": "p"}],
                    {"A": "fan_wiki", "B": "fan_wiki"})
    srcs = {s["id"]: s for s in d["sources"]}
    assert claim_readiness(d["claims"][0], srcs) == "matched"
    srcs["B"]["family"] = "press"
    assert claim_readiness(d["claims"][0], srcs) == "corroborated"
    d["claims"][0]["evidence"].append({"source_id": "A", "status": "disputed", "passage": "q"})
    assert claim_readiness(d["claims"][0], srcs) == "disputed"


def test_matched_evidence_must_record_a_passage(prod_dir):
    _, p = dossier_and_prod(prod_dir)
    d = _ev_dossier([{"source_id": "A", "status": "matched"}], {"A": "fan_wiki"})
    rep = validate_dossier(d, p)
    assert any(e["rule"] == "evidence_passage" for e in rep["errors"])
    d["claims"][0]["evidence"][0]["status"] = "proven"
    assert any(e["rule"] == "evidence_status" for e in validate_dossier(d, p)["errors"])


def test_outline_dependencies_keep_single_family_claims():
    from modules.gaming.script_engine import outline_dependencies
    outline = {"chapters": [{"id": "ch01", "claim_ids": ["A", "B", "C", "D"]}]}
    deps = outline_dependencies(outline, {"A": "verified", "B": "matched", "C": "corroborated", "D": "unsupported"})
    assert [u["claim"] for u in deps[0]["unverified"]] == ["B", "C"]
    assert [o["claim"] for o in deps[0]["omit"]] == ["D"]


def test_chapter_prompt_sends_only_that_chapters_claims_without_evidence():
    from modules.gaming.script_engine import chapter_prompts, script_estimate
    p = load_production(PILOT)
    d = json.load(open(os.path.join(os.path.dirname(PILOT), "research.json")))
    outline = {"chapters": [{"id": "ch01", "title": "t", "target_words": 200, "claim_ids": ["C11"]},
                            {"id": "ch02", "title": "u", "target_words": 200, "claim_ids": ["C12"]}]}
    _, user = chapter_prompts(p, d, outline, outline["chapters"][0], [])
    sent = json.loads(user)["claims"]
    assert [c["id"] for c in sent] == ["C11"] and "evidence" not in sent[0] and "source_ids" not in sent[0]
    assert len(user) < 6000                      # not the whole dossier

    class Paid:
        is_paid = True
    est = script_estimate(Paid(), p, d, outline)
    assert 0 < est["expected_usd"] < est["worst_case_usd"] < 0.5


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
    assert (prod_dir / "publish" / "monetization_checklist.md").exists()
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


def test_violent_imagery_in_opening_seconds_warns(prod_dir):
    assert run(prod_dir, "outline", "--dry-run") == 0
    assert run(prod_dir, "write", "--dry-run") == 0
    s = json.load(open(prod_dir / "script.json"))
    s["scenes"][0]["visuals"][1]["prompt"] = "Atmospheric documentary scene of a shooting at the docks, blood on the pier"
    s["scenes"][-1]["visuals"][-1]["prompt"] = "Atmospheric documentary scene with blood on the pier at night"
    (prod_dir / "script.json").write_text(json.dumps(s))
    run(prod_dir, "storyboard")
    sb = json.load(open(prod_dir / "storyboard.json"))
    opening = [w for w in sb["warnings"] if "first 15s" in w]
    assert len(opening) == 1 and "scene 1" in opening[0]      # only the opening is held to the strict rule


# ---------- review 5: local typography, reuse, reframing, extra visuals ----------

def test_text_card_styles_render(tmp_path):
    from PIL import Image
    from modules.gaming.packaging import text_card
    for style, spec in [("stamp", {"heading": "1986", "lines": ["TWO YEARS LATER"]}),
                        ("rows", {"heading": "VICE CITY, 1984", "rows": [["THE SERGEANT", "x"], ["THE AGENT", "y"]]}),
                        ("title", {"heading": "THE DARK HISTORY OF VICE CITY", "lines": ["Before GTA 6"], "note": "n"})]:
        p = text_card({"style": style, **spec}, str(tmp_path / f"{style}.png"))
        assert Image.open(p).size == (1920, 1080)


def test_zoom_to_motion_is_validated():
    from modules.render import motion_for, _parse_zoom_to
    assert _parse_zoom_to("zoom_to:0.5,0.6") == (0.5, 0.6, 0.35)
    assert _parse_zoom_to("zoom_to:0.2,0.3,0.9") == (0.2, 0.3, 0.9)
    assert _parse_zoom_to("zoom_to:1.5,0.3") is None and _parse_zoom_to("zoom_in") is None
    assert motion_for(0, "zoom_to:0.5,0.5") == "zoom_to:0.5,0.5"
    with pytest.raises(ValueError):
        motion_for(0, "zoom_to:abc")


def test_local_kinds_are_never_paid():
    from modules.gaming.script_engine import GENERATED_KINDS, LOCAL_KINDS
    assert not set(GENERATED_KINDS) & set(LOCAL_KINDS)


def test_regenerated_assets_missing_on_disk_do_not_block(tmp_path):
    from modules.gaming import provenance
    m = provenance.load(str(tmp_path))
    card = tmp_path / "out" / "cards" / "v1.png"
    card.parent.mkdir(parents=True)
    card.write_bytes(b"x")
    provenance.register(str(tmp_path), m, "v1", str(card), "chapter_card", "pipeline", "generated", "card")
    card.unlink()
    rep = provenance.check(str(tmp_path), m, [])
    assert not rep["errors"]


# ---------- production test revisions (review 6) ----------

def test_weighted_segments_sum_to_frames_and_default_is_even():
    from modules.render import segment_frames
    assert segment_frames([{"path": "a"}, {"path": "b"}, {"path": "c"}], 10) == [4, 3, 3]
    w = segment_frames([{"weight": 1}, {"weight": 3}], 100)
    assert w == [25, 75] and sum(w) == 100


def test_phrased_captions_leave_no_one_word_cues():
    from modules.captions import build_caption_cues
    text = "Behind the neon and the oceanfront mansions, a corrupt sergeant, rival drug lords and an undercover agent working both sides had been shaping the city since at least 1984."
    words = [{"word": w, "start": i * 0.3, "end": i * 0.3 + 0.25} for i, w in enumerate(text.split())]
    cues = build_caption_cues([{"start": 0, "words": words}], max_words=7, max_chars=42, uppercase=False, phrased=True)
    assert all(len(" ".join(c["lines"]).split()) >= 2 for c in cues)
    assert all(min(len(l.split()) for l in c["lines"]) >= 2 for c in cues if len(c["lines"]) > 1)
    # original behaviour unchanged when not asked for
    old = build_caption_cues([{"start": 0, "words": words}], max_words=3, max_chars=16)
    assert old and all(len(" ".join(c["lines"]).split()) <= 3 for c in old)


def test_reveal_steps_follow_cue_words():
    from modules.gaming.packaging import reveal_steps
    from modules.gaming.pipeline import _reveal_segments
    card = {"rows": [["THE SERGEANT", "x", "sergeant"], ["THE AGENT", "y", "agent"]]}
    steps = [{"path": f"s{k}.png"} for k in range(len(reveal_steps(card)))]
    assert len(steps) == 3
    words = [{"word": w, "start": float(i), "end": i + 0.9} for i, w in enumerate("a corrupt sergeant, and an agent".split())]
    segs = _reveal_segments(steps, card, {"words": words}, 8.0)
    assert [round(s["weight"], 2) for s in segs] == [2.0, 3.0, 3.0]


def test_scene_pause_after_is_carried_into_script():
    from modules.gaming.script_engine import assemble_script
    prod = {"title": "t"}
    outline = {"chapters": [{"id": "ch01", "title": "A"}]}
    chapters = [{"chapter_id": "ch01", "segments": [
        {"narration": "One.", "claim_ids": [], "visuals": [{"kind": "chapter_card"}], "pause_after": 1.3},
        {"narration": "Two.", "claim_ids": [], "visuals": [{"kind": "chapter_card"}]}]}]
    sc = assemble_script(prod, outline, chapters)["scenes"]
    assert sc[0]["pause_after"] == 1.3 and "pause_after" not in sc[1]
