"""
Reads scene image prompts from a CHAT.IMG-style batch_prompts.txt so the same
file you'd paste into CHAT.IMG can drive automatic generation instead.

Two layouts are supported (both appear in episodes/):

1. Prefixed, one block per scene:
       scene01.png - Create a 16:9 ...

       scene02.png - ...

2. Newer layout with character blocks and raw prompts:
       CHARACTER REFERENCE BLOCKS

       BOSTONIAN CITIZEN: ...

       SCENE PROMPTS

       First scene prompt...

       Second scene prompt...

   Prompts after "SCENE PROMPTS" are numbered 1, 2, 3... in order. If a file
   has neither prefixes nor that header, every block is treated as a scene
   prompt in order.
"""
import re

_PREFIX = re.compile(r"^(?:scene_?|tb_)(\d+)\.(?:png|jpe?g)\s*[-–—:]\s*(.+)$", re.I | re.S)
_SCENE_HEADER = re.compile(r"^scene prompts:?$", re.I)
_CHAR_HEADER = re.compile(r"^character reference blocks:?$", re.I)


def _blocks(text):
    text = text.lstrip("﻿").replace("\r\n", "\n")
    return [" ".join(b.split()) for b in re.split(r"\n\s*\n", text) if b.strip()]


def parse_batch_prompts(text):
    """Returns {scene_number: prompt}."""
    blocks = _blocks(text)
    prefixed = {}
    for b in blocks:
        m = _PREFIX.match(b)
        if m:
            prefixed[int(m.group(1))] = m.group(2).strip()
    if prefixed:
        return prefixed

    header_idx = next((i for i, b in enumerate(blocks) if _SCENE_HEADER.match(b)), None)
    if header_idx is not None:
        scene_blocks = blocks[header_idx + 1:]
    else:
        scene_blocks = [b for b in blocks if not _CHAR_HEADER.match(b)]
    return {i: b for i, b in enumerate(scene_blocks, start=1)}


def load_batch_prompts(path):
    with open(path, encoding="utf-8") as f:
        return parse_batch_prompts(f.read())


def resolve_scene_prompts(scenes, prompts_file=None):
    """
    Returns {scene_number: prompt} for every scene. A scene's own non-empty
    "image_prompt" wins; otherwise the prompt comes from `prompts_file`.
    Raises ValueError naming every scene that has no prompt, before anything
    is generated or paid for.
    """
    from_file = load_batch_prompts(prompts_file) if prompts_file else {}
    result, missing = {}, []
    for s in scenes:
        n = s["scene_number"]
        prompt = (s.get("image_prompt") or "").strip() or from_file.get(n, "")
        if prompt:
            result[n] = prompt
        else:
            missing.append(n)
    if missing:
        where = f" or in {prompts_file}" if prompts_file else " (pass --prompts-file batch_prompts.txt)"
        raise ValueError(f"No image prompt for scene(s) {missing} in the script{where}")
    return result
