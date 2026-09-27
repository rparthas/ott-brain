from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ott_brain.availability import get_availability_provider
from ott_brain.config import provider_cache_ttl_hours
from ott_brain.database import connect, utc_now_iso
from ott_brain.subscriptions import normalize_provider_name

COUNTRY_IN = "IN"


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def cache_is_fresh(checked_at: str | None, ttl_hours: float) -> bool:
    synced = _parse_iso(checked_at)
    if synced is None:
        return False
    return datetime.now(timezone.utc) - synced < timedelta(hours=ttl_hours)


def get_cached_providers(tmdb_id: int, country: str = COUNTRY_IN) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT provider, offer_type, url, checked_at
            FROM providers
            WHERE movie_id = ? AND country = ?
            ORDER BY provider
            """,
            (tmdb_id, country),
        ).fetchall()
    return [dict(r) for r in rows]


def providers_last_checked(tmdb_id: int, country: str = COUNTRY_IN) -> str | None:
    rows = get_cached_providers(tmdb_id, country)
    if not rows:
        return None
    return max(r["checked_at"] for r in rows)


def sync_providers(tmdb_id: int, *, force: bool = False) -> list[dict]:
    ttl = provider_cache_ttl_hours()
    last = providers_last_checked(tmdb_id)
    if not force and last and cache_is_fresh(last, ttl):
        return get_cached_providers(tmdb_id)

    provider = get_availability_provider()
    offers = provider.fetch_india_providers(tmdb_id)
    checked = utc_now_iso()
    with connect() as conn:
        conn.execute(
            "DELETE FROM providers WHERE movie_id = ? AND country = ?",
            (tmdb_id, COUNTRY_IN),
        )
        for offer in offers:
            conn.execute(
                """
                INSERT INTO providers (
                    movie_id, country, provider, offer_type, url, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(movie_id, country, provider, offer_type) DO UPDATE SET
                    url = excluded.url,
                    checked_at = excluded.checked_at
                """,
                (
                    tmdb_id,
                    COUNTRY_IN,
                    offer.provider_name,
                    offer.offer_type,
                    offer.url,
                    checked,
                ),
            )
    return get_cached_providers(tmdb_id)


def movie_provider_slugs(tmdb_id: int) -> set[str]:
    rows = get_cached_providers(tmdb_id)
    slugs: set[str] = set()
    for row in rows:
        slug = normalize_provider_name(row["provider"])
        if slug:
            slugs.add(slug)
    return slugs
