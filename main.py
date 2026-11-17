#!/usr/bin/env python3
"""
End-to-end pipeline: topic -> script -> narration -> images -> captioned MP4.

Every stage can be skipped in favor of your own files, so you can automate all of it
or just the parts you want (e.g. keep making your own images, automate the rest).

Examples:
  # Fully automated
  python3 main.py --topic "The man who survived two atomic bombs" --scenes 12 --project out/yamaguchi

  # Generate the script only, review/edit it, then continue later
  python3 main.py --topic "..." --scenes 12 --project out/yamaguchi --script-only

  # Bring your own images, automate script + narration + assembly
  python3 main.py --topic "..." --scenes 12 --project out/yamaguchi --skip-images --images-dir my_images/

  # Bring your own audio AND images, just assemble
  python3 main.py --project out/yamaguchi --skip-script --skip-audio --skip-images \\
      --script-file my_script.json --audio-dir my_audio/ --images-dir my_images/

  # Generate the images automatically from a CHAT.IMG-style prompt file
  # (see the cost first with --estimate-only; nothing is charged)
  python3 main.py --project out/molasses --skip-script --script-file my_script.json \\
      --prompts-file batch_prompts.txt --estimate-only

  # Render a 16:9 YouTube version as well as the vertical one
  python3 main.py --project out/yamaguchi --skip-script --script-file my_script.json \\
      --skip-images --images-dir my_images/ --format both
"""
import argparse
import glob
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

from modules.utils import load_env, save_json, load_json, get_duration
from modules.script_gen import generate_script, save_script, load_script
from modules.narration import generate_all_narration, plan_narration, resolve_voice_id
from modules.images import generate_all_images, plan_images
from modules.image_prompts import resolve_scene_prompts
from modules.costs import BudgetExceeded, CostLedger, GLOBAL_LEDGER_PATH
from modules.captions import build_caption_cues, wrap_lines
from modules.caption_images import render_all_captions, render_cue_image
from modules.assemble import concat_audio, build_video, generate_silence
from modules.qc import check_video, format_report
from modules.render import render_episode, MOTIONS

# Output formats. "vertical" is the original behavior (9:16 canvas, 16:9 image
# letterboxed in the middle, title in the top black bar) and stays the default.
# "landscape" is a full-frame 16:9 render for YouTube long-form.
FORMATS = ("vertical", "landscape")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--topic", help="Video topic (required unless --skip-script)")
    p.add_argument("--scenes", type=int, default=10, help="Number of scenes (default 10)")
    p.add_argument("--style", default="simple stick-figure illustration, minimal flat color",
                    help="Visual style description passed to the script/image prompts")
    p.add_argument("--project", required=True, help="Output project directory")

    p.add_argument("--skip-script", action="store_true")
    p.add_argument("--script-file", help="Existing script.json to use when --skip-script")
    p.add_argument("--script-only", action="store_true",
                    help="Generate the script and stop (no narration/images/video). "
                         "Lets you review/edit script.json before spending on the rest.")

    p.add_argument("--skip-audio", action="store_true")
    p.add_argument("--audio-dir", help="Directory of sceneNN.mp3 files to use when --skip-audio")

    p.add_argument("--skip-images", action="store_true")
    p.add_argument("--images-dir", help="Directory of sceneNN.png files to use when --skip-images")
    p.add_argument("--prompts-file",
                    help="batch_prompts.txt to take image prompts from when the script's "
                         "image_prompt fields are empty")
    p.add_argument("--style-file", default=os.path.join(_HERE, "config", "style_prompt.txt"),
                    help="Style text prepended to every image prompt (default config/style_prompt.txt)")
    p.add_argument("--no-style", action="store_true",
                    help="Use image prompts exactly as written, without the style text")
    p.add_argument("--image-model", default="gpt-image-2")
    p.add_argument("--image-quality", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--image-size", default="1536x1024",
                    help="Generated image size (default 1536x1024 landscape)")
    p.add_argument("--reference-image",
                    help="Your own master reference image to keep characters consistent, "
                         "instead of generating one")
    p.add_argument("--no-reference", action="store_true",
                    help="Generate each scene independently (cheaper, less consistent)")
    p.add_argument("--max-run-cost", "--max-image-cost", dest="max_run_cost", type=float, default=5.00,
                    help="Limit for everything paid in THIS run (images + narration), USD (default 5.00)")
    p.add_argument("--episode-budget", type=float, default=10.00,
                    help="Limit for everything ever spent on this project folder, USD (default 10.00). "
                         "Read from <project>/costs.jsonl, so re-running can't reset it.")
    p.add_argument("--total-budget", type=float, default=250.00,
                    help="Limit across ALL projects, USD (default 250.00). Read from the global "
                         f"ledger ({GLOBAL_LEDGER_PATH}; override with HO_SPEND_LEDGER).")
    p.add_argument("--estimate-only", action="store_true",
                    help="Print what would be generated and the estimated cost, then stop. "
                         "Nothing is charged.")

    p.add_argument("--voice-id", help="ElevenLabs voice ID (default: ELEVENLABS_VOICE_ID from .env; required, "
                                      "no fallback voice)")
    p.add_argument("--voice-speed", type=float, default=1.0,
                    help="Narration speed, 0.7 (slower) - 1.2 (faster), 1.0 = normal (default)")
    p.add_argument("--voice-seed", type=int, default=None,
                    help="Optional int (0-4294967295) for more consistent narration across re-runs. "
                         "ElevenLabs generation is non-deterministic by default, so re-running with "
                         "identical text/settings can still sound slightly different each time; a "
                         "fixed seed makes repeats sound much closer to identical.")
    p.add_argument("--pause", type=float, default=0.3,
                    help="Silence in seconds inserted between scenes (default 0.3). Use 0 for none.")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--format", choices=["vertical", "landscape", "both"], default="vertical",
                    help="vertical = 9:16 Shorts/Reels (default, original behavior) -> final_video.mp4; "
                         "landscape = 16:9 YouTube -> final_video_landscape.mp4; both = render each")
    p.add_argument("--width", type=int, default=1080, help="Vertical output width (default 1080)")
    p.add_argument("--height", type=int, default=1920, help="Vertical output height (default 1920)")
    p.add_argument("--landscape-width", type=int, default=1920)
    p.add_argument("--landscape-height", type=int, default=1080)
    p.add_argument("--motion", default="none", choices=["none", "kenburns", *MOTIONS],
                    help="Camera movement on scene images: none (default, static like before), "
                         "kenburns (cycles zoom in / pan right / zoom out / pan left), or one movement")
    p.add_argument("--legacy-render", action="store_true",
                    help="Use the original single-pass assembler instead of cached per-scene clips "
                         "(no motion support)")
    p.add_argument("--skip-qc", action="store_true",
                    help="Don't run the automatic ffprobe checks on the finished video(s)")
    p.add_argument("--no-title", action="store_true",
                    help="Don't show the script's title at the top of the video")
    return p.parse_args()


# Filename stems accepted for scene files, in priority order. "sceneNN" is the
# documented convention; "scene_NN" is what CHAT.IMG exports; "tb_NN" is how the
# August 2026 episode images were actually named.
SCENE_STEMS = ("scene{n:02d}", "scene_{n:02d}", "tb_{n:02d}")


def find_scene_files(directory, scene_number, extensions):
    """
    Returns a sorted list of files for one scene (empty list if none).

    An exact match like scene03.png wins and is returned alone. Otherwise every
    variant sharing the stem (e.g. tb_14_1.png, tb_14_2.png) is returned, in
    sorted order, so a scene can have more than one illustration; main() then
    splits that scene's on-screen time evenly between them.
    """
    stems = [t.format(n=scene_number) for t in SCENE_STEMS]
    for stem in stems:
        for ext in extensions:
            candidate = os.path.join(directory, f"{stem}.{ext}")
            if os.path.exists(candidate):
                return [candidate]
    exts = {e.lower() for e in extensions}
    for stem in stems:
        matches = sorted(
            m for m in glob.glob(os.path.join(directory, f"{stem}*"))
            if m.rsplit(".", 1)[-1].lower() in exts
            # don't let scene01 grab scene010+; the next char after the stem
            # must not be another digit
            and not os.path.basename(m)[len(stem):len(stem) + 1].isdigit()
        )
        if matches:
            return matches
    return []


def find_scene_file(directory, scene_number, extensions):
    """Backward-compatible single-file lookup: the first match, or None."""
    files = find_scene_files(directory, scene_number, extensions)
    return files[0] if files else None


def main():
    load_env()
    args = parse_args()
    os.makedirs(args.project, exist_ok=True)

    # ---- Stage 1: script ----
    script_path = os.path.join(args.project, "script.json")
    if args.skip_script:
        src = args.script_file or script_path
        print(f"[1/4] Using existing script: {src}")
        script = load_script(src)
    else:
        print(f"[1/4] Generating script for topic: {args.topic!r} ({args.scenes} scenes)")
        script = generate_script(args.topic, num_scenes=args.scenes, style=args.style)
        save_script(script, script_path)
        print(f"      Saved -> {script_path}")

    if args.script_only:
        print(f"\n[1/4] Script-only mode: stopping here.")
        print(f"      Review/edit {script_path}, then re-run with:")
        print(f"      python3 main.py --project {args.project} --skip-script "
              f"--script-file {script_path}")
        return

    scenes = sorted(script["scenes"], key=lambda s: s["scene_number"])

    # ---- Pre-flight: work out image prompts and cost before paying for anything ----
    images_dir = os.path.join(args.project, "images")
    audio_dir = os.path.join(args.project, "audio")
    image_prompts, style_text = None, ""
    ledger = CostLedger(args.project, run_cap=args.max_run_cost,
                        episode_cap=args.episode_budget, total_cap=args.total_budget)
    run_estimate = 0.0
    if not args.skip_images:
        try:
            image_prompts = resolve_scene_prompts(scenes, args.prompts_file)
        except ValueError as e:
            sys.exit(str(e))
        if not args.no_style and args.style_file and os.path.exists(args.style_file):
            with open(args.style_file, encoding="utf-8") as f:
                style_text = f.read().strip()
        plan = plan_images(scenes, images_dir, image_prompts, use_reference=not args.no_reference,
                           reference_image=args.reference_image, model=args.image_model,
                           size=args.image_size, quality=args.image_quality, style=style_text)
        run_estimate += plan["estimate_usd"]
        print(f"[pre-flight] Images: {len(plan['to_generate'])} to generate "
              f"({len(plan['stale'])} replacing outdated files, {len(plan['existing'])} reused), "
              f"estimated ${plan['estimate_usd']:.2f}")
    voice_id = None
    if not args.skip_audio:
        try:
            voice_id = resolve_voice_id(args.voice_id)
        except RuntimeError as e:
            sys.exit(str(e))
        nplan = plan_narration(scenes, audio_dir, voice_id, speed=args.voice_speed, seed=args.voice_seed)
        run_estimate += nplan["estimate_usd"]
        print(f"[pre-flight] Narration: {len(nplan['to_generate'])} clips to generate "
              f"({nplan['characters']} characters), {len(nplan['cached'])} cached, "
              f"estimated ${nplan['estimate_usd']:.2f}")
    if not (args.skip_images and args.skip_audio):
        print(f"[pre-flight] Spent so far: episode ~${ledger.episode_spent():.2f} of "
              f"${args.episode_budget:.2f}, overall ~${ledger.total_spent():.2f} of "
              f"${args.total_budget:.2f}; this run's limit ${args.max_run_cost:.2f}")
        try:
            ledger.check_room(run_estimate)
        except BudgetExceeded as e:
            sys.exit(str(e).replace("Stopping:", "Not starting:"))
    if args.estimate_only:
        print("\nEstimate only: nothing was generated or charged.")
        return

    # ---- Stage 2: narration ----
    if args.skip_audio:
        src_dir = args.audio_dir or audio_dir
        print(f"[2/4] Using existing audio from: {src_dir}")
        narration_results = []
        for s in scenes:
            path = find_scene_file(src_dir, s["scene_number"], ["mp3", "wav", "m4a"])
            if not path:
                raise FileNotFoundError(f"No audio file found for scene {s['scene_number']} in {src_dir}")
            narration_results.append({
                "scene_number": s["scene_number"],
                "audio_path": path,
                "duration": get_duration(path),
                "words": [],  # no word-level timing available -> captions fall back to even split
            })
    else:
        print(f"[2/4] Generating narration for {len(scenes)} scenes via ElevenLabs...")
        try:
            narration_results = generate_all_narration(scenes, audio_dir, voice_id=voice_id,
                                                       speed=args.voice_speed, seed=args.voice_seed,
                                                       ledger=ledger)
        except BudgetExceeded as e:
            sys.exit(str(e))
        save_json(narration_results, os.path.join(args.project, "narration_timing.json"))
    print(f"      {len(narration_results)} narration clips ready")

    # ---- Stage 3: images ----
    if args.skip_images:
        src_dir = args.images_dir or images_dir
        print(f"[3/4] Using existing images from: {src_dir}")
        image_results = []
        for s in scenes:
            paths = find_scene_files(src_dir, s["scene_number"], ["png", "jpg", "jpeg"])
            if not paths:
                raise FileNotFoundError(f"No image found for scene {s['scene_number']} in {src_dir}")
            image_results.append({"scene_number": s["scene_number"], "image_path": paths[0],
                                  "image_paths": paths})
    else:
        print(f"[3/4] Generating images via OpenAI...")
        try:
            image_results = generate_all_images(
                scenes, images_dir, size=args.image_size, use_reference=not args.no_reference,
                prompts=image_prompts, style=style_text, quality=args.image_quality,
                model=args.image_model, reference_image=args.reference_image,
                project_dir=args.project, ledger=ledger)
        except BudgetExceeded as e:
            sys.exit(str(e))
    print(f"      {len(image_results)} images ready")

    # ---- Stage 4: assemble ----
    print("[4/4] Assembling final video...")
    narration_by_scene = {r["scene_number"]: r for r in narration_results}
    images_by_scene = {r["scene_number"]: r for r in image_results}

    # A short silence is inserted between scenes (not after the last one) so the
    # narration doesn't run scene-to-scene with zero breathing room. The pause is
    # added to the *previous* scene's on-screen duration, so that image stays up
    # through the pause rather than cutting away right as the silence starts.
    silence_path = None
    if args.pause > 0:
        silence_path = os.path.join(args.project, "pause.mp3")
        generate_silence(args.pause, silence_path)

    ordered_audio, ordered_images, ordered_durations = [], [], []
    caption_scenes, scene_specs = [], []
    cursor = 0.0
    for i, s in enumerate(scenes):
        n = s["scene_number"]
        nar = narration_by_scene[n]
        img = images_by_scene[n]
        is_last = (i == len(scenes) - 1)

        ordered_audio.append(nar["audio_path"])

        scene_duration = nar["duration"]
        if silence_path and not is_last:
            ordered_audio.append(silence_path)
            scene_duration += args.pause

        # One image per scene (the usual case) or several, sharing the scene's
        # time equally.
        paths = img.get("image_paths") or [img["image_path"]]
        for path in paths:
            ordered_images.append(path)
            ordered_durations.append(scene_duration / len(paths))
        scene_specs.append({"image_paths": paths, "duration": scene_duration})

        if nar["words"]:
            caption_scenes.append({"start": cursor, "words": nar["words"]})
        else:
            caption_scenes.append({"start": cursor, "duration": nar["duration"], "text": s["narration"]})
        cursor += scene_duration

    full_audio_path = os.path.join(args.project, "full_audio.mp3")
    concat_audio(ordered_audio, full_audio_path)

    caption_cues = build_caption_cues(caption_scenes)
    caption_images_dir = os.path.join(args.project, "caption_images")
    caption_images = render_all_captions(caption_cues, caption_images_dir)

    title_text = script.get("title", "").strip()
    formats = FORMATS if args.format == "both" else (args.format,)
    expected_duration = sum(ordered_durations)
    outputs, failed = [], []

    for fmt in formats:
        if fmt == "vertical":
            size = (args.width, args.height)
            out_path = os.path.join(args.project, "final_video.mp4")
            bottom_margin = 0.18
        else:
            size = (args.landscape_width, args.landscape_height)
            out_path = os.path.join(args.project, "final_video_landscape.mp4")
            bottom_margin = -0.06  # caption's bottom edge 6% above the frame bottom

        title_image = None
        # The title lives in the vertical video's top black bar. A full-frame
        # landscape video has no bar (and YouTube shows the title anyway), so
        # it's left off there.
        if title_text and not args.no_title and fmt == "vertical":
            title_path = os.path.join(args.project, "title.png")
            # Wider wrap than captions since the title sits alone at the top with
            # more room to breathe; ~40% of frame width in characters at this font size.
            lines = wrap_lines(title_text.upper(), max_chars=26)
            _, tw, th = render_cue_image(lines, title_path, font_size=52)
            title_image = {"path": title_path, "width": tw, "height": th}

        print(f"      Rendering {fmt} {size[0]}x{size[1]} -> {out_path}")
        if args.legacy_render:
            if args.motion != "none":
                sys.exit("--motion needs the per-scene renderer; drop --legacy-render")
            build_video(ordered_images, ordered_durations, full_audio_path, caption_images, out_path,
                        size=size, fps=args.fps, title_image=title_image,
                        bottom_margin_frac=bottom_margin)
        else:
            result = render_episode(scene_specs, full_audio_path, caption_images, out_path,
                                    cache_dir=os.path.join(args.project, "render_cache", fmt),
                                    size=size, fps=args.fps, title_image=title_image,
                                    bottom_margin_frac=bottom_margin, motion=args.motion)
            print(f"      {len(result['rendered'])} scene clip(s) rendered, "
                  f"{len(result['reused'])} reused from cache")
        outputs.append(out_path)

        if not args.skip_qc:
            report = check_video(out_path, expected_size=size, expected_duration=expected_duration)
            save_json(report, os.path.splitext(out_path)[0] + "_qc.json")
            print(format_report(report))
            if not report["passed"]:
                failed.append(out_path)

    print("\nDone -> " + ", ".join(outputs))
    if failed:
        raise SystemExit(f"Quality check failed for: {', '.join(failed)}")


if __name__ == "__main__":
    main()
