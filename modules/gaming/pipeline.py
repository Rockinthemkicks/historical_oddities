"""
Gaming-lore documentary pipeline (production mode "gaming-lore").

  python3 main.py --mode gaming-lore --production <dir>/production.json <command> [options]

Commands, in order (see workflow.py for the approval stages):
  status                      where each stage stands
  check-research              stage 1: validate research.json -> research_review.md
  outline                     stage 2: chapter outline (paid text call, ~cents)
  write                       stage 3: chapter-by-chapter script (paid text calls)
  storyboard                  stage 4: visual list, prompt/IP check, asset rights
  estimate                    stage 5: cost of narration + images (free)
  produce                     stages 6-7: narration, images, render, QC (paid)
  package                     stage 8: description, chapters, sources
  approve <stage>             record owner approval of a stage's current files

--dry-run runs outline/write/produce/package fully offline with fixtures,
placeholder images and silent timed narration; it never needs keys or
approvals and never spends anything. --estimate-only shows what a paid
command would cost and stops before any paid call.
"""
import argparse
import json
import os
import sys

from .. import images as images_mod
from .. import narration as narration_mod
from ..assemble import concat_audio
from ..caption_images import render_all_captions
from ..captions import build_caption_cues
from ..costs import BudgetExceeded, CostLedger, image_unit_cost, narration_unit_cost
from ..prompt_lint import lint_prompt
from ..qc import check_video, format_report
from ..render import render_episode
from ..utils import load_env, save_json
from . import provenance, workflow
from .config import ConfigError, load_production, word_budget
from .dryrun import synthetic_image, synthetic_narration
from .llm import FixtureLLM, LLMError, OpenAIText
from .packaging import build_package, chapter_card, text_card, chapter_markers, validate_youtube_chapters
from .research import dossier_markdown, validate_dossier
from .script_engine import (script_estimate, GENERATED_KINDS, assemble_script, chapter_path, outline_prompts,
                            plan_estimate, validate_outline, write_chapters)

DEFAULT_SIZE = (1920, 1080)
DEFAULT_FPS = 30


def _size_fps(prod):
    s = prod["_settings"]
    return tuple(s.get("size", DEFAULT_SIZE)), int(s.get("fps", DEFAULT_FPS))


def _read(prod, name, required=True):
    path = os.path.join(prod["_dir"], name)
    if not os.path.exists(path):
        if required:
            raise SystemExit(f"Missing {name} in {prod['_dir']}")
        return None
    with open(path) as f:
        return json.load(f)


def _write(prod, name, obj):
    path = os.path.join(prod["_dir"], name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(obj, str):
        with open(path, "w") as f:
            f.write(obj)
    else:
        save_json(obj, path)
    return path


def _ledger(prod, args):
    return CostLedger(prod["_dir"], run_cap=args.max_run_cost, episode_cap=args.episode_budget,
                      total_cap=args.total_budget)


def _llm(prod, args):
    if args.dry_run:
        fixtures = _read(prod, "fixtures/llm.json")
        return FixtureLLM(fixtures)
    return OpenAIText(prod["_settings"].get("script_model", "gpt-5.4"), _ledger(prod, args))


def _gate(prod, args, stages, purpose):
    if args.dry_run:
        return
    try:
        workflow.require(prod["_dir"], stages, purpose)
    except workflow.NotApproved as e:
        raise SystemExit(str(e))


def _report(title, rep):
    print(f"{title}: {'PASSED' if rep['passed'] else 'FAILED'} "
          f"({len(rep['errors'])} error(s), {len(rep['warnings'])} warning(s))")
    for e in rep["errors"]:
        print(f"  [ERROR] {e if isinstance(e, str) else e['where'] + ': ' + e['detail']}")
    for w in rep["warnings"][:25]:
        print(f"  [warn ] {w if isinstance(w, str) else w['where'] + ': ' + w['detail']}")


# ---------------- stage commands ----------------

def cmd_status(prod, args):
    for s in workflow.status(prod["_dir"]):
        print(f"  {s['stage']} {s['name']:<11} {s['state']}")


def cmd_check_research(prod, args):
    dossier = _read(prod, "research.json")
    rep = validate_dossier(dossier, prod)
    _write(prod, "research_report.json", rep)
    approvals = {"editorial": workflow.is_approved(prod["_dir"], "research"),
                 "production": all(workflow.is_approved(prod["_dir"], st) for st in workflow.REQUIRED_FOR_PAID)}
    _write(prod, "research_review.md", dossier_markdown(dossier, rep, approvals))
    _report("Research check", rep)
    print(f"  Review: {os.path.join(prod['_dir'], 'research_review.md')}")
    return 0 if rep["passed"] else 1


def _valid_dossier(prod):
    dossier = _read(prod, "research.json")
    rep = validate_dossier(dossier, prod)
    if not rep["passed"]:
        _report("Research check", rep)
        raise SystemExit("Fix the research dossier first (check-research).")
    return dossier


def _budget(prod):
    s = prod["_settings"]
    return word_budget(prod["target_minutes"], s.get("words_per_minute", 140),
                       tuple(s.get("words_per_minute_range", (130, 150))))


def cmd_outline(prod, args):
    _gate(prod, args, ["research"], "Writing the outline")
    dossier = _valid_dossier(prod)
    budget = _budget(prod)
    system, user = outline_prompts(prod, dossier, budget)
    llm = _llm(prod, args)
    cost = llm.estimate(system, user, 8000)
    print(f"Outline: 1 text call, estimated ${cost:.2f}")
    if args.estimate_only:
        print("Estimate only: nothing was called or charged.")
        return 0
    try:
        outline = llm.complete_json(system, user, label="outline", max_output_tokens=8000)
    except (LLMError, BudgetExceeded) as e:
        raise SystemExit(str(e))
    rep = validate_outline(outline, dossier, budget)
    _write(prod, "outline.json", outline)
    _report("Outline check", rep)
    return 0 if rep["passed"] else 1


def cmd_write(prod, args):
    _gate(prod, args, ["research", "outline"], "Writing the script")
    dossier = _valid_dossier(prod)
    outline = _read(prod, "outline.json")
    rep = validate_outline(outline, dossier, _budget(prod))
    if not rep["passed"]:
        _report("Outline check", rep)
        raise SystemExit("Fix outline.json first.")
    llm = _llm(prod, args)
    todo = [c for c in outline["chapters"] if not os.path.exists(chapter_path(prod["_dir"], c["id"]))]
    est = script_estimate(llm, prod, dossier, outline, todo) if getattr(llm, "is_paid", False) else \
        {"expected_usd": 0.0, "worst_case_usd": 0.0, "input_tokens": 0}
    print(f"Script: {len(todo)} chapter(s) to write, estimated ${est['expected_usd']:.2f} "
          f"(worst case ${est['worst_case_usd']:.2f}; ~{est['input_tokens']:,} input tokens)")
    if args.estimate_only:
        print("Estimate only: nothing was called or charged.")
        return 0
    try:
        reports = write_chapters(llm, prod, dossier, outline)
    except (LLMError, BudgetExceeded, ValueError) as e:
        raise SystemExit(str(e))
    chapters = []
    for c in outline["chapters"]:
        with open(chapter_path(prod["_dir"], c["id"])) as f:
            chapters.append(json.load(f))
    script = assemble_script(prod, outline, chapters)
    _write(prod, "script.json", script)
    total = sum(r["words"] for r in reports.values())
    wpm = prod["_settings"].get("words_per_minute", 140)
    print(f"Script: {len(script['scenes'])} scenes, {total} words, about {total / wpm:.1f} min at {wpm} wpm")
    for cid, r in reports.items():
        for w in r["warnings"]:
            print(f"  [warn ] {w}")
    _write(prod, "script_review.md", script_markdown(script, dossier))
    return 0


def script_markdown(script, dossier):
    claims = {c["id"]: c for c in dossier["claims"]}
    lines = [f"# {script['title']}: script for review", ""]
    current = None
    for sc in script["scenes"]:
        if sc.get("chapter") != current:
            current = sc.get("chapter")
            lines += ["", f"## {current}: {sc.get('chapter_title', '')}", ""]
        tags = ", ".join(f"{c} ({claims[c]['status']})" for c in sc.get("claim_ids", []) if c in claims)
        lines.append(f"{sc['narration']}  \n*[{tags or 'no claims'}]*\n")
    return "\n".join(lines) + "\n"


# YouTube ad rules (Sep 2026 update): graphic game violence in the first 7 seconds earns no
# ads, 8-15 seconds limited ads; thumbnails are judged separately. Our art is illustrated, but
# keep the opening clean: these words in a visual's prompt during the first 15 s draw a warning.
OPENING_SECONDS = 15
OPENING_RISK_WORDS = ("blood", "gore", "corpse", "dead body", "gun", "shooting", "shoot", "kill", "murder",
                      "chainsaw", "torture", "explosion", "cocaine", "drugs", "syringe", "wound")


def _storyboard(prod, script):
    """Every visual in the script, with checks: generated prompt lint + IP, user asset rights,
    and the ad-safe opening rule."""
    franchise = prod["_franchise"]
    manifest = provenance.load(prod["_dir"])
    errors, warnings, items, used_assets = [], [], [], []
    wpm = prod["_settings"].get("words_per_minute", 140)
    t = 0.0
    for sc in script["scenes"]:
        if t < OPENING_SECONDS:
            for v in sc.get("visuals", []):
                hits = [w for w in OPENING_RISK_WORDS if w in (v.get("prompt") or "").lower()]
                if hits:
                    warnings.append(f"{v['id']} (scene {sc['scene_number']}): in the first {OPENING_SECONDS}s, "
                                    f"which YouTube judges strictly for ads; avoid {', '.join(hits)} imagery here")
                if v["kind"] == "user_asset":
                    warnings.append(f"{v['id']} (scene {sc['scene_number']}): gameplay footage in the first "
                                    f"{OPENING_SECONDS}s; make sure it shows no graphic violence")
        t += len(sc["narration"].split()) / wpm * 60
        for v in sc.get("visuals", []):
            item = {"visual_id": v["id"], "scene": sc["scene_number"], "chapter": sc.get("chapter"),
                    "kind": v["kind"]}
            if v["kind"] in GENERATED_KINDS:
                item["prompt"] = v["prompt"]
                e, w = [], []
                lint_prompt(v["id"], v["prompt"], e, w, style_conflicts=(), intensity_level="warning",
                            protected_terms=franchise.get("protected_terms", ()))
                errors += [f"{v['id']} (scene {sc['scene_number']}): {x['rule']}: {x['detail']}" for x in e]
                warnings += [f"{v['id']} (scene {sc['scene_number']}): {x['rule']}: {x['detail']}" for x in w]
            elif v["kind"] == "user_asset":
                item["asset_id"] = v["asset_id"]
                used_assets.append(v["asset_id"])
            items.append(item)
    rights = provenance.check(prod["_dir"], manifest, used_assets)
    errors += rights["errors"]
    warnings += rights["warnings"]
    return {"visuals": items, "errors": errors, "warnings": warnings, "passed": not errors}


def cmd_storyboard(prod, args):
    script = _read(prod, "script.json")
    sb = _storyboard(prod, script)
    _write(prod, "storyboard.json", sb)
    counts = {}
    for it in sb["visuals"]:
        counts[it["kind"]] = counts.get(it["kind"], 0) + 1
    print(f"Storyboard: {len(sb['visuals'])} visuals {counts}")
    _report("Storyboard check", sb)
    return 0 if sb["passed"] else 1


def _estimate(prod, script, args):
    s = prod["_settings"]
    quality = s.get("image_quality", "medium")
    voice = prod.get("voice_id") or os.environ.get("ELEVENLABS_VOICE_ID") or "unset"
    gen = [v for sc in script["scenes"] for v in sc.get("visuals", []) if v["kind"] in GENERATED_KINDS]
    gen += _extra_visuals(prod)
    pseudo = [{"scene_number": i + 1} for i in range(len(gen))]
    prompts = {i + 1: v["prompt"] for i, v in enumerate(gen)}
    style = _style(prod)
    iplan = images_mod.plan_images(pseudo, os.path.join(prod["_dir"], "out", "images"), prompts,
                                   use_reference=True, quality=quality, style=style, **_reference(prod)) if gen else \
        {"to_generate": [], "existing": [], "estimate_usd": 0.0}
    nplan = narration_mod.plan_narration(_tts_scenes(script), os.path.join(prod["_dir"], "out", "audio"), voice)
    total = iplan["estimate_usd"] + nplan["estimate_usd"]
    words = sum(len(sc["narration"].split()) for sc in script["scenes"])
    est = {
        "images": {"generated_visuals": len(gen), "to_generate": len(iplan["to_generate"]),
                   "reused": len(iplan["existing"]), "quality": quality,
                   "unit_usd": image_unit_cost("gpt-image-2", quality, "1536x1024", True),
                   "estimate_usd": round(iplan["estimate_usd"], 2)},
        "narration": {"characters": nplan["characters"], "clips_to_generate": len(nplan["to_generate"]),
                      "estimate_usd": round(nplan["estimate_usd"], 2)},
        "total_usd": round(total, 2),
        "words": words,
        "minutes_at_wpm": round(words / s.get("words_per_minute", 140), 1),
        "limits": {"run": args.max_run_cost, "episode": args.episode_budget, "overall": args.total_budget},
        "note": "Estimates; prices in modules/costs.py. Limits are never raised automatically.",
    }
    return est


def _style(prod):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        prod["_settings"]["style_file"])
    with open(path) as f:
        return f.read().strip()


def _reference(prod):
    """Optional character reference for every generated image: production 'reference_prompt'
    (generated once, paid) or 'reference_image' (your own file, free)."""
    ref_img = prod.get("reference_image")
    if ref_img:
        ref_img = os.path.join(prod["_dir"], ref_img)
    return {"reference_prompt": prod.get("reference_prompt"), "reference_image": ref_img}


def _extra_visuals(prod):
    """Generated images that aren't placed in the video (e.g. a thumbnail background), from
    production 'extra_visuals': [{"id", "prompt"}]. Same ledger, cache and provenance as the rest."""
    return [{"kind": "illustration", **v} for v in prod.get("extra_visuals", [])]


def _tts_scenes(script):
    return [{"scene_number": sc["scene_number"], "narration": sc["narration"]} for sc in script["scenes"]]


def cmd_estimate(prod, args):
    script = _read(prod, "script.json")
    est = _estimate(prod, script, args)
    _write(prod, "estimate.json", est)
    print(json.dumps(est, indent=2))
    ledger = _ledger(prod, args)
    try:
        ledger.check_room(est["total_usd"])
        print(f"Fits within the current limits (episode spent so far ~${ledger.episode_spent():.2f}).")
    except BudgetExceeded as e:
        print("Over a limit: " + str(e).replace("Stopping:", "").strip())
        print("Raise --max-run-cost / --episode-budget yourself if you want to go ahead; "
              "the pipeline never raises them.")
    return 0


def cmd_produce(prod, args):
    _gate(prod, args, workflow.REQUIRED_FOR_PAID, "Paid production (narration + images)")
    script = _read(prod, "script.json")
    sb = _storyboard(prod, script)
    if not sb["passed"]:
        _report("Storyboard check", sb)
        raise SystemExit("Fix the storyboard problems first.")
    out = os.path.join(prod["_dir"], "out")
    s = prod["_settings"]
    wpm = s.get("words_per_minute", 140)
    manifest = provenance.load(prod["_dir"])
    est = _estimate(prod, script, args)
    print(f"[pre-flight] {est['images']['to_generate']} images + {est['narration']['clips_to_generate']} "
          f"narration clips, estimated ${est['total_usd']:.2f}" + (" (dry run: $0)" if args.dry_run else ""))
    if args.estimate_only:
        print("Estimate only: nothing was generated or charged.")
        return 0
    ledger = _ledger(prod, args)
    if not args.dry_run:
        try:
            ledger.check_room(est["total_usd"])
        except BudgetExceeded as e:
            raise SystemExit(str(e).replace("Stopping:", "Not starting:"))

    # ---- narration ----
    print("[6] Narration" + (" (synthetic)" if args.dry_run else ""))
    tts_scenes = _tts_scenes(script)
    if args.dry_run:
        nar = synthetic_narration(tts_scenes, os.path.join(out, "audio"), wpm=wpm)
    else:
        nar = narration_mod.generate_all_narration(tts_scenes, os.path.join(out, "audio"),
                                                   voice_id=prod.get("voice_id"), ledger=ledger)
    nar = {n["scene_number"]: n for n in nar}

    # ---- visuals ----
    print("[6] Visuals" + (" (placeholders)" if args.dry_run else ""))
    gen = [(sc, v) for sc in script["scenes"] for v in sc.get("visuals", []) if v["kind"] in GENERATED_KINDS]
    gen += [(None, v) for v in _extra_visuals(prod)]
    files = {}
    img_dir = os.path.join(out, "images")
    if args.dry_run:
        for sc, v in gen:
            path = synthetic_image(v["prompt"], os.path.join(img_dir, f"{v['id']}.png"))
            files[v["id"]] = path
            provenance.register(prod["_dir"], manifest, v["id"], path, "synthetic_test",
                                "dry-run placeholder", "generated", "pipeline test only")
    elif gen:
        pseudo = [{"scene_number": i + 1} for i in range(len(gen))]
        prompts = {i + 1: v["prompt"] for i, (_, v) in enumerate(gen)}
        res = images_mod.generate_all_images(pseudo, img_dir, prompts=prompts, style=_style(prod),
                                             quality=s.get("image_quality", "medium"),
                                             project_dir=prod["_dir"], ledger=ledger, **_reference(prod))
        for (sc, v), r in zip(gen, res):
            files[v["id"]] = r["image_path"]
            provenance.register(prod["_dir"], manifest, v["id"], r["image_path"], "generated_image",
                                "OpenAI gpt-image-2 via pipeline", "generated",
                                "documentary illustration", notes=v["prompt"][:200])
    assets = {a["id"]: a for a in manifest["assets"]}
    for sc in script["scenes"]:
        for v in sc.get("visuals", []):
            if v["kind"] == "chapter_card":
                num = int((sc.get("chapter") or "ch00")[2:])
                path = chapter_card(num, sc.get("chapter_title", ""), os.path.join(out, "cards", f"{v['id']}.png"))
                files[v["id"]] = {"path": path, "motion": "none"}
                provenance.register(prod["_dir"], manifest, v["id"], path, "chapter_card",
                                    "made locally by the pipeline", "generated", "chapter title card")
            elif v["kind"] == "text_card":
                path = text_card(v, os.path.join(out, "cards", f"{v['id']}.png"), size=_size_fps(prod)[0])
                files[v["id"]] = {"path": path, "motion": v.get("motion", "zoom_in")}
                provenance.register(prod["_dir"], manifest, v["id"], path, "chapter_card",
                                    "made locally by the pipeline", "generated", "documentary typography")
            elif v["kind"] == "user_asset":
                files[v["id"]] = os.path.join(prod["_dir"], assets[v["asset_id"]]["path"])
    for sc in script["scenes"]:
        for v in sc.get("visuals", []):
            if v["kind"] in GENERATED_KINDS and v.get("motion") and v["id"] in files:
                p = files[v["id"]]
                files[v["id"]] = {"path": p["path"] if isinstance(p, dict) else p, "motion": v["motion"]}
    for sc in script["scenes"]:
        for v in sc.get("visuals", []):
            if v["kind"] == "reuse":
                src = files.get(v["of"])
                if src is None:
                    raise SystemExit(f"{v['id']}: reuses {v.get('of')!r}, which has no file")
                files[v["id"]] = {"path": src["path"] if isinstance(src, dict) else src,
                                  "motion": v.get("motion")}
    provenance.save(prod["_dir"], manifest)

    # ---- assembly ----
    print("[7] Assembly")
    pause = s.get("pause_seconds", 0.35)
    silence = os.path.join(out, "audio", "pause.mp3")
    from ..assemble import generate_silence
    generate_silence(pause, silence)
    audio_list, specs, cap_scenes, t = [], [], [], 0.0
    for i, sc in enumerate(script["scenes"]):
        n = nar[sc["scene_number"]]
        dur = n["duration"] + (pause if i < len(script["scenes"]) - 1 else 0)
        audio_list.append(n["audio_path"])
        if i < len(script["scenes"]) - 1:
            audio_list.append(silence)
        segs = [files[v["id"]] for v in sc.get("visuals", []) if v["id"] in files]
        if not segs:
            raise SystemExit(f"scene {sc['scene_number']} has no usable visual")
        specs.append({"image_paths": segs, "duration": dur})
        cap_scenes.append({"start": t, "words": n["words"], "duration": n["duration"], "text": sc["narration"]})
        t += dur
    full_audio = os.path.join(out, "narration_full.mp3")
    concat_audio(audio_list, full_audio)
    cap_cfg = s.get("captions", {})
    cues = build_caption_cues(cap_scenes, max_words=cap_cfg.get("max_words", 7),
                              max_chars=cap_cfg.get("max_chars", 42), uppercase=cap_cfg.get("uppercase", False))
    caps = render_all_captions(cues, os.path.join(out, "captions"), font_size=cap_cfg.get("font_size", 44))
    ambient = None
    bed = s.get("ambient_asset_id") or prod.get("ambient_asset_id")
    if bed:
        if bed not in assets or assets[bed]["kind"] not in ("licensed_music", "licensed_sfx"):
            raise SystemExit(f"ambient asset {bed!r} must be licensed audio in assets/provenance.json")
        ambient = {"path": os.path.join(prod["_dir"], assets[bed]["path"]),
                   "gain_db": s.get("ambient_gain_db", -26)}
    video = os.path.join(out, "documentary.mp4")
    size, fps = _size_fps(prod)
    res = render_episode(specs, full_audio, caps, video, os.path.join(out, "render_cache"), size=size,
                         fps=fps, motion=s.get("motion", "kenburns"), bottom_margin_frac=-0.06,
                         ambient=ambient)
    print(f"      {len(res['rendered'])} scene clip(s) rendered, {len(res['reused'])} reused")
    total = res["scene_ends"][-1]
    markers = chapter_markers(script, res["scene_starts"], total)
    qc = check_video(video, expected_size=size, expected_duration=total, duration_tolerance=1.0)
    print(format_report(qc))
    chapter_problems = validate_youtube_chapters(markers)
    report = {"dry_run": args.dry_run, "video": os.path.relpath(video, prod["_dir"]),
              "duration_seconds": total, "chapters": markers, "chapter_problems": chapter_problems,
              "qc": qc, "spent_this_run_usd": round(ledger.run_spent, 4)}
    _write(prod, "out/qc_report.json", report)
    _write(prod, "out/chapters.json", markers)
    for p in chapter_problems:
        print(f"  [warn ] chapters: {p}")
    print(f"Done: {video} ({total / 60:.1f} min, {len(markers)} chapters)")
    return 0 if qc["passed"] else 1


def cmd_package(prod, args):
    _gate(prod, args, ["assembly"], "The publishing package")
    script = _read(prod, "script.json")
    dossier = _read(prod, "research.json")
    report = _read(prod, "out/qc_report.json")
    manifest = provenance.load(prod["_dir"])
    used = [v["asset_id"] for sc in script["scenes"] for v in sc.get("visuals", []) if v["kind"] == "user_asset"]
    rights = provenance.check(prod["_dir"], manifest, used, for_publication=True)
    build_package(prod, script, dossier, report["chapters"], manifest, os.path.join(prod["_dir"], "publish"))
    _report("Publication rights check", rights)
    print(f"Package written to {os.path.join(prod['_dir'], 'publish')}")
    if report.get("dry_run"):
        print("DRY RUN package: built from placeholders; not publishable.")
    print("Publishing itself is never automatic: upload only after you approve the 'publishing' stage.")
    return 0 if rights["passed"] or report.get("dry_run") else 1


def cmd_approve(prod, args):
    try:
        e = workflow.approve(prod["_dir"], args.stage, note=args.note or "")
    except (workflow.NotApproved, ValueError) as ex:
        raise SystemExit(str(ex))
    print(f"Approved {args.stage} at {e['at']}")
    return 0


COMMANDS = {"status": cmd_status, "check-research": cmd_check_research, "outline": cmd_outline,
            "write": cmd_write, "storyboard": cmd_storyboard, "estimate": cmd_estimate,
            "produce": cmd_produce, "package": cmd_package, "approve": cmd_approve}


def main(argv):
    load_env()
    p = argparse.ArgumentParser(prog="main.py --mode gaming-lore",
                                description="Gaming-lore documentary pipeline")
    p.add_argument("--mode", choices=["gaming-lore"], default="gaming-lore")
    p.add_argument("--production", required=True, help="Path to the documentary's production.json")
    p.add_argument("command", choices=sorted(COMMANDS))
    p.add_argument("stage", nargs="?", help="For 'approve': the stage name")
    p.add_argument("--note", help="For 'approve': optional note")
    p.add_argument("--dry-run", action="store_true",
                   help="Offline: fixtures, placeholder images, silent narration; never spends")
    p.add_argument("--estimate-only", action="store_true", help="Show the cost, make no paid calls")
    p.add_argument("--max-run-cost", type=float, default=5.00)
    p.add_argument("--episode-budget", type=float, default=10.00)
    p.add_argument("--total-budget", type=float, default=250.00)
    args = p.parse_args(argv)
    if args.command == "approve" and not args.stage:
        p.error("approve needs a stage: " + ", ".join(workflow.STAGES))
    try:
        prod = load_production(args.production)
    except ConfigError as e:
        raise SystemExit(f"production.json: {e}")
    return COMMANDS[args.command](prod, args) or 0
