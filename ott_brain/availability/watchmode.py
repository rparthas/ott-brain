from __future__ import annotations

from ott_brain.availability.base import AvailabilityProvider, ProviderOffer


class WatchmodeAvailabilityProvider(AvailabilityProvider):
    """Stub — enable when TMDB coverage is insufficient (see README)."""

    def fetch_india_providers(self, tmdb_id: int) -> list[ProviderOffer]:
        raise NotImplementedError(
            "Watchmode provider is not enabled. Set AVAILABILITY_BACKEND=tmdb (default)."
        )
