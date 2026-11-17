from modules.captions import build_caption_cues, wrap_lines, _chunk_words


def test_wrap_lines_never_drops_words():
    text = "the great molasses flood of nineteen nineteen swept through boston"
    lines = wrap_lines(text, max_chars=16, max_lines=2)
    assert len(lines) <= 2
    assert " ".join(lines).split() == text.split()


def test_chunk_words_respects_max_words():
    words = [{"word": w, "start": i, "end": i + 0.5} for i, w in enumerate("a b c d e f g".split())]
    chunks = _chunk_words(words, max_words=3, max_chars=100)
    assert [len(c) for c in chunks] == [3, 3, 1]


def test_word_timed_cues_are_offset_by_scene_start():
    scenes = [{"start": 10.0, "words": [{"word": "beer", "start": 0.2, "end": 0.6}]}]
    cues = build_caption_cues(scenes)
    assert cues == [{"start": 10.2, "end": 10.6, "lines": ["BEER"]}]


def test_fallback_cues_split_evenly_over_scene():
    scenes = [{"start": 0.0, "duration": 6.0, "text": "one two three four five six"}]
    cues = build_caption_cues(scenes)
    assert len(cues) == 2
    assert cues[0]["start"] == 0.0 and cues[0]["end"] == 3.0
    assert cues[1]["end"] == 6.0
