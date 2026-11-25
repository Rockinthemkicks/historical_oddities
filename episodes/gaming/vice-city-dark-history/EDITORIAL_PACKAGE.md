# Editorial package: Vice City pilot (response to editorial review 3)

> **Superseded by [DRAFT_PACKAGE.md](DRAFT_PACKAGE.md) (review 4, Nov 24).** Kept as the record of review 3.

Date: 2026-11-23. Branch `gaming-lore-pilot` (draft PR #21, not merged).
**Status: waiting for editorial approval. No script has been generated and no paid call has been made.**

Working title: **Vice City's Dark History: How a City Was Built on Crime**
Thesis: *Vice City was not corrupted by Tommy Vercetti. He inherited an existing system of corruption and criminal power.*
Target: 12-16 minutes (about 2,060 words at 140 wpm, about 14.7 min).

## Readiness (four separate levels)

| Level | State |
|---|---|
| Structural validation | **PASSED** (0 errors; 9 warnings, all open research questions) |
| Factual verification | **NOT COMPLETE**: verified 0, corroborated 5, single-family 26, unsupported 11, disputed 1 (of 43) |
| Editorial approval | **NOT GIVEN** |
| Production approval | **NOT GIVEN** |

Structural validity only means the dossier is well-formed. It does not mean the facts are checked, and the pilot is **not production-ready**.

---

## 1. Revised research dossier

Files: [`research.json`](research.json) (data) and [`research_review.md`](research_review.md) (readable version with every passage).

What changed in this pass:
- **Reframed** around the thesis. Production target is now 12-16 minutes; the new title and description are in `production.json`.
- **Official sources for C01/C02.** Rockstar's launch release (S37, Nov 19, 2026) and Take-Two's release filed with the SEC (S38, Nov 20, 2026: "$3.79 billion in day one retail sales", the company's own figure). The Newswire and Take-Two IR pages couldn't be opened from my tools, so I read the same releases through Business Wire and the SEC filing. A human should open the two original pages. C02 now also gives Sensor Tower's separate ~$1.84B estimate, so the video never presents the company figure as independent.
- **"Last Stand" confirmed** as the VCS final mission by two wikis (C38). It's a Diaz mission: Vic attacks the Mendez Building and kills Diego Mendez and Jerry Martinez on the roof. It hasn't been checked in-game.
- **I re-read the three pages I'd relied on most** (S11, S12, S29) to record actual passages. That caught six claims that went further than their source, and I corrected all six:
  - **C24:** Tommy never says "Harwood". Sonny does, calling him "the Harwood Butcher". Tommy says he was sent "to kill one man" who "knew I was coming", and Sonny deflects ("Anyone would think you blame me..."). The setup is implied, not stated.
  - **C33:** Cortez promising to find the culprit isn't on the page, so I removed it. The VCS page also hedges Cortez's role ("apparently... according to Ken Rosenberg").
  - **C13:** "Public philanthropists" isn't supported. Only the "Mendez Foundation" building name is.
  - **C14:** The VCS page doesn't say Diaz employs the Vances. Mission credits do.
  - **C21:** It's Lance, not Tommy, who learns Diaz was behind the ambush.
  - **C31:** The page gives the medicine motive, not a reason for joining the army.
- **New claims for the thesis:**
  - **C39:** Forbes, an undercover agent selling deal information.
  - **C40:** Forbes's agency is **disputed**: DEA on most wikis vs "VCPD detective" on the VCS Fandom page.
  - **C41:** Forbes's ID is used to frame Martinez.
  - **C42:** Thesis claim: the Army, a federal agent and a retired colonel are all inside the drug trade.
  - **C43:** Tommy inherits Diaz's empire.
- **C26** stays a **fan theory**. The 2D, 3D and HD continuities stay separate, and GTA VI claims stay at setting level (spoiler "none").
- **Fixed URLs:** S10 now points to Wikipedia's Vice City Stories article and S32 to Wikipedia's Vice City article. Neither has been opened yet.

New in the code (`modules/gaming/research.py`, 3 new tests, 106 passing):
- **Per-claim evidence records:** source, status, passage and date.
- **Evidence ladder:** discovered → accessed → matched → primary_checked → human_verified (plus disputed).
- **Source families:** game / official / press / encyclopedia / fan_wiki / community. Three fan wikis repeating each other count as **one** family, never as independent corroboration.
- **A standing for each claim:** verified / corroborated / matched / unsupported / disputed.
- **An escalation list.**
- **The four readiness levels** shown above.

## 2. Claim-by-claim verification report

Standing:
- **verified:** checked in the game, or by a human. None yet.
- **corroborated:** passages matched in two or more independent families, or in an official source.
- **matched:** passages from a single family only.
- **unsupported:** found, but no passage matched yet.
- **disputed:** some evidence contradicts it.

Note: "corroborated" for story claims still means fan wikis plus TV Tropes or press, not the game itself.

| Claim | Type | Continuity | Standing | Chapter | Matched evidence | Next step |
|---|---|---|---|---|---|---|
| C01 | real world fact | real world | **corroborated** | ch01 | S37 (official, matched) | OK |
| C02 | real world fact | real world | **corroborated** | unused | S38 (official, matched); S47 (press, matched) | OK |
| C03 | real world fact | real world | **unsupported** | ch02 | none matched (S23 discovered) | Open S23 or another source for the 1997 game. |
| C04 | real world fact | real world | **unsupported** | ch02 | none matched (S09 discovered) | Open S09. |
| C05 | confirmed canon | HD | **unsupported** | ch01 | none matched (S07 discovered, S08 discovered, S23 discovered) | Open rockstargames.com/VI. |
| C06 | confirmed canon | HD | **unsupported** | ch01 | none matched (S07 discovered) | Open rockstargames.com/VI for the exact wording. |
| C07 | confirmed canon | HD | **unsupported** | unused | none matched (S07 discovered) | Open rockstargames.com/VI. |
| C08 | confirmed canon | 3D | **matched** | ch02 | S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C09 | interpretation | 3D | **matched** | ch02 | S11 (fan_wiki, matched) | Confirm in-game before final script. |
| C10 | confirmed canon | 3D | **matched** | ch03 | S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C11 | confirmed canon | 3D | **matched** | ch03 | S12 (fan_wiki, matched); S43 (fan_wiki, matched) | Confirm in-game before final script. |
| C12 | confirmed canon | 3D | **matched** | ch03 | S12 (fan_wiki, matched); S28 (fan_wiki, matched) | Confirm in-game before final script. |
| C13 | confirmed canon | 3D | **matched** | ch05 | S46 (fan_wiki, matched) | Confirm in-game before final script. |
| C14 | confirmed canon | 3D | **matched** | ch05 | S40 (fan_wiki, matched); S39 (fan_wiki, matched) | Confirm in-game before final script. |
| C15 | confirmed canon | 3D | **matched** | ch05 | S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C16 | confirmed canon | 3D | **matched** | ch05 | S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C17 | confirmed canon | 3D | **unsupported** | ch07 | none matched (S01 discovered, S24 discovered) | Needs any source for 1984-86. Otherwise rephrase as "by 1986 Diaz is the top drug baron" from S01. |
| C18 | confirmed canon | 3D | **matched** | ch08 | S29 (fan_wiki, matched) | Confirm in-game before final script. |
| C19 | confirmed canon | 3D | **matched** | ch01 | S11 (fan_wiki, matched) | Confirm in-game before final script. |
| C20 | confirmed canon | 3D | **matched** | ch01 | S11 (fan_wiki, matched); S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C21 | confirmed canon | 3D | **matched** | ch07 | S11 (fan_wiki, matched) | Confirm in-game before final script. |
| C22 | confirmed canon | 3D | **matched** | ch07 | S11 (fan_wiki, matched) | Confirm in-game before final script. |
| C23 | confirmed canon | 3D | **matched** | ch08 | S11 (fan_wiki, matched); S29 (fan_wiki, matched) | Confirm in-game before final script. |
| C24 | confirmed canon | 3D | **matched** / risk high | ch08 | S29 (fan_wiki, matched) | Watch the finale cutscene (S03). Narrate as implied, not stated. |
| C25 | interpretation | 3D | **matched** | ch08 | S11 (fan_wiki, matched); S29 (fan_wiki, matched) | Confirm in-game before final script. |
| C26 | fan theory | 3D | **unsupported** | ch08 | none matched (S19 discovered, S20 discovered) | Open S19/S20 to confirm the theory exists as described. Always labelled fan theory. |
| C27 | confirmed canon | 3D | **unsupported** | ch09 | none matched (S06 discovered, S16 discovered) | Open S16 or check in San Andreas. |
| C28 | confirmed canon | 3D | **unsupported** | ch09 | none matched (S06 discovered, S17 accessed) | Re-open S17 and record the passage. |
| C29 | confirmed canon | 3D | **unsupported** | unused | none matched (S06 discovered, S17 accessed) | Re-open S17; check SA "The Introduction". |
| C30 | speculation | HD | **unsupported** | ch09 | n/a (speculation) | Speculation; keep hedged. |
| C31 | confirmed canon | 3D | **matched** | ch03 | S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C32 | confirmed canon | 3D | **matched** / risk high | ch06 | S12 (fan_wiki, matched) | Watch the VCS ending (S05). Until then: "the game suggests". |
| C33 | confirmed canon | 3D | **matched** | ch06 | S11 (fan_wiki, matched); S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C34 | confirmed canon | 3D | **corroborated** / risk high | ch06 | S11, S51, S52 (fan_wiki, matched); S53 (community, matched) | 'Treacherous Swine': Gonzalez is named as the leak. Diaz as the recipient is implied only; say so. |
| C35 | confirmed canon | 3D | **matched** | ch07 | S11, S48, S49 (fan_wiki, matched) | 'Two Bit Hit'. Watch the briefing cutscene. |
| C36 | interpretation | 3D | **matched** / risk high | ch07 | S48, S50 (fan_wiki, matched) | Avery's briefing states the motive (a gang war lowers property prices). 'Built on violence' is our reading; label it as such. |
| C37 | interpretation | 3D | **matched** | ch08 | S11 (fan_wiki, matched); S29 (fan_wiki, matched) | Confirm in-game before final script. |
| C38 | confirmed canon | 3D | **matched** | ch05 | S39 (fan_wiki, matched); S40 (fan_wiki, matched); S12 (fan_wiki, matched) | Confirm in-game before final script. |
| C39 | confirmed canon | 3D | **corroborated** / risk high | ch04 | S41 (fan_wiki, matched); S42 (fan_wiki, matched); S26 (community, matched) | Confirm in-game before final script. |
| C40 | confirmed canon | 3D | **disputed** | ch04 | S41 (fan_wiki, matched); S42 (fan_wiki, matched); S12 (fan_wiki, disputed) | Find the in-game line. Fallback wording: "undercover agent". |
| C41 | confirmed canon | 3D | **matched** | ch04 | S41 (fan_wiki, matched); S42 (fan_wiki, matched); S43 (fan_wiki, matched) | Confirm in-game before final script. |
| C42 | interpretation | 3D | **corroborated** / risk high | ch09 | S12 (fan_wiki, matched); S41 (fan_wiki, matched); S11 (fan_wiki, matched); S26 (community, matched) | Thesis claim: stands only if C11, C39 and C33 hold up in-game; TV Tropes is weak corroboration. |
| C43 | interpretation | 3D | **matched** | ch07 | S11 (fan_wiki, matched) | Confirm in-game before final script. |

**Priority claims from the review:**
- **C24 (finale/Harwood):** matched to a fan transcript only. It's dialogue, and the setup is *implied*. Needs the cutscene.
- **C32 (Lance pulls Vic back in):** matched on one fan wiki only, which doesn't date the deal or say Vic left town. Needs the VCS ending.
- **C34 (Gonzalez):** updated Nov 24. In "Treacherous Swine", Cortez names Gonzalez as the man who leaked the deal. That Diaz received the leak is only implied (Vice City Stories shows Diaz blackmailing Gonzalez in 1984), so the script must say "implied".
- **C36 (property boom built on violence):** updated Nov 24. Avery's own briefing in "Two Bit Hit" gives the motive: start a Cuban-Haitian gang war at a funeral to drive property prices down. The motive is explicit dialogue; "the boom was built on violence" is our interpretation and is labelled that way.

## 3. Questions for the owner

1. **Human check (no game needed).** You can't capture gameplay, so the pilot is illustration-only. Would you watch these cutscenes in any published playthrough on YouTube and note the timestamps? Viewing only; nothing is downloaded. About 15 minutes in total:
   - VC "Keep Your Friends Close..." (C24)
   - The VCS ending, "Last Stand" (C32, C38)
   - VC "Treacherous Swine" (C34)
   - VC "Two Bit Hit" (C35, C36)
   - A Forbes mission, to settle his agency (C40)

   If you'd rather not, these claims stay at "transcript-matched" and the script hedges them.
2. **Footage.** Decided: none. The owner doesn't have the games, so the pilot is illustration-only (also the lowest monetization risk).
3. **Thesis and outline.** Do you approve the thesis, the 12-16 minute target and the chapter outline below?
4. **Title.** Which title and thumbnail concept (section 5)?
5. **Thumbnail.** Which concept from section 5?
6. **Forbes.** If his agency can't be confirmed, is "an undercover agent" acceptable wording?
7. **1986 corruption.** Do you want another research pass on 1986 corruption (VCPD, politicians, Tommy's fronts)? Or keep the thesis built on 1984 plus Cortez and Avery?
8. **Budget.** Do you approve an episode spending limit of $15 for the pilot (section 7)?

## 4. Proposed chapter outline (12-16 min)

File: [`outline_proposed.json`](outline_proposed.json) passes the outline checks (9 chapters, 2,060 words, inside the 1,560-2,400 budget). It's deliberately **not** named `outline.json`, so the pipeline can't use it until it's approved.

| # | Chapter | ~Words | ~Min | Role in the argument | Depends on unverified claims |
|---|---|---|---|---|---|
| 1 | A City That Was Already Waiting | 200 | 1.4 | Hook; calm first 15 s; GTA VI at setting level | C05, C06 (official page) |
| 2 | Boomtown, 1984 | 180 | 1.3 | The city and its drug-money boom | C03, C04 |
| 3 | The Sergeant | 260 | 1.9 | The Army is inside the drug trade | - |
| 4 | The Agent | 220 | 1.6 | Law enforcement is inside it too | C40 (disputed agency) |
| 5 | The Cartel's Tower | 280 | 2.0 | The cartel's respectable front; the Mendez war; "Last Stand" | C13 (philanthropy dropped) |
| 6 | The Exchange | 220 | 1.6 | 1984 to 1986; the colonel's deal | C32, C34 |
| 7 | The Heir | 300 | 2.1 | Tommy inherits Diaz's empire and a developer's war | C17, C35, C36 |
| 8 | This Is Business | 240 | 1.7 | The finale: what's said vs implied; fan theory labelled | C24, C26 |
| 9 | The System Outlives Its Kings | 160 | 1.1 | Thesis restated; GTA VI as an open question | C27, C28 |

## 5. Three title and thumbnail concepts

None of these uses Rockstar logos, logo-style lettering, cover art, character likenesses, game screenshots or graphic violence. All imagery is original illustration in `config/style_gaming_doc.txt`. "Vice City" and "GTA" appear only as plain words in titles, to say what the video is about.

1. **"Vice City's Dark History: How a City Was Built on Crime"** (working title)
   - **Thumbnail:** a neon coastal skyline at dusk in graphic-novel style, with a cracked badge in the foreground under palm-frond shadows.
   - **Text:** "BUILT ON CRIME"
2. **"Vice City Was Corrupt Before Tommy Ever Arrived"**
   - **Thumbnail:** an empty high-backed chair at the head of a mansion table, light through blinds, an open ledger and a set of keys left on the table.
   - **Text:** "HE INHERITED IT"
   - **Note:** the most thesis-forward option; the "Tommy" name is good for search.
3. **"The Soldier, the Agent and the Cartel: Who Really Ran 1980s Vice City?"**
   - **Thumbnail:** an evidence board with three silhouettes (army cap, sunglasses with an ID badge, a suit), joined by red string over a pastel skyline.
   - **Text:** "WHO RAN IT?"

## 6. Preliminary visual asset and rights plan

About 74 visual beats at ~12 s each.

| Asset type | ~Count | Source | Rights | Cost |
|---|---|---|---|---|
| Cinematic illustrations | ~44 | gpt-image-2, house style | Generated by us; prompts are IP-linted (no protected names or logos; characters described as archetypes, e.g. "a sergeant in fatigues") | Paid (section 7) |
| Chapter cards | 9 | Rendered locally | Ours | Free |
| Timelines (1984 → 1986, plus continuity explainer 2D/3D/HD) | ~6 | Rendered locally from dossier dates | Ours | Free |
| Relationship diagrams (who worked for whom; Forbes and Martinez's ID) | ~6 | Rendered locally | Ours | Free |
| Stylised maps (Fort Baxter, downtown, Starfish Island) | ~5 | Original drawing, not traced from game maps | Ours | Free or cheap |
| Evidence boards and on-screen sources | ~4 | Rendered locally; sources cited on screen | Ours | Free |
| Gameplay clips | **0 (decided Nov 24)** | **Only** footage you capture, logged in `assets/provenance.json` | Rockstar policy: non-commercial, removable at any time; ad revenue is at risk | Free |
| Music | bed only | Licensed library or owner-supplied, logged | No game music or radio (Content ID claims) | Free or licence |

**Rules carried into production:**
- Nothing is downloaded.
- The publication gate blocks any asset without provenance.
- No graphic violence in the first 15 s.
- Violence is shown by implication.
- Sources are listed in the description (`sources.json`).

## 7. Estimated pilot cost

All figures use the prices in `modules/costs.py` and are rough. No paid call has been made.

| Item | Basis | Estimate |
|---|---|---|
| Script (GPT-5.4) | Outline plus 9 chapters, ~255k input / ~39k output tokens, plus one revision round | $1.25-2.50 |
| Narration (ElevenLabs, "Todd") | ~2,060 words ≈ 12.4k chars × $0.30/1k, plus 30% retakes | $3.70-4.85 |
| Images (gpt-image-2 medium, 1536×1024, reference image) | 44 × $0.056; a 6-image test batch first ($0.34); up to 50% rerolls | $2.45-3.70 |
| Rendering, QC, diagrams, packaging | Local | $0 |
| **Total** | | **≈ $7.50-11** |

**Proposed limits:**
- $15 episode limit.
- $5 per run.
- The overall limit stays where you set it.
- Limits are never raised automatically.

The pipeline makes a free `--estimate-only` check before every paid stage.

---

**Stopping here for editorial approval.** Nothing in this package starts script generation or paid production. The next step depends on your answers to section 3, especially the in-game checks for C24, C32, C34 and C36.
