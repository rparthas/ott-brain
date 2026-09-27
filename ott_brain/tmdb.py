from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from ott_brain.config import tmdb_api_key

TMDB_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w200"


class TmdbError(Exception):
    """TMDB request failed."""


@dataclass(frozen=True)
class MovieSearchResult:
    tmdb_id: int
    title: str
    year: int | None
    poster_path: str | None
    overview: str | None


def poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{POSTER_BASE}{poster_path}"


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = dict(params or {})
    params["api_key"] = tmdb_api_key()
    try:
        response = requests.get(f"{TMDB_BASE}{path}", params=params, timeout=20)
    except requests.RequestException as exc:
        raise TmdbError(f"Network error talking to TMDB: {exc}") from exc

    if response.status_code == 401:
        raise TmdbError("Invalid TMDB API key. Check TMDB_API_KEY in your .env file.")
    if response.status_code == 429:
        raise TmdbError("TMDB rate limit reached. Try again in a few minutes.")
    if not response.ok:
        raise TmdbError(f"TMDB error {response.status_code}: {response.text[:200]}")

    return response.json()


def search_movies(query: str, page: int = 1) -> list[MovieSearchResult]:
    if not query.strip():
        return []
    data = _get("/search/movie", {"query": query.strip(), "page": page})
    results: list[MovieSearchResult] = []
    for item in data.get("results", []):
        release = item.get("release_date") or ""
        year = int(release[:4]) if len(release) >= 4 else None
        results.append(
            MovieSearchResult(
                tmdb_id=int(item["id"]),
                title=str(item.get("title") or ""),
                year=year,
                poster_path=item.get("poster_path"),
                overview=item.get("overview"),
            )
        )
    return results


def fetch_movie_details(tmdb_id: int) -> dict[str, Any]:
    return _get(
        f"/movie/{tmdb_id}",
        {"append_to_response": "keywords"},
    )


def normalize_movie_row(details: dict[str, Any]) -> dict[str, Any]:
    release = details.get("release_date") or ""
    year = int(release[:4]) if len(release) >= 4 else None
    genres = [g.get("name") for g in details.get("genres", []) if g.get("name")]
    languages = details.get("spoken_languages") or []
    lang_codes = [lang.get("iso_639_1") for lang in languages if lang.get("iso_639_1")]
    keywords_block = details.get("keywords") or {}
    keyword_names = [
        k.get("name") for k in keywords_block.get("keywords", []) if k.get("name")
    ]
    return {
        "tmdb_id": int(details["id"]),
        "title": str(details.get("title") or ""),
        "year": year,
        "overview": details.get("overview"),
        "genres": genres,
        "languages": lang_codes,
        "runtime": details.get("runtime"),
        "rating": details.get("vote_average"),
        "keywords": keyword_names,
        "poster_path": details.get("poster_path"),
    }
