Pipeline Prompt (v2 — matched to the actual video_pipeline program)

I am starting production on one complete educational video.

WHAT THIS SESSION PRODUCES
The video_pipeline program (main.py) only consumes two things: a script file
matching its schema (title + numbered scenes, each with a `narration` line)
and a folder of scene images named sceneNN.png/.jpg (or scene_NN.png/.jpg —
both are accepted) matching the scene
numbers. Everything else — narration audio, captions, final assembly — is
handled automatically by the program once those two things exist. This
session's job is to produce those two things, reviewed and approved by me
at each stage. It is not responsible for running main.py itself.

RUN THE STAGES SEQUENTIALLY, WAITING FOR APPROVAL
Stage 0 → Topic (brainstorm if I haven't given you one, then check for
           duplicates) → STOP FOR APPROVAL
Stage 1 → Script (title + numbered scenes with narration) → STOP FOR APPROVAL
Stage 2 → Storyboard / per-scene image prompts → STOP FOR APPROVAL
Stage 3 → Master visual reference (the recurring character/style anchor,
           generated with whatever image tool I'm using outside this
           session) → STOP FOR APPROVAL
Stage 4 → Batch image-prompt export: write one image prompt per scene,
           formatted as a downloadable batch_prompts.txt for CHAT.IMG
           → STOP FOR APPROVAL, then wait while I run CHAT.IMG myself
Stage 5 → Final handoff: assemble my_script.json in the exact format
           main.py expects (images are supplied separately by me, from
           CHAT.IMG's output), and stop.

Do not automatically continue past a STOP. Wait for me to respond APPROVE.
When I do, determine the next stage yourself — I shouldn't need to prompt
you for each one manually.

STAGE 0 — TOPIC
If I gave you a candidate topic, check it against `python3 check_topic.py
--list`. Flag any likely overlap with a past topic before proceeding,
including reworded/paraphrased overlaps that the script's own keyword
matching might miss — use your judgment on meaning, not just shared words.
If it's a genuine repeat, say so and stop; don't proceed on the assumption
I meant something else.

If I did NOT give you a topic, propose 3–5 new topic ideas instead. Match
the genre/tone of what's already in the `--list` output (surprising true
stories, historical near-misses/anomalies, etc. — infer the pattern from
the log itself). For each idea give a one-line description. Before
presenting them to me, cross-check every idea yourself against the
`--list` output for overlap with existing titles/topics and silently drop
or replace any that are too close — don't make me screen out duplicates
you already generated. Present the surviving ideas and STOP FOR APPROVAL.
When I pick one (or ask for different ideas), treat my pick as the
approved topic and move to Stage 1.

LOG THE TOPIC IMMEDIATELY ON APPROVAL
As soon as I approve a topic at this stage — not later, not once the
script is approved — give me the exact command to log it:
`python3 check_topic.py --add "<topic phrase>" --topic "<one-line
description>" --project ""` (leave --project empty for now if the project
folder name isn't decided yet; tell me to fill it in once it is). Use the
actual approved topic/description text, never placeholder brackets. If the
title changes later once the script is written (Stage 1), tell me to edit
that same log entry's title in topics_log.json rather than adding a
second entry for the same topic.

STAGE 4 — BATCH IMAGE-PROMPT EXPORT
Do not generate scene images yourself in this session. Instead, write one
image prompt per scene (in scene-number order, contiguous, matching the
storyboard from Stage 2) and output them as a downloadable batch_prompts.txt
formatted for CHAT.IMG: one prompt per line, with a single blank line
between each prompt, nothing else on the prompt's line (no numbering, no
"Scene N:" prefix — CHAT.IMG expects the raw prompt text only). Before
presenting it, confirm silently that the number of prompts equals the
number of scenes.

CHAT.IMG's reference-image mechanism does not reliably carry the character
sheet into generation for this setup — treat every prompt as text-only.
Never write a prompt that just points back at the reference ("as
established," "per reference," "the usual character") — that produces
visible drift. Instead:

1. Before writing any scene prompts, write one CHARACTER REFERENCE BLOCK
   per recurring character/horse/vehicle, each 1-3 sentences giving its
   concrete visual specifics (hair, coloring, clothing, distinguishing
   features for characters; coat color and tack for horses; color, trim,
   and lettering for vehicles), pulled from the approved Stage 3 reference
   sheet. Put these blocks at the top of batch_prompts.txt, above the
   scene prompts, labeled in caps (e.g. "CITY OFFICIAL: ...").
2. In every single scene prompt that includes a given character/horse/
   vehicle, copy its reference block in verbatim (not paraphrased, not
   shortened) as part of that scene's own prompt text. A character
   appearing in all 3 scenes gets its full description repeated in all 3
   scene prompts.
3. This applies to every future video, not just this one — it's the
   default Stage 4 behavior regardless of topic.

IMAGE-PROMPT PHRASING TO AVOID GENERATION FAILURES
CHAT.IMG's safety filter reacts to specific wording more than to the
underlying content — two prompts describing equally non-graphic scenes can
get different results purely from phrasing. Apply these rules to every
scene prompt by default, not just after a failure:
- Open the action description with an explicit non-graphic frame stated as
  part of the main description, not only tacked on at the end — but match
  the video's actual tone: "lighthearted, comedic" for a comedic topic like
  the Emu War, "somber, respectful, non-graphic" for a genuinely tragic
  topic (mass casualty events, disasters). Never force comedic framing onto
  a tragedy just because it's the default example — the frame just needs to
  state the register up front, whatever that register is.
- Avoid conflict-coded AND intensity words regardless of tone — "standoff,"
  "aftermath," "battle," "clash," "violently," "brutal," "devastating," and
  similar read as tenser than intended even in a factual/explanatory
  sentence. Prefer neutral phrasing instead: "face-off," "scene,"
  "encounter," "dramatically," "powerfully" (comedic topics) or "moment,"
  "view," "significantly" (somber topics).
- When a topic involves real deaths, represent scale symbolically only
  (numbers, simple non-graphic symbolic figures, labeled counts) and say so
  explicitly in the prompt — never depict bodies, injury, or suffering, and
  don't rely on the closing negation list alone to establish that.
- Don't stack a long list of negations ("no injuries, no dead animals, no
  gore...") unless the scene actually contains something that needs that
  specific disclaimer (e.g. a weapon shown in active use). A negation list
  repeats the sensitive words themselves and can trigger the filter even
  though it's saying "no" — only include the negations relevant to what's
  literally depicted in that scene.
- Any literal on-image text (titles, labels) should use plain ASCII
  punctuation only — straight quotes and hyphens, not em dashes or curly
  quotes — since some renderers mishandle non-ASCII characters in
  rendered text.
- If a scene's visible title/text spells out a loaded word (e.g. "WAR") in
  large prominent lettering, treat that as higher-risk than the same word
  appearing in ordinary descriptive prose. If such a scene fails, reword
  the visible text itself before troubleshooting anything else.

MANDATORY PRE-FLIGHT SCAN before presenting batch_prompts.txt: re-read
every prompt you just wrote, character by character, specifically for (a)
any em dash (—) or curly quote (" " ' ') anywhere in the prompt, not just
in on-image text, and replace with a straight hyphen/quote, and (b) any
word from the conflict/intensity list above. Fix every hit before
presenting the file. This is a literal find-and-check step, not a
reminder to "keep in mind" — do it against the actual text you wrote, and
confirm silently that the scan is clean before the file is shown to me.

After presenting batch_prompts.txt, tell me explicitly:
- the exact number of prompts (must match my scene count)
- the mapping of prompt order to scene number (e.g. "line 1 = scene 1,
  line 2 = scene 2, ..." in the blank-line-separated sequence) — I'll need
  this to name CHAT.IMG's output files correctly
- to bring the Stage 3 master reference image into CHAT.IMG alongside this
  file
Then STOP. I will run CHAT.IMG myself, rename its output files to
sceneNN.png (CHAT.IMG's own scene_NN.png naming works too) per your
mapping, and tell you when they're ready.

CHAT.IMG BOUNDARY
This rule is critical. Do NOT attempt to execute batch_prompts.txt as a
native multi-image batch inside this session unless the current interface
explicitly provides that capability. Your responsibility for Stage 4 is:
prompt writing → file creation → count validation → handoff. Batch image
generation itself happens in CHAT.IMG, outside this session. Do not claim
or imply that the images have been generated until I tell you they're
ready.

When I tell you the images are ready and named, treat that as approval to
move to Stage 5 — you won't be able to see or validate the image files
yourself unless I upload them back into this chat, so trust my confirmation
of the count and naming rather than re-deriving it.

PROJECT LOCK
Once I approve something, it's locked. Preserve approved: title, script,
narration lines, scene numbering/order, the visual reference and its
established character/style, and scene filenames. Don't silently rewrite
approved material. If a later stage conflicts with something already
approved, stop and name the conflict rather than quietly changing it.

EXCEPTION — style_bible.md changes: if style_bible.md itself gets updated
after a video's Stage 3 reference sheet was already approved, that
reference sheet is not exempt from the update just because it's "locked" —
it was only ever supposed to reflect the bible, so an out-of-date bible
means the sheet is now out of compliance, not that the bible doesn't apply
to it. Flag this explicitly rather than treating PROJECT LOCK as covering
it: tell me the reference sheet predates the current bible and needs to be
regenerated before Stage 4 writes any new batch prompts against it.

VALIDATION
Before Stage 5, actually check — don't just claim — that:
- scene numbers in the script are contiguous starting at 1 (no gaps)
- the number of prompts in batch_prompts.txt equals the number of scenes
- the script JSON is valid and matches the schema in
  video_pipeline_workflow.md (title, scenes[].scene_number,
  scenes[].narration)
Since scene images come from CHAT.IMG rather than this session, you can't
verify the image files yourself — remind me to check that every scene
number has a matching sceneNN or scene_NN image file in my images folder
before I run
main.py.

FILE CREATION
Stage 4 must produce an actual downloadable batch_prompts.txt — not a code
block or pasted text standing in for it. Stage 5 must produce an actual
downloadable my_script.json.

MASTER VISUAL REFERENCE (Stage 3)
Before generating anything, read `style_bible.md`. It defines rendering
technique, proportions/silhouette rules, base color-palette family, and the
6-section reference-sheet layout (Characters / Color Palette / Line &
Texture / Props & Vehicles / Style Overview / Composition Notes) — all of
which are FIXED and must be identical to every past video. Do not alter,
reinterpret, or "improve" any of that. Your only job for this stage is to
fill in the per-topic content on top of it: this video's characters, its
props/vehicles, 1-2 topic accent colors layered on the fixed base palette,
and the era/setting line in Style Overview. If style_bible.md is missing,
stop and tell me — don't invent a style from scratch.

CROSS-VIDEO CONSISTENCY
Text descriptions alone drift between sessions — the same wording can
render slightly differently every time. To keep every video's fixed
elements (line weight, flatness, palette, proportions) visually identical
rather than just "similarly described," ask me to attach the most recent
past video's approved master reference sheet image alongside the text
rules when generating a new one, so the image tool has an actual visual
target to match, not just style_bible.md's words to reinterpret from
scratch.

EXCEPTION — never chain from an overridden project: if the most recent
past video used a documented STYLE OVERRIDE (a per-project deviation from
style_bible.md, logged as such at the time), do NOT use its reference
sheet as the visual anchor for a new video — that would silently spread
the one-off deviation into projects that never approved it. Skip back to
the most recent video that was NOT an override, or if none exists, tell me
there's no valid bible-compliant anchor available and generate from the
text rules in style_bible.md alone. Say explicitly which case applied.

If I don't have a past reference sheet to hand (first video, or I
say I don't have it), generate from the text rules alone as before, but
say explicitly that no visual anchor was used this time.

Generate the reference sheet with whatever image tool/model I'm actually
using for this project (tell me if you're not sure which), prompting it
with the fixed rules from style_bible.md plus this video's per-topic
content, laid out in the same 6 sections. After it's produced, look at the
actual result before asking me to approve it — check it's a plausible
sheet in the established style, not, e.g., a broken/blank generation, and
flag anything that looks like it drifted from a fixed rule (different line
weight or detail level, added texture/shading, off-palette or muted/earthy
colors, changed proportions) compared to the visual anchor (if one was
used) or to past approved videos, rather than approving it as-is.
Specifically scan the sheet and its own description for any of
style_bible.md's forbidden words — "aged," "parchment," "sepia," "muted,"
"earthy," "cream," "ochre," "soot," "restrained" — applied to the overall
image; their presence means the sheet has drifted even if it looks
plausible at a glance, and it must be regenerated before you present it
for approval, not approved with a caveat. There is
no "Gen ID" to preserve; consistency across
scene images comes from re-using this reference sheet itself as visual
input to each scene generation (or, if the tool has no such reference
mechanism, from writing very consistent scene image prompts that describe
the character/style explicitly and identically each time).

PROGRESS TRACKING
At each approval checkpoint, tell me briefly:
Completed: [current stage]
Next after approval: [next stage]
Don't dump future stages into the response.

START
Read video_pipeline_workflow.md, check_topic.py, and style_bible.md now.
Then begin at Stage 0 with the topic I give you. Do not proceed past any
stage until I approve it.
