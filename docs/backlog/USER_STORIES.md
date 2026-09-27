# User stories — OTT Brain V1

**Product:** OTT Brain (personal OTT recommender)  
**Persona:** *Priya* — single user, watches on Indian OTT services, wants “what tonight?” without scrolling catalogs.

**Story format:** As a … / I want … / So that … + **Acceptance criteria** (AC) + **Notes**

**Priority:** Must (M) · Should (S) · Could (C)

---

## E0 — V1 non-goals (traceability)

No delivery stories. PRD explicitly excludes: social, multi-user, auth, mobile native app, notifications, chat history, autonomous agents, complex recsys ML, own OTT scraping, full TV episode tracking, subscription billing.

| ID | Note |
|----|------|
| OTT-0-01 | TV series deferred; V1 focuses on **movies** only (metadata/search path). |

---

## E1 — Foundation & data layer

### OTT-1-01 — Project scaffold (M)

**As a** developer  
**I want** a Python + Streamlit app with SQLite and environment-based secrets  
**So that** features can ship in small iterations without infra overhead.

**AC**

- App runs locally with one command (documented in README).
- `.env.example` lists required keys (e.g. TMDB API key); secrets are not committed.
- SQLite file path is configurable; default is local dev path.
- Single-user assumption: no login screen.

---

### OTT-1-02 — SQLite schema v1 (M)

**As a** developer  
**I want** tables for movies, watch_history, feedback, providers, and optional preferences  
**So that** all V1 features persist in one database.

**AC**

- `movies`: tmdb_id (PK), title, year, overview, genres, languages, runtime, rating, keywords, embedding (nullable blob/text).
- `watch_history`: movie_id (FK), watched_at, rating, liked, notes.
- `feedback`: movie_id, type, reason, created_at.
- `feedback.type` supports at least: LOVED, LIKED, NOT_INTERESTED, TOO_SLOW, TOO_VIOLENT, ALREADY_SEEN.
- `providers`: movie_id, country, provider, offer_type, url, checked_at.
- Migrations or init script creates schema idempotently.

---

### OTT-1-03 — TMDB movie search (M)

**As** Priya  
**I want** to search movies by title  
**So that** I can find titles to mark watched or inspect metadata.

**AC**

- Search calls TMDB; results show title, year, poster thumbnail.
- Selecting a result stores/updates row in `movies` with core metadata from TMDB.
- Errors (network, rate limit, invalid key) show a clear user-visible message.
- Movies only (no TV series in search for V1).

---

### OTT-1-04 — TMDB metadata sync for a movie (M)

**As a** system  
**I want** to fetch and cache TMDB details for a known `tmdb_id`  
**So that** filtering and ranking use consistent genre, runtime, language, rating, keywords.

**AC**

- Given `tmdb_id`, populate/update `movies` fields per PRD.
- Re-fetch is skipped or throttled if data is fresh (configurable TTL optional for V1).
- Overview and keywords available for downstream semantic use.

---

### OTT-1-05 — Basic Home shell (S)

**As** Priya  
**I want** a simple home screen with a search/query area  
**So that** the app has a clear entry point before recommendations exist.

**AC**

- Streamlit page labeled Home with placeholder for natural-language input (wired in E4).
- Navigation stub for Recommendations and History screens (can be single app with sections until E6).

---

## E2 — India OTT availability

### OTT-2-01 — Fetch India watch providers from TMDB (M)

**As a** system  
**I want** TMDB watch-provider data for country `IN` per movie  
**So that** recommendations only surface watchable content.

**AC**

- For a `tmdb_id`, persist providers into `providers` with country=IN, provider name, offer_type, url when available.
- Supports major Indian services reflected in TMDB (Netflix, Prime, JioHotstar, Sony LIV, ZEE5, etc. as returned by API).

---

### OTT-2-02 — Provider cache (M)

**As a** system  
**I want** locally cached provider rows with `checked_at`  
**So that** every search does not re-hit TMDB for availability.

**AC**

- Cache read used before network fetch; stale threshold configurable (e.g. 7 days).
- Manual or automatic refresh on cache miss or expiry.
- UI or logs indicate when data was last checked (developer-facing acceptable in V1).

---

### OTT-2-03 — User OTT subscriptions (M)

**As** Priya  
**I want** to select which OTT services I subscribe to  
**So that** recommendations prioritize (or restrict to) my catalogs.

**AC**

- Onboarding checklist: Netflix, Prime Video, JioHotstar, Sony LIV, ZEE5, Aha, Sun NXT (per PRD).
- Selections persist across sessions (SQLite `preferences` or dedicated table).
- Home screen shows toggles/checkboxes for active providers (per PRD mock).

---

### OTT-2-04 — Filter by subscribed providers (M)

**As** Priya  
**I want** candidate movies limited to those available on at least one of my selected services in India  
**So that** I do not get unwatchable suggestions.

**AC**

- Hard filter: no provider match on IN + user subscriptions → exclude from recommendation set.
- Optional “show all IN providers” mode is **out of scope** unless explicitly enabled later; default is subscription-aware.

---

### OTT-2-05 — Watchmode fallback (C)

**As a** developer  
**I want** a pluggable second availability source  
**So that** coverage gaps in TMDB can be filled without rewriting the app.

**AC**

- Interface `AvailabilityProvider` with TMDB implementation default.
- Watchmode implementation stub or feature flag; not required for V1 launch if TMDB suffices.
- Document decision criteria in README when enabled.

---

## E3 — Onboarding & watch history

### OTT-3-01 — Onboarding step: OTT selection (M)

**As** Priya  
**I want** onboarding to start with picking my streaming services  
**So that** I am not asked for a long profile upfront.

**AC**

- First-run or Settings flow presents OTT checklist (OTT-2-03).
- Can skip to add watches later but app warns recommendations need subscriptions for filtering.

---

### OTT-3-02 — Mark movie as watched (M)

**As** Priya  
**I want** to mark a searched movie as watched  
**So that** the app stops recommending it again.

**AC**

- Creates/updates `watch_history` with `watched_at`.
- Watched movies excluded from recommendation candidates (hard filter).

---

### OTT-3-03 — Rate and like watched titles (M)

**As** Priya  
**I want** to rate movies and mark loved/liked  
**So that** the taste model has positive signals.

**AC**

- Optional numeric rating and boolean `liked` / loved mapping to feedback or watch_history fields.
- Onboarding step 3 prompts to rate 5–10 favorites (can dismiss).

---

### OTT-3-04 — Bulk import watched list (M)

**As** Priya  
**I want** to paste a list of movie titles (one per line)  
**So that** I can bootstrap history quickly.

**AC**

- Text area accepts multiline titles.
- System resolves each line to TMDB movie via search (+ LLM disambiguation in E4 where ambiguous).
- Report: resolved, ambiguous (user pick), failed.
- Successful rows added to watch_history.

---

### OTT-3-05 — Explicit rejections (S)

**As** Priya  
**I want** to mark titles I do not want again  
**So that** they are filtered from future recommendations.

**AC**

- `feedback` type NOT_INTERESTED (and similar) excludes movie from candidates.
- Visible from History as “Rejected”.

---

## E4 — Natural-language discovery

### OTT-4-01 — Natural-language query input (M)

**As** Priya  
**I want** to describe what I want to watch in plain language  
**So that** I do not need to use rigid filters.

**AC**

- Home text field accepts examples like PRD (“dark psychological thriller under 2 hours”).
- Submit triggers recommendation pipeline (may show loading state).

---

### OTT-4-02 — Structured intent extraction (M)

**As a** system  
**I want** an LLM (via OpenRouter) to convert the query into structured intent JSON  
**So that** downstream steps are deterministic.

**AC**

- Output schema includes: genres, moods, themes, languages, runtime_max/min, avoid[], similar_to[], ott_providers (optional).
- Invalid or empty query returns friendly validation message.
- LLM is **not** used to search TMDB directly.

---

### OTT-4-03 — TMDB candidate retrieval (M)

**As a** system  
**I want** to retrieve candidate movies from TMDB using structured intent  
**So that** there is a bounded set to filter and rank.

**AC**

- Uses TMDB APIs (discover/search/keyword) appropriate to intent fields.
- Candidates normalized to `movies` rows (metadata sync).
- Reasonable cap on candidate count (e.g. 50–200) documented in code.

---

### OTT-4-04 — Title resolution for bulk and similar_to (M)

**As a** system  
**I want** to map free-text titles (Andhadhun, bulk paste) to `tmdb_id`  
**So that** similar_to and history import work reliably.

**AC**

- Uses TMDB search first; LLM assists tie-break for ambiguous matches.
- User confirmation UI for low-confidence matches (S).

---

## E5 — Personalization & ranking

### OTT-5-01 — Hard filters pipeline (M)

**As a** system  
**I want** to apply deterministic filters before scoring  
**So that** obviously wrong titles never rank highly.

**AC**

- Remove: watched, explicitly rejected, not on IN + user OTTs, runtime over max, language/genre mismatches when specified in intent.
- Filter order and counts logged for debugging (E9).

---

### OTT-5-02 — Semantic similarity feature (M)

**As a** system  
**I want** embeddings for movies and query context  
**So that** “something like X” and vibe matching work.

**AC**

- Store embedding on `movies` when computed.
- Query embedding from intent text and/or `similar_to` reference movies.
- Similarity score available per candidate for ranking.

---

### OTT-5-03 — Personal taste features from history (M)

**As a** system  
**I want** genre/theme/language affinities and avoid list derived from history + feedback  
**So that** ranking reflects Priya’s profile without a separate ML model.

**AC**

- Approximate profile: weighted genres/themes; avoid list from negative feedback.
- Taste match score per candidate (0–1 or comparable).

---

### OTT-5-04 — Jev personalized scoring (M)

**As a** system  
**I want** Jev (via OpenRouter) to score candidates given intent + taste context  
**So that** ranking is personalized beyond static rules.

**AC**

- Model behind interface; Jev used for candidate scoring per PRD.
- Returns scores for all candidates in batch or chunked with timeout handling.

---

### OTT-5-05 — Weighted final rank (M)

**As a** system  
**I want** a combined score using PRD weights  
**So that** results balance query, taste, semantics, quality, novelty, availability preference.

**AC**

- Formula: 30% query match + 30% taste + 15% semantic + 10% quality/rating + 10% novelty + 5% availability preference.
- Weights configurable in one place; defaults match PRD.
- Top 3–5 returned.

---

### OTT-5-06 — Novelty and quality sub-scores (S)

**As a** system  
**I want** explicit quality (TMDB rating) and novelty (not recently recommended/watched genre fatigue) terms  
**So that** logging and tuning are possible.

**AC**

- Each component score persisted in recommendation log (E9).

---

## E6 — Recommendations UI & explanations

### OTT-6-01 — Recommendations screen with 3–5 cards (M)

**As** Priya  
**I want** to see a small set of recommendations after I search  
**So that** I can decide quickly what to watch tonight.

**AC**

- Each card: poster, title, year, language, runtime, genre, OTT provider(s), rating, match score.
- Watch link when URL exists in `providers`.
- Empty state when filters eliminate all candidates (suggest relaxing query).

---

### OTT-6-02 — “Why this was recommended” (M)

**As** Priya  
**I want** a short explanation per title  
**So that** I trust and understand the suggestion.

**AC**

- LLM generates explanation from intent, taste signals, and movie metadata (cheap model via OpenRouter).
- Explanation references concrete history when available (e.g. loved Andhadhun).
- Fallback template if LLM fails.

---

### OTT-6-03 — Home screen integrated flow (M)

**As** Priya  
**I want** Home → Find Movies → Recommendations in one flow  
**So that** the core loop matches the three-screen PRD.

**AC**

- OTT toggles on Home affect OTT-2-04.
- Query + Find Movies navigates to Recommendations with results.

---

## E7 — Feedback & taste signals

### OTT-7-01 — Thumbs up / down on recommendations (M)

**As** Priya  
**I want** to like or dislike a recommendation  
**So that** the app learns from my reaction.

**AC**

- Persists to `feedback` with appropriate types.
- Downstream ranking uses negative signals (E5-03).

---

### OTT-7-02 — Structured rejection reasons (M)

**As** Priya  
**I want** to say “too slow”, “too violent”, or “already seen”  
**So that** avoid rules improve over time.

**AC**

- Buttons or menu map to TOO_SLOW, TOO_VIOLENT, ALREADY_SEEN.
- ALREADY_SEEN also updates watch_history if not already watched.

---

### OTT-7-03 — Post-watch feedback (S)

**As** Priya  
**I want** to mark a recommendation I watched as loved  
**So that** positive loop strengthens taste model.

**AC**

- LOVED/LIKED from recommendation card or History.

---

## E8 — History & preferences UI

### OTT-8-01 — History screen (M)

**As** Priya  
**I want** a searchable list of my watched movies  
**So that** I can review and edit my profile.

**AC**

- Tabs or filters: Watched, Favorites, Ratings, Rejected.
- Search by title.

---

### OTT-8-02 — Edit history entry (S)

**As** Priya  
**I want** to change rating or remove a watched mark  
**So that** mistakes do not poison recommendations.

**AC**

- Update watch_history; remove rejection feedback optionally.

---

### OTT-8-03 — View taste summary (C)

**As** Priya  
**I want** a simple text view of genres/themes I lean toward  
**So that** I can sanity-check what the app thinks I like.

**AC**

- Renders approximate profile from E5-03 (not required for V1 DoD but aligns with PRD taste model).

---

## E9 — Observability & quality (personal metrics)

### OTT-9-01 — Recommendation session log (M)

**As** Priya (as product owner)  
**I want** each search to log intent, candidates, sub-scores, and final ranking  
**So that** I can tune weights and models with evidence.

**AC**

- Log includes timestamp, query, structured intent, candidate ids, component scores, final order.
- Storage: SQLite table or structured log files.

---

### OTT-9-02 — Track acceptance and watch-through (M)

**As** Priya  
**I want** to see recommendation acceptance rate and watched recommendation rate  
**So that** I know if V1 is succeeding.

**AC**

- **Acceptance:** user marks “would watch” or positive feedback / click-through to watch link (define one primary event).
- **Watched recommendation rate:** recommendations later marked watched.
- Simple dashboard or export script (Streamlit sidebar acceptable).

---

### OTT-9-03 — Quality counters (S)

**As** Priya  
**I want** thumbs ratio, loved rate, repeat searches, already-seen rejections, diversity, OTT accuracy samples  
**So that** PRD quality signals are visible.

**AC**

- Metrics computed from logs + feedback; no multi-user analytics.

---

## E10 — Model abstraction

### OTT-10-01 — OpenRouter client (M)

**As a** developer  
**I want** a single OpenRouter integration with API key from env  
**So that** models are swappable.

**AC**

- Supports at least: cheap LLM for intent + explanations; Jev for scoring.
- Timeouts and retries documented; user sees generic error on failure.

---

### OTT-10-02 — Model role interface (M)

**As a** developer  
**I want** interfaces for IntentParser, CandidateScorer, ExplanationGenerator  
**So that** implementations can change without touching UI.

**AC**

- Default implementations use OpenRouter models per PRD table.
- Unit tests or manual test hooks for mock implementations.

---

## Epic — V1 end-to-end

### OTT-V1-01 — Golden path acceptance (M)

**As** Priya  
**I want** the full PRD scenario to work end-to-end  
**So that** V1 is complete.

**AC**

Given onboarding with OTTs and some watched/rated titles, when I enter:

> “I want a Korean psychological thriller, less than 2 hours, similar to movies I've loved, and it must be available on Netflix or Prime India.”

Then the app:

1. Produces structured intent.  
2. Retrieves TMDB candidates.  
3. Filters watched/rejected/unavailable/runtime/language.  
4. Ranks with combined scoring including Jev.  
5. Shows 3–5 cards with explanations and IN watch links.  
6. Records feedback that affects future runs.  

---

## Dependency highlights

```text
OTT-1-02 → most epics
OTT-2-01, OTT-2-03 → OTT-2-04 → OTT-5-01, OTT-V1-01
OTT-3-02 → OTT-5-01
OTT-10-01 → OTT-4-02, OTT-5-04, OTT-6-02
OTT-4-02, OTT-4-03 → OTT-5-* → OTT-6-01
OTT-7-* → OTT-5-03 (ongoing)
OTT-9-01 → OTT-9-02, OTT-9-03
```
