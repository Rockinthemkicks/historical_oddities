# Unplayed History: video pipeline (topic → finished captioned MP4)

The production pipeline behind **Unplayed History** (gaming-lore documentaries). It also keeps the original
Historical Oddities mode. Repo renamed from `historical_oddities` on 2026-11-25; old GitHub links redirect.

Turns a topic into a numbered-scene script, narration audio (ElevenLabs), scene
images (OpenAI), and a finished captioned MP4 (vertical 9:16, landscape 16:9,
or both) with word-synced captions — or run only the stages you want and bring your own
audio/images for the rest.

## Setup

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional: for running tests (pytest -q)
cp .env.example .env   # then fill in your API keys
```

Requires `ffmpeg`/`ffprobe` on your PATH (already installed on most systems;
`brew install ffmpeg` / `apt install ffmpeg` if not).

## Usage

**Fully automated:**
```bash
python3 main.py --topic "The man who survived two atomic bombs" \
  --scenes 12 --project out/yamaguchi
```

**Bring your own images (still auto-generate script + narration):**
```bash
python3 main.py --topic "..." --scenes 12 --project out/yamaguchi \
  --skip-images --images-dir my_images/
```
(`my_images/` should contain `scene01.png`, `scene02.png`, ... matching the
script's scene numbers.)

**Bring your own audio and images, just assemble:**
```bash
python3 main.py --project out/yamaguchi \
  --skip-script --skip-audio --skip-images \
  --script-file my_script.json --audio-dir my_audio/ --images-dir my_images/
```

Every stage writes its output into `--project`, so you can also re-run just
one stage later (e.g. regenerate images without redoing narration) by
combining `--skip-*` flags as needed and pointing at the files already in the
project folder.

## What each stage does

| Stage | Module | Skip flag |
|---|---|---|
| Script (topic → numbered scenes) | `modules/script_gen.py` | `--skip-script` |
| Narration (ElevenLabs, with word timestamps) | `modules/narration.py` | `--skip-audio` |
| Images (OpenAI) | `modules/images.py` | `--skip-images` |
| Assembly (ffmpeg: captions, title, mux) + QC | `modules/assemble.py` + `modules/captions.py` | always runs |

Narration audio is generated **per scene**, so each scene's exact duration
comes directly from its own clip — no error-prone alignment across a full
narration track is needed. Scene clips are concatenated with hard cuts
(frame-accurate sync with the audio).

## Camera motion and scene-by-scene rendering

`--motion kenburns` adds slow, eased camera moves to every image, cycling
zoom in, pan right, zoom out and pan left. You can also pick one move, e.g.
`--motion zoom_in`. The default is `none`: still images, exactly like before.

Each scene is rendered as its own clip, cached in
`<project>/render_cache/<format>/` by a hash of its images, timing, captions,
title, motion and size. The clips are then joined and the narration is added.
Re-running an unchanged episode reuses every clip. Changing one scene's image
or narration re-renders just that scene. Scene boundaries are snapped to whole
frames on the running total, so the picture never drifts from the audio, even
at 8–10 minutes.

`--legacy-render` uses the original one-pass assembler, which has no motion
support. Keep it as a fallback.

## Output formats

`--format vertical` (default, the original behavior) → `final_video.mp4`, a 9:16
canvas with the 16:9 image in the middle, the title in the top black bar and
captions below.

`--format landscape` → `final_video_landscape.mp4`, full-frame 16:9 (1920×1080)
for YouTube, captions near the bottom, no title overlay.

`--format both` renders both from the same narration and captions.

## Image file names

Images for scene N can be named `sceneNN.png`, `scene_NN.png` or `tb_NN.png`
(png/jpg). If a scene has several images — e.g. `tb_14_1.png` and
`tb_14_2.png` — they're shown in that sorted order, splitting the scene's time
evenly. A missing scene image stops the run with an error naming the scene.

## Automatic image generation

If you don't pass `--skip-images`, scene images are generated with OpenAI
(`gpt-image-2`, 1536×1024, medium quality by default). Prompts come from each
scene's `image_prompt`, or from a CHAT.IMG-style `batch_prompts.txt` via
`--prompts-file`. Every prompt gets the house style from
`config/style_prompt.txt` added in front (turn that off with `--no-style`).

```bash
# 1. See what it will cost (free; nothing is generated)
python3 main.py --project out/molasses --skip-script --script-file my_script.json \
  --prompts-file batch_prompts.txt --estimate-only

# 2. Generate images + narration and render both formats
python3 main.py --project out/molasses --skip-script --script-file my_script.json \
  --prompts-file batch_prompts.txt --format both
```

Spending safeguards:
- Three limits, all checked before anything is paid for (narration included)
  and again before every single image:
  - `--max-run-cost` (default $5; the old name `--max-image-cost` still works):
    everything paid in this run, images and narration.
  - `--episode-budget` (default $10): everything ever spent in this project
    folder, from `<project>/costs.jsonl`.
  - `--total-budget` (default $250): everything across all projects, from
    `~/.historical_oddities/spend_ledger.jsonl` (move it with `HO_SPEND_LEDGER`).
  Restarting or re-running can't reset these; only deleting a ledger file does.
- Every call is logged as pending *before* it's made, then closed with the
  actual cost OpenAI reports. A call that never closes (crash, timeout) is
  counted at its estimate, since it may have been billed. An API error
  response counts as $0.
- `images/manifest.json` records what each image was made from (prompt,
  style, model, size, quality, reference). An image is reused only if all of
  that is unchanged and the file hasn't been edited. Otherwise the old file is
  moved to `images/_replaced/` and a new one is generated.
- `--reference-image my_ref.png` uses your own master reference instead of
  generating one; `--no-reference` skips the reference (cheaper, less consistent).

Prices in `modules/costs.py` were checked on 2026-11-16 and are estimates;
re-check OpenAI's pricing page now and then. The saved episodes' prompt files
were written for the older sepia notebook look, so they will fight the new
colorful style. Regenerate those prompts with the current
`pipeline_prompt.md`, or use `--no-style` to keep the old look.

## Prompt check (runs before any image is paid for)

Every image prompt is checked first, and generation is refused if any check fails:
- **Prompt count:** exactly one prompt per scene, with contiguous scene numbers.
- **Old style words:** no sepia or notebook wording that fights the locked
  colorful style. Negated mentions like "no paper texture" are fine.
- **Risky wording:** no conflict or intensity words such as "aftermath" or "battle".
- **Unusable references:** no "as established" or "Master Gen ID" pointers
  the API can't see.
- **Punctuation:** no em dashes or curly quotes.
- **Character blocks:** each one is copied word for word wherever that character appears.

Warnings, which don't block generation:
- Filter-sensitive words, even inside "no ..." lists.
- No tone frame at the start ("Lighthearted, non-graphic...").
- Very long prompts.

Results go to `<project>/prompt_check.json`. Run it by hand with
`python3 -m modules.prompt_lint --script script.json --prompts batch_prompts.txt`.
To override, use `--ignore-lint` (not recommended).

## Recording your own narration: clean-up presets

`python3 -m modules.voice my_recording.m4a --out-dir voice_test/` writes
`_raw`, `_light` and `_heavy` versions, all at the same loudness (-16 LUFS),
so you can compare them on headphones and on a phone speaker:
- **light** (recommended): rumble filter, gentle hiss reduction, a bit of
  clarity, softer "s" sounds, mild compression.
- **heavy:** for noisy rooms; stronger noise reduction and compression.

Noise reduction is kept gentle on purpose: overdone, it makes a voice sound metallic.

## Narration caching and voice

`ELEVENLABS_VOICE_ID` (or `--voice-id`) is required: the run stops with a clear
message instead of silently using a stock voice.

Each narration clip is cached in `<project>/audio/cache/`, keyed on its text,
voice, model, speed and seed, with its word timings for captions. Rebuilding
an unchanged episode makes no ElevenLabs calls. Editing one scene's line
regenerates only that clip, and changing the voice or speed regenerates all of them.
Narration counts toward the same run, episode and overall budgets as images,
at `ELEVENLABS_USD_PER_1K_CHARS` (default $0.30, the conservative end of
ElevenLabs' published rates; set it to your plan's rate).

## Automatic quality check

After each render, `ffprobe` checks the file is readable and decodes to the
end, is H.264/yuv420p, has audio, has the expected dimensions, and matches the
narration length (±1 s). Results go to `final_video*_qc.json`, and the run
exits with an error if any check fails. Skip with `--skip-qc`, or check any
file by hand: `python3 -m modules.qc path/to/video.mp4 --size 1920x1080`.

If you bring your own audio (`--skip-audio`), captions fall back to splitting
each scene's script text evenly across its measured duration, since word-level
timestamps are only available from the ElevenLabs "with timestamps" endpoint.

## Notes / things to check before relying on this

- **API request/response shapes**: the OpenAI and ElevenLabs calls in
  `script_gen.py`, `narration.py`, and `images.py` are written against each
  provider's documented API as of my knowledge, but I could not actually test
  them against the live services from this environment (no network access
  here). Before a real run, sanity-check one call against each provider's
  current API docs — model names (`gpt-4o-mini`, `gpt-image-1`,
  `eleven_multilingual_v2`) and endpoint URLs are the most likely things to
  have shifted.
- **The assembly step (the ffmpeg part) is fully tested** — I built it and
  ran it end-to-end against synthetic images/audio in a sandbox and confirmed
  scene switching, zoom/pan, and caption sync all work correctly frame-by-frame.
- **Cost**: image generation and TTS both cost money per call, scaling with
  scene count — check current pricing before running a large batch.
- **Style**: the `--style` flag feeds into both the script's image prompts and
  is meant for something like "simple stick-figure illustration, minimal flat
  color" to match a consistent look across scenes — adjust to your taste.
