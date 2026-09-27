from __future__ import annotations

import re
from dataclasses import dataclass

from ott_brain.preferences import OTT_SUBSCRIPTIONS, get_json_preference, set_json_preference

INDIAN_OTT_SERVICES: tuple[tuple[str, str], ...] = (
    ("netflix", "Netflix"),
    ("prime", "Prime Video"),
    ("jiohotstar", "JioHotstar"),
    ("sonyliv", "Sony LIV"),
    ("zee5", "ZEE5"),
    ("aha", "Aha"),
    ("sunnxt", "Sun NXT"),
)

_SLUG_BY_LABEL = {label.lower(): slug for slug, label in INDIAN_OTT_SERVICES}
_TMDB_ALIASES: dict[str, str] = {
    "netflix": "netflix",
    "amazon prime video": "prime",
    "prime video": "prime",
    "hotstar": "jiohotstar",
    "jio hotstar": "jiohotstar",
    "disney+ hotstar": "jiohotstar",
    "sony liv": "sonyliv",
    "zee5": "zee5",
    "aha": "aha",
    "sun nxt": "sunnxt",
}


@dataclass(frozen=True)
class OttService:
    slug: str
    label: str


def all_services() -> list[OttService]:
    return [OttService(slug, label) for slug, label in INDIAN_OTT_SERVICES]


def get_subscribed_slugs() -> set[str]:
    raw = get_json_preference(OTT_SUBSCRIPTIONS, [])
    if not isinstance(raw, list):
        return set()
    return {str(s) for s in raw}


def set_subscribed_slugs(slugs: set[str]) -> None:
    valid = {slug for slug, _ in INDIAN_OTT_SERVICES}
    set_json_preference(OTT_SUBSCRIPTIONS, sorted(slugs & valid))


def normalize_provider_name(tmdb_name: str) -> str | None:
    key = re.sub(r"\s+", " ", tmdb_name.strip().lower())
    if key in _TMDB_ALIASES:
        return _TMDB_ALIASES[key]
    if key in _SLUG_BY_LABEL:
        return _SLUG_BY_LABEL[key]
    for slug, label in INDIAN_OTT_SERVICES:
        if label.lower() in key or key in label.lower():
            return slug
    return None
