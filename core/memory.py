"""
core/memory.py
==============
This is SUNDAY's "long-term memory" for shortcuts - things like
"youtube" -> open youtube.com directly, learned from how you actually
use the assistant over time.

WHY SQLITE:
  - It's built into Python (the `sqlite3` module) - no extra install needed.
  - It's just a single file on disk (memory.db) - easy to inspect or delete.
  - It's more than fast enough for the small amount of data stored here.

If you've never used a database before, think of a SQLite table like an
Excel sheet that your code can read and write to directly, one row at a time.
"""

import sqlite3
import json
from config import MEMORY_DB_PATH

# check_same_thread=False is required because SUNDAY accesses this database
# from more than one thread (the wake-word thread and the UI thread).
_connection = sqlite3.connect(MEMORY_DB_PATH, check_same_thread=False)


def _init_table():
    """Creates the 'shortcuts' table the first time SUNDAY ever runs."""
    _connection.execute("""
        CREATE TABLE IF NOT EXISTS shortcuts (
            phrase      TEXT PRIMARY KEY,   -- what you said, e.g. "youtube"
            action_json TEXT NOT NULL,      -- the JSON action to run for it
            hits        INTEGER DEFAULT 1   -- how many times you've used it
        )
    """)
    _connection.commit()


def seed_defaults():
    """
    Pre-loads a few obvious shortcuts so SUNDAY is useful immediately,
    without having to "learn" the basics first. Add your own favourite
    sites here if you like.
    """
    _init_table()
    defaults = {
        "youtube": {"action": "open_url", "target": "https://www.youtube.com"},
        "gmail": {"action": "open_url", "target": "https://mail.google.com"},
        "github": {"action": "open_url", "target": "https://github.com"},
    }
    for phrase, action in defaults.items():
        _connection.execute(
            "INSERT OR IGNORE INTO shortcuts (phrase, action_json) VALUES (?, ?)",
            (phrase, json.dumps(action)),
        )
    _connection.commit()


def lookup(phrase: str):
    """
    Checks whether we already have a remembered action for this EXACT
    phrase. Returns a dict (the action) if found, otherwise None.
    """
    row = _connection.execute(
        "SELECT action_json FROM shortcuts WHERE phrase = ?",
        (phrase.lower().strip(),),
    ).fetchone()
    return json.loads(row[0]) if row else None


def remember(phrase: str, action: dict):
    """
    Saves (or reinforces) a phrase -> action mapping.
    If the phrase already exists, we just bump its "hits" counter up by 1,
    so frequently used shortcuts naturally rise to the top later.
    """
    _connection.execute(
        """
        INSERT INTO shortcuts (phrase, action_json, hits)
        VALUES (?, ?, 1)
        ON CONFLICT(phrase) DO UPDATE SET hits = hits + 1
        """,
        (phrase.lower().strip(), json.dumps(action)),
    )
    _connection.commit()


def context_string(limit: int = 20) -> str:
    """
    Builds a short text summary of your most-used shortcuts, ranked by how
    often you use them. This gets inserted into the LLM's system prompt so
    it can reuse what you've already taught it instead of guessing a URL.
    """
    rows = _connection.execute(
        "SELECT phrase, action_json FROM shortcuts ORDER BY hits DESC LIMIT ?",
        (limit,),
    ).fetchall()
    if not rows:
        return "(no shortcuts learned yet)"
    return "\n".join(f"{phrase} -> {action}" for phrase, action in rows)
