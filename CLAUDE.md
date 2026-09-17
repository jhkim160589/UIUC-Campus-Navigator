# Campus Navigator — working agreement

Solo rebuild of a 2024 team project. Owner: Jihwan Kim (UIUC CompE '28).
Timeline: 2026-09-17 → 2026-10-25. Budget: 5 h/week.
Purpose: Summer 2027 SWE internship portfolio project.

---

## The one rule that matters

A previous project failed as a resume item because AI wrote the code and the
author could not explain it in an interview. **Preventing that repeat is a
precondition, not a preference.**

### Jihwan types these himself. Do not write them for him.

- Graph construction and Dijkstra implementation
- PostgreSQL schema design
- Time-feasibility logic (walking time, warning thresholds)
- API endpoint signatures (what goes in, what comes out)

If asked to write one of these, explain the concept and the trade-offs, then stop
and let him type it. Reviewing and debugging code he wrote is fine and encouraged.

### Claude may write these

- Project setup, requirements.txt, Docker, CI
- XML parsing boilerplate, DB connection management, migration scaffolding
- React component shells, styling, map library init
- Deploy scripts, env var handling
- Test scaffolding (Jihwan decides the test cases)

### Process rules

1. **Explanation before code.** New concept → explain why, confirm understanding, then code.
2. **No commit of un-understood code.** He must be able to explain each week's work aloud.
3. **Ask interview questions.** 2–3 at the end of each week. Examples:
   - "What is a node in your graph, and how did you choose edge weights?"
   - "Why Dijkstra and not A*? What's the difference?"
   - "You could have called Google Directions. Why implement it yourself?"
   - "Why does this foreign key need to exist?"
4. **Measurements go in the README the day they are taken.** Never write a number
   in a resume bullet that was not measured.

---

## What it does

Student enters their courses → app computes the optimal daily walking route and
flags transitions that cannot be made in the scheduled passing time.

The feasibility warning is the differentiator. Registration systems only check for
time overlap; they will happily approve a 10-minute passing period between buildings
15 minutes apart. Distance ÷ 1.4 m/s vs. the gap between classes.

## Architecture

```
UIUC course API (XML)  ->  parse  ->  PostgreSQL  <-  building coords (geocoded once, cached)
                                          |
                                   campus graph (buildings + path intersections)
                                          |
                                   Dijkstra (hand-implemented)
                                          |
                            feasibility check (dist / 1.4 m/s vs. gap)
                                          |
                                   FastAPI endpoints
                                          |
                            React + map (route overlay + warning badges)
```

## Stack

Python / FastAPI · PostgreSQL · React · Leaflet or Google Maps (Week 1 decision) ·
pytest · Vercel (frontend) + Supabase or Railway (DB/backend)

Backend is Python, not Node — Python + SQL is the most commonly requested pairing
in intern postings, and it is his strongest language. SQL is the clearest gap on
the current resume.

## Schedule — do not advance until "Done when" is met

| Week | Dates | Focus | Done when |
|---|---|---|---|
| 1 | 9/17–27 | Data foundation | Query DB by course name → meeting times with building + coords |
| 2 | 9/28–10/4 | Graph + Dijkstra ⭐ | Two buildings in → shortest path + distance out, visually sane |
| 3 | 10/5–11 | Route chaining + feasibility | Deliberately impossible schedule → says which leg and why |
| 4 | 10/12–18 | Frontend | His real schedule renders with route and warnings |
| 5 | 10/19–25 | Validation + deploy ⭐ | A stranger opens the URL and gets results |
| 6 | 10/26–11/1 | Polish | A newcomer can run it locally from the README alone |

⭐ = resume gets updated that week. Do not wait for completion.

## Measurements to collect

| When | What |
|---|---|
| W1 | courses / sections / buildings ingested |
| W2 | graph node count, edge count; route computation time (ms) |
| W3 | infeasible transitions detected in a real schedule |
| W5 | distance deviation vs. Google Directions (N pairs, mean %) |
| W5 | API response time p50 / p99 |

## Scope discipline

Login, schedule sharing, notifications → all deferred past Week 6.
An unshipped feature is worth zero. Cap the graph at 20–30 buildings;
graph size is not a bragging point.

LeetCode gets 5 h/week and the project never borrows from it. Failing the OA
means nobody ever looks at this repo.

## README must state this is a solo rebuild

"Solo rebuild of a 2024 team project, redesigned around a public course-data API
and a self-implemented routing engine." Honesty here protects him in interviews.
