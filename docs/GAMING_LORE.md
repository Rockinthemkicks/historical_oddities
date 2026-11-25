# Gaming-lore mode

Long-form (20–60 min) fictional investigative documentaries about game worlds, built on
the same pipeline as Historical Oddities. The gaming-lore channel is branded **Unplayed History** (`config/brand.json`). Historical mode is unchanged and stays the default.

```
python3 main.py --mode gaming-lore --production <folder>/production.json <command> [--dry-run] [--estimate-only]
```

## Stages and approvals

| # | Stage | Command | Artifact you approve |
|---|---|---|---|
| 0 | Topic | – | production.json |
| 1 | Research | `check-research` | research.json (review: research_review.md) |
| 2 | Outline | `outline` (paid, ~cents) | outline.json |
| 3 | Script | `write` (paid, one call per chapter) | script.json (review: script_review.md) |
| 4 | Storyboard + rights | `storyboard` | storyboard.json + assets/provenance.json |
| 5 | Budget | `estimate` | estimate.json |
| 6–7 | Generation + assembly | `produce` (paid) | out/qc_report.json |
| 8 | Publishing package | `package` | publish/description.txt |

Approve with `... approve <stage>`. An approval stores a hash of the files. If you edit them
afterwards, the approval lapses and the stage must be approved again. `produce` needs stages
1–5 approved; `package` needs stage 7. Uploading is never automated.

## Building blocks
- **`config/modes/*.json`:** mode defaults. Gaming uses landscape, Ken Burns motion, 140 wpm,
  12 s per visual, and long-form captions.
- **`config/franchises/gta.json`:** 2D/3D/HD continuities, games, protected names (blocked in
  image prompts) and Rockstar's posting policy. No release dates are stored; verify them per episode.
- **`modules/gaming/research.py`:** the dossier. Sources (game, official, secondary, community)
  and claim-level evidence, labelled confirmed canon, interpretation, fan theory or speculation.
  Also continuity mixing, spoiler level, timeline conflicts and unverified sources.
- **`modules/gaming/script_engine.py`:** outline, then the script one chapter at a time
  (resumable). Every factual passage must cite dossier claims. Theories must be hedged. Text
  copied from a source excerpt, stock AI phrases and repetition are caught.
- **`modules/gaming/provenance.py`:** source and rights for every asset. "Unverified" blocks
  publishing; "publisher_policy" and "fair_use_claim" need the owner's sign-off.
- **Renderer:** still images and user video clips mixed in a scene, per-image motion (chapter
  cards stay still), an optional licensed ambient bed that ducks under the narration, and
  chapter times taken from the actual render.
- **`--dry-run`:** fixtures, placeholder images and silent timed narration. The whole pipeline
  runs offline for $0 (see `tests/fixtures/gaming_synthetic/`).

## Cost of the pilot (22.5 min target)
About 3,150 words, 113 visual slots (105 generated after chapter cards), 18,900 narration characters.
- Images: about $5.90, plus about $1.20 if 1 in 5 is redone.
- Narration: $1.90–5.70, depending on your ElevenLabs plan's rate.
- Script writing: about $0.50 typical, $1.70 worst case.
- **Total: about $9 typical, about $14.50 conservative.**

That's over the default per-run ($5) and per-episode ($10) limits. Raise them yourself with
`--max-run-cost` / `--episode-budget`; the pipeline never raises them. Using your own gameplay
footage in place of some illustrations lowers the image cost.
