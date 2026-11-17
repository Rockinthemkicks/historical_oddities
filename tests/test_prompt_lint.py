"""Quality gate 2: prompt checks run before any paid image call."""
import json
import os
import subprocess
import sys

from modules.prompt_lint import character_blocks, lint

SCENES = [{"scene_number": n, "narration": "x", "image_prompt": ""} for n in (1, 2)]
GOOD = ("CHARACTER REFERENCE BLOCKS\n\n"
        "MRS. CROUCH: a farm woman with a round head and a blue dress.\n\n"
        "SCENE PROMPTS\n\n"
        "Lighthearted, non-graphic scene of a farm. MRS. CROUCH: a farm woman with a round head "
        "and a blue dress. She looks up.\n\n"
        "Lighthearted, non-graphic scene of lumps on grass, no on-image text.\n")


def rules(report, kind="errors"):
    return {f["rule"] for f in report[kind]}


def test_clean_prompts_pass():
    r = lint(SCENES, GOOD, "Flat colors with no paper texture and no cross-hatching.")
    assert r["passed"], r


def test_old_style_words_block():
    bad = "scene01.png - Lighthearted notebook-cartoon on warm sepia parchment\n\n" \
          "scene02.png - Lighthearted scene with subtle pencil shading and muted earth tones\n"
    r = lint(SCENES, bad)
    assert not r["passed"] and rules(r) == {"style_conflict"}


def test_negated_style_words_are_fine():
    ok = "scene01.png - Lighthearted farm, no paper texture, without cross-hatching\n\n" \
         "scene02.png - Lighthearted field, never sepia\n"
    assert lint(SCENES, ok)["passed"]


def test_count_mismatch_blocks():
    r = lint(SCENES, "scene01.png - Lighthearted farm\n")
    assert "prompt_count" in rules(r)
    r = lint(SCENES, "scene01.png - Lighthearted a\n\nscene02.png - Lighthearted b\n\n"
                     "scene03.png - Lighthearted c\n")
    assert "prompt_count" in rules(r)


def test_reference_pointers_and_gen_ids_block():
    r = lint(SCENES, "scene01.png - Lighthearted farm, same character as established\n\n"
                     "scene02.png - Lighthearted field. Master Gen ID: 8203c503\n")
    assert rules(r) == {"reference_pointer"}


def test_non_ascii_punctuation_blocks():
    r = lint(SCENES, "scene01.png - Lighthearted farm — sunny\n\nscene02.png - Lighthearted “field”\n")
    assert rules(r) == {"non_ascii"}


def test_intensity_words_block_and_sensitive_words_warn():
    r = lint(SCENES, "scene01.png - Lighthearted farm in the aftermath\n\n"
                     "scene02.png - Lighthearted field, no blood, no gore\n")
    assert rules(r) == {"intensity_words"}
    assert "sensitive_words" in rules(r, "warnings")


def test_character_block_must_be_verbatim():
    paraphrased = GOOD.replace("MRS. CROUCH: a farm woman with a round head and a blue dress. She looks up.",
                               "MRS. CROUCH in her blue dress looks up.")
    r = lint(SCENES, paraphrased)
    assert rules(r) == {"character_block"}
    assert list(character_blocks(GOOD)) == ["MRS. CROUCH"]


def test_missing_tone_frame_warns():
    r = lint(SCENES, "scene01.png - A farm\n\nscene02.png - A field\n")
    assert r["passed"] and "tone_frame" in rules(r, "warnings")


def test_saved_demo_prompts_pass():
    scenes = json.load(open("episodes/kentucky-meat-shower/script.json"))["scenes"][:3]
    r = lint(scenes, open("episodes/kentucky-meat-shower/demo_prompts.txt").read(),
             open("config/style_prompt.txt").read())
    assert r["passed"] and not r["warnings"], r


def test_main_blocks_failing_prompts_before_spending(tmp_path):
    r = subprocess.run([sys.executable, "main.py", "--project", str(tmp_path / "p"),
                        "--skip-script", "--script-file", "episodes/london-beer-flood/script.json",
                        "--prompts-file", "episodes/london-beer-flood/batch_prompts.txt"],
                       capture_output=True, text=True,
                       env={**os.environ, "ELEVENLABS_VOICE_ID": "v", "OPENAI_API_KEY": "k"})
    assert r.returncode != 0 and "Prompt check failed" in r.stderr
    assert (tmp_path / "p" / "prompt_check.json").exists()
    assert not (tmp_path / "p" / "costs.jsonl").exists()
