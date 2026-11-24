"""
Scene-by-scene renderer: each scene becomes its own short silent video clip
(image(s) + optional pan/zoom + title + that scene's captions), cached by a
hash of everything that goes into it. The clips are then joined and the full
narration track is added in one cheap final pass.

Why: the original assembler built the whole video in ONE ffmpeg call with one
overlay input per caption cue, which is fine at 90 seconds but becomes a
huge, fragile filter graph at 8-10 minutes, and any change meant redoing it
all. Here, changing one scene re-renders only that scene's clip.

Timing: scene boundaries are snapped to whole frames on the *cumulative*
timeline (frame_end = round(scene_end * fps)), so rounding never drifts the
picture away from the audio, however many scenes there are.

Layout is identical to modules.assemble.build_video: the image fills a box of
`image_aspect` centered in the canvas (letterboxed on a 9:16 canvas), the
title sits centered in the top bar, captions sit `bottom_margin_frac` up from
the bottom.
"""
import hashlib
import json
import os
import shutil
import tempfile

from .utils import run_ffmpeg

RENDER_VERSION = "1"  # bump when the clip recipe changes, to invalidate old clips

MOTIONS = ("zoom_in", "pan_right", "zoom_out", "pan_left")
ZOOM = 0.10        # zoom_in/zoom_out travel: 1.00 <-> 1.10
PAN_ZOOM = 1.12    # pans run at a fixed zoom so there's room to move
PRESCALE = 2       # motion works on a 2x image so movement is sub-pixel smooth


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".mkv", ".webm")


def as_segment(seg):
    """A scene segment is an image path (original behavior) or a dict
    {"path", "type": "image"|"video", "motion": optional per-segment override}."""
    if isinstance(seg, dict):
        path = seg["path"]
        kind = seg.get("type") or ("video" if path.lower().endswith(VIDEO_EXTS) else "image")
        return {"path": path, "type": kind, "motion": seg.get("motion")}
    kind = "video" if str(seg).lower().endswith(VIDEO_EXTS) else "image"
    return {"path": seg, "type": kind, "motion": None}


def _segment_motion(seg, index, mode):
    if seg["type"] == "video":
        return "none"
    return motion_for(index, seg["motion"]) if seg["motion"] else motion_for(index, mode)


def motion_for(index, mode):
    """mode: 'none' | 'kenburns' (cycles through MOTIONS) | one of MOTIONS."""
    if mode in (None, "none"):
        return "none"
    if mode == "kenburns":
        return MOTIONS[index % len(MOTIONS)]
    if mode in MOTIONS:
        return mode
    raise ValueError(f"Unknown motion {mode!r}; use none, kenburns, or one of {MOTIONS}")


def _box(size, image_aspect):
    w, h = size
    box_h = int(round(w * image_aspect[1] / image_aspect[0] / 2)) * 2
    box_h = min(box_h, h if h % 2 == 0 else h - 1)
    return w, box_h, (h - box_h) // 2


def _segment_filter(label_in, label_out, box_w, box_h, frames, fps, motion):
    """Filter chain turning one looped still into `frames` frames of box_w x box_h."""
    if motion == "none":
        return (f"[{label_in}]scale={box_w}:{box_h}:force_original_aspect_ratio=increase,"
                f"crop={box_w}:{box_h},setsar=1,trim=end_frame={frames},setpts=PTS-STARTPTS[{label_out}]")
    pw, ph = box_w * PRESCALE, box_h * PRESCALE
    last = max(frames - 1, 1)
    p = f"(on/{last})"
    ease = f"({p}*{p}*(3-2*{p}))"  # smoothstep: gentle start and stop
    if motion == "zoom_in":
        z, x, y = f"1+{ZOOM}*{ease}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "zoom_out":
        z, x, y = f"{1 + ZOOM}-{ZOOM}*{ease}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z, x, y = f"{PAN_ZOOM}", f"(iw-iw/zoom)*{ease}", "(ih-ih/zoom)/2"
    elif motion == "pan_left":
        z, x, y = f"{PAN_ZOOM}", f"(iw-iw/zoom)*(1-{ease})", "(ih-ih/zoom)/2"
    else:
        raise ValueError(motion)
    return (f"[{label_in}]scale={pw}:{ph}:force_original_aspect_ratio=increase,crop={pw}:{ph},setsar=1,"
            f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={box_w}x{box_h}:fps={fps},"
            f"trim=end_frame={frames},setpts=PTS-STARTPTS[{label_out}]")


def _video_filter(label_in, label_out, box_w, box_h, frames, fps):
    """User footage: fill the box, conform frame rate, loop if short (input is
    -stream_loop'ed), cut to exactly `frames`. Its own audio is never used."""
    return (f"[{label_in}]scale={box_w}:{box_h}:force_original_aspect_ratio=increase,"
            f"crop={box_w}:{box_h},fps={fps},setsar=1,trim=end_frame={frames},setpts=PTS-STARTPTS[{label_out}]")


def frame_plan(scene_durations, fps):
    """Whole-frame counts per scene that add up exactly to round(total*fps)."""
    frames, cum, prev = [], 0.0, 0
    for d in scene_durations:
        cum += d
        end = int(round(cum * fps))
        frames.append(max(end - prev, 1))
        prev = end
    return frames


def render_scene_clip(segments, frames, out_path, size, fps, motion_index, motion_mode,
                      captions=None, title_image=None, bottom_margin_frac=0.18,
                      image_aspect=(16, 9), crf=20, preset="veryfast"):
    """
    segments: images and/or video clips shown in order within this scene (split
        evenly); each an image path or a dict, see as_segment().
    frames: total frames for the scene.
    captions: list of {"start", "end", "path", "height"} with times RELATIVE to the scene.
    Writes a silent H.264 clip of exactly `frames` frames.
    """
    w, h = size
    box_w, box_h, pad_y = _box(size, image_aspect)
    segments = [as_segment(x) for x in segments]
    n = len(segments)
    seg_frames = [frames // n + (1 if i < frames % n else 0) for i in range(n)]

    inputs, filters = [], []
    for i, seg in enumerate(segments):
        if seg["type"] == "video":
            inputs += ["-stream_loop", "-1", "-i", seg["path"]]
            filters.append(_video_filter(f"{i}:v", f"s{i}", box_w, box_h, seg_frames[i], fps))
        else:
            inputs += ["-loop", "1", "-framerate", str(fps), "-i", seg["path"]]
            filters.append(_segment_filter(f"{i}:v", f"s{i}", box_w, box_h, seg_frames[i], fps,
                                           _segment_motion(seg, motion_index + i, motion_mode)))
    if n > 1:
        filters.append("".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[img]")
    else:
        filters.append("[s0]null[img]")
    filters.append(f"[img]pad={w}:{h}:0:{pad_y}:black,setsar=1[v0]")
    current, idx = "v0", n

    if title_image:
        inputs += ["-i", title_image["path"]]
        title_y = max(0, int(pad_y / 2 - title_image["height"] / 2))
        filters.append(f"[{current}][{idx}:v]overlay=x=(W-w)/2:y={title_y}[vt]")
        current, idx = "vt", idx + 1

    # bottom_margin_frac >= 0: top of the caption sits that far up from the
    # bottom (original vertical layout). < 0: the caption's BOTTOM edge sits
    # abs(value) up from the bottom, so two-line captions never run off-frame.
    if bottom_margin_frac >= 0:
        y_pos = f"H-{int(h * bottom_margin_frac)}"
    else:
        y_pos = f"H-h-{int(h * -bottom_margin_frac)}"
    for j, cap in enumerate(captions or []):
        inputs += ["-i", cap["path"]]
        filters.append(f"[{current}][{idx}:v]overlay=x=(W-w)/2:y={y_pos}:"
                       f"enable='between(t,{cap['start']:.3f},{cap['end']:.3f})'[c{j}]")
        current, idx = f"c{j}", idx + 1

    tmp = out_path + ".part.mp4"
    run_ffmpeg(inputs + [
        "-filter_complex", ";".join(filters), "-map", f"[{current}]",
        "-frames:v", str(frames), "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", preset, "-crf", str(crf),
        "-video_track_timescale", str(fps * 1000), "-an", tmp,
    ], description=f"render scene clip {os.path.basename(out_path)}")
    os.replace(tmp, out_path)
    return out_path


def _clip_key(segments, frames, size, fps, motion_index, motion_mode, captions, title_image,
              bottom_margin_frac, image_aspect, crf, preset):
    payload = {
        "v": RENDER_VERSION, "frames": frames, "size": list(size), "fps": fps,
        "motions": [_segment_motion(as_segment(x), motion_index + i, motion_mode)
                    for i, x in enumerate(segments)],
        "images": [[as_segment(x)["type"], _sha_file(as_segment(x)["path"])] for x in segments],
        "captions": [[round(c["start"], 3), round(c["end"], 3), _sha_file(c["path"])]
                     for c in (captions or [])],
        "title": _sha_file(title_image["path"]) if title_image else None,
        "margin": bottom_margin_frac, "aspect": list(image_aspect), "crf": crf, "preset": preset,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


def split_captions(caption_images, scene_starts, scene_ends):
    """Assigns absolute-time caption cues to scenes (by start), as scene-relative times."""
    per_scene = [[] for _ in scene_starts]
    for cap in caption_images or []:
        for i, (s, e) in enumerate(zip(scene_starts, scene_ends)):
            if s - 1e-6 <= cap["start"] < e or (i == len(scene_starts) - 1 and cap["start"] >= s):
                per_scene[i].append({**cap, "start": cap["start"] - s,
                                     "end": min(cap["end"], e) - s})
                break
    return per_scene


def render_episode(scenes, audio_path, caption_images, out_path, cache_dir, size=(1080, 1920),
                   fps=30, title_image=None, bottom_margin_frac=0.18, motion="none",
                   image_aspect=(16, 9), crf=20, preset="veryfast", ambient=None):
    """
    scenes: list of {"image_paths": [...], "duration": seconds} in order
        (image_paths entries may also be video clips, see as_segment()).
    caption_images: as from modules.caption_images.render_all_captions (absolute times).
    ambient: optional {"path": licensed audio bed, "gain_db": -26}; looped under
        the narration and ducked automatically while the narrator speaks.
    Renders/reuses one clip per scene in cache_dir, joins them, adds audio.
    Returns {"path", "rendered", "reused", "scene_starts", "scene_ends", "fps"};
    scene times are the actual rendered times (whole frames), for chapter markers.
    """
    os.makedirs(cache_dir, exist_ok=True)
    durations = [s["duration"] for s in scenes]
    frames = frame_plan(durations, fps)
    starts, ends, t = [], [], 0
    for f in frames:
        starts.append(t / fps)
        t += f
        ends.append(t / fps)
    caps = split_captions(caption_images, starts, ends)

    clips, rendered, reused = [], [], []
    motion_index = 0
    for i, scene in enumerate(scenes):
        segs = scene["image_paths"]
        key = _clip_key(segs, frames[i], size, fps, motion_index, motion, caps[i], title_image,
                        bottom_margin_frac, image_aspect, crf, preset)
        clip = os.path.join(cache_dir, f"scene{i + 1:03d}_{key}.mp4")
        if os.path.exists(clip):
            reused.append(i)
        else:
            for old in os.listdir(cache_dir):  # drop this slot's outdated clip(s)
                if old.startswith(f"scene{i + 1:03d}_") and old.endswith(".mp4"):
                    os.remove(os.path.join(cache_dir, old))
            render_scene_clip(segs, frames[i], clip, size, fps, motion_index, motion, caps[i],
                              title_image, bottom_margin_frac, image_aspect, crf, preset)
            rendered.append(i)
        clips.append(clip)
        motion_index += len(segs)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
        list_path = f.name
    tmp = out_path + ".part.mp4"
    try:
        if ambient:
            gain = ambient.get("gain_db", -26)
            run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_path, "-i", audio_path,
                        "-stream_loop", "-1", "-i", ambient["path"],
                        "-filter_complex",
                        f"[2:a]volume={gain}dB,aresample=48000[bed];[1:a]aresample=48000,asplit=2[nar][key];"
                        f"[bed][key]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[duck];"
                        f"[nar][duck]amix=inputs=2:duration=first:normalize=0[aout]",
                        "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", tmp],
                       description="join scene clips + narration + ambient bed")
        else:
            run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_path, "-i", audio_path,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", tmp],
                       description="join scene clips + audio")
    finally:
        os.unlink(list_path)
    os.replace(tmp, out_path)
    return {"path": out_path, "rendered": rendered, "reused": reused,
            "scene_starts": starts, "scene_ends": ends, "fps": fps}
