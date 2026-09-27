from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderOffer:
    provider_name: str
    offer_type: str
    url: str | None


class AvailabilityProvider(ABC):
    """Pluggable availability source (TMDB default; Watchmode optional)."""

    @abstractmethod
    def fetch_india_providers(self, tmdb_id: int) -> list[ProviderOffer]:
        raise NotImplementedError
