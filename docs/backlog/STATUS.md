# Implementation status

**Purpose:** Canonical progress tracker for OTT Brain V1. Update this file when you finish stories or epics so future sessions know where to continue.

**Last updated:** 2026-09-27  
**Next epic (sprint order):** E2 — India OTT availability ([EPICS.md](EPICS.md), stories OTT-2-01 … OTT-2-05)  
**Run the app:** `uv sync` → `.env` with `TMDB_API_KEY` → `uv run streamlit run app.py` (see [README](../../README.md)).

## Stack (as built)

| Piece | Location |
|-------|----------|
| Python package | `ott_brain/` |
| Streamlit entry | `app.py` |
| DB init | `scripts/init_db.py`, schema in `ott_brain/database.py` |
| TMDB client | `ott_brain/tmdb.py` |
| Movie cache / sync | `ott_brain/movies.py` |
| Dependencies | `pyproject.toml` + `uv.lock` (**uv**, not pip/requirements.txt) |

## Epic summary

| Epic | Status | Notes |
|------|--------|-------|
| E0 | n/a | Non-goals / traceability only |
| E1 | **done** | Foundation & data layer |
| E2 | **todo** | India OTT availability |
| E3 | todo | Onboarding & watch history |
| E4 | todo | Natural-language discovery |
| E5 | todo | Personalization & ranking |
| E6 | todo | Recommendations UI & explanations |
| E7 | todo | Feedback & taste signals |
| E8 | todo | History & preferences UI |
| E9 | todo | Observability & quality (cross-cutting) |
| E10 | todo | Model abstraction |
| V1 E2E | todo | OTT-V1-01 after core loop |

## Stories

Status: `done` · `todo` · `n/a` (traceability)

| ID | Status | Epic |
|----|--------|------|
| OTT-0-01 | n/a | E0 |
| OTT-1-01 | done | E1 |
| OTT-1-02 | done | E1 |
| OTT-1-03 | done | E1 |
| OTT-1-04 | done | E1 |
| OTT-1-05 | done | E1 |
| OTT-2-01 | todo | E2 |
| OTT-2-02 | todo | E2 |
| OTT-2-03 | todo | E2 |
| OTT-2-04 | todo | E2 |
| OTT-2-05 | todo | E2 |
| OTT-3-01 | todo | E3 |
| OTT-3-02 | todo | E3 |
| OTT-3-03 | todo | E3 |
| OTT-3-04 | todo | E3 |
| OTT-3-05 | todo | E3 |
| OTT-4-01 | todo | E4 |
| OTT-4-02 | todo | E4 |
| OTT-4-03 | todo | E4 |
| OTT-4-04 | todo | E4 |
| OTT-5-01 | todo | E5 |
| OTT-5-02 | todo | E5 |
| OTT-5-03 | todo | E5 |
| OTT-5-04 | todo | E5 |
| OTT-5-05 | todo | E5 |
| OTT-5-06 | todo | E5 |
| OTT-6-01 | todo | E6 |
| OTT-6-02 | todo | E6 |
| OTT-6-03 | todo | E6 |
| OTT-7-01 | todo | E7 |
| OTT-7-02 | todo | E7 |
| OTT-7-03 | todo | E7 |
| OTT-8-01 | todo | E8 |
| OTT-8-02 | todo | E8 |
| OTT-8-03 | todo | E8 |
| OTT-9-01 | todo | E9 |
| OTT-9-02 | todo | E9 |
| OTT-9-03 | todo | E9 |
| OTT-10-01 | todo | E10 |
| OTT-10-02 | todo | E10 |
| OTT-V1-01 | todo | V1 |

## Maintainer checklist

When completing work:

1. Set story row(s) to `done` and epic row to `done` when all its delivery stories are done.
2. Set **Last updated** and **Next epic** at the top.
3. Add a one-line note under the epic table if the next session needs context (new modules, env vars, blockers).
