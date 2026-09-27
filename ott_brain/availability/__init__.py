from __future__ import annotations

import os

from ott_brain.availability.base import AvailabilityProvider, ProviderOffer
from ott_brain.availability.tmdb_provider import TmdbAvailabilityProvider
from ott_brain.availability.watchmode import WatchmodeAvailabilityProvider

__all__ = [
    "AvailabilityProvider",
    "ProviderOffer",
    "get_availability_provider",
]


def get_availability_provider() -> AvailabilityProvider:
    backend = os.getenv("AVAILABILITY_BACKEND", "tmdb").strip().lower()
    if backend == "watchmode":
        return WatchmodeAvailabilityProvider()
    return TmdbAvailabilityProvider()
