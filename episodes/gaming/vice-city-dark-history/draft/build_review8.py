"""Writes REVIEW8_PACKAGE.md: the consolidated package for final production approval. Offline."""
import json, os, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_expansion as be

prod, dossier, rep, outline, chapters, results, orep, deps = be.build()
PILOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = rep["readiness"]; S = {s["id"]: s for s in dossier["sources"]}; C = {c["id"]: c for c in dossier["claims"]}
est = json.load(open(os.path.join(PILOT, "estimate.json")))
script = json.load(open(os.path.join(PILOT, "script.json")))
words = sum(len(s["narration"].split()) for s in script["scenes"])
scenes = len(script["scenes"])
holds = sum(s.get("pause_after", 0.45) for s in script["scenes"])
used = sorted({c for ch in chapters for s in ch["segments"] for c in s["claim_ids"]}, key=lambda x: int(x[1:]))
cnt = {}
for c in used: cnt.setdefault(R[c], []).append(c)
shots = sum((len(v.get("rows") or []) + 1) if v.get("reveal") else 1 for sc in script["scenes"] for v in sc["visuals"])
def mins(wpm, extra=0.0): return (words / wpm) + (holds + extra * scenes) / 60

L = []; A = L.append
A("# Review 8: final production approval package")
A("")
A(f"**Unplayed History, episode 1: {prod['title']}.** Branch `gaming-lore-pilot` (draft PR #21). 2026-11-25.")
A("")
A("**Decision requested: approve full-episode production of the script below, with a $15 ceiling.** Everything in this package was done offline; nothing was spent this round. Publishing remains a separate authorization.")
A("")
A("## At a glance")
A("")
A("| | |")
A("|---|---|")
A(f"| Script | {words} words, {len(chapters)} chapters, {scenes} scenes. The outline and every chapter pass the checks. The storyboard check (IP lint, opening-15-second risk words) passes with 0 warnings |")
A(f"| Evidence | {len(used)} claims used: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(cnt.items())) + ". No unsupported or disputed claim. None human-verified |")
A(f"| Runtime | about **{mins(179):.1f} min** at the measured 0.9 pace; about **{mins(162):.1f}-{mins(162, 0.15):.1f} min** expected at 0.8 (to be measured) |")
A(f"| Visuals | **{shots} shots**, no shot held over 7.5 s. 32 new paid illustrations plus the 5 from the test; everything else is reframes, reveals and cards made at no cost |")
A(f"| Cost | full episode **${est['total_usd']:.2f}** estimated (images ${est['images']['estimate_usd']:.2f}, narration ${est['narration']['estimate_usd']:.2f}); test spend to date $1.03 |")
A("| Safeguards | PR #24 verified and merged (tests passed): the episode ledger now carries between runs; test budget left $0.95; $5 per run, $10 per episode and the overall limit are unchanged |")
A("")
A("## 1. Final editorial corrections (this round)")
A("")
A("| Where | Change | Why |")
A("|---|---|---|")
for w, c, y in [
 ("Finale (ch10)", "'Sonny deflects. He never admits a setup, and the game never confirms one' → Sonny's actual line, then 'It lands as a confession.'", "Wikipedia, press and the fan wikis all read the scene as an admission. Our earlier wording overreached. The spoken line is fact (C24); the reading is labelled interpretation (C64)."),
 ("Last Stand (ch06)", "Added: Lance suggests hiding the leftover cocaine to sell later; Vic: 'I am not interested.'", "From the mission transcript (C65). The strongest evidence for the exit/keys contrast."),
 ("1986 opening (ch07)", "Merged two near-duplicate lines about Sonny's motive; his reason now comes before the airport, in story order", "Flow. Sonny's own line is quoted: 'Vice City is twenty-four carat gold these days.'"),
 ("Two Bit Hit (ch09)", "Paraphrase replaced by Avery's line: 'nothing brings down real estate prices quicker than a good old-fashioned gang war'", "Exact dialogue (transcript) is stronger and safer than a paraphrase."),
 ("Conclusion (ch11)", "'The colonel was there before Tommy' now cites the 1984 evidence (C49)", "Every statement must be supported by what it cites."),
]:
    A(f"| {w} | {c} | {y} |")
A("")
A("## 2. Targeted lore verification")
A("")
A("| Claim | Before | After | What changed |")
A("|---|---|---|---|")
for cid, before, what in [
 ("C24", "single-family", "Narrowed to the spoken line, now matched in two transcripts plus press quotes. The reading of it (C64) is corroborated by an encyclopedia, press and a fan wiki."),
 ("C32", "single-family", "Last Stand transcript ('we should get out of town or lay low') plus two press recaps."),
 ("C36", "single-family, high-risk", "Avery's exact line in a transcript, plus a press mission guide (flagged as weak: the same page contains an error)."),
 ("C63", "single-family", "Intro script (Sonny's 'twenty-four carat gold') plus Wikipedia on why Sonny sent Tommy south."),
 ("C54", "corroborated", "Re-checked: the GamesRadar passage I'd recorded earlier was confirmed word for word. I also caught and removed an evidence entry of mine for C65 that cited a passage I hadn't actually seen."),
]:
    A(f"| {cid} | {before} | **{R[cid]}** | {what} |")
single = [c for c in used if R[c] == "matched"]
A("")
A(f"**Still single-family ({len(single)} of {len(used)}):** {', '.join(single)}. These are story facts backed by one or more fan wikis or transcripts; none is the thesis. All evidence is assistant-matched, never presented as checked in the game.")
A("")
A("## 3. Final script")
A("")
A("Claim ids in brackets are for review only and aren't read aloud. Lines starting 'It lands as...', 'In Avery's plan...' or 'The evidence points...' are labelled interpretations, backed by interpretation claims.")
A("")
for och, ch, r in zip(outline["chapters"], chapters, results):
    A(f"**{int(och['id'][2:])}. {och['title']}** ({r['words']} words)")
    A("")
    A(" ".join(f"{s['narration']} <sub>[{', '.join(s['claim_ids'])}]</sub>" for s in ch["segments"]))
    A("")
A("Full statement-by-statement sources: `research.json` (passages, families, statuses) and `draft/expanded_checks.json`.")
A("")
A("## 4. Visual plan (existing assets first)")
A("")
A(f"- **{shots} shots in about {mins(179):.0f}-{mins(162):.0f} minutes** (about 5 s each), with no shot held over 7.5 s. Long lines get a second, reframed shot of their own image; list cards reveal row by row as the narrator speaks.")
A("- **Paid images:** 32 new illustrations, plus the reference sheet and thumbnail background. The 5 test illustrations and the Corporal reference sheet should be **reused, not regenerated**, both for character consistency and to save about $0.30 (see section 7).")
A("- **Made at no cost:** 9 chapter cards, 17 typography cards (name stamps, quotes such as 'HE WASHES THE MONEY FOR US' and 'I AM NOT INTERESTED', evidence boards with timed reveals), and 48 reframed reuses.")
A("- **Style:** cinematic graphic-novel illustrations, original character designs, no game footage, no Rockstar logos or art. The disclosure appears once, on the title card, plus in the description.")
A("")
A("## 5. Branding")
A("")
A("- **Title card:** 'THE DARK HISTORY OF VICE CITY / Before GTA 6 / An Unplayed History documentary'.")
A("- **New end card:** 'UNPLAYED HISTORY: Sources for every claim are in the description', over the cracked-badge image, held 4 s.")
A("- **Thumbnails:** the tag now reads 'UNPLAYED HISTORY · VICE CITY 1984-86'. Four options are attached in the chat: *Built on Crime* (approved concept), *Before Tommy*, *The Hidden Empire*, *Vice City 1984*.")
A("- **Description footer:** reads 'Unplayed History'.")
A("- **Still pending from the owner:** logo, colors and tagline. Without them the current gold, pink and teal look is used. Adding them later re-styles cards and thumbnails at no cost and never touches illustrations.")
A("")
A("## 6. Narration speed comparison (ready; one button press)")
A("")
A("| | 0.9 (measured) | 0.8 (ready to run) |")
A("|---|---|---|")
A("| 60-second test | run 45547596599: 53.2 s, about 179 wpm | button run renders the same opening at 0.8; images reused |")
A(f"| Full episode, estimated | about {mins(179):.1f} min | about {mins(162):.1f} min; with 0.6 s pauses about {mins(162, 0.15):.1f} min |")
A("| Cost | already paid | about $0.22 (test budget left $0.95) |")
A("")
A("After PR #24, the run page itself shows the measured pace and loudness, so the comparison can be read straight from the run summary, plus a listen to both videos. **Recommendation:** pick by ear. If 0.8 sounds natural, use 0.8 with 0.6 s pauses to land at about 10 minutes, the low end of the 10-12 minute target, without filler.")
A("")
A("## 7. What production would do once approved")
A("")
A("1. **Speed:** decide 0.8 or 0.9 from the comparison above.")
A("2. **Small prep:** a 'Produce full episode' button following the same pattern as the test button: RUN confirmation, fixed caps, ledger and cache carried. It would reuse the test's Corporal reference sheet and its 5 illustrations rather than regenerate them. This is the only remaining pipeline change, and it's needed to run the episode without a laptop.")
A("3. **Approve stages:** the owner approves the pipeline stages for the full production.")
A(f"4. **Paid run:** about ${est['total_usd']:.2f} estimated: ${est['images']['estimate_usd']:.2f} for images, ${est['narration']['estimate_usd']:.2f} for narration. Run cap $15, episode cap $15 (pending approval; the episode limit is currently $10). Nothing is raised automatically.")
A("5. **Review the cut:** I check it frame by frame, run QC, measure loudness and fix captions. Any fixes use the cached assets.")
A("6. **Publish:** a separate, explicit authorization from the owner, with the description, chapters, sources and monetization checklist that the pipeline generates.")
A("")
A("## 8. Approvals needed")
A("")
A("1. **Final script:** this script as the episode script.")
A("2. **Narration speed:** after the comparison, or decide now.")
A("3. **Full-episode production:** about $4.62 estimated, with a $15 ceiling.")
A("4. **Thumbnail:** *Built on Crime*, or one of the alternatives.")
A("5. **Brand assets (optional before publishing):** logo, colors and tagline.")
open(os.path.join(PILOT, "REVIEW8_PACKAGE.md"), "w").write("\n".join(L) + "\n")
print("ok", words, scenes, shots, round(mins(179), 1), round(mins(162), 1), round(mins(162, 0.15), 1))
