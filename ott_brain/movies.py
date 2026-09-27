from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from ott_brain.config import movie_metadata_ttl_hours
from ott_brain.database import connect, utc_now_iso
from ott_brain.tmdb import TmdbError, fetch_movie_details, normalize_movie_row


def _parse_synced_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def metadata_is_fresh(synced_at: str | None, ttl_hours: float) -> bool:
    synced = _parse_synced_at(synced_at)
    if synced is None:
        return False
    if synced.tzinfo is None:
        synced = synced.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - synced < timedelta(hours=ttl_hours)


def upsert_movie_from_details(details: dict[str, Any], *, synced_at: str | None = None) -> None:
    row = normalize_movie_row(details)
    synced = synced_at or utc_now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO movies (
                tmdb_id, title, year, overview, genres, languages, runtime,
                rating, keywords, poster_path, metadata_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tmdb_id) DO UPDATE SET
                title = excluded.title,
                year = excluded.year,
                overview = excluded.overview,
                genres = excluded.genres,
                languages = excluded.languages,
                runtime = excluded.runtime,
                rating = excluded.rating,
                keywords = excluded.keywords,
                poster_path = excluded.poster_path,
                metadata_synced_at = excluded.metadata_synced_at
            """,
            (
                row["tmdb_id"],
                row["title"],
                row["year"],
                row["overview"],
                json.dumps(row["genres"]),
                json.dumps(row["languages"]),
                row["runtime"],
                row["rating"],
                json.dumps(row["keywords"]),
                row["poster_path"],
                synced,
            ),
        )


def sync_movie_metadata(tmdb_id: int, *, force: bool = False) -> dict[str, Any]:
    ttl = movie_metadata_ttl_hours()
    with connect() as conn:
        existing = conn.execute(
            "SELECT metadata_synced_at FROM movies WHERE tmdb_id = ?",
            (tmdb_id,),
        ).fetchone()

    if not force and existing and metadata_is_fresh(existing["metadata_synced_at"], ttl):
        return get_movie(tmdb_id) or {}

    try:
        details = fetch_movie_details(tmdb_id)
    except TmdbError:
        raise
    upsert_movie_from_details(details)
    return get_movie(tmdb_id) or {}


def get_movie(tmdb_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM movies WHERE tmdb_id = ?", (tmdb_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    for field in ("genres", "languages", "keywords"):
        raw = data.get(field)
        if raw:
            try:
                data[field] = json.loads(raw)
            except json.JSONDecodeError:
                pass
    return data
