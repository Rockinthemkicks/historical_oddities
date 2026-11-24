# Pilot: The Dark History of Vice City Before GTA 6

**Review 4 (Nov 24): see [DRAFT_PACKAGE.md](DRAFT_PACKAGE.md) (draft script, source map, visual plan). Review 3: [EDITORIAL_PACKAGE.md](EDITORIAL_PACKAGE.md). Draft script waiting for script and visual-direction approval.**

Gaming-lore pilot (20–25 min, fictional investigative history).

**Scope (owner decision, Nov 23):** a deep dive on the 1980s (3D-universe) Vice City, from Vice City
Stories (1984) and Vice City (1986), framed for GTA VI audiences. GTA VI's Vice City appears only in
the opening and closing, at setting level. Spoiler level "full" covers the 2002 and 2006 games' plots;
every GTA VI claim is rated "none".

**Status:** stage 1, research, second pass done. `research.json` has 37 claims and 36 sources and
passes its checks (0 errors). The key wiki pages and the finale transcript were read in full by Claude,
and four claims were corrected. **No source is human-verified yet.**
Read `research_review.md`, open or play through the sources, set `"verified": true` on the ones you've
checked, and work through the open questions. Then approve the research stage.

## Steps
1. Fill in `research.json` (sources and claims) and run
   `python3 main.py --mode gaming-lore --production episodes/gaming/vice-city-dark-history/production.json check-research`.
   Read `research_review.md`, fix the flags, then run `... approve research`.
2. `... outline --estimate-only`, then `... outline` (one paid text call), review, then `... approve outline`.
3. `... write --estimate-only`, then `... write` (one paid call per chapter), read `script_review.md`, then `... approve script`.
4. Add any footage or screenshots to `assets/` with rights recorded in `assets/provenance.json`, run `... storyboard`, then `... approve storyboard`.
5. `... estimate`, then `... approve budget`. Raise `--max-run-cost` / `--episode-budget` yourself if the estimate needs it.
6. `... produce`, check `out/documentary.mp4` and `out/qc_report.json`, then `... approve assembly`.
7. `... package`, review `publish/`, then `... approve publishing`. Uploading is always done by hand.

To rehearse any step for free: add `--dry-run`. That needs `fixtures/llm.json` here, like the one in
`tests/fixtures/gaming_synthetic/`.

## Known risks for this episode
- **GTA VI** came out on Nov 19, 2026 (per Rockstar's announced date). Rockstar removes spoiler videos
  (endings, cutscene compilations, big reveals), so keep the HD material to setting-level detail.
- **Rockstar's posting policy** covers occasional, non-commercial fan use. A monetized channel using
  gameplay footage is outside its stated scope. Original illustrations avoid most of this risk;
  footage needs the owner's explicit sign-off in `assets/provenance.json`.
