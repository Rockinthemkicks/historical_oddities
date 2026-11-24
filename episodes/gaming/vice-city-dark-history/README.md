# Pilot: The Dark History of Vice City

Gaming-lore pilot (20–25 min, fictional investigative history, spoiler level "light").

**Status:** stage 1, research. `research.json` has no claims yet, so `check-research` will
report it isn't ready. That's expected: the claims have to come from sources a human has checked.

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
