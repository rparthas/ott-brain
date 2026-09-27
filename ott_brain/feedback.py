from __future__ import annotations

from ott_brain.database import connect, utc_now_iso

REJECTION_TYPES = frozenset(
    {
        "NOT_INTERESTED",
        "TOO_SLOW",
        "TOO_VIOLENT",
        "ALREADY_SEEN",
    }
)


def add_feedback(movie_id: int, feedback_type: str, reason: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO feedback (movie_id, type, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (movie_id, feedback_type, reason, utc_now_iso()),
        )


def get_rejected_movie_ids() -> set[int]:
    placeholders = ",".join("?" for _ in REJECTION_TYPES)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT DISTINCT movie_id FROM feedback
            WHERE type IN ({placeholders})
            """,
            tuple(REJECTION_TYPES),
        ).fetchall()
    return {int(r["movie_id"]) for r in rows}


def list_rejections(limit: int = 100) -> list[dict]:
    placeholders = ",".join("?" for _ in REJECTION_TYPES)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT f.movie_id, f.type, f.reason, f.created_at, m.title, m.year
            FROM feedback f
            JOIN movies m ON m.tmdb_id = f.movie_id
            WHERE f.type IN ({placeholders})
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (*REJECTION_TYPES, limit),
        ).fetchall()
    return [dict(r) for r in rows]
