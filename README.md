# AI STAT-GROWTH

AI-powered competency intelligence and adaptive learning prototype for India's Official Statistical System (SIH Problem Statement 26101).

Phase 2 implements the first complete employee workflow:

`Profile → Assessment → Competency update → Skill-gap prioritisation → Explainable recommendations → iGOT + NSSTA/TPAC learning path → Persisted learning progress`

The product is intentionally positioned as a competency intelligence platform, not a conventional LMS. It continuously compares an official's current capability with role requirements and turns the most important gaps into a defensible next action.

The forensic extension adds a prototype FRAC-aware chain (`Position → Role → Activity → Competency → Level`), confidence-weighted competency evidence, vector alignment, Sunbird-compatible telemetry, structured source-grounded assessment-item generation, human review gates, StatBot retrieval, and server-calculated admin intelligence. These are integration-ready prototype boundaries, not claims of official FRAC, iGOT, NSSTA, or MoSPI production data.

## What works in Phase 2

- JWT demo authentication with EMPLOYEE, ADMIN, and TRAINER role boundaries.
- API-backed employee profile for Dr. Ananya Sharma; no employee profile values are hardcoded in React.
- 35-competency framework across Statistical, Technical, Digital Governance, and Behavioural & Managerial domains.
- 1–5 competency levels mapped to a configurable 0–100 score model.
- 20-question cross-domain baseline assessment plus focused seeded assessments.
- Server-side answer validation, evaluation, category scores, strengths, weaknesses, answer explanations, and attempt history.
- Closed-loop competency updates that blend assessment evidence with existing scores and persist `competency_score_history`.
- Ranked skill gaps with severity thresholds, role relevance, department priority, future demand, learning history, and explanations.
- Deterministic recommendation engine with a stable contract for future semantic/LLM ranking.
- Replaceable iGOT and NSSTA/TPAC adapter boundaries over clearly labelled synthetic prototype datasets. No live government API is claimed or connected.
- Personalized learning path grouped into top priority, next best learning, and optional development.
- Persisted not-started, in-progress, and completed learning progress.
- Responsive employee dashboard, profile, competency radar, assessment player, results view, skill gaps, learning pathway, and FRAC intelligence view.
- Phase 3 forensic verification and hardening record covering reality checks, fixes, malformed-output validation, provenance, review gates, telemetry, grounding, and live acceptance evidence (`docs/phase3-verification.md`).
- FRAC-compatible Position → Role → Activity → Competency mappings for the seeded demo role.
- Competency evidence records with source type, confidence, evidence counts, and immutable score history.
- Competency vector endpoint with normalized dimensions, weighted Euclidean distance, cosine similarity, and alignment score.
- Sunbird-compatible telemetry envelope, batch ingestion, deduplication, learner velocity, and skill-profile endpoints.
- Functional trainer assessment studio: local document upload, TXT/DOCX/PPTX/PDF extraction boundary, chunk provenance, deterministic MCQ fallback, validation, review, approval, and quiz publishing.
- Functional StatBot general and document-grounded answer endpoint with source chunk citations.
- Server-calculated admin workforce overview, department comparison, skill-gap aggregation, training effectiveness, and prototype forecast APIs.
- Loading, retry, empty, validation, and error states in the core workflow.

## Repository layout

```text
backend/
  app/
    api/routes/       FastAPI routes for auth, users, learning, employee intelligence, admin boundary
    core/              settings and JWT security
    db/                SQLAlchemy engine, Base, and additive schema upgrades
    integrations/      iGOT/NSSTA contracts and seeded adapters
    models/            Phase 2 plus FRAC/evidence/vector/telemetry models
    schemas/           Pydantic API contracts
    services/          intelligence, documents, studio, quiz, telemetry, admin, and Phase 2 services
    ai/                provider abstraction and MCQ quality validation
  tests/               Phase 2 plus forensic intelligence/studio/telemetry tests
frontend/
  src/
    auth/              session context
    components/        role-aware shell and shared UI primitives
    pages/              employee workflow, FRAC intelligence, StatBot, trainer studio, and admin intelligence
    services/          typed API client
    types.ts           frontend API contracts
data/                  reserved seed/data area
docs/                   architecture, API, database, AI, security, deployment, demo notes
```

## Requirements

- Python 3.11+
- Node.js 18+
- npm
- Docker is optional; no paid API or external AI provider is required.

## Local setup

From the repository root:

```bash
cp .env.example .env

cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend uses `VITE_API_BASE_URL` from `frontend/.env.local` when supplied; otherwise it defaults to `http://localhost:8000/api`.

The seed script is idempotent for normal local use. To intentionally recreate the demo database after schema/seed changes:

```bash
rm -f backend/data/ai_stat_growth.db
(cd backend && .venv/bin/python scripts/seed.py)
```

## Demo accounts

All identities and records are fictional synthetic demo data.

| Role | Email | Password |
| --- | --- | --- |
| Employee | `employee.demo@aistatgrowth.gov.in` | `Demo@123` |
| Admin | `admin.demo@aistatgrowth.gov.in` | `Demo@123` |
| Trainer | `trainer.demo@aistatgrowth.gov.in` | `Demo@123` |

The primary employee is Dr. Ananya Sharma, Assistant Director, National Statistical Office, with a seeded five-year profile and baseline signals including Statistics 82, Python 45, SQL 64, GIS 31, Artificial Intelligence 38, and Data Visualization 72.

## Test and build commands

```bash
# backend, from repository root
backend/.venv/bin/python -m pytest -q backend/tests

# frontend
cd frontend
npm run build
```

The test suite covers profile loading, baseline scores, FRAC relationships, competency vectors, evidence aggregation, severity thresholds, weighted priority ordering, cross-domain assessment submission, persisted competency changes, both prototype recommendation sources, explainability fields, learning progress upsert, structured question validation, document extraction, human review gates, quiz evaluation, telemetry deduplication/velocity, admin aggregation, and employee-to-employee RBAC blocking.

## API

Base URL: `http://localhost:8000/api`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

Authentication:

- `POST /auth/login`
- `GET /users/me`

Employee intelligence:

- `GET /users/{id}`
- `GET /users/{id}/dashboard`
- `GET /users/{id}/competencies`
- `GET /users/{id}/competency-domain-summary`
- `GET /users/{id}/frac-profile`
- `GET /users/{id}/competency-vector`
- `GET /users/{id}/evidence`
- `GET /users/{id}/skill-gaps`
- `GET /users/{id}/recommendations`
- `GET /users/{id}/learning-progress`
- `POST /users/{id}/learning-progress`

Framework and learning sources:

- `GET /competencies`
- `GET /assessments`
- `GET /assessments/{id}`
- `POST /assessments/start`
- `POST /assessments/{attempt_id}/submit`
- `GET /assessments/{attempt_id}/result`
- `GET /courses`
- `GET /training-programmes`

Assessment studio and assistant:

- `POST /documents/upload`
- `GET /documents`
- `POST /documents/{id}/process`
- `POST /assessment-items/generate`
- `GET /assessment-items/review-queue`
- `POST /assessment-items/{id}/approve`
- `POST /assessment-items/{id}/reject`
- `POST /assessment-items/{id}/edit`
- `POST /quizzes/publish`
- `GET /quizzes/{id}`
- `POST /quizzes/{id}/submit`
- `POST /ai/chat`

Telemetry and administration:

- `POST /telemetry/events`
- `POST /telemetry/batch`
- `GET /telemetry/events/{user_id}`
- `GET /telemetry/learner/{user_id}/velocity`
- `GET /telemetry/learner/{user_id}/skill-profile`
- `GET /telemetry/organization/summary`
- `GET /telemetry/organization/recent` (admin-only demo inspection)
- `POST /demo/reset` (admin-only, development/demo mode only)
- `GET /admin/overview`
- `GET /admin/departments`
- `GET /admin/skill-gaps`
- `GET /admin/training-effectiveness`
- `GET /admin/forecast`

See [docs/api.md](docs/api.md) for response examples and access rules.

## Environment variables

Copy `.env.example` to `.env` and adjust only what is needed:

- `DATABASE_URL` defaults to local SQLite.
- `JWT_SECRET` must be replaced for any non-demo deployment.
- `LLM_PROVIDER=mock` keeps this phase deterministic and zero-cost.
- `LLM_PROVIDER=mock` is deterministic and zero-cost; `ollama` and `openai_compatible` are optional providers.
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL` configure optional providers.
- `TELEMETRY_VERSION` controls the Sunbird-compatible envelope version (default `3.0`).
- `CORS_ORIGINS` controls allowed frontend origins.
- `UPLOAD_MAX_MB` controls document upload validation.
- `DEMO_MODE=true` enables the protected admin reset control only when `APP_ENV` is development, demo, or test. Set it to false for non-demo environments.

No API key is included in the repository or sent to the frontend.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The API is exposed on port 8000 and the frontend on port 4173. Docker is not required for local development.

## Demo flow

1. Sign in as the Employee demo.
2. Open My profile and verify the API-backed Ananya Sharma record.
3. Open Competency profile and inspect readiness, radar, strengths, and low scores.
4. Open Assessment centre and start the recommended 20-question baseline.
5. Select options and submit; evaluation is performed by FastAPI, not React.
6. Inspect the result, explanations, and competency deltas.
7. Open Skill gaps; GIS, Python, and Artificial Intelligence will be visible with recalculated values.
8. Open Learning pathway; inspect the ranked iGOT-style and NSSTA/TPAC prototype resources and “Why this recommendation?” evidence.
9. Start a resource and mark it complete; reload to verify persisted progress.
10. Open FRAC intelligence and inspect the database-traceable position, role, activities, evidence, and vector alignment.
11. Use StatBot in general mode, or use document mode after a trainer has processed a document.
12. Sign in as Trainer, open AI Assessment Studio, upload a PDF/DOCX/PPTX/TXT file, process it, generate questions, approve them, and publish a quiz.
13. Sign in as Employee, attempt the published quiz, and inspect explanations and competency evidence updates.
14. Sign in as Admin and review live organization aggregates and prototype future-demand records.

## Prototype boundary and production roadmap

Prototype data is synthetic. iGOT and NSSTA/TPAC records are adapter-backed representative records, not live government integrations. FRAC records are synthetic mappings, not an official FRAC catalogue. Telemetry follows the configured Sunbird-compatible envelope boundary but is stored locally. The mock provider and deterministic retrieval/generation path are zero-cost fallbacks; Ollama and OpenAI-compatible providers are optional.

Production would add government SSO/OAuth/SAML, PostgreSQL migrations, approved iGOT/NSSTA APIs, managed vector storage, signed httpOnly sessions, centralized audit and observability, malware scanning and object storage for uploads, multilingual content governance, accessibility/security review, and real workforce data governance.
