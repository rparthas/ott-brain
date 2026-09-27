from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "ott_brain.db"


def database_path() -> Path:
    raw = os.getenv("OTT_BRAIN_DB_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return DEFAULT_DB_PATH


def tmdb_api_key() -> str:
    key = os.getenv("TMDB_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "TMDB_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return key


def movie_metadata_ttl_hours() -> float:
    raw = os.getenv("MOVIE_METADATA_TTL_HOURS", "168").strip()
    try:
        return float(raw)
    except ValueError:
        return 168.0
