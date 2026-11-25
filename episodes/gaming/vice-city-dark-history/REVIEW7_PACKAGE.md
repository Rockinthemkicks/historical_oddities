# Review 7 package: Unplayed History, Vice City pilot

Branch `gaming-lore-pilot` (draft PR #21, not merged). The rebrand migration report is in [docs/MIGRATION_UNPLAYED_HISTORY.md](../../../docs/MIGRATION_UNPLAYED_HISTORY.md).

**Status: ready for final review.** The revised 60-second test ran successfully. The expanded script is drafted and passes every check. No limit was raised, and full-episode generation has not started.

## 1. Revised 60-second test (run 45547596599, approved by the owner)

| | Original test | Revised test |
|---|---|---|
| Length | 46.0 s | **53.2 s** (QC passed: 1920x1080, decodes to the end, duration matches the narration) |
| Narration speed setting | 1.0 | 0.9 |
| Speech pace (words / speech time) | about 189 wpm | **about 179 wpm** (from the run log: 53.2 s minus 7.9 s of pauses and holds, 135 words) |
| Pauses | 0.35 s | 0.45 s, plus a 1.3 s dramatic pause and a 3.0 s title hold |
| Images | 7 generated | **7 reused, $0.00** |
| Cost | $0.60 | **$0.22** (narration only) |

**Findings:**

- **The 0.9 speed setting slows Todd by only about 5%, not 10%.** The setting does reach ElevenLabs, and all 10 clips were regenerated with it; this voice just responds less than expected. My earlier 158 wpm figure was a prediction, not a measurement. That changes the runtime maths below.
- **Loudness and the ambient-bed level still need confirming.** The pipeline now normalizes to -14 LUFS / -1.5 dBTP and records the measurements in `qc_report.json`. That report is inside the run's results zip, which this workspace can't download (GitHub stores it on blob storage outside the allowlist). Once PR #24 is merged, the run summary prints loudness and pacing directly. For this run, the owner can upload the zip.
- **Cost so far: $1.03** of the $2.00 test cap (overall ledger). PR #24 sets the remaining test budget to $0.95.

## 2. Expanded Vice City script (proposed; the approved script is unchanged)

**1442 words, 11 chapters.** Both the outline and chapter checks pass. Nothing is padded; every addition rests on new evidence (section 3).

**Runtime:**
- At the measured **~179 wpm**, the speech runs about **8.1 min**. With about 120 inter-line pauses and the title and chapter holds, the episode is **about 9.3-9.6 min**.
- If Todd's speed were set to 0.8, the pace would be roughly 160 wpm: about **9.0 min** of speech, or **about 10.3-10.6 min** in total.
- **Recommendation:** decide the speed with one short narration sample (one chapter, under $0.10) before the full episode. 10-12 minutes is reachable through pacing without adding filler.

**What the expansion adds:**
- **The Reluctant Empire** (new chapter 4): Vic takes over Marty Jay Williams's businesses and builds the Vance Crime Family. Even the man who wanted out runs rackets by the end of 1984.
- **The Lawyer**: the first person Tommy meets is the Forellis' lawyer, Ken Rosenberg.
- **24-carat gold**: Sonny's reason for sending Tommy south.
- **The Big Corrupt Bank**: El Banco Corrupto Grande; Tommy jokes that Ken "washes the money for us".
- **The Apprentice**: Donald Love takes notes on Avery's gang-war tactic and later becomes a GTA III real-estate and media owner.
- **A conclusion that ties these together.**

Kept out on purpose: the domestic-abuse detail around Marty (not needed for the thesis), Love's later fate in Liberty City Stories, the real person Love is said to be based on, and any GTA VI story connection.

### Expanded narration (claim ids in brackets, for review only)

**1. The Man Who Tried to Leave** (135 words)

Two years before Tommy Vercetti took over Vice City, another man was trying to escape it. <sub>[C08, C32, C22]</sub> His name was Victor Vance. <sub>[C10]</sub> A soldier turned drug dealer, Vic had survived a corrupt sergeant, a war with a powerful cartel, and the loss of the woman he loved. <sub>[C10, C11, C15, C16, C50]</sub> By the end of 1984, he was ready to leave it all behind. <sub>[C32, C47]</sub> Two years later, he was back, at a drug deal that would end his life and begin Tommy Vercetti's rise to power. <sub>[C32, C20, C48]</sub> Vice City tells the story of Tommy building a criminal empire. <sub>[C48]</sub> But the empire was already there. <sub>[C22, C43]</sub> Behind the neon and the oceanfront mansions, a corrupt sergeant, rival drug lords and an undercover agent working both sides had been shaping the city since at least 1984. <sub>[C11, C13, C14, C39, C49]</sub> Tommy didn't invent the system. <sub>[C43]</sub> He inherited it. <sub>[C43]</sub>

**2. Which Vice City?** (62 words)

First, which Vice City is this? <sub>[C51, C52]</sub> Vice City Stories, set in 1984, and Vice City, set in 1986, share one continuity: the series' 3D era. <sub>[C08, C51]</sub> Grand Theft Auto VI's modern Vice City, in the fictional state of Leonida, belongs to a separate continuity. <sub>[C05, C52]</sub> This is the story of the older city. It isn't GTA VI's backstory, and it won't spoil GTA VI. <sub>[C51, C52]</sub>

**3. The Sergeant** (119 words)

In 1984, Victor Vance is an Army corporal at Fort Baxter, on the edge of Vice City. <sub>[C08, C10]</sub> He needs money for his brother Pete's asthma medication. <sub>[C31]</sub> His sergeant, Jerry Martinez, runs a secret drug business, and Vic is drawn in as a reluctant middleman. <sub>[C11]</sub> Then Martinez frames him. Drugs are found, there's a sex worker in Vic's car, and Vic is dishonorably discharged. <sub>[C11]</sub> Vic later learns whose cocaine Martinez had been moving: the Mendez brothers', the most powerful drug family in the city. <sub>[C12, C13]</sub> An Army sergeant, working as a courier for a cartel. <sub>[C12]</sub> Vic, meanwhile, keeps saying he wants out of the drug game. When Lance offers him twenty kilos of cocaine to get started, he turns it down. <sub>[C47]</sub>

**4. The Reluctant Empire** (103 words)

Vic's way out of the Army leads straight into the rackets. <sub>[C53, C11]</sub> He goes to work for Marty Jay Williams, the leader of a street gang called the Trailer Park Mafia. <sub>[C53]</sub> When Marty is killed, Louise suggests that Vic take over Marty's businesses. He does, and the gang becomes the Vance Crime Family. <sub>[C53, C50]</sub> Its businesses read like a map of the city's underground economy: protection, loan sharking, prostitution, drugs, smuggling and robbery. <sub>[C54]</sub> So the reluctant soldier closes out 1984 as the head of a crime family, side by side with his brother. In this city, even the exit seems to run through the rackets. <sub>[C55, C53]</sub>

**5. The Agent** (99 words)

Then there's Bryan Forbes, an undercover agent who sells the Vance brothers information about drug deals. <sub>[C39]</sub> Forbes's own ID becomes part of the scheme. In The Mugshot Longshot, Lance pastes Martinez's photo onto it, to convince the Mendez brothers that their sergeant is working for the law. <sub>[C41]</sub> An agent selling tips to dealers. A sergeant running cocaine for a cartel. <sub>[C39, C12]</sub> Neither proves the whole Army or the whole police force was corrupt, and the games never say so. <sub>[C42]</sub> But in these cases, the men trusted to stand between Vice City and its drug trade were already part of it. <sub>[C42]</sub>

**6. The Cartel's Tower** (173 words)

The Mendez brothers, Armando and Diego, run the 1984 drug trade from a downtown tower also known as the Mendez Foundation building. <sub>[C13]</sub> A charitable-sounding name on a cartel's headquarters. A small detail, and a telling one. <sub>[C13]</sub> The brothers use the Vances for a few jobs, then betray them, and Vic goes to war with the cartel. <sub>[C15]</sub> It costs him dearly. Louise, the woman he loves, dies after the Mendez brothers kidnap her, and Armando is killed at the Mendez mansion. <sub>[C16, C50]</sub> Vic's last backer is a rival drug baron, Ricardo Diaz, who gives him work against the Mendez operation. <sub>[C14]</sub> Diaz is already maneuvering. That same year he blackmails Gonzalez, the right-hand man of a retired colonel, for information on the colonel's drug shipments, as part of his plan to become the city's drug baron. <sub>[C49, C34]</sub> The final mission, Last Stand, is a job for Diaz. Vic attacks the Mendez building from the air and kills Diego Mendez and Martinez on the roof. <sub>[C38, C14]</sub> Then Vic and Lance decide to leave town and lay low. <sub>[C32]</sub>

**7. The Exchange** (174 words)

Two years later, Vic is back at a deal table. The games never show how he returned. <sub>[C32]</sub> The first person Tommy meets in Vice City isn't a gangster. It's a lawyer. <sub>[C56]</sub> Ken Rosenberg, the Forelli family's lawyer, picks Tommy up at the airport and drives him straight to the deal. <sub>[C56]</sub> According to Rosenberg, the deal was set up with help from a retired colonel, Juan Garcia Cortez. <sub>[C33]</sub> Sonny Forelli has sent Tommy south to profit from the city's growing drug trade. <sub>[C19]</sub> Sonny's reason for sending him says a lot. In the opening, he compares Vice City to twenty-four-carat gold, because of the money being made there. <sub>[C63]</sub> The deal is ambushed. Vic and two Forelli men are killed, the money and the cocaine are taken, and Lance escapes. <sub>[C20]</sub> Cortez later tells Tommy who talked: his own right-hand man, Gonzalez, gave away information about the deal. Tommy kills him in Treacherous Swine. <sub>[C34]</sub> The game never says who Gonzalez talked to. But two years earlier, Diaz had blackmailed him for information on Cortez's shipments. <sub>[C34, C49]</sub>

**8. The Heir** (79 words)

Tommy goes to work for Diaz. Lance, working alongside him, learns that Diaz's gang carried out the ambush. <sub>[C21]</sub> Together they storm Diaz's mansion on Starfish Island and kill him, and Tommy takes the mansion and Diaz's empire. <sub>[C22]</sub> From there, Tommy rises to become Vice City's major criminal power. <sub>[C48]</sub> But the mansion and the drug empire he builds on belonged to Diaz first. <sub>[C22, C43]</sub> Lance stays at his side, but he starts to feel underappreciated in a rise he helped begin. <sub>[C25]</sub>

**9. The Business of Vice** (307 words)

Drugs weren't the only business in Tommy's Vice City. <sub>[C46, C45]</sub> Avery Carrington is a real-estate developer who gives Tommy work in a set of optional side missions. <sub>[C46]</sub> In Four Iron, a rival developer won't sell Avery some land, and Tommy kills him on a golf course. <sub>[C46]</sub> In Demolition Man, a competing construction site is in Avery's way, and Tommy blows it up. <sub>[C46]</sub> In Two Bit Hit, Avery explains that a gang war will drive property prices down. <sub>[C36]</sub> Tommy dresses as a Cuban gang member and attacks a Haitian funeral, so the two gangs go to war. <sub>[C35]</sub> In Avery's plan, violence is simply a way to move the market. <sub>[C36]</sub> Taking notes through all of this is Avery's young protégé, Donald Love, who writes down the gang-war tactic in Two Bit Hit. <sub>[C59]</sub> Years later, in Grand Theft Auto III, Love is a real-estate developer who owns a media company. Avery's playbook didn't stay in Vice City. <sub>[C60, C62]</sub> Tommy's own businesses run on similar logic. At the Print Works, the foreman suggests printing money, and Tommy steals a courier's printing plates to start counterfeiting. <sub>[C45]</sub> Then there's the bank. From his new nightclub, the Malibu, Tommy plans a robbery of El Banco Corrupto Grande, a name that translates as the big corrupt bank. <sub>[C58]</sub> Introducing his crew, Tommy jokes that Ken, the lawyer, washes the money for them. <sub>[C57]</sub> Even the bank wears its corruption on its sign. It's the game's own satire, and it's hard to miss. <sub>[C61]</sub> And when Congressman Alex Shrub moves to ban pornography to win puritan votes, Tommy, who now owns a film studio, gets incriminating photos of the congressman to stop him. <sub>[C44]</sub> A developer who uses murder to win land. A business that prints its own money. A congressman kept in line with photographs. <sub>[C46, C45, C44]</sub> By 1986, Tommy isn't outside Vice City's system. He's fluent in it. <sub>[C48, C43]</sub>

**10. This Is Business** (89 words)

The counterfeit money has one destination: Sonny Forelli, who comes south to collect. <sub>[C23, C45]</sub> In the final confrontation, Sonny calls Tommy the Harwood Butcher and says Tommy's fifteen years in prison were his to spend. <sub>[C18, C24]</sub> Tommy says he was sent to kill one man, and they knew he was coming. Sonny deflects. He never admits a setup, and the game never confirms one. <sub>[C24]</sub> Lance has already switched sides. He tells Sonny about the fake money, and Tommy kills them both. <sub>[C23]</sub> Lance's explanation for the betrayal is short: this is business. <sub>[C23, C25]</sub>

**11. Built on Crime** (102 words)

Two men, two years apart. <sub>[C08]</sub> Vic Vance said he wanted out, and the city brought him back to a deal table where he died. <sub>[C47, C32, C20]</sub> Tommy Vercetti wanted the top, and he got it. <sub>[C48]</sub> The difference is that Vic kept looking for the exit, and Tommy went looking for the keys. <sub>[C47, C48]</sub> Vic built an empire because the city left him little else. Rosenberg washed Tommy's money. Avery's protégé carried the playbook to another city. <sub>[C55, C57, C62]</sub> The sergeant, the agent, the cartel and the colonel were all there before Tommy arrived. <sub>[C42, C13, C33]</sub> The evidence points one way. Tommy didn't corrupt Vice City. He inherited it. <sub>[C43]</sub>

## 3. Source verification

The expanded script uses **48 claims**: corroborated 15, matched 33. None is human-verified or checked in the game; all evidence is assistant-matched and recorded with passages in `research.json`. No unsupported or disputed claim is used.

**New claims from this pass:**

| Claim | Standing | Evidence |
|---|---|---|
| C53: Vic works for Marty Jay Williams, leader of the Trailer Park Mafia; after Marty is killed, Vic takes over his businesses on Louise's suggestion and the gang becomes the Vance Crime Family. | corroborated | 4 matched passage(s) across encyclopedia, fan_wiki |
| C54: The Vance empire's businesses are protection rackets, loan sharking, prostitution, drugs, smuggling and robbery. | corroborated | 2 matched passage(s) across fan_wiki, press |
| C55: Even Vic, who says he wants out, ends 1984 running a criminal empire: the story is built around him reluctantly building one. | corroborated | 2 matched passage(s) across community, encyclopedia |
| C56: Ken Rosenberg, the Forelli family's lawyer, meets Tommy at the airport and drives him to the deal. | corroborated | 2 matched passage(s) across encyclopedia, fan_wiki |
| C57: Introducing his heist crew in 'The Job', Tommy says of Ken Rosenberg: 'Ken here, he washes the money for us.' | corroborated | 3 matched passage(s) across community, fan_wiki |
| C58: In 'The Job', planned from his Malibu Club, Tommy's crew robs El Banco Corrupto Grande, a name that is Spanish for 'the big corrupt bank'. | corroborated | 3 matched passage(s) across fan_wiki, press |
| C59: Avery's protégé Donald Love follows him with a notepad and writes down the gang-war tactic during 'Two Bit Hit'. | matched | 3 matched passage(s) across fan_wiki |
| C60: In Grand Theft Auto III (2001), Donald Love is a real-estate developer and the owner of Love Media. | corroborated | 2 matched passage(s) across fan_wiki, press |
| C61: The bank's name is the game's own satire: even Vice City's bank is labelled corrupt. | matched | 1 matched passage(s) across fan_wiki |
| C62: Avery's methods outlive Vice City: his protégé carries the criminal real-estate playbook into GTA III. | corroborated | 2 matched passage(s) across fan_wiki, press |
| C63: In the opening, Sonny Forelli compares Vice City to 24-carat gold because of the money being made there, which is why he sends Tommy south. | matched | 1 matched passage(s) across fan_wiki |

**Highlights:**
- Tommy's "Ken here, he washes the money for us" is in two independent mission transcripts and an IMDb quote list.
- Vic's takeover of Marty's businesses is on Wikipedia and two fan wikis.

**Single-family claims, best candidates for a human cutscene check if one is ever done:** C24 (finale dialogue), C32 (Vic's return), C59 (Love's notepad) and C63 ("24-carat gold").

## 4. Reusable documentary graphics

No new components this round, to avoid scope growth. What exists and is used in the expanded script, all made locally at no cost:
- Name, date and quote stamps.
- Title and chapter cards.
- List and evidence boards whose rows appear as the narrator says them.
- Cards over blurred artwork.
- Reframing reused images.

The new "Vance Empire" board and the two quote stamps use these. A timeline and a relationship diagram stay proposals for after the pilot.

## 5. Brand integration

`config/brand.json` now drives the channel name, logo, colors and tagline on everything the pipeline draws: title, chapter and text cards, thumbnails, and the YouTube description footer. Generated illustrations are never regenerated for branding. **The logo, colors and tagline haven't been provided yet**, so the current look is kept until they are.

## 6. Cost outlook (nothing spent this round)

| Item | Basis | Estimate |
|---|---|---|
| Test so far | ledger | $1.03 of $2.00 |
| Narration sample to set the speed (optional) | one chapter, about 600 chars | under $0.20 |
| Full episode narration | 8,043 chars × $0.30/1k budget figure | about $2.41 |
| Full episode images | 32 new illustrations (the 5 test images are reused) × $0.056, plus up to 50% rerolls | about $1.79-2.69 |
| **Full episode total** | | **about $4.20-5.82**, within the proposed $15 ceiling (needs the owner's approval) |

## 7. Approvals needed

1. **Expanded script:** approve it (or edit it) as the full-episode script.
2. **Narration speed:** keep 0.9 (about 9.5 min) or test 0.8 with a short sample (about 10.5 min).
3. **Brand assets:** the owner provides the logo, colors and tagline.
4. **PR #24:** merge it, so the test cap and ledger hold across runs.
5. **Full-episode production:** a separate, explicit go-ahead with the $15 ceiling. Publishing needs its own authorization after that.
