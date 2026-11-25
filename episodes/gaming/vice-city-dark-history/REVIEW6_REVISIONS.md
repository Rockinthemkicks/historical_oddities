# Review 6: production-test revisions, pipeline guidelines and expansion proposal

Response to ChatGPT's production-test review (Nov 24, 2026). Branch `gaming-lore-pilot`, draft PR #21 (not merged).

**Status: approved changes 1-7 are built and checked offline with the real test images. The revised test video needs one paid run (narration at 0.9 speed, about $0.22; images are reused at $0). Full-episode production is not started, and no limit was raised.**

## 1. Approved changes: what was built

| # | Change | How |
|---|---|---|
| 1 | Ambient level + normalized mix | Bed raised from -26 dB to -8 dB gain (it measured -55 dB in pauses, effectively silent). Ducking under the voice is kept. The final mix is normalized in two passes (EBU R128) to **-14 LUFS integrated, true peak -1.5 dBTP**. |
| 2 | Cards over artwork + progressive reveals | Text cards now sit on a blurred, darkened version of the most recent illustration, not black. The "VICE CITY, 1984" board reveals its rows **on the narrator's words**: each row appears when its cue word ("sergeant", "drug", "agent") is spoken, using the narration's word timings. Rows now match the narration (sergeant / drug lords / agent). |
| 3 | Title hold | The title card holds **3.0 s** after "He inherited it." |
| 4 | Caption chunking | New phrase-aware chunker for gaming mode: breaks after punctuation, never leaves a one-word cue, and balances two-line captions so no line is a single word. Historical mode is unchanged. |
| 5 | Narration at 0.9 speed | `narration_speed: 0.9` in gaming mode. It's part of the narration cache key, so it regenerates once (approved, about $0.22) and is cached after that. |
| 6 | Dramatic pauses | Per-scene `pause_after`: **1.3 s** between "Tommy didn't invent the system." and "He inherited it."; the default gap between lines rises from 0.35 to 0.45 s. |
| 7 | Keep the images | No image prompt, style, reference or order changed. The button restores the paid images from the Actions cache, so the estimate shows **0 images to generate**. |

QC now records loudness (integrated, true peak, range, target) and pacing (words, speech time, words per minute) in `qc_report.json`. 116 tests pass.

## 2. Pacing comparison

| | Original test (paid run) | Revised (offline preview) |
|---|---|---|
| Narration speed | 1.0 | 0.9 |
| Speech pace | **176 wpm** (135 words in 46 s) | **about 158 wpm** (to be confirmed by the paid run) |
| Total length | 46.0 s | **about 59 s** |
| Pauses | 0.35 s between every line | 0.45 s default, 1.3 s dramatic pause, 3.0 s title hold |
| Longest static visual | about 10 s (four-row card on black) | the same sentence now changes 4 times, as each row is spoken |

The preview timings use stand-in narration at 158 wpm. The paid run will replace them with measured values in `qc_report.json` (`pacing`).

## 3. Loudness

| | Original test | Revised |
|---|---|---|
| Integrated loudness | -17.9 LUFS | target -14 LUFS (offline preview: -13.6 LUFS, TP -1.42 dBTP) |
| Ambient bed in pauses | -55 dB (inaudible) | about -32 dB expected (bed -35.6 dB before normalization, about +4 dB of gain) |

The preview's bed reading isn't meaningful: its stand-in narration is silent, so normalization lifts the bed alone. The paid run gives the real figures.

## 4. Cost ledger

| Item | Amount |
|---|---|
| Run 1 (narration only; failed at images, no OpenAI credits) | ~$0.22 (ledger budget figure) |
| Run 2 (narration + 7 images) | $0.60 (images $0.37 actual) |
| **Spent on the test so far** | **~$0.81 of the $2.00 cap** |
| Next run (narration at 0.9; images reused) | ~$0.22 estimated |
| Left after the next run | ~$0.97 |

Episode, run and overall limits are unchanged. Narration is budgeted at $0.30 per 1,000 characters, above ElevenLabs' current list prices, so the ledger overstates the real cost.

## 5. Thumbnail concepts

Made from the existing test images at no cost, with our own lettering (plain bold sans, pink tag, teal bar). No Rockstar logo, cover art, character likeness or lettering style. Files are in the chat; the tool is `draft/make_thumbnail.py`.

1. **BEFORE TOMMY**: the Corporal at the night pier with the briefcase, text on the right. Strongest hook for fans who know Tommy.
2. **VICE CITY 1984**: the Corporal at the base at dusk. Tag: "THE STORY BEFORE GTA 6". Clearest about the era.
3. **THE HIDDEN EMPIRE**: the clockwork city reframed so the empty chair sits beside the title. Strongest link to the thesis.

(The earlier "BUILT ON CRIME" with the cracked badge is kept for comparison.)

## 6. Pipeline guidelines and investigations

### Visual pacing guidelines (now the house rules)

- **Change the picture when the meaning changes, not on a timer.** One statement per scene. A new visual for each new person, place, year or claim.
- **Typical shot: 3-8 s.** Over about 8 s on one static image, add movement (push-in, `zoom_to` reframe) or a reveal. Text-only beats stay short (2-5 s) unless they reveal progressively.
- **Reuse before generating.** One paid image should normally give 2-3 shots (wide, reframe, push-in). New paid images only for new places or moments.
- **Typography for facts that need anchoring:** names, years, lists, quotes. Always over blurred artwork, never on plain black (except the end card).
- **Pauses are editorial:** 0.45 s between lines, 1-1.5 s before a turn or reveal, about 3 s for title and chapter cards.
- **Openings:** no violence in the first 15 s, and the first image within the first second.
- **Disclosure:** once, on the title card ("Illustrations are original artwork, not game footage"), plus the description. Never on every frame.

### Reusable documentary graphics

The new progressive-reveal mechanism (one card, several steps, each timed to a word) generalizes. Proposed components, all made locally at no cost:

| Component | Status | Notes |
|---|---|---|
| Name and date stamps, title cards | built | stamp / title styles |
| Lists and evidence boards with word-timed reveals | built | rows style + `reveal` |
| Timeline (points appear along a line as dates are spoken) | proposed | same reveal steps; 1984 → 1986 → 2001 |
| Relationship diagram (who worked for whom; nodes and links appear) | proposed | drawn with PIL; reveal per link |
| Original stylized map with pins | proposed | our own map art, never traced from the game map |
| Claim labels ("Confirmed in game" / "Interpretation" / "GTA VI: speculation") | proposed | a small corner tag keeps the three distinguishable on screen |

### Game-related assets

- Rockstar's policy allows use of game material in videos on a non-commercial basis. It doesn't mention YouTube monetization, and Take-Two can ask for removal (see the earlier monetization notes). Game music is a known Content ID risk.
- **Proper sourcing in practice:** footage or screenshots the owner captures from her own legal copy, logged in `assets/provenance.json`, used briefly, game audio muted. Nothing downloaded from wikis or YouTube. Wiki screenshots and maps are Rockstar's material re-hosted, not licensed to us.
- **Recommendation:** keep original artwork as the identity. If the owner buys Vice City and Vice City Stories later, short muted clips of recognisable locations could anchor fandom relevance, each clearly labelled as game footage. No action until she decides.
- **Rockstar's own press screenshots and artwork:** not assumed to be licensed for this use; would need checking first.

## 7. Proposed full-episode expansion (for editorial review, not applied)

**Goal: 10-12 minutes.** At the measured pace (about 158 wpm at speed 0.9), the current 1,148 words come to about 7.3 minutes of speech, or about 8 with pauses and holds. About **+500 words** of new material reaches roughly 10.5-11 minutes. Every proposed point below was found in this pass. Evidence is assistant-matched (fan wikis, Wikipedia, press, a fan transcript), not verified in game, and would be recorded in the dossier with statuses before any script change.

| # | Where | New material (about words) | Why it serves the thesis | Evidence found so far |
|---|---|---|---|---|
| E1 | after ch03: **"The Reluctant Empire"** | After killing Marty Jay Williams, Vic takes over his businesses and builds the Vance crime family: protection rackets, loan sharking, prostitution, drugs, smuggling, robbery (~140) | An honest complication: even the man who wanted out had to become a boss to survive. The city's economy *required* an empire. | Wikipedia: the story centres on Vic building a criminal empire with Lance. gta.wiki: Vic takes over all of Marty's businesses and builds the Vance Crime Family. Grand Theft Wiki: six business types. TV Tropes: "(reluctantly)". Rockstar's game description, as quoted by GTABase: "build an empire or be crushed" (official wording to confirm). |
| E2 | ch06: **"The Lawyer"** | Ken Rosenberg, the Forelli family's lawyer: he meets Tommy at the deal, knows Cortez, later works with Tommy, and in Tommy's words "washes the money" (~110) | Professionals serving the crime economy: the respectable layer of the system. | Wikipedia: "the Forellis' crooked lawyer". Fan wiki and fan-site character bios: Cortez is Rosenberg's acquaintance who helped set up the exchange. IMDb quotes: Tommy's line "he washes the money for us" (needs transcript or in-game check). |
| E3 | ch08: **"The Big Corrupt Bank"** | The Malibu Club heist targets "El Banco Corrupto Grande", Spanish for "the big corrupt bank" (~80) | The game's own satire: Vice City names its bank as corrupt. Tommy's crew is planned from his nightclub with his lawyer at the table. | Grand Theft Wiki (name and translation); Fandom and Grand Theft Wiki: "The Job", with Rosenberg in the planning scene. |
| E4 | ch08: **"The Apprentice"** | Avery's protégé Donald Love follows him with a notepad and writes down the gang-war tactic in "Two Bit Hit"; by GTA III he's a real-estate and media mogul (~120) | Avery's method outlives Vice City: the system passes on. It stays inside the 3D continuity. | gta.wiki / GTABase: protégé with notepad; wikigta: writes down the tactic in Two Bit Hit; Grand Theft Wiki / GTABase: Love Media owner in GTA III. |
| E5 | ch10 conclusion | Tie E1-E4 together: Vic's empire, Rosenberg's money, Avery's playbook, Tommy's throne (~60) | Makes the ending earn the "system" claim. | Draws on E1-E4. |

**Deliberately left out:**
- Love's later fate in Liberty City Stories (a grisly spoiler, and off-thesis).
- Who Love is said to be based on (a real person; it adds nothing).
- Real-world 1980s Miami history (would need its own real-world sourcing pass; possible for a later episode).
- Any GTA VI story connection.

**Labelling on screen:** E3's "satire" point and E1/E5's "the economy required an empire" are interpretations and would be narrated as such ("the game makes the point itself..."), with an "Interpretation" tag if the claim-label component is approved.

## 8. What happens next

1. **Owner:** run the button once more (Actions → Vice City 60-second test → `RUN`). It regenerates the narration at 0.9 speed (about $0.22) and reuses the images. The results zip will contain the revised video, the updated QC report with loudness and pacing, and the ledger tail.
2. **Me:** measure the real pacing and loudness, check the frames, and finish sections 2-4 with measured numbers.
3. **Editorial review:** approve or adjust the expansion outline (section 7) before any change to the full script.
