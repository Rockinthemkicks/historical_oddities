"""Writes REVIEW5_TEST.md: revised narration, corrections, the 60-second test plan and its estimate. Offline."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from build_draft import build, PILOT, REFERENCE_PROMPT

prod, dossier, rep, outline, chapters, results, orep, deps = build()
TEST = os.path.join(os.path.dirname(PILOT), "vice-city-60s-test")
R = rep["readiness"]
script = json.load(open(os.path.join(TEST, "script.json")))
tprod = json.load(open(os.path.join(TEST, "production.json")))
est = json.load(open(os.path.join(TEST, "estimate.json"))) if os.path.exists(os.path.join(TEST, "estimate.json")) else None
qc = json.load(open(os.path.join(TEST, "out", "qc_report.json"))) if os.path.exists(os.path.join(TEST, "out", "qc_report.json")) else None
words = sum(r["words"] for r in results)

L = []; A = L.append
A("# Review 5: revised narration and the 60-second production test")
A("")
A("Response to ChatGPT editorial review 5 (Nov 24, 2026). Branch `gaming-lore-pilot`, draft PR #21 (not merged).")
A("")
A("**Status: everything free is done. The paid 60-second test is ready to run and waits for the owner's explicit authorization.** No paid call has been made.")
A("")
A("## 1. Narration polish and accuracy corrections")
A("")
A("| Review item | What changed |\n|---|---|")
for a, b in [
 ("Sound like a documentary, not a research report", "Removed 'the sources we could check', 'our reading', 'our inference', 'we won't fill that gap' and 'our argument is simple'. Uncertainty now uses natural phrasing ('the game never says who...', 'he never admits a setup, and the game never confirms one', 'the evidence points one way')."),
 ("New opening", "Used the suggested opening almost word for word, with three evidence fixes: (1) 'Most people remember...' became 'Vice City tells the story of...', with no claim about what fans believe. (2) The 'already shaping the city' list names the sergeant, rival drug lords and the agent, but drops 'wealthy developers': Avery's missions are only shown in 1986, during Tommy's rise. (3) 'By 1984' became 'By the end of 1984', which matches when the brothers decide to lay low."),
 ("Exit/keys line in the conclusion", "Kept word for word."),
 ("GTA VI sales figures", "Removed."),
 ("Continuity in 20-30 seconds", "Chapter 2 is now 62 words (about 25 seconds). It says plainly that Vice City Stories and Vice City share the 3D continuity and GTA VI's Vice City belongs to a separate one. Two new claims back this, C51 and C52, split by universe after the continuity check flagged the first version for mixing them."),
 ("Boat arrival", "Removed. Tommy's arrival isn't described."),
 ("What fans believe", "Removed the 'many fan accounts' passage."),
 ("Badge as currency", "Replaced with Forbes's documented actions: he sells deal information, and his ID is used in The Mugshot Longshot."),
 ("'Ran it harder'", "Removed."),
 ("Optional vs story missions", "Avery's missions are introduced as 'a set of optional side missions'. Everything else in the script is main-story."),
 ("Avery's chronology", "Avery no longer appears in any 'before Tommy' statement, including the conclusion."),
 ("Statement-level support", "The script is now split into one statement (one or two sentences) per scene, and each scene carries its own claim ids. [SOURCE_MAP.md](SOURCE_MAP.md) lists the evidence statement by statement."),
 ("'The woman he loved'", "New claim C50: Louise as Vic's love interest. Corroborated by two fan wikis plus press."),
]:
    A(f"| {a} | {b} |")
A("")
A(f"**Runtime: {words} words, about {words/140:.1f} minutes at 140 words per minute** (Todd may read faster). As the review asked, I didn't pad. That's below the approved 12-16 minutes, so this needs a decision:")
A("- Accept an 8-10 minute pilot (the outline check flags the gap until the target changes), or")
A("- Add more Vice City Stories material that is already well documented (for example, Vic taking over Marty Jay Williams's businesses), which would mean one more small research pass.")
A("")
A("## 2. Revised complete narration")
A("")
A("Claim ids in brackets are for review only.")
A("")
for och, ch, r in zip(outline["chapters"], chapters, results):
    A(f"### {och['id'][2:]}. {och['title']} ({r['words']} words)")
    A("")
    A(" ".join(f"{seg['narration']} <sub>[{', '.join(seg['claim_ids'])}]</sub>" for seg in ch["segments"]))
    A("")
used = sorted({c for ch in chapters for seg in ch["segments"] for c in seg["claim_ids"]}, key=lambda x: int(x[1:]))
by = {}
for c in used: by.setdefault(R[c], []).append(c)
A("**Evidence standing of the claims used:** " + "; ".join(f"{k} {len(v)}" for k, v in sorted(by.items())) +
  ". None is human-verified or checked in the game. Fan transcripts and wikis are recorded as assistant-matched, never as primary evidence. No unsupported or disputed claim is used.")
A("")
A("## 3. The 60-second test: ready to run")
A("")
A("It runs through the real production pipeline as its own small production ([`../vice-city-60s-test/`](../vice-city-60s-test/)): the opening chapter, about 57 seconds.")
A("")
A("**Dress rehearsal (free, offline, done):**")
A("- Placeholder images and timing-only audio.")
A("- Rendered at 1920x1080 and passed QC" + (f" at {qc['duration_seconds']:.1f} s." if qc else "."))
A("- No letterboxing: the 1536x1024 images fill the 16:9 frame through a safe crop.")
A("- Fixed along the way: a text-card layout bug, a title that ran off-frame, the disclosure line colliding with captions, and a rights-check bug that blocked rebuilt cards.")
A("")
A("**What the paid run adds:**")
A("- The ElevenLabs narrator (Todd, model eleven_multilingual_v2).")
A("- Real illustrations.")
A("- Scene timing taken from the actual narration audio. Each statement is its own scene, so the visuals change on the narrator's words, not on an estimated reading speed.")
A("")
A("| # | Narration | Visuals (camera move) |\n|---|---|---|")
for sc in script["scenes"]:
    vs = []
    for v in sc["visuals"]:
        if v["kind"] == "illustration": vs.append(f"**new image** `{v['id']}` ({v.get('motion', 'auto')})")
        elif v["kind"] == "reuse": vs.append(f"reuse `{v['of']}` ({v['motion']})")
        elif v["kind"] == "text_card": vs.append(f"typography: {v['style']} '{v.get('heading', '')}' ({v.get('motion')})")
    A(f"| {sc['scene_number']} | {sc['narration']} | {'; '.join(vs)} |")
A("")
A("**Character consistency test.** One reference sheet for an original character, 'the Corporal'. It deliberately avoids the game character's look, and every generated image uses it as its reference. He then appears in three settings: an army base (1984), a hospital corridor, and a harbor pier (1986, civilian clothes).")
A("")
A("**Images to generate (7, plus nothing else):**")
A("- The reference sheet.")
A("- Five scene images: waterfront, Corporal at the base, Corporal in the hospital, Corporal at the pier, the clockwork city.")
A("- The thumbnail background.")
A("")
A("Every prompt passes the IP lint; none names a game character, brand or logo.")
A("")
A("Reference sheet prompt:")
A(f"> {REFERENCE_PROMPT}")
A("")
A("**Typography and graphics (free, made locally):**")
A("- Name stamp: 'VICTOR VANCE / VICE CITY, 1984'.")
A("- '1986 / TWO YEARS LATER'.")
A("- A four-row 'VICE CITY, 1984' board: sergeant, cartel, rival, agent.")
A("- The title card. It carries the one synthetic-art disclosure: 'Illustrations are original artwork, not game footage.'")
A("")
A("**Reframing:** three beats reuse earlier images with a push-in to a new point (`zoom_to`). That's new framing without paying for new images.")
A("")
A("**Sound:**")
A("- An original ambient pad made locally with ffmpeg, registered in the rights manifest as our own work, mixed low under the narration.")
A("- No game music and no third-party audio.")
A("")
A("**Thumbnail mockup:** `draft/make_thumbnail.py` sets the generated background with our own lettering:")
A("- 'BUILT ON CRIME', with a pink 'VICE CITY LORE · 1984-1986' tag and a teal accent bar.")
A("- Plain bold sans-serif, deliberately not Rockstar's lettering, logo or art.")
A("")
if est:
    A(f"**Estimate:** {est['images']['to_generate']} images (${est['images']['estimate_usd']:.2f}) + {est['narration']['characters']} narration characters (${est['narration']['estimate_usd']:.2f}) = **${est['total_usd']:.2f}**. That's against a **$2.00 run cap**, and the existing episode and overall limits stay in place. The ledger figures are conservative: images include a reference allowance, and narration is budgeted at $0.30 per 1,000 characters, above ElevenLabs' current list prices.")
A("")
A("**Known limits of this test:**")
A("- Cuts between beats, no crossfades.")
A("- Typography 'animation' is a slow camera push, not animated text.")
A("- Sound design is the ambient pad only (no hits or risers).")
A("- Captions are burned in.")
A("")
A("Each of these is a small follow-up if the test shows it's needed.")
A("")
A("## 4. What I need from the owner")
A("")
A("1. **Authorize the paid test:** up to $2.00, estimated $" + (f"{est['total_usd']:.2f}" if est else "0.60") + ". That covers 7 images and about 57 seconds of narration. Nothing paid runs until you say so.")
A("2. **Runtime:** accept 8-10 minutes, or approve a small research pass to add Vice City Stories material.")
A("")
A("After the test I'll return:")
A("- The rendered MP4.")
A("- The images and the reference sheet.")
A("- The thumbnail mockup.")
A("- Actual costs and the remaining budget.")
A("- Any rendering, consistency or factual issues.")
open(os.path.join(PILOT, "REVIEW5_TEST.md"), "w").write("\n".join(L) + "\n")
print("ok", words)
