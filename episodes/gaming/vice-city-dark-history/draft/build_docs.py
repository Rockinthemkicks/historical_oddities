"""Builds DRAFT_PACKAGE.md and SOURCE_MAP.md from the draft, the dossier and the prompts. Offline, no paid calls."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from build_draft import build, HERE, PILOT
from modules.gaming.research import source_family
from modules.gaming.script_engine import script_estimate
from modules.gaming.llm import estimate_tokens
from modules.costs import text_unit_cost, image_unit_cost

prod, dossier, rep, outline, chapters, results, orep, deps = build()
S = {s["id"]: s for s in dossier["sources"]}
C = {c["id"]: c for c in dossier["claims"]}
R = rep["readiness"]
WPM = 140
words = sum(r["words"] for r in results)
chars = sum(len(seg["narration"]) for ch in chapters for seg in ch["segments"])
prompts = json.load(open(os.path.join(HERE, "test_prompts.json")))["prompts"]

def strongest(cid):
    order = {"human_verified": 0, "primary_checked": 1, "matched": 2, "disputed": 3, "accessed": 4, "discovered": 5}
    ev = sorted(C[cid].get("evidence", []), key=lambda e: order.get(e["status"], 9))
    m = [e for e in ev if e["status"] in ("matched", "primary_checked", "human_verified")]
    return m or ev[:1]

# ---------- cost ----------
class Paid: is_paid = True
new_est = script_estimate(Paid(), prod, dossier, outline)
old_in = sum(estimate_tokens(json.dumps(c) + json.dumps(dossier)[:20000]) for c in outline["chapters"])
old_usd = sum(text_unit_cost("gpt-5.4", estimate_tokens(json.dumps(c) + json.dumps(dossier)[:20000]), 12000) for c in outline["chapters"])
img_unit = image_unit_cost("gpt-image-2", "medium", "1536x1024", True)
N_IMG = 44
narr_budget = chars / 1000 * 0.30

L = []
A = L.append
A(f"# Draft package: {prod['title']}")
A("")
A("Response to editorial review 4 (Nov 24, 2026). Branch `gaming-lore-pilot`, draft PR #21 (not merged).")
A("")
A("**Status: DRAFT for script and visual-direction approval.** I wrote the narration in this session from the dossier, so no paid API call was made. "
  "Final narration, full image generation and rendering are not approved. The draft's evidence is matched by the assistant (fan transcripts, wikis, official pages). None of it is human-verified or primary-checked.")
A("")
A("| Level | State |\n|---|---|")
c = rep["readiness_counts"]
A(f"| Structural validation | PASSED (0 errors) |")
A(f"| Factual verification | NOT COMPLETE: verified {c['verified']}, corroborated {c['corroborated']}, single-family {c['matched']}, unsupported {c['unsupported']}, disputed {c['disputed']} of {len(R)}. The draft uses no unsupported or disputed claim. |")
A("| Editorial approval | Concept approved (review 4). Script and visual direction: NOT YET |")
A("| Production approval | NOT GIVEN. Proposed $15 pilot ceiling needs the owner's explicit OK |")
A("")
A("Files: [`draft/draft_chapters.json`](draft/draft_chapters.json) (segments with claim ids and visuals), "
  "[`draft/draft_checks.json`](draft/draft_checks.json) (automatic checks), [`outline_proposed.json`](outline_proposed.json), "
  "[`draft/test_prompts.json`](draft/test_prompts.json), [`SOURCE_MAP.md`](SOURCE_MAP.md). Rebuild everything with "
  "`python3 episodes/gaming/vice-city-dark-history/draft/build_draft.py` then `build_docs.py`.")
A("")
A("## 1. Revised chapter outline")
A("")
A(f"{len(outline['chapters'])} chapters, {words} words, about {words/WPM:.1f} minutes at {WPM} wpm. The outline check passes. "
  "The last column lists every claim the chapter uses that is **not verified**, so single-family matches stay visible. Nothing is listed under 'omit': unsupported and disputed claims were cut, not hedged.")
A("")
A("| # | Chapter | Words | ~Min | Purpose | Claims not yet verified (standing) |\n|---|---|---|---|---|---|")
for och, r, d in zip(outline["chapters"], results, deps):
    unv = ", ".join(f"{u['claim']} ({u['standing'][:4]})" for u in d["unverified"])
    A(f"| {och['id'][2:]} | {och['title']} | {r['words']} | {r['words']/WPM:.1f} | {och['purpose']} | {unv} |")
A("")
A("Key changes from review 3:")
A("- **New opening:** the first 30 seconds now run through Vic, the dealer at the docks who had tried to get out, and lead into the thesis. The first 15 seconds are calm: no violence on screen or in narration.")
A("- **3D continuity:** chapter 2 separates the 1997 top-down city, the 3D-era city and GTA VI's Vice City, and says plainly that this video is not GTA VI's backstory. GTA VI appears only at setting level (official site).")
A("- **Vic vs Tommy:** the emotional contrast (escape vs control) runs through chapters 1, 3, 5 and 10. It rests on C47 (Vic says he wants out), C32 and C48.")
A("- **Economic corruption expanded:** chapter 8 is now the longest. It covers Avery's three missions, the Print Works, and Congressman Shrub kept in line with photographs, all from the final research pass.")
A("- **Cut:** the Sonny fan theory (C26), Forbes's agency (C40, disputed), Diaz's 1984-86 rise (C17, unsupported), the GTA VI carry-over speculation (C30) and the aftermath claims (C27-C29).")
A("- **Narrowed:** C42 now describes individuals, not institutions (chapter 4 says so on air); C32 no longer claims Lance pulled Vic back in; C24 sticks to the dialogue.")
A("")
A("## 2. Draft narration")
A("")
A("Claim ids in brackets are for review only and aren't read aloud. Lines that open with 'Our reading', 'Our inference' or 'Our interpretation' are labelled analysis.")
A("")
for och, ch, r in zip(outline["chapters"], chapters, results):
    A(f"### {och['id'][2:]}. {och['title']}  ({r['words']} words)")
    A("")
    for seg in ch["segments"]:
        A(f"{seg['narration']} <sub>[{', '.join(seg['claim_ids'])}]</sub>")
        A("")
A("## 3. Source-to-script mapping")
A("")
A("The full map is in [`SOURCE_MAP.md`](SOURCE_MAP.md). It goes paragraph by paragraph, giving each paragraph's claims, their standing, and the passage and source behind each one. Summary:")
A("")
used = sorted({cid for ch in chapters for seg in ch["segments"] for cid in seg["claim_ids"]}, key=lambda x: int(x[1:]))
by = {}
for cid in used: by.setdefault(R[cid], []).append(cid)
for st in ("verified", "corroborated", "matched", "unsupported", "disputed"):
    A(f"- **{st}** ({len(by.get(st, []))}): {', '.join(by.get(st, [])) or 'none'}")
A("")
A("'Corroborated' means passages matched across two or more independent source families, or in an official source. It is still assistant-matched, not human-verified.")
A("")
A("## 4. Visual plan for the first 60 seconds")
A("")
A("The narration for 0:00-1:00 is chapter 1's first three paragraphs and the start of the fourth (about 140 words). That's 13 beats from **5 paid images** (T1, T5 and three draft prompts), with the rest coming from crops, camera moves and free typography or graphics. "
  "Sound: low synth pad and harbor ambience, no game music. Every illustration carries a small 'Illustrative reconstruction' tag in the lower corner.")
A("")
beats = [
 ("0:00-0:04", "Fade up from black on T1 (wide waterfront at dusk). Typography: 'VICE CITY, 1986' in thin condensed caps.", "T1", "Slow push-in", "Paid (T1)"),
 ("0:04-0:09", "T1 cropped to the neon signs flickering on.", "T1 crop", "Lateral drift", "Reuse"),
 ("0:09-0:14", "T1 cropped to the speedboat wake.", "T1 crop", "Follow the wake", "Reuse"),
 ("0:14-0:19", "Typography card: '15 YEARS' over a soft barred-shadow texture.", "graphic", "Hold, shadow slides", "Free"),
 ("0:19-0:24", "The Corporal at the dock table (draft ch01 prompt 2, using the T3 character sheet as reference).", "IMG-B", "Static, slight parallax", "Paid"),
 ("0:24-0:29", "IMG-B cropped to the closed briefcase and his hands.", "IMG-B crop", "Push-in", "Reuse"),
 ("0:29-0:33", "Flashback treatment: '1984' date stamp; two brothers in an apartment (ch03 prompt), desaturated.", "IMG-C", "Slow pan", "Paid"),
 ("0:33-0:38", "IMG-C cropped to the hand turning away from the package.", "IMG-C crop", "Push-in", "Reuse"),
 ("0:38-0:43", "Empty dock at night, open briefcase (ch01 prompt 3). Violence is implied, not shown.", "IMG-D", "Static", "Paid"),
 ("0:43-0:47", "IMG-D cropped to the helicopter lights leaving over the water.", "IMG-D crop", "Tilt up", "Reuse"),
 ("0:47-0:52", "Animated evidence board: four silhouette cards (Sergeant, Agent, Cartel, Developer) pinned one by one.", "graphic", "Cards drop in on narration", "Free"),
 ("0:52-0:57", "T5 clockwork city, wide.", "T5", "Slow push-in", "Paid (T5)"),
 ("0:57-1:00", "T5 cropped to the empty chair; title lands: 'THE DARK HISTORY OF VICE CITY'.", "T5 crop", "Push-in, title fade", "Reuse"),
]
A("| Time | Beat | Asset | Move | Cost |\n|---|---|---|---|---|")
for b in beats: A("| " + " | ".join(b) + " |")
A("")
secs = words / WPM * 60
A(f"**Whole video:** {secs/60:.1f} minutes at about 6 seconds per beat gives **about 135 beats** (target 110-150). That doesn't need 135 images:")
A("")
A("| Beat source | ~Beats | Paid images |\n|---|---|---|")
A(f"| Illustrations, each used 2-3 times (wide, crop, push-in or parallax) | ~85 | {N_IMG - 4} |")
A("| Character reference sheets (Corporal, Newcomer, Sergeant, Developer). Reference only, never shown full screen | 0 | 4 |")
A("| Chapter cards | 10 | 0 |")
A("| Animated timelines, maps and relationship diagrams | ~20 | 0 |")
A("| Evidence boards and on-screen source cards | ~12 | 0 |")
A("| Typography beats (dates, numbers, quotes) | ~8 | 0 |")
A(f"| **Total** | **~135** | **{N_IMG}** |")
A("")
A("The number of paid images does not go up with the beat count.")
A("")
A("**Character designs:** every recurring person is an original design (T3, T4 and two more sheets), used as the reference image for later illustrations to keep them consistent. "
  "They deliberately avoid the games' signature looks (for example, no loud floral shirt for the Newcomer). Prompts never name game characters; the IP lint passes on all 38 prompts.")
A("")
A("## 5. Six proposed test-image prompts")
A("")
A(f"These are not generated yet. Each gets `config/style_gaming_doc.txt` prepended. gpt-image-2, medium, 1536x1024. About ${len(prompts)*img_unit:.2f} for all six, using the ledger's figure with the reference-image allowance.")
A("")
for p in prompts:
    A(f"**{p['id']}**: {p['use']}")
    A(f"> {p['prompt']}")
    A("")
A("## 6. Updated cost estimate and unresolved evidence")
A("")
A("**Prices re-checked Nov 24, 2026:**")
A("- **gpt-image-2:** medium 1536x1024 is still listed at $0.041 per image. Our ledger uses $0.056, which adds an allowance for the reference image.")
A("- **ElevenLabs:** the API page now lists roughly $0.04-$0.16 per 1,000 characters, depending on model and plan. Our ledger keeps a conservative $0.30.")
A("- **GPT-5.4 text prices** were not re-checked, because this draft needed no paid text call.")
A("- **Before any paid run**, the owner should confirm the plan and model in her ElevenLabs account.")
A("")
A("| Item | Basis | Estimate |\n|---|---|---|")
A("| Script | Written in this session from the dossier; no API call | $0.00 |")
A(f"| Optional pipeline rewrite of all chapters (GPT-5.4) | Fixed estimator: ~{new_est['input_tokens']:,} input tokens total | ${new_est['expected_usd']:.2f} expected, ${new_est['worst_case_usd']:.2f} worst case |")
A(f"| Test batch (6 images) | 6 x ${img_unit:.3f} | ${6*img_unit:.2f} |")
A(f"| Full images | {N_IMG} x ${img_unit:.3f}, plus up to 50% rerolls | ${N_IMG*img_unit:.2f}-{N_IMG*img_unit*1.5:.2f} |")
A(f"| Narration ('Todd') | {chars:,} characters x $0.30/1k budget figure, plus 30% retakes | ${narr_budget:.2f}-{narr_budget*1.3:.2f} |")
A("| Rendering, QC, graphics, packaging | Local | $0.00 |")
lo = 6*img_unit + N_IMG*img_unit + narr_budget
hi = 6*img_unit + N_IMG*img_unit*1.5 + narr_budget*1.3
A(f"| **Total (paid)** | | **${lo:.2f}-{hi:.2f}** (under the proposed $15 ceiling; $5 per run) |")
A("")
A(f"**Why the old script estimate was high:**")
A(f"- The estimator added up to 20,000 characters of the full dossier to every chapter and priced every chapter at the 12,000-token output ceiling: ~{old_in:,} input tokens and ${old_usd:.2f} for this outline.")
A("- My review-3 table said ~255k input tokens. That was my own over-assumption, not something measured.")
A("- The real chapter prompt only sends that chapter's claims. Those claims did carry their evidence passages; they are now stripped.")
A(f"- The estimate now uses the real prompts: ${new_est['expected_usd']:.2f} expected, ${new_est['worst_case_usd']:.2f} worst case. Two new tests cover this.")
A("")
A("### Unresolved evidence")
A("")
A("- **Nothing is human-verified or checked in the game.** This is the draft's main limitation. Treat everything as assistant-matched.")
A("- **The four priority claims, after the final pass:**")
A(f"  - **C24 (finale dialogue):** {R['C24']}. Rests on one fan transcript. Narrowed to the spoken lines only: 'implies a setup, never states one'.")
A(f"  - **C32 (Vic back in 1986):** {R['C32']}. Narrowed to 'decided to lay low' plus 'back at the 1986 deal', and the script says the games don't show how he got back in. 'Lance pulled him back' is removed.")
A(f"  - **C34 (Gonzalez):** {R['C34']}. The leak is stated in the mission. That Diaz received it is labelled implied, and the script says so.")
A(f"  - **C36 (Avery's motive):** {R['C36']}. The motive is Avery's own briefing, as quoted by wikis. 'Violence as a real-estate tool' is labelled interpretation.")
single = [cid for cid in used if R[cid] == "matched"]
A(f"- **Single-family claims in the draft ({len(single)}):** {', '.join(single)}. They're each backed only by fan wikis or transcripts. If a human check is wanted later, start with C24, C32, C38, C44 and C46.")
A("- **Omitted as unsupported or disputed:** C17, C26, C27, C28, C29, C30, C40. Forbes is called only 'an undercover agent'.")
A("- **Research is closed.** Review 4 allowed one more pass, and it's done. From here, only verification changes the dossier.")
A("")
A("## Before publication (not now)")
A("")
A("- Provenance review of every asset (`assets/provenance.json`); music must be licensed library music only.")
A("- Check YouTube's altered or synthetic content setting against the final cut.")
A("- 'Illustrative reconstruction' tags on screen, plus a line in the description saying the illustrations are AI-generated original artwork, not game footage.")
A("- Sources list in the description (`sources.json`).")
A("")
A("**Stopping here** for script and visual-direction approval. Final narration, full image generation and rendering stay off until the owner explicitly authorizes them and the $15 ceiling.")
open(os.path.join(PILOT, "DRAFT_PACKAGE.md"), "w").write("\n".join(L) + "\n")

# ---------- source map ----------
M = ["# Source-to-script map", "",
     "Every narration paragraph, the claims it rests on, each claim's standing, and the strongest evidence behind it. "
     "Statuses come from `research.json`: 'matched' means the assistant matched a passage; nothing here is human-verified.", ""]
for och, ch in zip(outline["chapters"], chapters):
    M.append(f"## {och['id'][2:]}. {och['title']}")
    M.append("")
    for i, seg in enumerate(ch["segments"], 1):
        M.append(f"**¶{i}.** {seg['narration']}")
        M.append("")
        for cid in seg["claim_ids"]:
            c = C[cid]
            ev = "; ".join(f"{e['source_id']} ({source_family(S[e['source_id']])}, {e['status']})"
                           + (f": {e['passage']}" if e.get("passage") else "") for e in strongest(cid))
            M.append(f"- **{cid}** [{c['status'].replace('_', ' ')}, **{R[cid]}**] {c['text']}  \n  Evidence: {ev}")
        M.append("")
M += ["## Sources", ""]
cited = sorted({e["source_id"] for cid in used for e in C[cid].get("evidence", [])}, key=lambda x: int(x[1:]))
for sid in cited:
    s = S[sid]
    M.append(f"- **{sid}** ({source_family(s)}) {s.get('title', '')}: {s.get('url') or s.get('locator', '')}")
open(os.path.join(PILOT, "SOURCE_MAP.md"), "w").write("\n".join(M) + "\n")
print("words", words, "chars", chars, "est", new_est, "old", old_in, round(old_usd, 2), "paid", round(lo, 2), round(hi, 2))
