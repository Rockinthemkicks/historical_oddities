"""Turns scene images + narration audio + caption images into a finished MP4."""
import os
import tempfile

from .utils import run_ffmpeg


def generate_silence(duration, out_path):
    """Generates a silent audio clip of the given duration (seconds), used to insert
    short pauses between scenes."""
    run_ffmpeg(
        ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{duration:.3f}",
         "-c:a", "libmp3lame", "-q:a", "4", out_path],
        description="generate_silence",
    )
    return out_path


def concat_audio(scene_audio_paths, out_path):
    """
    Concatenate a list of audio clips (narration + any silence clips) into one
    track. Re-encodes rather than stream-copying, so clips with differing
    sample rates/codecs (e.g. narration mp3s alongside generated silence) still
    concatenate correctly.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in scene_audio_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
        list_path = f.name
    try:
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_path,
                    "-c:a", "libmp3lame", "-q:a", "2", out_path],
                   description="concat audio")
    finally:
        os.unlink(list_path)
    return out_path


def build_video(scene_images, scene_durations, audio_path, caption_images, out_path,
                 size=(1080, 1920), fps=30, bottom_margin_frac=0.18,
                 title_image=None, image_aspect=(16, 9)):
    """
    scene_images: list of image file paths, one per scene, in order.
    scene_durations: list of floats (seconds), same length/order as scene_images.
    audio_path: path to the full, already-concatenated narration track.
    caption_images: list of {"start", "end", "path", "width", "height"} dicts from
        modules.caption_images.render_all_captions, or None/[] to skip captions.
    title_image: optional {"path", "width", "height"} dict (from
        modules.caption_images.render_cue_image) shown just above the scene
        image (within the letterbox area) for the entire video, or None to skip.
    image_aspect: (w, h) aspect ratio the scene image itself is displayed at,
        centered within the `size` canvas. Defaults to 16:9 -- if `size` is a
        taller 9:16 canvas, this letterboxes the image with black bars above
        and below rather than cropping it to fill the whole vertical frame.
    Renders scenes back-to-back with hard cuts (frame-accurate sync with the audio).
    Each image is scaled/cropped to fill an `image_aspect`-ratio box centered in
    the frame and held static for its scene's duration (no zoom or pan); any
    leftover canvas space is filled with black. Captions/title are pre-rendered
    PNGs composited via the `overlay` filter -- a core ffmpeg filter with no
    optional library dependency, unlike drawtext/ass/subtitles which need
    libfreetype/libass.
    """
    n = len(scene_images)
    if n != len(scene_durations):
        raise ValueError("scene_images and scene_durations must be the same length")

    w, h = size
    inputs = []
    filters = []

    # The box the image itself fills, centered in the (possibly taller/wider)
    # canvas. Sized to the canvas width, height derived from image_aspect,
    # rounded to an even number (required for yuv420p encoding).
    box_w = w
    box_h = int(round(w * image_aspect[1] / image_aspect[0] / 2)) * 2
    box_h = min(box_h, h if h % 2 == 0 else h - 1)
    pad_y = (h - box_h) // 2

    for i, (img, dur) in enumerate(zip(scene_images, scene_durations)):
        # -r sets a fixed frame rate on the looped image input; trim then hard-cuts
        # this branch to exactly `dur` seconds, which terminates the stream cleanly
        # for concat.
        inputs += ["-loop", "1", "-r", str(fps), "-i", img]
        filters.append(
            f"[{i}:v]scale={box_w}:{box_h}:force_original_aspect_ratio=increase,"
            f"crop={box_w}:{box_h},pad={w}:{h}:0:{pad_y}:black,"
            f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,setsar=1[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filters.append(f"{concat_inputs}concat=n={n}:v=1:a=0[vconcat]")

    # Audio is input index n.
    inputs += ["-i", audio_path]
    next_input_index = n + 1

    current_label = "vconcat"

    if title_image:
        inputs += ["-loop", "1", "-i", title_image["path"]]
        # Centered halfway between the top of the screen and the top of the
        # image box (i.e. vertically centered within the top letterbox gap).
        title_y = max(0, int(pad_y / 2 - title_image["height"] / 2))
        filters.append(
            f"[{current_label}][{next_input_index}:v]overlay=x=(W-w)/2:y={title_y}[titled]"
        )
        current_label = "titled"
        next_input_index += 1

    if caption_images:
        y_pos = f"H-{int(h * bottom_margin_frac)}"
        for i, cap in enumerate(caption_images):
            inputs += ["-loop", "1", "-i", cap["path"]]
            out_label = f"cap{i}"
            filters.append(
                f"[{current_label}][{next_input_index}:v]overlay=x=(W-w)/2:y={y_pos}:"
                f"enable='between(t,{cap['start']:.3f},{cap['end']:.3f})'[{out_label}]"
            )
            current_label = out_label
            next_input_index += 1

    filter_complex = ";".join(filters)

    args = inputs + [
        "-filter_complex", filter_complex,
        "-map", f"[{current_label}]",
        "-map", f"{n}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        # Writes the MP4 index ("moov" atom) at the start of the file: the
        # video is playable/streamable before it fully downloads, and an
        # interrupted upload can't leave a file with the index missing.
        "-movflags", "+faststart",
        "-shortest",
        out_path,
    ]
    run_ffmpeg(args, description="build_video")
    return out_path
