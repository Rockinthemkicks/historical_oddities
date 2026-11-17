# Video Pipeline: topic → finished captioned MP4

Turns a topic into a numbered-scene script, narration audio (ElevenLabs), scene
images (OpenAI), and a finished vertical MP4 with Ken Burns zoom/pan and
word-synced captions — or run only the stages you want and bring your own
audio/images for the rest.

## Setup

```bash
pip install -r requirements.txt
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
| Assembly (ffmpeg: zoom/pan, captions, mux) | `modules/assemble.py` + `modules/captions.py` | always runs |

Narration audio is generated **per scene**, so each scene's exact duration
comes directly from its own clip — no error-prone alignment across a full
narration track is needed. Scene clips are concatenated with hard cuts
(frame-accurate sync with the audio) and each gets an alternating Ken Burns
zoom-in / zoom-out / pan movement for visual variety.

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
