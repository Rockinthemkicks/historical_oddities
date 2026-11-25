# Review 9: production readiness ("The Dark History of Vice City Before GTA 6")

Response to the Review 8 conditional final production approval (2026-11-25). Nothing paid has run
since Review 8. Spend to date: **$1.03** (the 60-second test).

## 1. What the owner does next (two buttons, both on the phone)

1. **Speed comparison:** Actions → "Vice City 60-second test" → Run workflow → type `RUN`.
   One run renders the test at **0.9** (narration already paid, $0) and at **0.8** (new narration,
   about $0.24, inside the $0.95 left in the test budget). The run page lists runtime, words per
   minute and loudness for both. The download (`vice-city-60s-test-results`) has
   `compare/test_speed_0.9.mp4` and `compare/test_speed_0.8.mp4`.
2. **Full episode:** Actions → "Produce full episode" → pick the speed → type `RUN`.
   Estimated **$4.27**. The download (`vice-city-full-episode`) has the video, captions, thumbnails,
   the draft YouTube package and the QC report.

Nothing is published, merged or started beyond that.

## 2. Safeguards (tested offline: 131 tests pass, 13 of them new)

| Safeguard | How |
|---|---|
| Explicit approval | Nothing runs unless `RUN` is typed. The speed must be picked; the "choose" placeholder stops the run. |
| $15 pilot ceiling, including tests, retries and failures | `pilot_budget.py` subtracts everything the test spent ($1.03 before the ledger was carried, plus the test ledger). Pending calls count at their estimate. The pipeline then enforces the rest as the episode cap. |
| Fails closed | If the overall ledger wasn't restored, or this episode's ledger is missing spending the overall ledger shows, the run stops before any paid call. |
| Per-run cap | $8. The pipeline's overall $250 limit still applies. |
| Defaults unchanged | The $15 lives only in this workflow and this episode's script. Pipeline defaults stay $5 per run and $10 per episode. |
| Shared ledgers | Both buttons use the same ledger cache (same paths and key), so test spend always counts. |
| Stage approvals | Research, outline and script approvals are committed and pinned to file hashes. If any of those files changes, `produce` refuses. Typing `RUN` approves the storyboard and budget for that run. |
| Caching | Paid images and narration are kept between runs. A re-run after a failure doesn't pay twice. |
| Reuse of the test's media | `seed` copies the test's reference sheet, the five approved illustrations and the thumbnail background, but only where the inputs are identical (matched by input hash). Simulated: 7 reused, 32 new. |

## 3. Editorial

**The script is unchanged except for one factual correction.** The approved finale said Sonny's
"those fifteen years were mine to spend" was his answer to Tommy's "they knew I was coming". Two
mission transcripts (GTA Wiki and Grand Theft Wiki) give a different order:

1. Tommy: "they knew I was coming"; Sonny tells him to watch his tone.
2. Lance's betrayal ("this is Vice City. This is business.").
3. Lance is killed.
4. Tommy: "You took fifteen years from me".
5. Sonny: "Those fifteen years were mine to spend!"

My Review 8 evidence note had joined two lines that are far apart in the scene. The finale now
follows the real order and keeps the beat, still marked as interpretation:

> Tommy kills Lance. Then, face to face, he tells Sonny those fifteen years were taken from him.
> Sonny's answer: they were his to spend. / It lands as a confession. / Then Tommy kills him too.

Net change: 83 → 85 lines, 1,459 → 1,472 words.

**Spot-check against dialogue transcripts.** These are not checked in the game itself; nobody here
has the game.

| Claim | Line in the video | Matched in |
|---|---|---|
| C24 | finale exchange (order corrected) | GTA Wiki transcript, Grand Theft Wiki script, IMDb quotes, Sportskeeda |
| C18 | "the Harwood Butcher" | Grand Theft Wiki script, GTA Wiki transcript |
| C23 | "this is business" | GTA Wiki transcript, Grand Theft Wiki script |
| C63 | "twenty-four carat gold" | Grand Theft Wiki intro script, GTA Wiki walkthrough, TV Tropes |
| C36 | Avery's gang-war line | GTA Wiki transcript, Grand Theft Wiki walkthrough, Giant Bomb |
| C57 | "he washes the money for us" | GTA Wiki transcript, IMDb quotes |
| C65 | "No! No, No, I am not interested, got it?" | Grand Theft Wiki mission page |

The strongest remaining check is human: the owner (or anyone) watching these seven cutscenes in a
YouTube playthrough. That would move them to `human_verified`.

**Facts vs interpretation:** unchanged. C36, C61, C62 and C64 and the thesis are stated as reading.
SOURCES.md labels every interpretation.

**GTA VI continuity:** the description now opens with: "Continuity note: these games belong to the
older 3D-era continuity. GTA VI is set in a separate continuity, so nothing here is presented as GTA
VI's backstory or canon." Chapter 2 already says this on screen.

The title is kept as approved. "Before GTA 6" can be read as in-universe history, though the
description and Chapter 2 correct that. A safer option, if wanted: *"The Dark History of the
Original Vice City (Before GTA 6)"*.

## 4. Visuals and branding

- **Chapter 9 ("The Business of Vice"),** narration unchanged:
  - The run of push-ins is replaced by an **"Avery's Jobs" evidence board** that adds one mission
    per line.
  - Avery's plan reveals step by step on the line about it.
  - A **then-and-now card** covers Donald Love.
  - **The bank's name is set as typography.** The old shot zoomed into a blank sign.
  - A closing **"The System, 1986" board** reveals each row as the narrator names it.
- **Whole episode:**
  - Repeated push-ins are down from 26 to 15; pans are up from 7 to 16.
  - New **dip-to-black transitions** into each chapter card, plus a 1.5-second fade at the end.
  - 37 illustrations, 23 typography cards, 9 chapter cards, 44 reframed reuses.
- **Character consistency:** the Corporal reference sheet from the test is reused, so every new
  image is generated against the same sheet.
- **Fixes found while checking:**
  - Long stamp quotes ("HE WASHES THE MONEY FOR US.") ran off the frame; they now shrink to fit.
  - Reusing a revealed card would have crashed the render.
- **Thumbnails:**
  - Built on Crime is the primary.
  - Options: Built on Crime (face-off background), Before Tommy, The Hidden Empire.
- **Brand:** current palette retained. The logo and tagline will be used once supplied.

## 5. Deliverables the full run produces

- **Video:** `documentary.mp4`, 1920x1080, 16:9.
- **Captions:**
  - burned in;
  - `captions.srt` for upload. Uploading the SRT shows a second caption track if a viewer turns
    CC on; YouTube's own auto-captions would too.
- **Thumbnails:** `thumbnails/` (4 options).
- **Draft YouTube package:** `publish_draft/`
  - `description.txt`, about 4,600 characters (YouTube's limit is 5,000), with the chapters and
    key sources;
  - `chapters.txt`, `sources.json`, `monetization_checklist.md`, `cost.json`.
  - The full claim-by-claim list (91 sources) is too long for the description. It lives in
    `SOURCES.md` and the description links to it. Before publishing, swap that link for a
    permanent one.
- **QC:** `qc_report.json` with QC checks, loudness and pacing.
- **Cost:** actual cost is in the run summary and `cost.json`.
- **End card:** now reads "Sources for every claim are linked in the description."

## 6. Runtime

| Speed | Speech | With pauses |
|---|---|---|
| 0.9 | 8.2 min | about 9.0 min |
| 0.8 | 9.3 min | about 10.0 min |

These use the measured 179 wpm at 0.9; the comparison run measures both. Nothing is padded to
reach ten minutes.

## 7. Risk assessment (not legal advice)

**Copyright: low.**
- No game footage, music, radio, art or logos.
- Illustrations are original and generated from prompts that never name protected characters or
  brands (storyboard check passes).
- The ambient score is synthesized here.
- On-screen quotes are a few words of dialogue used for commentary.
- Residual risk: an AI image that happens to resemble a game character. The owner should glance
  at the 32 new images before publishing.

**Trademark: low.** Game names are used to identify the subject. The thumbnail uses no Rockstar
logo or lettering style. The description says "Not affiliated with or endorsed by".

**Disclosure: covered.**
- The description states the AI voice and AI-generated illustrations.
- YouTube's "altered or synthetic content" label targets realistic content that could mislead.
  These illustrations are stylized and the voice imitates no real person, so it is likely not
  required.
- Ticking it costs nothing if in doubt. Re-check the policy at upload (checklist dated 2026-11-23).

**Monetization: moderate.**
1. **Inauthentic/mass-produced content (YPP):**
   - Risk: AI voice plus AI images.
   - Mitigation: original research, sourced claims, human editorial review, and a channel
     description saying how videos are made.
2. **Advertiser-friendly guidelines:** drug trade, murder and a congressman's blackmail are
   discussed non-graphically in a documentary context. Expect possible "limited ads"; the first
   seconds and the thumbnail are non-graphic.
3. **Spoilers:** full spoilers for 2002/2006 games are flagged in the description. There are no
   GTA VI story spoilers.

## 8. Cost

| Item | Amount |
|---|---|
| Spent so far | $1.03 |
| Speed comparison | about $0.24 |
| Full episode | about $4.27 (less if the test's opening narration is reused at the chosen speed) |
| Projected total | **about $5.55** of the $15 ceiling |
