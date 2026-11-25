# Migration report: historical_oddities → Unplayed History

Date: 2026-11-25. Performed on branch `gaming-lore-pilot`, plus PR #24 for the test button.

## Summary

The repository is now `Rockinthemkicks/unplayedhistory`, and **Unplayed History** is the official brand. Nothing was lost. The working copy points at the new URL, and every branch, pull request, paid asset, cache and production path still works. **118/118 tests pass.**

## Checks

| Item | Result |
|---|---|
| Git remote | `origin` → `https://github.com/Rockinthemkicks/unplayedhistory` (fetch and push verified). Old URLs redirect on GitHub. |
| Branches | All remote branches present: `main`, `gaming-lore-pilot`, `fix-flaky-voice-test`, `narration-decision`, `test-button-keep-media`, `vice-city-test-button`, `voice-limiter`, and the new `button-episode-ledger`. Local branches kept. |
| Pull requests | History intact (#1-#23). Open: #20 (flaky test fix), #21 (pilot draft, not merged). New: #24 (episode ledger fix). |
| Actions | The test button and test workflows ran successfully after the rename. The revised test (run 45547596599, 04:33 UTC) restored both caches. |
| Paid assets | 7 test images reused from the Actions cache ($0.00 in the revised run). No image prompt, style, reference or order changed. |
| Spend ledger | Overall ledger carried correctly: **$1.03** across the three test runs. |
| Test suite | 118 passed (offline, placeholder media, no paid calls). |
| Gaming pipeline | Research check passes (0 errors); the approved draft and the expanded draft both pass the outline and chapter checks; the offline 60-second dry run renders and passes QC. |
| Historical mode | Unchanged; its tests pass. |

## Problem found during the migration (fixed in PR #24)

The **per-episode** ledger (`costs.jsonl`, kept in the episode folder) wasn't carried between Actions runs, so the button's $2 episode cap restarted every run. The overall ledger was carried, so spend was always recorded. PR #24:
- caches the episode ledger too;
- sets the remaining test budget to **$0.95** ($2.00 − $1.03), so the test cap holds;
- prints loudness and pacing into the run summary.

No limit was raised.

## What changed

- `CLAUDE.md`, `README.md`, `docs/GAMING_LORE.md`, `run_test.sh`: brand and new repo name.
- `config/brand.json` + `modules/gaming/brand.py`: name **Unplayed History**, with slots for logo, colors and tagline. These restyle only what the pipeline draws itself (title, chapter and text cards; thumbnails; the YouTube description footer). Generated illustrations are never regenerated for branding. Until values arrive, the defaults reproduce the current look.
- YouTube description footer: now reads "Unplayed History". I also corrected a sentence that wrongly said the video was "fact-checked against the games"; nothing has been checked in-game. It now says facts are researched against the listed sources.

## Deliberately not renamed

| Kept | Why |
|---|---|
| `~/.historical_oddities/spend_ledger.jsonl`, `HO_SPEND_LEDGER` | Renaming would start a new, empty ledger and silently reset overall spending limits |
| Actions cache paths and keys | Renaming would orphan the cached paid images and narration |
| Module names, historical mode, "Historical Oddities" references | Historical Oddities is still the on-hold historical channel; its mode must keep working |
| `docs/PROJECT_BRIEF.md`, `docs/AUDIT.md` | Historical records |

## Owner action (optional)

On your Mac, the old remote URL keeps working through GitHub's redirect. To update it:
`git remote set-url origin https://github.com/Rockinthemkicks/unplayedhistory`.
The local folder name doesn't matter.

## Still needed for the brand

**Logo file, brand colors and tagline.** None were provided, and none have been invented. Once they're in `config/brand.json`, cards and thumbnails pick them up automatically.
