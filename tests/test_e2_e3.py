"""Offline tests for E2/E3 logic (no TMDB network)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Set DB before ott_brain modules connect
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["OTT_BRAIN_DB_PATH"] = _tmp.name

from ott_brain.availability.base import ProviderOffer  # noqa: E402
from ott_brain.database import connect, ensure_database  # noqa: E402
from ott_brain.feedback import add_feedback, get_rejected_movie_ids  # noqa: E402
from ott_brain.filters import filter_candidate_ids  # noqa: E402
from ott_brain.providers_service import sync_providers  # noqa: E402
from ott_brain.subscriptions import normalize_provider_name, set_subscribed_slugs  # noqa: E402
from ott_brain.watch_history import (  # noqa: E402
    get_watched_movie_ids,
    mark_watched,
    parse_scraped_watchlist_text,
    parse_watchlist_text,
)


class E2E3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_database(Path(_tmp.name))

    def setUp(self) -> None:
        with connect() as conn:
            for table in ("feedback", "watch_history", "providers", "movies", "preferences"):
                conn.execute(f"DELETE FROM {table}")

    def test_normalize_provider_names(self) -> None:
        self.assertEqual(normalize_provider_name("Netflix"), "netflix")
        self.assertEqual(normalize_provider_name("Amazon Prime Video"), "prime")

    def test_provider_cache_and_subscription_filter(self) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO movies (tmdb_id, title) VALUES (1, 'A'), (2, 'B')
                """
            )
        set_subscribed_slugs({"netflix"})

        class FakeProvider:
            def fetch_india_providers(self, tmdb_id: int) -> list[ProviderOffer]:
                if tmdb_id == 1:
                    return [ProviderOffer("Netflix", "flatrate", "http://x")]
                return [ProviderOffer("ZEE5", "flatrate", None)]

        with patch("ott_brain.providers_service.get_availability_provider", lambda: FakeProvider()):
            sync_providers(1, force=True)
            sync_providers(2, force=True)

        filtered = filter_candidate_ids([1, 2])
        self.assertEqual(filtered, [1])

    def test_parse_scraped_watchlist(self) -> None:
        raw = "GoodFellas\n (1990), The\nBridge on the River Kwai\n (1957),"
        entries = parse_scraped_watchlist_text(raw)
        self.assertEqual(
            entries,
            [("GoodFellas", 1990), ("The Bridge on the River Kwai", 1957)],
        )
        cleaned = "GoodFellas (1990)\nThe Bridge on the River Kwai (1957)\n"
        self.assertEqual(
            parse_watchlist_text(cleaned),
            [("GoodFellas", 1990), ("The Bridge on the River Kwai", 1957)],
        )

    def test_watched_and_rejected_excluded(self) -> None:
        with connect() as conn:
            conn.execute("INSERT INTO movies (tmdb_id, title) VALUES (10, 'W'), (11, 'R')")
            conn.execute(
                """
                INSERT INTO providers (movie_id, country, provider, offer_type, checked_at)
                VALUES (10, 'IN', 'Netflix', 'flatrate', '2026-01-01T00:00:00+00:00'),
                       (11, 'IN', 'Netflix', 'flatrate', '2026-01-01T00:00:00+00:00')
                """
            )
        set_subscribed_slugs({"netflix"})
        mark_watched(10)
        add_feedback(11, "NOT_INTERESTED")
        self.assertIn(10, get_watched_movie_ids())
        self.assertIn(11, get_rejected_movie_ids())
        self.assertEqual(filter_candidate_ids([10, 11]), [])


if __name__ == "__main__":
    unittest.main()
