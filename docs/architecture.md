# Architecture — Phase 2

## Product spine

The first complete vertical slice is implemented as a server-owned adaptive loop:

```text
Authenticated employee
  → profile context
  → assessment questions
  → server-side evaluation
  → competency score update + history
  → skill-gap calculation
  → deterministic recommendation ranking
  → iGOT / NSSTA-TPAC prototype learning sources
  → persisted learning progress
```

The frontend never owns authoritative scores, gap severity, or assessment evaluation. It renders typed API responses and sends answer/progress intents to FastAPI.

## Backend layers

- `api/routes`: HTTP transport, authentication dependencies, role/user ownership checks, response models.
- `schemas`: Pydantic contracts for stable request/response payloads.
- `services`: business rules for assessment evaluation, competency updates, gaps, recommendations, and learning progress.
- `models`: SQLAlchemy persistence models designed for SQLite now and PostgreSQL later.
- `integrations`: replaceable source contracts and seeded iGOT/NSSTA adapters.
- `ai`: existing provider boundary reserved for later AI slices; Phase 2's gap and recommendation fallback is deterministic.

## Closed-loop rules

1. An attempt is owned by the authenticated user.
2. Every question must be answered exactly once with an option from the server response.
3. The server calculates overall and competency-level evidence.
4. Scores are blended (`65% existing score + 35% assessment evidence`) to avoid erasing history.
5. Each update writes a `competency_score_history` row.
6. The next gap read uses the updated score.
7. Recommendation refresh deletes/rebuilds the user's persisted recommendation snapshot while keeping a stable response contract.

## Recommendation contract

The deterministic scorer exposes the signals required for a future semantic/LLM layer: gap, current and required score, role relevance, department priority, future demand, learning-history relevance, relevance score, priority, reason, and expected improvement. A future ranker can replace `build_recommendations` without changing the frontend contract.

## Source adapters

`SeededIGOTAdapter` and `SeededNSSTAAdapter` read API-shaped records from SQLite and explicitly set prototype source labels. Production adapters can implement the same `search` contract using approved authenticated APIs. The product does not claim a live government integration.

## Frontend boundaries

React Router protects employee routes with the existing auth context. Employee pages are intentionally data-driven:

- dashboard consumes one aggregate payload;
- profile consumes `/users/{id}`;
- competencies consumes the competency profile;
- assessment consumes assessment/start/submit/result;
- skill gaps consumes ranked gap rows;
- learning path consumes recommendations and progress and persists actions.

Shared Phase 2 UI primitives provide loading, retry, empty, score, severity, radar, and delta states without introducing a design-system dependency.

## Deployment shape

The frontend remains Vercel-compatible and the backend remains Docker-compatible. SQLite is the local default; SQLAlchemy keeps the model layer portable to PostgreSQL. Production identity, storage, observability, official source APIs, and data governance remain explicit future integrations.

## Forensic audit outcome

The original Phase 2 was reusable and functional for profile → assessment → gap → recommendation → progress, but it had a generic `User → Competency → Score` shape, no first-class evidence table, no FRAC relationships, no vector alignment, no telemetry envelope, no human review state machine, no source-grounded assessment studio, and only RBAC smoke endpoints for administration. The refactor is additive: existing Phase 2 tables, routes, and frontend contracts remain in place while new intelligence tables and response fields extend them.

## Target intelligence graph

```text
User/Employee
  → EmployeeRole → Position → Department
  → PositionRole → RoleActivity → ActivityCompetency
  → RoleCompetencyRequirement → Competency → CompetencyLevel
  → CompetencyEvidence → derived EmployeeCompetency
  → vector alignment → skill gap → recommendation factors
  → learning progress + telemetry → new evidence → updated profile
```

The seeded FRAC graph is synthetic and intentionally labelled as such. It demonstrates traceability for Ananya’s Assistant Director — Statistical Analysis role across Survey Data Analysis, Statistical Validation, Data Visualization, and Analytical Reporting. It is not an official FRAC catalogue.

## Evidence and auditability

`CompetencyEvidence` stores source type, source ID, score, confidence, timestamp, and metadata. The current score is derived from the latest evidence per source using configurable weights in `skill_gaps.py`. `CompetencyScoreHistory` and `CompetencyUpdateAudit` preserve old score, new score, source, evidence ID, and calculation text.

## AI and human review boundary

`LLMProvider` supports mock, Ollama, and OpenAI-compatible providers. Structured output is parsed and validated with Pydantic; malformed output raises a provider error for a deterministic fallback. The local studio currently uses deterministic source-grounded generation so it remains usable with no API key. Items retain document/chunk/page/slide provenance and cannot be published until a trainer/admin approves them.

## Telemetry boundary

The telemetry service stores the Sunbird-compatible envelope fields (`eid`, `ets`, `ver`, `mid`, `actor`, `context`, `object`, `edata`, `tags`) and deduplicates by `mid`. Assessment and learning-progress actions emit events automatically. Learner velocity is deterministic: `(learning hours + 2 × completed resources + completed assessments) / window days`; telemetry-derived confidence is deliberately bounded and does not silently replace formal evidence.

## Migration strategy

`db/migrations.py` is a lightweight additive upgrade runner for the prototype. It adds newly required columns to existing Phase 2 tables before `create_all` creates new tables. Production should replace this with versioned Alembic migrations and PostgreSQL constraints.
