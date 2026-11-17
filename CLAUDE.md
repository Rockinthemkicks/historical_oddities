# Historical Oddities — notes for Claude

Automated pipeline for illustrated, narrated educational videos (YouTube long-form + Shorts/Reels).
Full requirements: `docs/PROJECT_BRIEF.md`. Current state and risks: `docs/AUDIT.md`.

## Ground rules
- Preserve working behavior. `python3 main.py` with no new flags must render exactly what it did
  before (9:16 canvas, 16:9 image letterboxed, title in the top bar, captions below).
- Don't change the script JSON schema (`title`, `scenes[].scene_number/narration/image_prompt`)
  without backward compatibility. `image_prompt` is often intentionally empty.
- Small changes on feature branches, opened as PRs. Never merge major changes without the owner's OK.
- Never commit `.env`, API keys, tokens, or generated media (`out/`, images, mp3/mp4).
- Don't call paid APIs (ElevenLabs, OpenAI) in tests or experiments without the owner's approval.
  Tests must run offline with placeholder media.
- The visual style is an open owner decision (style_bible.md vs the brief's Vintage
  Notebook-Cartoon). Don't hard-code either one into prompts or code until it's settled.
- Publishing always needs the owner's explicit authorization.

## Commands
- Tests: `pip install -r requirements.txt -r requirements-dev.txt && pytest -q` (needs ffmpeg)
- Assemble from your own files:
  `python3 main.py --project out/x --skip-script --script-file my_script.json --skip-images --images-dir my_images/ [--format both]`
- QC an existing video: `python3 -m modules.qc out/x/final_video.mp4 --size 1080x1920`

## Layout
- `main.py`: the entry point. `modules/`: stages. `modules/qc.py`: ffprobe checks.
- `episodes/<slug>/`: saved scripts and batch prompts (images stay local, not committed).
- `pipeline_prompt.md`, `docs/video_pipeline_workflow.md`: the ChatGPT creative workflow.
