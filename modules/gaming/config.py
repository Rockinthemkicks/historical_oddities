"""
Production modes, franchise data and per-documentary production settings.

A gaming-lore documentary lives in its own folder with a production.json:

  {
    "mode": "gaming-lore",
    "title": "The Dark History of Vice City",
    "franchise": "gta",                    -> config/franchises/gta.json
    "games": ["gtavc", "gtavcs"],          -> ids from the franchise file
    "continuity": "3D",                    -> one continuity, or a list to compare
                                              several (every claim still names one)
    "documentary_format": "fictional investigative history",
    "target_minutes": [20, 25],            -> a number or a [min, max] range
    "spoiler_level": "light",              -> none | light | full
    "voice_id": null,                      -> optional; else ELEVENLABS_VOICE_ID
    "overrides": {}                        -> optional mode-setting overrides
  }

Everything the pipeline produces for that documentary goes in the same
folder (research.json, outline.json, chapters/, script.json, assets/, out/).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODES = ("historical", "gaming-lore")
SPOILER_LEVELS = ("none", "light", "full")
# A claim's spoiler rating vs what each production level allows.
SPOILER_ALLOWED = {"none": {"none"}, "light": {"none", "minor"}, "full": {"none", "minor", "major"}}


class ConfigError(ValueError):
    pass


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_mode(mode):
    if mode not in MODES:
        raise ConfigError(f"Unknown mode {mode!r}; use one of {MODES}")
    return _load(os.path.join(ROOT, "config", "modes", f"{mode}.json"))


def load_franchise(franchise_id, path=None):
    path = path or os.path.join(ROOT, "config", "franchises", f"{franchise_id}.json")
    if not os.path.exists(path):
        raise ConfigError(f"No franchise file for {franchise_id!r} (expected {path})")
    data = _load(path)
    for key in ("franchise_id", "name", "continuities", "games"):
        if key not in data:
            raise ConfigError(f"{path} is missing {key!r}")
    for g in data["games"]:
        if g["continuity"] not in data["continuities"]:
            raise ConfigError(f"Game {g['id']} has unknown continuity {g['continuity']!r}")
    return data


def target_range(target_minutes):
    if isinstance(target_minutes, (int, float)):
        return float(target_minutes), float(target_minutes)
    lo, hi = target_minutes
    if lo > hi:
        raise ConfigError("target_minutes range is backwards")
    return float(lo), float(hi)


def load_production(path):
    """Loads and validates a production.json; returns it with resolved settings added."""
    prod = _load(path)
    prod["_dir"] = os.path.dirname(os.path.abspath(path))
    if prod.get("mode") != "gaming-lore":
        raise ConfigError("production.json must have \"mode\": \"gaming-lore\"")
    for key in ("title", "franchise", "continuity", "target_minutes", "spoiler_level"):
        if key not in prod:
            raise ConfigError(f"production.json is missing {key!r}")
    mode = load_mode("gaming-lore")
    settings = {**mode, **prod.get("overrides", {})}
    franchise_file = prod.get("franchise_file")
    if franchise_file:  # a franchise defined next to the production (used by test fixtures)
        franchise_file = os.path.join(prod["_dir"], franchise_file)
    franchise = load_franchise(prod["franchise"], franchise_file)

    continuities = prod["continuity"] if isinstance(prod["continuity"], list) else [prod["continuity"]]
    for c in continuities:
        if c not in franchise["continuities"]:
            raise ConfigError(f"continuity {c!r} isn't one of "
                              f"{sorted(franchise['continuities'])} for {franchise['name']}")
    prod["_continuities"] = continuities
    game_ids = {g["id"]: g for g in franchise["games"]}
    for gid in prod.get("games", []):
        if gid not in game_ids:
            raise ConfigError(f"unknown game id {gid!r} for {franchise['name']}")
        if game_ids[gid]["continuity"] not in continuities:
            raise ConfigError(f"{game_ids[gid]['title']} is in the {game_ids[gid]['continuity']} "
                              f"universe, which this production doesn't cover ({continuities}). "
                              f"Add that continuity to compare them explicitly, or drop the game")
    if prod["spoiler_level"] not in SPOILER_LEVELS:
        raise ConfigError(f"spoiler_level must be one of {SPOILER_LEVELS}")
    lo, hi = target_range(prod["target_minutes"])
    mlo, mhi = settings["target_minutes_range"]
    if lo < mlo or hi > mhi:
        raise ConfigError(f"target_minutes {prod['target_minutes']} is outside the {mlo}-{mhi} "
                          f"minute range for gaming-lore documentaries")
    prod["_settings"] = settings
    prod["_franchise"] = franchise
    return prod


def word_budget(target_minutes, wpm=140, wpm_range=(130, 150)):
    """Planning estimate of narration words for a target duration (range-aware)."""
    lo, hi = target_range(target_minutes)
    mid = (lo + hi) / 2
    return {
        "target_words": int(round(mid * wpm)),
        "min_words": int(round(lo * wpm_range[0])),
        "max_words": int(round(hi * wpm_range[1])),
        "wpm": wpm,
        "minutes": [lo, hi],
    }
