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
"""
import argparse
import glob
import os

from modules.utils import load_env, save_json, load_json, get_duration
from modules.script_gen import generate_script, save_script, load_script
from modules.narration import generate_all_narration
from modules.images import generate_all_images
from modules.captions import build_caption_cues, wrap_lines
from modules.caption_images import render_all_captions, render_cue_image
from modules.assemble import concat_audio, build_video, generate_silence


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

    p.add_argument("--voice-id", help="ElevenLabs voice ID (defaults to ELEVENLABS_VOICE_ID env or a stock voice)")
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
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    p.add_argument("--no-title", action="store_true",
                    help="Don't show the script's title at the top of the video")
    return p.parse_args()


def find_scene_file(directory, scene_number, extensions):
    # Accepts both "sceneNN.ext" and "scene_NN.ext" naming (CHAT.IMG exports
    # the underscore form; some other tools/manual naming use the no-underscore
    # form), so either is fine to drop into the images/audio directory.
    stems = [f"scene{scene_number:02d}", f"scene_{scene_number:02d}"]
    for stem in stems:
        for ext in extensions:
            candidate = os.path.join(directory, f"{stem}.{ext}")
            if os.path.exists(candidate):
                return candidate
    for stem in stems:
        matches = glob.glob(os.path.join(directory, f"{stem}*"))
        if matches:
            return matches[0]
    return None


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

    # ---- Stage 2: narration ----
    audio_dir = os.path.join(args.project, "audio")
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
        narration_results = generate_all_narration(scenes, audio_dir, voice_id=args.voice_id,
                                                     speed=args.voice_speed, seed=args.voice_seed)
        save_json(narration_results, os.path.join(args.project, "narration_timing.json"))
    print(f"      {len(narration_results)} narration clips ready")

    # ---- Stage 3: images ----
    images_dir = os.path.join(args.project, "images")
    if args.skip_images:
        src_dir = args.images_dir or images_dir
        print(f"[3/4] Using existing images from: {src_dir}")
        image_results = []
        for s in scenes:
            path = find_scene_file(src_dir, s["scene_number"], ["png", "jpg", "jpeg"])
            if not path:
                raise FileNotFoundError(f"No image found for scene {s['scene_number']} in {src_dir}")
            image_results.append({"scene_number": s["scene_number"], "image_path": path})
    else:
        print(f"[3/4] Generating {len(scenes)} images via OpenAI...")
        image_results = generate_all_images(scenes, images_dir)
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
    caption_scenes = []
    cursor = 0.0
    for i, s in enumerate(scenes):
        n = s["scene_number"]
        nar = narration_by_scene[n]
        img = images_by_scene[n]
        is_last = (i == len(scenes) - 1)

        ordered_audio.append(nar["audio_path"])
        ordered_images.append(img["image_path"])

        scene_duration = nar["duration"]
        if silence_path and not is_last:
            ordered_audio.append(silence_path)
            scene_duration += args.pause
        ordered_durations.append(scene_duration)

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

    title_image = None
    title_text = script.get("title", "").strip()
    if title_text and not args.no_title:
        title_path = os.path.join(args.project, "title.png")
        # Wider wrap than captions since the title sits alone at the top with
        # more room to breathe; ~40% of frame width in characters at this font size.
        lines = wrap_lines(title_text.upper(), max_chars=26)
        _, tw, th = render_cue_image(lines, title_path, font_size=52)
        title_image = {"path": title_path, "width": tw, "height": th}

    out_path = os.path.join(args.project, "final_video.mp4")
    build_video(ordered_images, ordered_durations, full_audio_path, caption_images, out_path,
                size=(args.width, args.height), fps=args.fps, title_image=title_image)

    print(f"\nDone -> {out_path}")


if __name__ == "__main__":
    main()
