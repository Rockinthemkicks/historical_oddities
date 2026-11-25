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
    assert b["target_words"] == 1540 and b["min_words"] == 1300 and b["max_words"] == 1800


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
    assert not {"C24", "C32", "C36"} & flagged        # all resolved in review 8 (corroborated)
    assert rep["readiness"]["C24"] == rep["readiness"]["C32"] == "corroborated"  # resolved in review 8
    assert rep["readiness"]["C40"] == "disputed"       # Forbes's agency: sources disagree
    assert rep["readiness"]["C01"] == rep["readiness"]["C02"] == "corroborated"  # official sources
    fan = [c for c in d["claims"] if c["status"] == "fan_theory"]
    assert fan and all(c["id"] == "C26" for c in fan)
    hd = [c for c in d["claims"] if c.get("continuity") == "HD"]
    assert hd and all(c["spoiler"] == "none" for c in hd)  # GTA VI stays setting-level
    assert p["target_minutes"] == [10, 12]          # review 6: 10-12 minutes, no filler


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


# ---------- brand (Unplayed History) ----------

def test_brand_defaults_keep_the_original_look(tmp_path):
    from modules.gaming.brand import load_brand
    b = load_brand(str(tmp_path / "missing.json"))
    assert b["name"] == "Unplayed History" and b["logo"] is None
    assert b["colors"]["accent"] == (214, 170, 80)


def test_brand_colors_and_logo_apply_to_cards(tmp_path, monkeypatch):
    from PIL import Image
    from modules.gaming.brand import load_brand
    from modules.gaming.packaging import text_card
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (200, 100), (255, 0, 0, 255)).save(logo)
    cfg = tmp_path / "brand.json"
    cfg.write_text(json.dumps({"name": "Unplayed History", "tagline": "t", "logo": str(logo),
                               "colors": {"accent": "#00FF00", "background": "#000"}}))
    monkeypatch.setenv("UH_BRAND_FILE", str(cfg))
    b = load_brand()
    assert b["colors"]["accent"] == (0, 255, 0) and b["colors"]["background"] == (0, 0, 0) and b["logo"]
    out = text_card({"style": "title", "heading": "X"}, str(tmp_path / "t.png"))
    im = Image.open(out).convert("RGB")
    m = int(im.width * 0.04)
    r, g, b_ = im.getpixel((im.width - m - 5, m + 5))
    assert r > 200 and g < 30 and b_ < 30  # logo (90% opacity), top right


# ---- production approval (2026-11-25): full-episode safeguards, offline ----

PILOT_DIR = os.path.join(ROOT, "episodes", "gaming", "vice-city-dark-history")


def _pilot_budget():
    import importlib.util
    spec = importlib.util.spec_from_file_location("pilot_budget", os.path.join(PILOT_DIR, "pilot_budget.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ledger_line(path, call_id, project, est, status="pending", actual=None):
    with open(path, "a") as f:
        f.write(json.dumps({"call_id": call_id, "status": "pending", "project": project, "estimate_usd": est}) + "\n")
        if status != "pending":
            f.write(json.dumps({"call_id": call_id, "status": status, "actual_usd": actual}) + "\n")


def test_pilot_budget_fails_closed_without_overall_ledger(tmp_path):
    pb = _pilot_budget()
    with pytest.raises(pb.LedgerProblem):
        pb.compute(str(tmp_path / "missing.jsonl"), str(tmp_path / "t.jsonl"), str(tmp_path / "p.jsonl"))


def test_pilot_budget_counts_test_spend_retries_and_failures(tmp_path):
    pb = _pilot_budget()
    g, t, p = tmp_path / "g.jsonl", tmp_path / "t.jsonl", tmp_path / "p.jsonl"
    _ledger_line(g, "old", "vice-city-60s-test", 1.03, "done", 1.03)       # pre-ledger test runs
    for path in (g, t):
        _ledger_line(path, "speed08", "vice-city-60s-test", 0.24, "done", 0.24)
        _ledger_line(path, "failed", "vice-city-60s-test", 0.05)           # never closed: counts
        _ledger_line(path, "refused", "vice-city-60s-test", 0.05, "not_billed")
    for path in (g, p):
        _ledger_line(path, "img1", "vice-city-dark-history", 2.00, "done", 2.10)
    r = pb.compute(str(g), str(t), str(p))
    assert r["test_spent"] == pytest.approx(1.03 + 0.29)
    assert r["pilot_spent"] == pytest.approx(2.10)
    assert r["cumulative"] == pytest.approx(1.32 + 2.10)
    assert r["episode_budget"] == pytest.approx(15 - 1.32)
    assert r["remaining"] == pytest.approx(15 - 3.42)


def test_pilot_budget_refuses_when_episode_ledger_was_lost(tmp_path):
    pb = _pilot_budget()
    g = tmp_path / "g.jsonl"
    _ledger_line(g, "img1", "vice-city-dark-history", 3.0, "done", 3.0)
    with pytest.raises(pb.LedgerProblem):
        pb.compute(str(g), str(tmp_path / "t.jsonl"), str(tmp_path / "p.jsonl"))


def test_pilot_episode_cap_stops_paid_calls_at_the_ceiling(tmp_path):
    from modules.costs import BudgetExceeded, CostLedger
    pb = _pilot_budget()
    g, t = tmp_path / "g.jsonl", tmp_path / "t.jsonl"
    _ledger_line(g, "old", "vice-city-60s-test", 1.27, "done", 1.27)
    r = pb.compute(str(g), str(t), str(tmp_path / "pilot" / "costs.jsonl"))
    ledger = CostLedger(str(tmp_path / "pilot"), run_cap=8, episode_cap=r["episode_budget"], global_path=str(g))
    ledger.begin("openai-image", "x", 7.9)
    _ledger_line(tmp_path / "pilot" / "costs.jsonl", "prior", "vice-city-dark-history", 5.8)  # 7.9 + 5.8 = 13.70 of 13.73
    with pytest.raises(BudgetExceeded):
        ledger.begin("openai-image", "y", 0.06)  # run cap 8 would allow it; the $15 ceiling does not


def test_full_episode_workflow_keeps_safeguards():
    text = open(os.path.join(ROOT, ".github", "workflows", "produce-full-episode.yml")).read()
    assert '"$CONFIRM" != "RUN"' in text and "Nothing was spent" in text
    assert 'options: ["choose", "0.9", "0.8"]' in text                 # speed must be chosen
    assert "pilot_budget.py --github-env" in text                       # $15 incl. tests, fails closed
    assert '--max-run-cost 8 --episode-budget "$EPISODE_BUDGET"' in text
    assert "--episode-budget 15" not in text and "--total-budget" not in text
    # shares the exact ledger cache with the test button, so test spend is counted
    shared = "~/.historical_oddities\n            episodes/gaming/vice-city-60s-test/costs.jsonl"
    assert shared in text and "key: spend-ledger-v2-${{ github.run_id }}" in text
    for word in ("publish", "merge", "git push"):
        assert f"run: {word}" not in text
    assert "approve \"$s\"" in text and "for s in storyboard budget" in text   # research/outline/script stay pinned
    assert "default=10.00" in open(os.path.join(ROOT, "modules", "gaming", "pipeline.py")).read()  # defaults unchanged


def test_committed_pilot_approvals_pin_the_approved_files():
    for st in ("research", "outline", "script"):
        assert workflow.is_approved(PILOT_DIR, st), st


def test_seed_reuses_only_hash_identical_verified_images(tmp_path):
    from modules import images
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    for label, h, data in [("scene01", "h1", b"a"), ("scene02", "h2", b"b"), ("scene03", "h3", b"c")]:
        (src / f"{label}.png").write_bytes(data)
    man = {"scene01": {"input_hash": "h1", "file_sha256": images._file_sha(str(src / "scene01.png"))},
           "scene02": {"input_hash": "h2", "file_sha256": "tampered"},
           "scene03": {"input_hash": "h3", "file_sha256": images._file_sha(str(src / "scene03.png"))}}
    images._save_manifest(str(src), man)
    seeded = images.seed_from(str(src), str(dst), {"reference": None, "scene07": "h1", "scene08": "h2", "scene09": "hX"})
    assert seeded == ["scene07"]
    assert (dst / "scene07.png").read_bytes() == b"a"
    assert images._is_current(str(dst), images._load_manifest(str(dst)), "scene07", "h1")
    assert images.seed_from(str(src), str(dst), {"scene07": "h1"}) == []   # already current


def test_segment_fades_render_and_leave_old_clips_unchanged(tmp_path):
    from modules import render
    from PIL import Image
    img = tmp_path / "a.png"
    Image.new("RGB", (320, 180), (200, 50, 50)).save(img)
    plain = render._clip_key([str(img)], 24, (320, 180), 24, 0, "none", None, None, 0.1, (16, 9), 20, "veryfast")
    same = render._clip_key([{"path": str(img)}], 24, (320, 180), 24, 0, "none", None, None, 0.1, (16, 9), 20, "veryfast")
    faded = render._clip_key([{"path": str(img), "fade_in": 0.3}], 24, (320, 180), 24, 0, "none", None, None, 0.1,
                             (16, 9), 20, "veryfast")
    assert plain == same != faded
    out = tmp_path / "c.mp4"
    render.render_scene_clip([{"path": str(img), "fade_in": 0.3, "fade_out": 0.3}], 24, str(out), (320, 180), 24, 0, "none")
    frames = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                             "stream=nb_read_frames", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout
    assert frames.strip() == "24"
    first = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt",
                            "gray", "-"], capture_output=True).stdout
    assert max(first) < 30          # starts from black


def test_chapter_transitions_dip_into_chapter_cards():
    script = {"scenes": [{"visuals": [{"kind": "illustration"}]}, {"visuals": [{"kind": "chapter_card"}, {"kind": "reuse"}]}]}
    specs = [{"image_paths": ["a.png"]}, {"image_paths": [{"path": "card.png", "motion": "none"}, "b.png"]}]
    pipeline._chapter_transitions(script, specs, 0.35, 1.5)
    assert specs[0]["image_paths"][0] == {"path": "a.png", "fade_out": 0.35}
    assert specs[1]["image_paths"][0]["fade_in"] == 0.35
    assert specs[1]["image_paths"][1] == {"path": "b.png", "fade_out": 1.5}
    specs2 = [{"image_paths": ["a.png"]}]
    pipeline._chapter_transitions({"scenes": [{"visuals": [{"kind": "illustration"}]}]}, specs2, 0, 0)
    assert specs2 == [{"image_paths": ["a.png"]}]   # off by default


def test_srt_export(tmp_path):
    from modules.captions import write_srt
    p = write_srt([{"start": 0, "end": 1.5, "lines": ["Hello"]}, {"start": 61.25, "end": 3725.0, "lines": ["a", "b"]}],
                  str(tmp_path / "c.srt"))
    assert open(p).read() == "1\n00:00:00,000 --> 00:00:01,500\nHello\n\n2\n00:01:01,250 --> 01:02:05,000\na\nb\n\n"


def test_long_stamp_fits_the_frame(tmp_path):
    from PIL import Image
    from modules.gaming.packaging import text_card
    out = text_card({"style": "stamp", "heading": "“HE WASHES THE MONEY FOR US.”", "lines": ["X"], "_bg_path": None},
                    str(tmp_path / "s.png"))
    img = Image.open(out).convert("L")
    w, h = img.size
    band = img.crop((0, int(h * 0.38), w, int(h * 0.5)))
    edge = [band.getpixel((x, y)) for x in (0, 1, w - 2, w - 1) for y in range(0, band.size[1], 4)]
    assert max(edge) < 60           # no text touching the frame edges


def test_pilot_description_fits_youtube_and_states_continuity():
    from modules.gaming.packaging import DESCRIPTION_LIMIT, build_package
    prod = load_production(os.path.join(PILOT_DIR, "production.json"))
    script = json.load(open(os.path.join(PILOT_DIR, "script.json")))
    dossier = json.load(open(os.path.join(PILOT_DIR, "research.json")))
    import tempfile
    markers = [{"chapter": "ch01", "title": "A", "start": 0.0, "end": 10.0}]
    with tempfile.TemporaryDirectory() as d:
        desc = build_package(prod, script, dossier, markers, {"assets": []}, d)
    assert len(desc) <= DESCRIPTION_LIMIT
    assert "separate continuity" in desc and "nothing here is presented as GTA VI's backstory" in desc
    assert prod["sources_url"] in desc
    assert os.path.exists(os.path.join(PILOT_DIR, "SOURCES.md"))


def test_pilot_finale_follows_transcript_order():
    script = json.load(open(os.path.join(PILOT_DIR, "script.json")))
    lines = [sc["narration"] for sc in script["scenes"] if sc["chapter_title"] == "This Is Business"]
    i_knew = next(i for i, l in enumerate(lines) if "they knew he was coming" in l)
    i_lance = next(i for i, l in enumerate(lines) if "this is business" in l)
    i_spend = next(i for i, l in enumerate(lines) if "his to spend" in l)
    assert i_knew < i_lance < i_spend
    assert "his to spend" not in lines[i_knew]
