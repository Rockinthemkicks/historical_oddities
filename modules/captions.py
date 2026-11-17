"""
Builds caption cue data (grouped, timed chunks of words) for burning captions
into the video via ffmpeg's drawtext filter.

drawtext is used instead of the ass/subtitles filters because those require
ffmpeg to be built with libass, which isn't guaranteed on every system
(notably: some Homebrew ffmpeg installs on macOS don't include it). drawtext
only needs libfreetype, which is present in virtually every ffmpeg build.
"""


def _chunk_words(words, max_words=3, max_chars=16):
    """Group a list of {'word','start','end'} dicts into short caption cues."""
    chunks, current = [], []
    current_chars = 0
    for w in words:
        current.append(w)
        current_chars += len(w["word"]) + 1
        if len(current) >= max_words or current_chars >= max_chars:
            chunks.append(current)
            current, current_chars = [], 0
    if current:
        chunks.append(current)
    return chunks


def wrap_lines(text, max_chars=16, max_lines=2):
    """Break text into at most max_lines lines for on-screen display. Returns a list of lines."""
    words = text.split()
    lines = [[]]
    length = 0
    for w in words:
        if length + len(w) + 1 <= max_chars or not lines[-1]:
            lines[-1].append(w)
            length += len(w) + 1
        elif len(lines) < max_lines:
            lines.append([w])
            length = len(w) + 1
        else:
            lines[-1].append(w)  # last line just keeps growing rather than dropping words
            length += len(w) + 1
    return [" ".join(line) for line in lines]


def build_caption_cues(scenes):
    """
    scenes: list of dicts, each either:
      {"start": float, "words": [{"word": str, "start": float, "end": float}, ...]}
        (times in `words` are relative to the scene; `start` is the scene's
        offset in the full timeline)
      or, as a fallback when no word-level timing exists:
      {"start": float, "duration": float, "text": str}

    Returns a list of {"start": float, "end": float, "lines": [str, ...]} cues
    (each with 1-2 lines), in timeline order, ready to render via drawtext.
    """
    cues = []

    for scene in scenes:
        scene_start = scene["start"]

        if "words" in scene and scene["words"]:
            for chunk in _chunk_words(scene["words"]):
                cue_start = scene_start + chunk[0]["start"]
                cue_end = scene_start + chunk[-1]["end"]
                text = " ".join(w["word"] for w in chunk).upper()
                cues.append({"start": cue_start, "end": cue_end, "lines": wrap_lines(text)})
        else:
            # Fallback: no word timings, split scene text evenly across its duration.
            text = scene.get("text", "").strip()
            duration = scene.get("duration", 0)
            words = text.split()
            if not words or duration <= 0:
                continue
            chunks = [words[i:i + 3] for i in range(0, len(words), 3)]
            per_chunk = duration / len(chunks)
            for i, chunk in enumerate(chunks):
                cue_start = scene_start + i * per_chunk
                cue_end = scene_start + (i + 1) * per_chunk
                cues.append({
                    "start": cue_start,
                    "end": cue_end,
                    "lines": wrap_lines(" ".join(chunk).upper()),
                })

    return cues
