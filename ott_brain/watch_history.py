from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from ott_brain.database import connect, utc_now_iso
from ott_brain.feedback import add_feedback
from ott_brain.movies import sync_movie_metadata
from ott_brain.tmdb import MovieSearchResult, TmdbError, search_movies

_SCRAPED_YEAR_RE = re.compile(r"(.+?)\s*\((\d{4})\)")
_LINE_YEAR_RE = re.compile(r"^(.*?)\s*\((\d{4})\)\s*$")


def _clean_import_title(title: str) -> str:
    return title.strip().lstrip(",").strip()


def parse_import_line(line: str) -> tuple[str, int | None]:
    line = line.strip()
    if not line:
        return "", None
    match = _LINE_YEAR_RE.match(line)
    if match:
        return _clean_import_title(match.group(1)), int(match.group(2))
    return _clean_import_title(line), None


def parse_scraped_watchlist_text(text: str) -> list[tuple[str, int]]:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if not collapsed:
        return []
    entries: list[tuple[str, int]] = []
    for raw_title, year_s in _SCRAPED_YEAR_RE.findall(collapsed):
        title = _clean_import_title(raw_title)
        if title:
            entries.append((title, int(year_s)))
    return entries


def parse_watchlist_text(text: str) -> list[tuple[str, int | None]]:
    """Parse bulk watchlist text (one title per line or scraped multi-line export)."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    parsed_lines = [parse_import_line(line) for line in lines]
    with_year = sum(1 for title, year in parsed_lines if title and year is not None)
    if with_year >= max(1, len(lines) // 2):
        return [(title, year) for title, year in parsed_lines if title]
    return [(title, year) for title, year in parse_scraped_watchlist_text(text)]


def _pick_search_result(
    hits: list[MovieSearchResult],
    *,
    title: str,
    year: int | None,
) -> MovieSearchResult | None:
    if not hits:
        return None
    if year is not None:
        same_year = [hit for hit in hits if hit.year == year]
        if len(same_year) == 1:
            return same_year[0]
        if len(same_year) > 1:
            title_key = title.casefold()
            exact = [hit for hit in same_year if hit.title.casefold() == title_key]
            if len(exact) == 1:
                return exact[0]
        close_year = [
            hit
            for hit in hits
            if hit.year is not None and abs(hit.year - year) <= 1
        ]
        if len(close_year) == 1:
            return close_year[0]
    if len(hits) == 1:
        return hits[0]
    return None


def _search_movies_with_retry(
    query: str,
    *,
    year: int | None = None,
    attempts: int = 4,
) -> list[MovieSearchResult]:
    delay = 0.5
    for attempt in range(attempts):
        try:
            return search_movies(query, year=year)
        except TmdbError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)
            delay *= 2
    return []


def _resolve_movie_search(title: str, year: int | None) -> MovieSearchResult | None:
    hits = _search_movies_with_retry(title)
    hit = _pick_search_result(hits, title=title, year=year)
    if hit is not None:
        return hit
    if year is None:
        return None
    narrowed = _search_movies_with_retry(title, year=year)
    return _pick_search_result(narrowed, title=title, year=year)


def _ensure_movie_row(
    movie_id: int,
    *,
    title: str | None = None,
    year: int | None = None,
) -> None:
    with connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM movies WHERE tmdb_id = ?",
            (movie_id,),
        ).fetchone()
    if exists is not None:
        return
    delay = 0.5
    for attempt in range(4):
        try:
            sync_movie_metadata(movie_id, force=False)
            return
        except TmdbError:
            if attempt == 4 - 1:
                break
            time.sleep(delay)
            delay *= 2
    if not title:
        raise TmdbError(f"Could not load TMDB metadata for movie id {movie_id}")
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO movies (tmdb_id, title, year) VALUES (?, ?, ?)",
            (movie_id, title, year),
        )


def get_watched_movie_ids() -> set[int]:
    with connect() as conn:
        rows = conn.execute("SELECT DISTINCT movie_id FROM watch_history").fetchall()
    return {int(r["movie_id"]) for r in rows}


def mark_watched(
    movie_id: int,
    *,
    rating: float | None = None,
    liked: bool | None = None,
    loved: bool = False,
    title: str | None = None,
    year: int | None = None,
) -> None:
    _ensure_movie_row(movie_id, title=title, year=year)
    watched_at = utc_now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO watch_history (movie_id, watched_at, rating, liked, notes)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (
                movie_id,
                watched_at,
                rating,
                1 if liked else (0 if liked is False else None),
            ),
        )
    if loved:
        add_feedback(movie_id, "LOVED")
    elif liked:
        add_feedback(movie_id, "LIKED")


def update_watch_entry(
    movie_id: int,
    *,
    rating: float | None = None,
    liked: bool | None = None,
) -> None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT id FROM watch_history
            WHERE movie_id = ?
            ORDER BY watched_at DESC
            LIMIT 1
            """,
            (movie_id,),
        ).fetchone()
        if row is None:
            mark_watched(movie_id, rating=rating, liked=liked)
            return
        conn.execute(
            """
            UPDATE watch_history
            SET rating = COALESCE(?, rating),
                liked = COALESCE(?, liked)
            WHERE id = ?
            """,
            (
                rating,
                1 if liked else (0 if liked is False else None),
                row["id"],
            ),
        )


def list_watch_history(limit: int = 200) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT h.movie_id, h.watched_at, h.rating, h.liked, m.title, m.year
            FROM watch_history h
            JOIN movies m ON m.tmdb_id = h.movie_id
            ORDER BY h.watched_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


@dataclass
class BulkImportLine:
    line: str
    status: str
    tmdb_id: int | None = None
    title: str | None = None
    candidates: list[dict] = field(default_factory=list)


@dataclass
class BulkImportResult:
    resolved: list[BulkImportLine]
    ambiguous: list[BulkImportLine]
    failed: list[BulkImportLine]


def bulk_import_titles(lines: list[str]) -> BulkImportResult:
    entries = parse_watchlist_text("\n".join(lines))
    return bulk_import_entries(entries)


def bulk_import_entries(
    entries: list[tuple[str, int | None]],
    *,
    skip_movie_ids: set[int] | None = None,
    pause_seconds: float = 0.0,
) -> BulkImportResult:
    resolved: list[BulkImportLine] = []
    ambiguous: list[BulkImportLine] = []
    failed: list[BulkImportLine] = []
    skip_ids = skip_movie_ids or set()
    already_watched = get_watched_movie_ids()

    for title, year in entries:
        display = f"{title} ({year})" if year is not None else title
        try:
            hit = _resolve_movie_search(title, year)
        except TmdbError:
            failed.append(BulkImportLine(line=display, status="failed"))
            if pause_seconds:
                time.sleep(pause_seconds)
            continue

        if hit is None:
            try:
                hits = _search_movies_with_retry(title)
            except TmdbError:
                hits = []
            if not hits:
                failed.append(BulkImportLine(line=display, status="failed"))
            else:
                ambiguous.append(
                    BulkImportLine(
                        line=display,
                        status="ambiguous",
                        candidates=[
                            {"tmdb_id": h.tmdb_id, "title": h.title, "year": h.year}
                            for h in hits[:5]
                        ],
                    )
                )
            if pause_seconds:
                time.sleep(pause_seconds)
            continue

        if hit.tmdb_id in skip_ids or hit.tmdb_id in already_watched:
            resolved.append(
                BulkImportLine(
                    line=display,
                    status="skipped",
                    tmdb_id=hit.tmdb_id,
                    title=hit.title,
                )
            )
            if pause_seconds:
                time.sleep(pause_seconds)
            continue

        try:
            mark_watched(
                hit.tmdb_id,
                title=hit.title or title,
                year=hit.year if hit.year is not None else year,
            )
        except TmdbError:
            failed.append(BulkImportLine(line=display, status="failed"))
            if pause_seconds:
                time.sleep(pause_seconds)
            continue

        already_watched.add(hit.tmdb_id)
        resolved.append(
            BulkImportLine(
                line=display,
                status="resolved",
                tmdb_id=hit.tmdb_id,
                title=hit.title,
            )
        )
        if pause_seconds:
            time.sleep(pause_seconds)

    return BulkImportResult(resolved=resolved, ambiguous=ambiguous, failed=failed)


def import_watchlist_file(
    path: Path,
    *,
    pause_seconds: float = 0.15,
) -> BulkImportResult:
    text = path.read_text(encoding="utf-8")
    entries = parse_watchlist_text(text)
    return bulk_import_entries(entries, pause_seconds=pause_seconds)
