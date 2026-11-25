> **Superseded by [REVIEW5_TEST.md](REVIEW5_TEST.md) (review 5, Nov 24).** Kept as the record of review 4; its narration is out of date.

# Draft package: The Dark History of Vice City Before GTA 6

Response to editorial review 4 (Nov 24, 2026). Branch `gaming-lore-pilot`, draft PR #21 (not merged).

**Status: DRAFT for script and visual-direction approval.** I wrote the narration in this session from the dossier, so no paid API call was made. Final narration, full image generation and rendering are not approved. The draft's evidence is matched by the assistant (fan transcripts, wikis, official pages). None of it is human-verified or primary-checked.

| Level | State |
|---|---|
| Structural validation | PASSED (0 errors) |
| Factual verification | NOT COMPLETE: verified 0, corroborated 11, single-family 31, unsupported 6, disputed 1 of 49. The draft uses no unsupported or disputed claim. |
| Editorial approval | Concept approved (review 4). Script and visual direction: NOT YET |
| Production approval | NOT GIVEN. Proposed $15 pilot ceiling needs the owner's explicit OK |

Files: [`draft/draft_chapters.json`](draft/draft_chapters.json) (segments with claim ids and visuals), [`draft/draft_checks.json`](draft/draft_checks.json) (automatic checks), [`outline_proposed.json`](outline_proposed.json), [`draft/test_prompts.json`](draft/test_prompts.json), [`SOURCE_MAP.md`](SOURCE_MAP.md). Rebuild everything with `python3 episodes/gaming/vice-city-dark-history/draft/build_draft.py` then `build_docs.py`.

## 1. Revised chapter outline

10 chapters, 1927 words, about 13.8 minutes at 140 wpm. The outline check passes. The last column lists every claim the chapter uses that is **not verified**, so single-family matches stay visible. Nothing is listed under 'omit': unsupported and disputed claims were cut, not hedged.

| # | Chapter | Words | ~Min | Purpose | Claims not yet verified (standing) |
|---|---|---|---|---|---|
| 01 | The Man at the Docks | 166 | 1.2 | Hook: the dealer who wanted out; thesis. | C16 (matc), C18 (matc), C19 (matc), C20 (matc), C32 (matc), C42 (corr), C43 (matc), C46 (matc), C47 (matc), C48 (matc) |
| 02 | Before GTA 6, Another Vice City | 195 | 1.4 | Continuity: this is the 3D-era city, not GTA VI's backstory. | C01 (corr), C02 (corr), C03 (corr), C04 (corr), C05 (corr), C06 (corr), C07 (corr), C08 (matc) |
| 03 | The Sergeant | 196 | 1.4 | Institution 1: an Army sergeant inside the cartel trade. | C10 (matc), C11 (matc), C12 (matc), C13 (matc), C31 (matc), C47 (matc), C48 (matc) |
| 04 | The Agent | 173 | 1.2 | Institution 2: an undercover agent selling information. | C39 (corr), C41 (matc), C42 (corr) |
| 05 | The Cartel's Tower | 245 | 1.8 | The Mendez war, Diaz's maneuvering, and 'Last Stand'. | C13 (matc), C14 (matc), C15 (matc), C16 (matc), C32 (matc), C38 (matc), C49 (matc) |
| 06 | The Exchange | 179 | 1.3 | 1986: the colonel, the leak, the ambush. | C11 (matc), C19 (matc), C20 (matc), C32 (matc), C33 (matc), C34 (corr), C49 (matc) |
| 07 | The Heir | 156 | 1.1 | Tommy inherits Diaz's empire. | C21 (matc), C22 (matc), C25 (matc), C43 (matc), C48 (matc) |
| 08 | The Business of Vice | 327 | 2.3 | Economic corruption: Avery, the Print Works, Congressman Shrub. | C35 (matc), C36 (matc), C44 (corr), C45 (matc), C46 (matc) |
| 09 | This Is Business | 162 | 1.2 | The finale: what is said vs implied. | C18 (matc), C23 (matc), C24 (matc), C25 (matc), C37 (matc) |
| 10 | Built on Crime | 128 | 0.9 | Conclusion: Vic and Tommy, the thesis restated. | C05 (corr), C20 (matc), C32 (matc), C33 (matc), C42 (corr), C43 (matc), C46 (matc), C47 (matc), C48 (matc) |

Key changes from review 3:
- **New opening:** the first 30 seconds now run through Vic, the dealer at the docks who had tried to get out, and lead into the thesis. The first 15 seconds are calm: no violence on screen or in narration.
- **3D continuity:** chapter 2 separates the 1997 top-down city, the 3D-era city and GTA VI's Vice City, and says plainly that this video is not GTA VI's backstory. GTA VI appears only at setting level (official site).
- **Vic vs Tommy:** the emotional contrast (escape vs control) runs through chapters 1, 3, 5 and 10. It rests on C47 (Vic says he wants out), C32 and C48.
- **Economic corruption expanded:** chapter 8 is now the longest. It covers Avery's three missions, the Print Works, and Congressman Shrub kept in line with photographs, all from the final research pass.
- **Cut:** the Sonny fan theory (C26), Forbes's agency (C40, disputed), Diaz's 1984-86 rise (C17, unsupported), the GTA VI carry-over speculation (C30) and the aftermath claims (C27-C29).
- **Narrowed:** C42 now describes individuals, not institutions (chapter 4 says so on air); C32 no longer claims Lance pulled Vic back in; C24 sticks to the dialogue.

## 2. Draft narration

Claim ids in brackets are for review only and aren't read aloud. Lines that open with 'Our reading', 'Our inference' or 'Our interpretation' are labelled analysis.

### 01. The Man at the Docks  (166 words)

Vice City, 1986. A boat cuts across a bay lined with pastel hotels and new money. On board is a man just out of fifteen years in prison, sent south by his old crime family to oversee a drug deal. <sub>[C18, C19]</sub>

Waiting at the exchange is a dealer named Victor Vance. Two years earlier, Vic had tried to walk away from all of it. He told his brother he wanted to stay away from drugs. After a war that cost him nearly everything, the brothers decided to leave town and lay low. <sub>[C47, C16, C32]</sub>

Now he's back at a deal table, and the deal is ambushed. Vic and two of the newcomer's men are killed. The money and the cocaine are gone. Vic's brother Lance escapes. <sub>[C20]</sub>

The newcomer is Tommy Vercetti, and the usual story says Vice City's crime begins with him. It doesn't. An Army sergeant, an undercover agent, a cartel and a property developer were already running the machine. Tommy walked into it, and took it over. <sub>[C48, C42, C46, C43]</sub>

### 02. Before GTA 6, Another Vice City  (195 words)

First, which Vice City is this? Grand Theft Auto VI came out on November 19, 2026. It's set in the state of Leonida, and Rockstar describes its Vice City as the darkest side of the sunniest place in America. <sub>[C01, C05, C06]</sub>

That launch was enormous. Take-Two says the game made 3.79 billion dollars in day-one retail sales, its own figure, while the analytics firm Sensor Tower estimated about 1.84 billion by release day. Either way, millions of people are now walking Vice City's streets. <sub>[C02]</sub>

This video is not about that city's backstory. The name goes back to the first Grand Theft Auto in 1997, a top-down game in its own separate continuity, where Vice City was one of three cities and a stand-in for Miami. <sub>[C03, C04]</sub>

Our story belongs to the 3D era: Vice City Stories, set in 1984, and Vice City, set two years later in 1986. Different games, different continuities, the same name on the map. We'll keep them apart. <sub>[C08, C03]</sub>

GTA VI has its own Vice City and its own leads, Jason and Lucia. Nothing in this video is that game's official history, and none of it spoils that story. <sub>[C07, C05]</sub>

### 03. The Sergeant  (196 words)

In 1984, Victor Vance is an Army corporal at Fort Baxter, the base on the edge of the city. He needs money for his brother Pete's asthma medication, and that need is the lever his sergeant pulls. <sub>[C10, C31]</sub>

Sergeant Jerry Martinez runs a secret drug business and uses Vic to do his jobs. When Vic stops being useful, Martinez sets him up. Drugs are found, there's a sex worker in Vic's car, and Vic is thrown out of the Army with a dishonorable discharge. <sub>[C11]</sub>

Here is the detail that matters. After Vic and Lance take a shipment of cocaine from Martinez, they find out whose it really was. It belonged to the Mendez brothers, the most powerful drug family in the city. Martinez wasn't a lone dealer in uniform. An Army sergeant was working as a courier for a cartel. <sub>[C12, C13]</sub>

And Vic? Again and again he says he wants out of the drug game but has no choice. When Lance offers him twenty kilos of cocaine to get started, he turns it down. Hold on to that. This is the story of a man who wanted out of the system, and another who wanted to own it. <sub>[C47, C48]</sub>

### 04. The Agent  (173 words)

Vic's next contact is Bryan Forbes, an undercover agent who sells the Vance brothers information about drug deals. The sources we could check disagree about which agency he works for, so we won't name one. <sub>[C39]</sub>

His ID becomes a weapon. In a mission called The Mugshot Longshot, Lance pastes the sergeant's photo onto Forbes's ID, to convince the Mendez brothers that Martinez himself is working for the law. <sub>[C41]</sub>

Think about what that trick depends on. It only works in a city where everyone assumes the law is just another buyer at the table. In our reading, the badge isn't a threat to the drug trade here. It's a currency inside it. <sub>[C41, C42]</sub>

By 1984, then, a sergeant is moving cartel cocaine and an undercover agent is selling information to dealers. That doesn't prove the whole Army or the whole police force was corrupt, and the games never claim it. What they show is narrower and maybe more unsettling: the individuals trusted to stand between the city and its drug trade were already inside it. <sub>[C42]</sub>

### 05. The Cartel's Tower  (245 words)

The Mendez brothers, Armando and Diego, rule the 1984 drug trade from a downtown tower known as the Mendez Foundation building. A foundation's name on a cartel headquarters is a small detail. Our reading: it fits a city where crime liked to look respectable. <sub>[C13]</sub>

They use the Vance brothers for a few jobs, then betray them, and Vic goes to war. It costs him dearly. Louise, one of the people closest to him, dies after the Mendez brothers kidnap her, and Armando is killed at the Mendez mansion. <sub>[C15, C16]</sub>

Vic's last ally is a rival drug baron, Ricardo Diaz, who gives him work against the Mendez operation. Diaz is already maneuvering. That same year he blackmails Gonzalez, the right-hand man of a retired colonel named Cortez, for information on the colonel's drug shipments, as part of his plan to become the city's drug baron. <sub>[C14, C49]</sub>

The final mission, Last Stand, is a job for Diaz. Vic attacks the Mendez building from the air and kills Diego Mendez and Sergeant Martinez on the roof. Then he and Lance decide to leave town and lay low. Vic had escaped. For now. <sub>[C38, C32]</sub>

Step back and look at who gave the order. Vic did the fighting, but Last Stand was Diaz's job, aimed at Diaz's biggest rivals. Our inference is that Diaz is the one who stands to gain most from that rooftop. The games don't show how he spends the next two years, so we won't fill that gap. <sub>[C14, C38]</sub>

### 06. The Exchange  (179 words)

Two years later, Vic is back at a deal table, and the games never show how he got back in. According to Tommy's lawyer, Ken Rosenberg, the retired colonel Juan Garcia Cortez helped set the exchange up. Two years after a sergeant ran cocaine through Fort Baxter, a retired colonel is helping arrange a cocaine deal. Military rank, again, sitting inside the trade. <sub>[C32, C33, C11]</sub>

Sonny Forelli sent Tommy to profit from the city's growing drug trade. We've seen how that ended: an ambush, two dead Forelli men, a dead dealer, and the money gone. <sub>[C19, C20]</sub>

Cortez later tells Tommy who talked: his own right-hand man, Gonzalez, gave away information about the deal. Tommy kills him in a mission called Treacherous Swine. Notice the shape of that betrayal. The leak didn't come from the street. It came from inside a colonel's own circle. <sub>[C34, C33]</sub>

Who received that information, the game never says outright. It's implied to be Diaz, and the 1984 blackmail suggests the line ran through Gonzalez long before Tommy arrived. That connection is our inference, not something the games state. <sub>[C34, C49]</sub>

### 07. The Heir  (156 words)

Tommy goes to work for Diaz. It's Lance, working alongside him, who learns that Diaz's gang carried out the ambush. The two of them storm Diaz's mansion on Starfish Island, kill him, and Tommy moves in and takes over the operation. <sub>[C21, C22]</sub>

This is usually told as Tommy's rise, and he does rise, to become the city's major criminal power. But look at what he actually acquires: a mansion, a drug empire and a set of relationships that Diaz had already built. <sub>[C48, C43]</sub>

From the mansion, Tommy spreads into businesses across the city. Lance stays at his side, but the story shows Lance starting to feel underappreciated, pushed to the edge of a rise he helped start. That resentment will matter at the end. <sub>[C22, C25]</sub>

Our interpretation: Tommy didn't corrupt Vice City. He inherited its corruption, sat down at its center, and ran it harder. And the most revealing part of that system wasn't the drug trade at all. <sub>[C43]</sub>

### 08. The Business of Vice  (327 words)

It was property. Avery Carrington is a Texan real-estate developer, and his missions are optional side stories you can skip. They're also the clearest picture of how business works in this city. <sub>[C46]</sub>

In the first, a rival developer won't sell Avery some land, so Avery sends Tommy to persuade him at a golf course. The developer ends up dead. In the second, a competing construction site down the street is in Avery's way, so Tommy blows it up, and they talk about it as saving the rejuvenation of the area. <sub>[C46]</sub>

In the third, Avery spells out his strategy. A gang war, he says, brings property prices down. Tommy dresses as a member of one gang and attacks a funeral held by another, so the two go to war. <sub>[C35, C36]</sub>

The motive comes from Avery's own mouth. What we take from it is our interpretation: in Avery's Vice City, violence is a tool for moving real-estate prices. <sub>[C36]</sub>

These missions run beside the main story, and you can finish them even after the final mission. The player can skip them. The city's property war, though, is there either way. <sub>[C46]</sub>

Tommy learns fast. He buys a print shop, the Print Works, and it's the foreman who suggests that printing money is the profitable thing to do. Tommy turns it into a counterfeiting operation by stealing a courier's printing plates. He buys a film studio, and when Congressman Alex Shrub moves to ban pornography to win puritan votes, Tommy gets incriminating photos of the congressman to stop him. <sub>[C45, C44]</sub>

Notice how Shrub is handled. He isn't bribed and he isn't threatened with a gun. He's managed with leverage, the way a business manages a problem. That's our reading of the mission, and it's the same logic Avery used with land. <sub>[C44, C36]</sub>

A developer using murder to win land. A businessman printing his own money. A congressman kept in line with photographs. By 1986, Tommy isn't outside the system. He's fluent in it. <sub>[C46, C45, C44]</sub>

### 09. This Is Business  (162 words)

The fake money has one destination. Sonny Forelli comes south to collect what he considers his. In the final confrontation, Sonny calls Tommy the Harwood Butcher and says the fifteen years Tommy spent in prison were Sonny's to spend. <sub>[C23, C18, C24]</sub>

Sonny talks about Tommy's fifteen years in prison like an investment, and he has come south to cash it in. <sub>[C18, C24]</sub>

Tommy says he was sent to kill one man, and they knew he was coming. Sonny doesn't confess. He deflects. The game implies a setup. It never states one. <sub>[C24]</sub>

This matters because many fan accounts state the setup as fact: Sonny framed Tommy and let him serve his fifteen years. The game itself is more careful. It gives you Sonny's evasion and lets you draw your own conclusion. <sub>[C37, C24]</sub>

Lance has already switched sides. He tells Sonny about the fake money, and Tommy kills them both. Lance had felt underappreciated in Tommy's rise, and his explanation for the betrayal is simple: this is business. <sub>[C23, C25]</sub>

### 10. Built on Crime  (128 words)

Two men, two years apart. Vic Vance kept saying he wanted out, and the city brought him back to a deal table where he died. Tommy Vercetti wanted the top, and he got it. <sub>[C47, C32, C20, C48]</sub>

The difference between them isn't that one was good. Vic dealt drugs and fought a war. The difference is that Vic kept looking for the exit, and Tommy went looking for the keys. <sub>[C47, C48]</sub>

But the sergeant, the agent, the cartel, the colonel and the developer were all there first. Our argument is simple. Tommy Vercetti didn't corrupt Vice City. He inherited a city that was already built on crime. When the series returns to Vice City in GTA VI, it does so in a different continuity, with a different history still to be told. <sub>[C42, C33, C46, C43, C05]</sub>

## 3. Source-to-script mapping

The full map is in [`SOURCE_MAP.md`](SOURCE_MAP.md). It goes paragraph by paragraph, giving each paragraph's claims, their standing, and the passage and source behind each one. Summary:

- **verified** (0): none
- **corroborated** (11): C01, C02, C03, C04, C05, C06, C07, C34, C39, C42, C44
- **matched** (30): C08, C10, C11, C12, C13, C14, C15, C16, C18, C19, C20, C21, C22, C23, C24, C25, C31, C32, C33, C35, C36, C37, C38, C41, C43, C45, C46, C47, C48, C49
- **unsupported** (0): none
- **disputed** (0): none

'Corroborated' means passages matched across two or more independent source families, or in an official source. It is still assistant-matched, not human-verified.

## 4. Visual plan for the first 60 seconds

The narration for 0:00-1:00 is chapter 1's first three paragraphs and the start of the fourth (about 140 words). That's 13 beats from **5 paid images** (T1, T5 and three draft prompts), with the rest coming from crops, camera moves and free typography or graphics. Sound: low synth pad and harbor ambience, no game music. Every illustration carries a small 'Illustrative reconstruction' tag in the lower corner.

| Time | Beat | Asset | Move | Cost |
|---|---|---|---|---|
| 0:00-0:04 | Fade up from black on T1 (wide waterfront at dusk). Typography: 'VICE CITY, 1986' in thin condensed caps. | T1 | Slow push-in | Paid (T1) |
| 0:04-0:09 | T1 cropped to the neon signs flickering on. | T1 crop | Lateral drift | Reuse |
| 0:09-0:14 | T1 cropped to the speedboat wake. | T1 crop | Follow the wake | Reuse |
| 0:14-0:19 | Typography card: '15 YEARS' over a soft barred-shadow texture. | graphic | Hold, shadow slides | Free |
| 0:19-0:24 | The Corporal at the dock table (draft ch01 prompt 2, using the T3 character sheet as reference). | IMG-B | Static, slight parallax | Paid |
| 0:24-0:29 | IMG-B cropped to the closed briefcase and his hands. | IMG-B crop | Push-in | Reuse |
| 0:29-0:33 | Flashback treatment: '1984' date stamp; two brothers in an apartment (ch03 prompt), desaturated. | IMG-C | Slow pan | Paid |
| 0:33-0:38 | IMG-C cropped to the hand turning away from the package. | IMG-C crop | Push-in | Reuse |
| 0:38-0:43 | Empty dock at night, open briefcase (ch01 prompt 3). Violence is implied, not shown. | IMG-D | Static | Paid |
| 0:43-0:47 | IMG-D cropped to the helicopter lights leaving over the water. | IMG-D crop | Tilt up | Reuse |
| 0:47-0:52 | Animated evidence board: four silhouette cards (Sergeant, Agent, Cartel, Developer) pinned one by one. | graphic | Cards drop in on narration | Free |
| 0:52-0:57 | T5 clockwork city, wide. | T5 | Slow push-in | Paid (T5) |
| 0:57-1:00 | T5 cropped to the empty chair; title lands: 'THE DARK HISTORY OF VICE CITY'. | T5 crop | Push-in, title fade | Reuse |

**Whole video:** 13.8 minutes at about 6 seconds per beat gives **about 135 beats** (target 110-150). That doesn't need 135 images:

| Beat source | ~Beats | Paid images |
|---|---|---|
| Illustrations, each used 2-3 times (wide, crop, push-in or parallax) | ~85 | 40 |
| Character reference sheets (Corporal, Newcomer, Sergeant, Developer). Reference only, never shown full screen | 0 | 4 |
| Chapter cards | 10 | 0 |
| Animated timelines, maps and relationship diagrams | ~20 | 0 |
| Evidence boards and on-screen source cards | ~12 | 0 |
| Typography beats (dates, numbers, quotes) | ~8 | 0 |
| **Total** | **~135** | **44** |

The number of paid images does not go up with the beat count.

**Character designs:** every recurring person is an original design (T3, T4 and two more sheets), used as the reference image for later illustrations to keep them consistent. They deliberately avoid the games' signature looks (for example, no loud floral shirt for the Newcomer). Prompts never name game characters; the IP lint passes on all 38 prompts.

## 5. Six proposed test-image prompts

These are not generated yet. Each gets `config/style_gaming_doc.txt` prepended. gpt-image-2, medium, 1536x1024. About $0.34 for all six, using the ledger's figure with the reference-image allowance.

**T1**: Opening beats 1-3 and thumbnail background
> Calm, atmospheric, non-graphic. Wide establishing view of a fictional 1980s subtropical coastal city at dusk: pastel art-deco hotels along a beachfront boulevard, palm silhouettes, the first neon signs flickering on in pink and teal, a lone speedboat wake crossing the calm bay toward the shore. Quiet, expectant mood. Signs are abstract glowing shapes with no letters.

**T2**: Thumbnail concept (text 'BUILT ON CRIME' added later in layout, not in the image)
> Somber, dramatic, non-graphic. Dramatic low-angle composition: an old, generic police-style badge with no insignia or lettering lies cracked on a wet seawall railing in the foreground, sharp focus; behind it, out of focus, a neon-lit 1980s coastal skyline at dusk in magenta and teal. Strong rim light on the badge's crack. Large empty area of sky on the left for title text.

**T3**: Character reference sheet: 'The Corporal' (original design, used for every Vic-era scene)
> Neutral, clean reference style, non-graphic. Character reference sheet on a plain warm-grey background for an original character, 'the Corporal': a man in his late twenties with a tired, decent face, short cropped dark hair and light stubble, wearing a plain olive army field jacket over a white T-shirt, dog tags. Three views side by side: front, three-quarter and profile, plus two small expression studies (worried, resolved). Consistent proportions, clean even lighting, no text labels.

**T4**: Character reference sheet: 'The Newcomer' (original design for the 1986 protagonist role)
> Neutral, clean reference style, non-graphic. Character reference sheet on a plain warm-grey background for an original character, 'the Newcomer': a broad-shouldered man around forty with slicked-back dark hair, a hard jaw and watchful eyes, wearing a ivory linen suit over a dark open-collared shirt, gold wristwatch. Three views side by side: front, three-quarter and profile, plus two small expression studies (calculating, furious). Consistent proportions, clean even lighting, no text labels.

**T5**: Thesis visual, opening beat 12-13 and conclusion callback
> Somber, investigative, non-graphic. Surreal editorial illustration: an enormous brass clockwork mechanism whose gears are built from miniature city blocks, palm trees, hotel towers and neon tubes, glowing softly at dusk. At its center sits a single empty leather executive chair under a spotlight, waiting. Wide composition, deep perspective, investigative documentary tone.

**T6**: Chapter 5 environment: the cartel tower
> Cold, ominous, non-graphic. Night view of an imposing 1980s downtown skyscraper with a smoked-glass facade and a lit marble lobby. At street level, a blank polished brass plaque beside the revolving door; two black limousines idle at the curb with their headlights on. Wet pavement reflections, cold blue and gold palette, sense of quiet power.

## 6. Updated cost estimate and unresolved evidence

**Prices re-checked Nov 24, 2026:**
- **gpt-image-2:** medium 1536x1024 is still listed at $0.041 per image. Our ledger uses $0.056, which adds an allowance for the reference image.
- **ElevenLabs:** the API page now lists roughly $0.04-$0.16 per 1,000 characters, depending on model and plan. Our ledger keeps a conservative $0.30.
- **GPT-5.4 text prices** were not re-checked, because this draft needed no paid text call.
- **Before any paid run**, the owner should confirm the plan and model in her ElevenLabs account.

| Item | Basis | Estimate |
|---|---|---|
| Script | Written in this session from the dossier; no API call | $0.00 |
| Optional pipeline rewrite of all chapters (GPT-5.4) | Fixed estimator: ~9,536 input tokens total | $0.56 expected, $1.82 worst case |
| Test batch (6 images) | 6 x $0.056 | $0.34 |
| Full images | 44 x $0.056, plus up to 50% rerolls | $2.46-3.70 |
| Narration ('Todd') | 10,616 characters x $0.30/1k budget figure, plus 30% retakes | $3.18-4.14 |
| Rendering, QC, graphics, packaging | Local | $0.00 |
| **Total (paid)** | | **$5.98-8.17** (under the proposed $15 ceiling; $5 per run) |

**Why the old script estimate was high:**
- The estimator added up to 20,000 characters of the full dossier to every chapter and priced every chapter at the 12,000-token output ceiling: ~50,466 input tokens and $1.93 for this outline.
- My review-3 table said ~255k input tokens. That was my own over-assumption, not something measured.
- The real chapter prompt only sends that chapter's claims. Those claims did carry their evidence passages; they are now stripped.
- The estimate now uses the real prompts: $0.56 expected, $1.82 worst case. Two new tests cover this.

### Unresolved evidence

- **Nothing is human-verified or checked in the game.** This is the draft's main limitation. Treat everything as assistant-matched.
- **The four priority claims, after the final pass:**
  - **C24 (finale dialogue):** matched. Rests on one fan transcript. Narrowed to the spoken lines only: 'implies a setup, never states one'.
  - **C32 (Vic back in 1986):** matched. Narrowed to 'decided to lay low' plus 'back at the 1986 deal', and the script says the games don't show how he got back in. 'Lance pulled him back' is removed.
  - **C34 (Gonzalez):** corroborated. The leak is stated in the mission. That Diaz received it is labelled implied, and the script says so.
  - **C36 (Avery's motive):** matched. The motive is Avery's own briefing, as quoted by wikis. 'Violence as a real-estate tool' is labelled interpretation.
- **Single-family claims in the draft (30):** C08, C10, C11, C12, C13, C14, C15, C16, C18, C19, C20, C21, C22, C23, C24, C25, C31, C32, C33, C35, C36, C37, C38, C41, C43, C45, C46, C47, C48, C49. They're each backed only by fan wikis or transcripts. If a human check is wanted later, start with C24, C32, C38, C44 and C46.
- **Omitted as unsupported or disputed:** C17, C26, C27, C28, C29, C30, C40. Forbes is called only 'an undercover agent'.
- **Research is closed.** Review 4 allowed one more pass, and it's done. From here, only verification changes the dossier.

## Before publication (not now)

- Provenance review of every asset (`assets/provenance.json`); music must be licensed library music only.
- Check YouTube's altered or synthetic content setting against the final cut.
- 'Illustrative reconstruction' tags on screen, plus a line in the description saying the illustrations are AI-generated original artwork, not game footage.
- Sources list in the description (`sources.json`).

**Stopping here** for script and visual-direction approval. Final narration, full image generation and rendering stay off until the owner explicitly authorizes them and the $15 ceiling.
