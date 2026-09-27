# OTT Brain

Personal movie discovery app (V1). Python + Streamlit + SQLite, with TMDB for metadata.

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd ~/git/ott-brain
uv sync
cp .env.example .env
# Edit .env and set TMDB_API_KEY (https://www.themoviedb.org/settings/api)
uv run python scripts/init_db.py
uv run streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). No login — single-user local app.

## Configuration

| Variable | Purpose |
|----------|---------|
| `TMDB_API_KEY` | Required for search and metadata sync |
| `OTT_BRAIN_DB_PATH` | SQLite file path (default: `./data/ott_brain.db`) |
| `MOVIE_METADATA_TTL_HOURS` | Skip TMDB re-fetch when row is newer than this (default: 168) |

## Product backlog

| Document | Description |
|----------|-------------|
| [docs/backlog/EPICS.md](docs/backlog/EPICS.md) | Epic map and release phasing |
| [docs/backlog/USER_STORIES.md](docs/backlog/USER_STORIES.md) | Full story backlog with acceptance criteria |
| [docs/backlog/STORY_INDEX.md](docs/backlog/STORY_INDEX.md) | Story ID quick reference |
| [docs/backlog/STATUS.md](docs/backlog/STATUS.md) | **Implementation progress** (update when shipping) |

**Story IDs:** `OTT-<Epic#>-<Story#>` (e.g. `OTT-1-03` = Epic 1, story 3).

## V1 definition of done

A natural-language query flows through: **intent → TMDB candidates → India OTT filter → personal history → ranked top 3–5 → explanations → feedback → learning signals**.
