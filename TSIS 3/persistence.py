"""
persistence.py
--------------
Tiny JSON-backed storage for settings and the leaderboard.

We keep file paths next to the script (not the cwd) so running the game
from anywhere still finds the same data files.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
LEADERBOARD_PATH = os.path.join(BASE_DIR, "leaderboard.json")

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "red",      # one of: red, blue, green, yellow, white
    "difficulty": "normal",  # one of: easy, normal, hard
}

MAX_LEADERBOARD_ENTRIES = 10


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def load_settings():
    """Return a dict of settings, falling back to defaults if the file
    is missing or corrupt. Missing keys are filled in from defaults."""
    if not os.path.exists(SETTINGS_PATH):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # merge — newer versions of the game may add keys that old saves lack
        merged = dict(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError as e:
        print(f"[settings] save failed: {e}")


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
def load_leaderboard():
    """Return a list of entries: [{name, score, distance, coins}, ...]
    sorted by score (desc). Empty list if the file is missing/corrupt."""
    if not os.path.exists(LEADERBOARD_PATH):
        return []
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        # filter out malformed entries defensively — old files might not have all fields
        clean = []
        for e in data:
            if not isinstance(e, dict):
                continue
            clean.append({
                "name": str(e.get("name", "Player"))[:12],
                "score": int(e.get("score", 0)),
                "distance": int(e.get("distance", 0)),
                "coins": int(e.get("coins", 0)),
            })
        clean.sort(key=lambda r: r["score"], reverse=True)
        return clean[:MAX_LEADERBOARD_ENTRIES]
    except (json.JSONDecodeError, OSError, ValueError):
        return []


def save_leaderboard(entries):
    try:
        with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
            json.dump(entries[:MAX_LEADERBOARD_ENTRIES], f, indent=2)
    except OSError as e:
        print(f"[leaderboard] save failed: {e}")


def add_score(name, score, distance, coins):
    """Insert a new run, keep top 10, persist, return updated list."""
    entries = load_leaderboard()
    entries.append({
        "name": (name or "Player")[:12],
        "score": int(score),
        "distance": int(distance),
        "coins": int(coins),
    })
    entries.sort(key=lambda r: r["score"], reverse=True)
    entries = entries[:MAX_LEADERBOARD_ENTRIES]
    save_leaderboard(entries)
    return entries
