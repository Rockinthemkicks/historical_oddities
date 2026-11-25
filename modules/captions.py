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


PHRASE_END = (",", ".", "?", "!", ";", ":")


def _chunk_words_phrased(words, max_words=7, max_chars=42, min_words=2):
    """Like _chunk_words, but prefers to break after punctuation and never leaves a
    one-word cue: a short tail is merged into the previous cue (or borrows from it)."""
    chunks, current, chars = [], [], 0
    for w in words:
        current.append(w)
        chars += len(w["word"]) + 1
        full = len(current) >= max_words or chars >= max_chars
        phrase = w["word"].endswith(PHRASE_END) and len(current) >= 3
        if full or phrase:
            chunks.append(current)
            current, chars = [], 0
    if current:
        chunks.append(current)
    fixed = []
    for c in chunks:
        if fixed and len(c) < min_words:
            prev = fixed[-1]
            if len(prev) + len(c) <= max_words + 2:
                fixed[-1] = prev + c
                continue
            if len(prev) > min_words:
                fixed[-1], c = prev[:-1], prev[-1:] + c
        fixed.append(c)
    return fixed


def wrap_balanced(text, max_chars=42, max_lines=2):
    """Two lines of similar length when one line is too long (no one-word second line)."""
    words = text.split()
    if len(text) <= max_chars or len(words) < 2 or max_lines < 2:
        return [text]
    best, best_score = None, None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = abs(len(a) - len(b)) + (100 if min(i, len(words) - i) < 2 else 0)
        if best_score is None or score < best_score:
            best, best_score = [a, b], score
    return best


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


def build_caption_cues(scenes, max_words=3, max_chars=16, uppercase=True, max_lines=2, phrased=False):
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
            chunker = _chunk_words_phrased if phrased else _chunk_words
            for chunk in chunker(scene["words"], max_words=max_words, max_chars=max_chars):
                cue_start = scene_start + chunk[0]["start"]
                cue_end = scene_start + chunk[-1]["end"]
                text = " ".join(w["word"] for w in chunk)
                text = text.upper() if uppercase else text
                lines = (wrap_balanced(text, max_chars=max_chars, max_lines=max_lines) if phrased
                         else wrap_lines(text, max_chars=max_chars, max_lines=max_lines))
                cues.append({"start": cue_start, "end": cue_end, "lines": lines})
        else:
            # Fallback: no word timings, split scene text evenly across its duration.
            text = scene.get("text", "").strip()
            duration = scene.get("duration", 0)
            words = text.split()
            if not words or duration <= 0:
                continue
            chunks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
            per_chunk = duration / len(chunks)
            for i, chunk in enumerate(chunks):
                cue_start = scene_start + i * per_chunk
                cue_end = scene_start + (i + 1) * per_chunk
                cues.append({
                    "start": cue_start,
                    "end": cue_end,
                    "lines": wrap_lines(" ".join(chunk).upper() if uppercase else " ".join(chunk),
                                        max_chars=max_chars, max_lines=max_lines),
                })

    return cues
