# Video Pipeline — Full Workflow Guide

Your setup: you write the script and supply the images. The program generates
narration (ElevenLabs) and captions, and assembles everything into a finished
vertical video with your images letterboxed to 16:9 and your title centered
in the black space above the image.

---

## 0. One-time setup (already done, listed for reference)

```bash
cd ~/Desktop/video_pipeline
pip install -r requirements.txt
```

`.env` has your `ELEVENLABS_API_KEY` filled in. `ffmpeg -version` runs
without error.

---

## 0. Check your topic isn't a repeat

Before writing a new script, check the proposed topic against everything
you've already produced:

```bash
python3 check_topic.py --list
python3 check_topic.py --check "your candidate topic here"
```

`--check` flags likely overlaps using keyword matching, but it will miss
duplicates that are heavily reworded (e.g. "The Dancing Plague of 1518" vs.
"When an Entire City Couldn't Stop Dancing" won't be caught by the script
itself). If you're doing this inside a chat session, paste the `--list`
output in and ask the model to judge whether the new topic overlaps with
anything on it — that catches paraphrased duplicates the script misses.

Once you've approved a topic (right after Stage 0, before you even write
the script), log it immediately:

```bash
python3 check_topic.py --add "The Topic You Approved" \
  --topic "one-line description of the underlying subject" \
  --project out/whatever_you_named_it
```

Leave `--project` as an empty string (`--project ""`) if you haven't
picked a project folder name yet — you can edit `topics_log.json` by hand
to fill it in later. If the polished title changes once the script is
written, edit that same entry's `title` field in `topics_log.json` instead
of adding a second entry for the same topic.

---

## 1. Write your script

Create `my_script.json` **inside the `video_pipeline` folder**.

```json
{
  "title": "The Man Who Survived Two Atomic Bombs",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "Imagine surviving an atomic bomb.",
      "image_prompt": ""
    },
    {
      "scene_number": 2,
      "narration": "Now imagine surviving two of them, in the same week.",
      "image_prompt": ""
    }
  ]
}
```

Field-by-field:

| Field | Required? | What it does |
|---|---|---|
| `title` | Yes, if you want a title shown | Displayed centered above the image (in the letterboxed black space) for the video's full duration. Leave as `""` or omit to show no title. |
| `scene_number` | Yes | Starts at 1, increases by 1, no gaps. Determines scene order and which image file matches which scene. |
| `narration` | Yes | The exact line spoken by ElevenLabs for that scene, and the exact text captioned. Write it the way you want it heard. |
| `image_prompt` | Not used in your workflow | Only matters if the program is generating images itself. Leave blank. |

Fast way to create the file without copy-paste formatting issues: run
`nano my_script.json`, paste your JSON, then `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## 2. Prepare your images

Create a folder (e.g. `my_images/`) inside `video_pipeline`:

```bash
mkdir my_images
```

Drop your images in, named to match scene numbers, zero-padded to 2 digits:

```
my_images/
  scene_01.png
  scene_02.png
  ...
```

- `.png`, `.jpg`, `.jpeg` all work.
- Both `scene01.png` and `scene_01.png` naming (with or without the
  underscore) are accepted — use whichever your image tool exports.
- Every scene number in your script needs a matching file, or the run fails
  with "no image found for scene N".
- **Any resolution/aspect ratio is fine.** The program automatically crops
  each image to a 16:9 box and centers it in the vertical frame with black
  bars above/below — you don't need to pre-crop or resize anything.

---

## 3. Run it

From inside `video_pipeline`:

```bash
python3 main.py --project out/my_video \
  --skip-script --skip-images \
  --script-file my_script.json --images-dir my_images/
```

This generates narration (ElevenLabs — the only paid step in this workflow),
builds captions, and assembles the final video. Narration is the one part
you can't skip in this workflow, since captions are timed off of it.

### Optional flags

| Flag | Default | What it does |
|---|---|---|
| `--project <path>` | *(required)* | Output folder. Use a new name each time to keep past videos. |
| `--voice-speed <0.7-1.2>` | `1.0` | Narration speed. Below 1.0 = slower, above 1.0 = faster. `0.9` has worked well. |
| `--pause <seconds>` | `0.3` | Silence inserted between scenes. `0` disables it. |
| `--voice-id <id>` | your `.env` default | Use a specific ElevenLabs voice for this run. |
| `--no-title` | *(off)* | Skip the title overlay even if `title` is set in your script. |
| `--width` / `--height` | `1080` / `1920` | Canvas size. Default is vertical 9:16 with images letterboxed to 16:9 inside it. |
| `--fps` | `30` | Output frame rate. |

Example with a couple of options:

```bash
python3 main.py --project out/my_video --skip-script --skip-images \
  --script-file my_script.json --images-dir my_images/ \
  --voice-speed 0.9 --pause 0.4
```

---

## 4. Get your video

```bash
open out/my_video/final_video.mp4
```

Watch it through and check: images match their narration, captions are
readable and synced, title is correct, no odd cuts.

Other files saved in `out/my_video/` if you want to inspect anything:
- `audio/sceneNN.mp3` -- individual narration clips
- `full_audio.mp3` -- narration + pauses joined into one track
- `caption_images/` -- the individual rendered caption PNGs
- `title.png` -- the rendered title overlay

---

## 5. Next video

Same steps, new project folder:

1. Write a new `my_script.json` (or edit the old one)
2. Drop matching images into a folder
3. Run the command again with a new `--project out/whatever_name`

---

## Troubleshooting

**"No such file or directory: my_script.json"**
You're not in the `video_pipeline` folder, or the file isn't there. Run `ls`
to check, and `find ~ -iname "my_script.json" 2>/dev/null` to locate it.

**"No image file found for scene N"**
Check filenames match `sceneNN.ext` or `scene_NN.ext` (two digits,
zero-padded, either with or without the underscore) for every scene number
in your script.

**"402 Payment Required" (ElevenLabs)**
Your ElevenLabs account is out of character quota or has no payment method.
Check elevenlabs.io/app/usage and elevenlabs.io/app/subscription.

**"429 Too Many Requests"**
The script automatically retries these with a short wait built in. If it
persists, wait a minute and re-run the same command.

**Re-running after a partial failure**
Safe to re-run as-is. Nothing is corrupted by re-running -- but each run
regenerates narration from scratch in this workflow, so a re-run does re-spend
ElevenLabs usage even if earlier scenes had already succeeded.
