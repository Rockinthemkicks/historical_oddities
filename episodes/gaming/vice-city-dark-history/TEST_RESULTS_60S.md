# 60-second production test: results (Nov 24, 2026)

Ran on GitHub Actions with the owner's authorization ($2 test cap). Media isn't committed: the owner has
the video, the images, the reference sheet and the thumbnail mockup from the run's artifact.

## Output

| | |
|---|---|
| Video | 46.0 s, 1920x1080, 30 fps, H.264/AAC. QC passed: dimensions, decodes to the end, duration matches the narration |
| Framing | All 1536x1024 images fill 16:9 cleanly. No letterboxing, no distortion |
| Images | 1 reference sheet + 6 scene and thumbnail images, all 1536x1024 |
| Thumbnail mockup | 1280x720: generated badge-and-skyline background + our own lettering ("BUILT ON CRIME", "VICE CITY LORE · 1984-1986") |

## Cost

| Item | Basis | Amount |
|---|---|---|
| Images (7) | actual, from OpenAI usage | $0.37 |
| Narration, this run (726 chars) | ledger budget figure ($0.30/1k); ElevenLabs bills in plan credits | $0.22 |
| Narration, first run (failed later at the images because the OpenAI account had no credits) | ledger budget figure | ~$0.22 |
| **Test total** | | **~$0.81 of the $2.00 test cap**, ~$1.19 left |

Since PR #23, the button keeps paid narration and images between runs, so a re-run with unchanged inputs costs nothing.

## What worked

- **Character consistency, the main test goal: good.** The Corporal is recognisably the same man on the reference sheet, at the base (1984, field jacket), in the hospital corridor and at the night pier (1986, civilian shirt). Small drift: long rolled sleeves in the hospital vs short sleeves on the sheet.
- **Art direction holds across all 6 images:** painterly, cinematic lighting, warm-dusk and neon-night palette. No text artifacts, logos or recognisable game characters.
- **The clockwork-city metaphor reads well**, including the reframed push-in to the empty chair.
- **Timing:** scene timing follows the real narration audio. Visual changes land on the narrator's sentences.

## Issues found (by watching the frames and measuring the audio)

1. **The ambient bed is inaudible:** -55 dB in the pauses. Overall loudness is -17.9 LUFS. Fix: raise the bed to roughly -30 dB under the voice and normalize the mix to -14 to -16 LUFS. Free.
2. **Typography beats look flat next to the illustrations.** The four-row "VICE CITY, 1984" board sits static on black for about 10 s (the longest sentence), which feels like a slide. Fix: put cards over a darkened, blurred version of the previous illustration, and reveal rows one at a time by splitting that sentence into four beats. Free; no new images.
3. **The title card flashes for about 1 s** ("He inherited it." is a short line). Fix: hold the title for about 3 s after the line, over the ambient bed. Free.
4. **Caption orphans:** single words like "had" and "1984." land on their own line or cue. Fix: caption chunking that never leaves a one-word cue. Free.
5. **Pace: Todd reads at about 176 words per minute** (135 words in 46 s), much faster than the 140 wpm planning figure and fast for a documentary. Fix options: ElevenLabs speed about 0.9 plus slightly longer pauses. That means regenerating the narration, about $0.22 for this test.
6. **Runtime consequence:** at the real pace, the full 1,148-word script is **about 6.5 minutes** (about 7.5 at speed 0.9), not 8. That makes the runtime decision more pressing.
7. **Factual:** no new issues from the test. The opening narration is as reviewed, with its claim mapping in [REVIEW5_TEST.md](REVIEW5_TEST.md) and [SOURCE_MAP.md](SOURCE_MAP.md).

## Next step (needs approval)

Fix issues 1-4 in code (free), then re-render the test from the cached images and narration. With the cache this re-render costs $0, or about $0.22 if the slower voice (issue 5) is approved. Full-episode production stays unapproved.
