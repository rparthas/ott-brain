# OTT Brain — Product Backlog

Personal movie/TV discovery app (V1). This repository holds product artifacts for **OTT Brain**, starting with user stories derived from the V1 PRD.

## Contents

| Document | Description |
|----------|-------------|
| [docs/backlog/EPICS.md](docs/backlog/EPICS.md) | Epic map and release phasing |
| [docs/backlog/USER_STORIES.md](docs/backlog/USER_STORIES.md) | Full story backlog with acceptance criteria |
| [docs/backlog/STORY_INDEX.md](docs/backlog/STORY_INDEX.md) | Story ID quick reference |

## Story ID convention

`OTT-<Epic#>-<Story#>` — e.g. `OTT-1-03` = Epic 1 (Foundation), story 3.

## V1 definition of done

A natural-language query flows through: **intent → TMDB candidates → India OTT filter → personal history → ranked top 3–5 → explanations → feedback → learning signals**.

## Git

From your machine (if `.git` is not initialized yet):

```bash
cd ~/git/ott-brain
git init -b main
git add .
git commit -m "Add V1 user story backlog from PRD"
```
