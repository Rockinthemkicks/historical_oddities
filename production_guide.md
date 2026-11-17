# Video Pipeline — Production Guide (with topic-dedup check)

This covers how the four pieces fit together and the exact steps to produce
one video, start to finish:

- `check_topic.py` — checks/logs topics so you don't accidentally repeat one
- `topics_log.json` — the log itself
- `pipeline_prompt.md` — what you paste into a chat session to start a new
  video's creative production (script → images)
- `video_pipeline_workflow.md` — the reference doc for running `main.py`
  (narration, captions, final assembly)

The short version of the design: **you and a chat session handle everything
creative and reviewable** (topic, script, storyboard, reference image, scene
images), and **`main.py` handles everything mechanical** (voice generation,
caption timing, video assembly). The two meet at exactly two files:
`my_script.json` and a folder of `sceneNN.png` images.

---

## 0. One-time setup

Drop these two files into your `video_pipeline` folder, next to `main.py`:

- `check_topic.py`
- `topics_log.json`

That's it — no extra dependencies, `check_topic.py` only uses Python's
standard library. Everything else you already have from before.

If you have earlier finished videos that aren't reflected in
`topics_log.json` yet, back them in now (see §3 below) so the log is
complete before you rely on it.

---

## 1. Start a new video: kick off the chat session

Open a new chat session (or a fresh conversation) and paste in the full
contents of `pipeline_prompt.md`, then tell it your candidate topic.

The session will work through these stages, stopping for your approval
after each one:

| Stage | What happens |
|---|---|
| 0 | Checks your topic against the log (see §2) |
| 1 | Drafts the script — title + numbered scenes with narration |
| 2 | Drafts storyboard / per-scene image prompts |
| 3 | Generates the master visual reference (the recurring character/style anchor) |
| 4 | Generates scene images against that reference, one at a time or in small batches |
| 5 | Hands off `my_script.json` + an `images/` folder in the format `main.py` expects |

At each stop, review what it produced and reply `APPROVE` to move on, or
give feedback to revise before approving. Once you approve something, the
session treats it as locked and won't silently change it later — if a
later stage would conflict with something you already approved, it's
supposed to stop and tell you rather than quietly overwrite it.

---

## 2. Stage 0 in practice: the topic check

This stage runs `check_topic.py --list` and `check_topic.py --check "your
topic"` and reviews the output against your proposed topic.

You can also run this yourself before even starting the chat session, if
you want a sanity check first:

```bash
cd video_pipeline
python3 check_topic.py --list
python3 check_topic.py --check "The Dancing Plague of 1518"
```

**What `--check` catches:** topics that share a lot of the same keywords
with something already logged.

**What it misses:** a topic that's the same underlying subject but heavily
reworded — e.g. "The Dancing Plague of 1518" vs. "When an Entire City
Couldn't Stop Dancing" won't trigger a flag from the script alone, because
they don't share enough literal words. This is a real limitation of
keyword matching, not a bug.

That's why Stage 0 also has the chat session look at the full `--list`
output and use its own judgment on *meaning*, not just wording — paste the
list in and ask directly: "does this new topic overlap with anything on
this list, even if worded differently?" That combination (script for the
obvious cases, judgment for the reworded ones) is the actual safety net —
neither one alone is reliable.

If Stage 0 flags a likely repeat, it should stop and tell you rather than
guessing you meant something else or quietly picking a different angle.

---

## 3. Logging a topic (and backfilling old ones)

**Only log a topic once you've actually approved its script** (end of
Stage 1) — not every draft you float. Logging too early means abandoned
ideas end up blocking real future topics.

```bash
python3 check_topic.py --add "The Title You Approved" \
  --topic "one-line description of the underlying subject" \
  --project out/whatever_you_named_it
```

- `--topic` is optional but improves future matching — it's what actually
  gets compared, not just the (often more stylized) title.
- `--project` is just for your own reference; it's not used in matching.

**To backfill videos made before you had this tool:** run `--add` once per
past video the same way, using the title (and, if you remember it, a short
topic description) from each one. There's no automatic way to discover
these — they need to be added by hand.

---

## 4. Command reference

```bash
# List everything logged so far
python3 check_topic.py --list

# Check a candidate topic against the log
python3 check_topic.py --check "your candidate topic"

# Log an approved topic
python3 check_topic.py --add "Title" --topic "short description" --project out/name
```

Run any of these from inside the `video_pipeline` folder (or point Python
at the full path to `check_topic.py`). The log file (`topics_log.json`)
lives next to the script and is read/written automatically — you don't
pass its path in.

---

## 5. Stage 5 handoff → running `main.py`

Once the chat session reaches Stage 5, you'll have:

- `my_script.json` — matching the schema in `video_pipeline_workflow.md`
  (`title`, `scenes[].scene_number`, `scenes[].narration`)
- an `images/` folder with `scene01.png`, `scene02.png`, ... matching every
  scene number in the script

From here, follow `video_pipeline_workflow.md` steps 2 onward (you can skip
its own §1, since the chat session already wrote the script for you):

```bash
python3 main.py --project out/your_project_name \
  --skip-script --skip-images \
  --script-file my_script.json --images-dir my_images/
```

This is the one paid/automated step — it generates narration via
ElevenLabs, builds synced captions, and assembles `final_video.mp4`.
Everything before this point (topic, script, images) was already handled
in chat.

---

## 6. Quick checklist for one full video

1. `python3 check_topic.py --list` / `--check "..."` — sanity-check the
   topic yourself (optional, since Stage 0 does this too)
2. Paste `pipeline_prompt.md` into a new chat session with your topic
3. Approve Stage 0 (topic check) → 1 (script) → 2 (storyboard) →
   3 (reference image) → 4 (scene images) → 5 (handoff)
4. `python3 check_topic.py --add "..."` — log the approved topic
5. Run `main.py` with `--skip-script --skip-images` pointing at the
   handed-off `my_script.json` and `images/` folder
6. Check `out/your_project/final_video.mp4`

---

## 7. Known limitations, honestly

- `check_topic.py`'s automatic matching is a heuristic, not a guarantee.
  It's there to catch the obvious cases cheaply; the chat session's own
  read of the `--list` output is what catches the subtler ones.
- The log is only as complete as what you've added to it — a topic won't
  get flagged if it was never logged, including any pre-existing videos
  you haven't backfilled yet.
- Nothing here prevents you from proceeding past a flagged topic if you
  genuinely want to (e.g. a legitimate follow-up video on a related but
  distinct subject) — it's a check, not a hard block.
