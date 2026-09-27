from __future__ import annotations

from ott_brain.availability.base import AvailabilityProvider, ProviderOffer
from ott_brain.tmdb import TmdbError, fetch_watch_providers


class TmdbAvailabilityProvider(AvailabilityProvider):
    def fetch_india_providers(self, tmdb_id: int) -> list[ProviderOffer]:
        try:
            data = fetch_watch_providers(tmdb_id)
        except TmdbError:
            raise
        offers: list[ProviderOffer] = []
        for offer_type, entries in data.items():
            if offer_type == "link":
                continue
            if not isinstance(entries, list):
                continue
            for entry in entries:
                name = entry.get("provider_name")
                if not name:
                    continue
                offers.append(
                    ProviderOffer(
                        provider_name=str(name),
                        offer_type=str(offer_type),
                        url=data.get("link"),
                    )
                )
        return offers
