import json
import os
from typing import Dict, List, Any

HISTORY_DIR = "src/data/history"
MAX_HISTORY_SIZE = 100000


def _get_history_filepath(user_id: int) -> str:
    """Constructs the file path for a user's history file."""
    return os.path.join(HISTORY_DIR, f"{user_id}.json")


def load_history(user_id: int) -> List[Dict[str, Any]]:
    """Loads the history for a given user."""
    filepath = _get_history_filepath(user_id)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(user_id: int, history: List[Dict[str, Any]]) -> None:
    """Saves the history for a given user."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    filepath = _get_history_filepath(user_id)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


def add_to_history(user_id: int, url: str, summary: str, hashtags: List[str]) -> None:
    """Adds a new entry to the user's history, avoiding duplicates."""
    history = load_history(user_id)

    # Check for duplicate URLs
    if any(entry.get("url") == url for entry in history):
        return

    new_entry = {
        "url": url,
        "summary": summary,
        "hashtags": hashtags,
    }

    # Add new entry at the beginning (FIFO: most recent first)
    history.insert(0, new_entry)

    # Enforce history size limit - remove oldest entries if limit exceeded
    if len(history) > MAX_HISTORY_SIZE:
        # Keep only the most recent MAX_HISTORY_SIZE entries
        # This removes the oldest entries from the end of the list
        history = history[:MAX_HISTORY_SIZE]

    save_history(user_id, history)
