# Milestone 1 — Existing Pipeline Audit

Date: 2026-11-16 · Scope: the `video_pipeline` folder from `Historical_Oddities.zip`
(last modified 2026-08-26), plus the ChatGPT workflow docs and six episode folders.

This was read and run in a Linux sandbox. Nothing here was tested against the
live ElevenLabs or OpenAI APIs: no keys were used and no money was spent.

## 1. What exists

| Piece | What it does |
|---|---|
| `main.py` | The single entry point. Four stages: script → narration → images → assembly. Each can be skipped with `--skip-script/--skip-audio/--skip-images` and replaced by your own files. |
| `check_topic.py` | Stand-alone duplicate-topic checker. Uses token overlap, not meaning. `topics_log.json` is **empty**, so it currently protects nothing. |
| `modules/script_gen.py` | OpenAI `gpt-4o-mini` writes a Shorts-style JSON script. **In practice you don't use it**: scripts come from the ChatGPT workflow (`pipeline_prompt.md`). |
| `modules/narration.py` | ElevenLabs `/with-timestamps`, model `eleven_multilingual_v2`. Character timings are turned into word timings for the captions. |
| `modules/images.py` | OpenAI image API (`gpt-image-2`): one reference image, then edits of it per scene. **Also unused in practice**: images come from ChatGPT/CHAT.IMG. |
| `modules/captions.py` + `caption_images.py` | Groups words into 3-word cues and renders each cue as a PNG with Pillow. This avoids the FFmpeg `drawtext`/`libass` problems seen before. |
| `modules/assemble.py` | One FFmpeg call: static image per scene, hard cuts, title PNG in the top bar, a caption PNG overlay per cue, H.264/AAC. |
| `pipeline_prompt.md`, `docs/video_pipeline_workflow.md`, `production_guide.md` | The human + ChatGPT workflow, Stages 0–5, with explicit `APPROVE` stops. |

There were **three copies** of the code. `video_pipeline/` is the newest: it
accepts the `scene_NN` CHAT.IMG naming and has the updated dedup wording.
That copy is the one now on `main`. The other two copies are older and the
same as each other.

### How it actually runs today
The creative stages run in ChatGPT and CHAT.IMG. `main.py` only runs
narration and assembly:
```
python3 main.py --project out/x --skip-script --script-file my_script.json \
                --skip-images --images-dir my_images/
```

## 2. JSON schema (unchanged)
```json
{"title": "...", "scenes": [{"scene_number": 1, "narration": "...", "image_prompt": ""}]}
```
`image_prompt` is empty in all six saved scripts, as expected. Prompts live in
`batch_prompts.txt`. Saved episodes have 17–25 scenes and 214–230 words,
which is about 85–90 s of narration.

## 3. Findings and risks

**Blocking or high**
1. **Your images don't match the names the code looks for.** Your episode
   images are named `tb_NN.png`, sometimes with `tb_NN_1/_2` variants, but the
   code only looked for `sceneNN`/`scene_NN`. Where a scene had two
   variants, it picked one arbitrarily. *Fixed in the Milestone 2 PR:*
   `tb_NN` is now accepted, and multiple images in one scene share its time
   in order.
2. **Missing or mismatched episode assets.**
   - London Beer is missing scenes 4 and 15.
   - Niagara is missing 15.
   - Lake Peigneur is missing 1–3 and 24.
   - Boston Molasses and the 1904 Olympic marathon have no images.
   - The `Meat Shower` folder holds the *Olympic marathon* script next to
     Kentucky Meat Shower images and prompts. The real Meat Shower script was
     in `1-The Day Niagra Falls Stopped Flowing`.

   With that pairing fixed, **Kentucky Meat Shower is the only episode with a
   complete image set.** `episodes/` in the repo is organized by real topic.
3. **The visual style is contradictory.** `docs/style_bible.md` (Aug 26) bans
   paper texture, sepia and cross-hatching and asks for a bright, saturated,
   flat palette. Every saved `batch_prompts.txt` and the Project Brief's
   "locked" *Vintage Notebook-Cartoon* ask for exactly those things. **Owner
   decision needed** before any image automation is built.
4. **The repo is public**, but the brief says private. No secrets are committed:
   `.env` is git-ignored and has been checked. The uploaded zip does contain a
   real `.env` with live keys, so keep that zip private.

**Medium**
5. **The voice can silently drift.** If `ELEVENLABS_VOICE_ID` is unset,
   narration falls back to a stock voice without any warning. This is the
   "inconsistent voice" issue from before. Proposed fix: fail instead of
   falling back, or pin the voice in config.
6. **Nothing is cached.** Re-running regenerates every narration clip, and you
   pay again. Retries cover only HTTP 429, not timeouts or 5xx errors. There
   are no spend limits or cost logs.
7. **README says "Ken Burns zoom/pan", but the code renders static images**
   with hard cuts (see `build_video`'s docstring). Motion is Milestone 3 work.
8. **Assembly won't scale to 6–9 minutes as it stands.** Every caption cue is
   a separate FFmpeg input and overlay, so a 7-minute episode means ~400 inputs
   in one filter graph. That is slow and fragile, and any failure restarts the
   whole render. Long-form needs per-scene segment rendering, so each scene
   is cached and the render can restart from where it stopped.
9. **The unused generators are out of step with the workflow.** `images.py`
   defaults to *portrait* 1024×1536, while scenes are 16:9.
   `script_gen.py` defaults to a "stick-figure" style and a 2–5 s-per-scene
   Shorts prompt. The model names (`gpt-image-2`, `gpt-4o-mini`) and all
   prices must be re-checked before use.

**Low**
10. `requirements.txt` listed only `requests`; Pillow was missing. *Fixed.*
11. There were no tests. *Added:* 14 tests, including real FFmpeg renders.
12. Folder names have typos (`Niagra`, `Molases`). Harmless, but it's why
    `episodes/` uses clean slugs.

## 4. Smallest safe upgrade path

| Step | Change | Status |
|---|---|---|
| M2 | `--format vertical\|landscape\|both`, with vertical as the untouched default. Automatic ffprobe QC (`*_qc.json`, exits non-zero on failure). `+faststart` MP4s. `tb_NN` and multi-image scenes. Tests and CI. | **This PR** |
| M3a | Render per scene, then concat (cached and restartable). Ken Burns pan/zoom on each segment. Captions burned per segment. | Next |
| M3b | Narration cache keyed on text + voice + settings. Voice pinned in config. Cost log per run with a spend cap. | Next |
| M3c | Long-form script structure (hook → context → mechanism → consequences → payoff) in `pipeline_prompt.md`, kept to the same JSON schema. | Needs owner input |
| M4 | Shorts: pick 3 segments, write standalone narration, and recompose for 9:16 instead of letterboxing. | Later |
| M5+ | Topic research and scoring, orchestration, publishing, analytics. | Later |

**Owner decisions (2026-11-16):** (a) style: more color, so `style_bible.md` is
the locked style; (b) the repo stays public; (c) automate image generation
through the API. Done in the `auto-image-generation` PR.
