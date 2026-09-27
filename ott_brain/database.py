from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ott_brain.config import database_path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS movies (
    tmdb_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER,
    overview TEXT,
    genres TEXT,
    languages TEXT,
    runtime INTEGER,
    rating REAL,
    keywords TEXT,
    poster_path TEXT,
    embedding BLOB,
    metadata_synced_at TEXT
);

CREATE TABLE IF NOT EXISTS watch_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL REFERENCES movies(tmdb_id),
    watched_at TEXT NOT NULL,
    rating REAL,
    liked INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL REFERENCES movies(tmdb_id),
    type TEXT NOT NULL CHECK (
        type IN (
            'LOVED', 'LIKED', 'NOT_INTERESTED', 'TOO_SLOW',
            'TOO_VIOLENT', 'ALREADY_SEEN'
        )
    ),
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL REFERENCES movies(tmdb_id),
    country TEXT NOT NULL,
    provider TEXT NOT NULL,
    offer_type TEXT,
    url TEXT,
    checked_at TEXT NOT NULL,
    UNIQUE(movie_id, country, provider, offer_type)
);

CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_database(path: Path | None = None) -> Path:
    db_path = path or database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    return db_path


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or database_path()
    ensure_database(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)
