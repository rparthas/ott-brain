# Epics — OTT Brain V1

| ID | Epic | PRD phase | Goal |
|----|------|-----------|------|
| E1 | Foundation & data layer | Phase 1 | Runnable app shell, SQLite schema, TMDB search |
| E2 | India OTT availability | Phase 2 | Provider data for IN, user subscriptions, cache |
| E3 | Onboarding & watch history | Phase 3 | Bootstrap taste without heavy manual profiling |
| E4 | Natural-language discovery | Phase 4 (part) | Query → structured intent → candidate retrieval |
| E5 | Personalization & ranking | Phase 4 (part) | Filters, embeddings, Jev scoring, top 5 |
| E6 | Recommendations UI & explanations | Phase 4–5 | Cards, why strings, watch links |
| E7 | Feedback & taste signals | Phase 5 | Thumbs, rejection reasons, profile derivation |
| E8 | History & preferences UI | Phase 3–5 | Searchable history, favorites, rejected |
| E9 | Observability & quality | Cross-cutting | Logging rankings, success metrics (personal) |
| E10 | Model abstraction | Phase 4 | OpenRouter + swappable models |

## Suggested sprint / session order

1. **E1** → **E2** → **E3** (data + availability + memory)
2. **E10** + **E4** + **E5** (AI pipeline)
3. **E6** + **E7** + **E8** (complete loop in UI)
4. **E9** throughout; harden before calling V1 done

## Out of scope (V1 non-goals)

Captured as epic **E0** in stories file — no implementation stories, only traceability.
