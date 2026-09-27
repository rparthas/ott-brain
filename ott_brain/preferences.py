from __future__ import annotations

import json
from typing import Any

from ott_brain.database import connect, utc_now_iso

ONBOARDING_COMPLETE = "onboarding_complete"
OTT_SUBSCRIPTIONS = "ott_subscriptions"


def get_preference(key: str, default: str | None = None) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM preferences WHERE key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return default
    return row["value"]


def set_preference(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO preferences (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, utc_now_iso()),
        )


def get_json_preference(key: str, default: Any) -> Any:
    raw = get_preference(key)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def set_json_preference(key: str, value: Any) -> None:
    set_preference(key, json.dumps(value))
