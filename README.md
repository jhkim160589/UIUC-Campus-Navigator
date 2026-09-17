# Campus Navigator

Plans a student's daily walking route across their registered classes at UIUC, and
flags transitions that cannot be made within the scheduled passing time.

> Solo rebuild of a 2024 team project, redesigned around a public course-data API
> and a self-implemented routing engine.

**Status:** Week 1 of 6 — in progress. Not yet deployed.

---

## Why the warning matters

Registration systems only check that your classes do not overlap in time. They will
happily approve a schedule with a 10-minute passing period between two buildings that
are a 15-minute walk apart. That schedule is valid on paper and impossible in practice,
and nobody tells you until you are already late.

Campus Navigator computes the actual walking distance between consecutive classes over
a campus graph, converts it to time at 1.4 m/s, and compares that against the real gap.

## How it works

```
UIUC course API (XML)  ->  parse  ->  PostgreSQL  <-  building coords (geocoded once, cached)
                                          |
                                   campus graph (buildings + path intersections)
                                          |
                                   Dijkstra (hand-implemented, no library)
                                          |
                            feasibility check (distance / 1.4 m/s vs. gap)
                                          |
                                   FastAPI endpoints
                                          |
                            React + map (route overlay + warning badges)
```

**Stack:** Python · FastAPI · PostgreSQL · React · pytest

Routing is implemented from scratch rather than delegated to the Google Directions
API. Directions would return a route; it would not produce a graph whose node and
edge choices can be defended. Week 5 validates the hand-rolled distances *against*
Directions rather than depending on it.

## Measurements

Filled in as they are taken. An empty cell means not yet measured — no number
appears here or in a resume bullet before it has been measured.

| Metric | Value | Taken |
|---|---|---|
| Subjects available, Fall 2026 | 186 | 2026-09-17 |
| API throughput | 0.24 s/course | 2026-09-17 |
| Course sections ingested | — | |
| Buildings geocoded | — | |
| Graph nodes / edges | — | |
| Route computation time | — | |
| Infeasible transitions found in a real schedule | — | |
| Distance deviation vs. Google Directions | — | |
| API response time p50 / p99 | — | |

## Running it locally

Requires Python 3.12+ and Docker.

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env            # defaults match docker-compose.yml
docker compose up -d            # starts Postgres on :5432

pytest
```

Explore the course API without touching the database:

```bash
python scripts/explore_api.py CS ECE MATH PHYS --limit 15
```

Prints section counts, every distinct building with frequency, day-code
distribution, and every meeting that has no usable location.

## Repository layout

```
backend/app/config.py       environment handling
backend/app/db.py           Postgres connections, migration runner
backend/app/ingest/         UIUC API client + XML parsing
backend/app/graph/          campus graph + Dijkstra          (Week 2)
backend/app/api/            FastAPI endpoints                (Week 3)
backend/migrations/         schema
scripts/explore_api.py      API recon tool, no DB required
docs/week1-api-recon.md     measured findings about the course API
tests/
```

## Data source

UIUC's public CIS course API — `https://courses.illinois.edu/cisapp/explorer/schedule`.
No authentication. `?mode=detail` on a course URL expands all sections and their
meetings inline, which collapses N+1 requests into one.
Full endpoint map and data quality notes: [docs/week1-api-recon.md](docs/week1-api-recon.md).
