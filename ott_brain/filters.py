from __future__ import annotations

from ott_brain.feedback import get_rejected_movie_ids
from ott_brain.providers_service import movie_provider_slugs, sync_providers
from ott_brain.subscriptions import get_subscribed_slugs
from ott_brain.watch_history import get_watched_movie_ids


def movie_available_on_user_subscriptions(tmdb_id: int, *, refresh_providers: bool = False) -> bool:
    subscribed = get_subscribed_slugs()
    if not subscribed:
        return False
    if refresh_providers:
        sync_providers(tmdb_id)
    slugs = movie_provider_slugs(tmdb_id)
    return bool(slugs & subscribed)


def filter_candidate_ids(
    tmdb_ids: list[int],
    *,
    refresh_providers: bool = False,
) -> list[int]:
    """Hard filters for recommendation candidates (E2-04, E3-02, E3-05)."""
    watched = get_watched_movie_ids()
    rejected = get_rejected_movie_ids()
    subscribed = get_subscribed_slugs()
    out: list[int] = []
    for mid in tmdb_ids:
        if mid in watched or mid in rejected:
            continue
        if not subscribed:
            continue
        if refresh_providers:
            sync_providers(mid)
        if movie_provider_slugs(mid) & subscribed:
            out.append(mid)
    return out
