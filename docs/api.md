# Phase 4 API

Base URL: `http://localhost:8000/api`. OpenAPI is available at `http://localhost:8000/docs`.

All routes below except `/health` and `/auth/login` require `Authorization: Bearer <access_token>`.

## Authentication and access

```http
POST /auth/login
Content-Type: application/json

{"email":"employee.demo@aistatgrowth.gov.in","password":"Demo@123"}
```

The response returns `access_token`, `token_type`, and a role-aware user summary. The demo roles are `EMPLOYEE`, `ADMIN`, and `TRAINER`.

Employee intelligence routes only allow a user to read or mutate their own employee record. An `ADMIN` may read another user's employee intelligence record. Cross-user employee access is rejected with `403`.

## Employee profile and dashboard

- `GET /users/me` — signed-in user summary.
- `GET /users/{user_id}` — full employee profile, including education and completed previous training.
- `GET /users/{user_id}/dashboard` — aggregate dashboard payload: profile, competency profile, gaps, recommendations, learning progress, hours, completed-course count, and latest assessment score.
- `GET /users/{user_id}/competencies` — current competency profile and category scores.
- `GET /users/{user_id}/competency-domain-summary` — database-driven domain counts plus employee current/target averages.
- `GET /users/{user_id}/skill-gaps` — ranked, explainable skill gaps.
- `GET /users/{user_id}/recommendations` — ranked learning resources with recommendation inputs and explanation.
- `GET /users/{user_id}/learning-progress` — persisted progress rows.
- `POST /users/{user_id}/learning-progress` — upsert a resource progress row.

Example skill-gap row:

```json
{
  "competency_id": 17,
  "competency": "GIS",
  "code": "GIS",
  "category": "Technical",
  "current_score": 31.0,
  "required_score": 80.0,
  "gap": 49.0,
  "severity": "critical",
  "priority_score": 80.2,
  "role_relevance": 95.0,
  "department_priority": 95.0,
  "future_demand": 76.0,
  "explanation": "GIS is critical priority because the current score is 31% against a 80% role target...",
  "recommended_next_action": "Complete a practical learning resource...",
  "current_level": "Elementary",
  "required_level": "Advanced"
}
```

## Competencies and learning sources

- `GET /competencies` — all seeded framework records with definitions, target level, target score, category, and weight.
- `GET /courses` — iGOT-shaped course records. `is_prototype: true` and source text make the dataset boundary explicit.
- `GET /training-programmes` — NSSTA/TPAC-shaped programme records. These are also prototype records.

## Assessment loop

- `GET /assessments` — published assessment summaries.
- `GET /assessments/{assessment_id}` — questions without correct answers.
- `POST /assessments/start` with `{ "assessment_id": 1 }` — creates a user-owned started attempt and returns its questions.
- `POST /assessments/{attempt_id}/submit` with `{ "answers": [{"question_id": 1, "answer": "..."}] }` — evaluates answers server-side, rejects missing/invalid answers, saves answer records, blends evidence into competency scores, writes score history, and refreshes recommendations.
- `GET /assessments/{attempt_id}/result` — completed result, category performance, competency changes, and explanation review.

The seeded `Competency Intelligence Baseline` contains 20 questions across Statistical, Technical, Digital Governance, and Behavioural & Managerial categories. A successful submission updates only the competencies assessed in that attempt and preserves prior scores in `competency_score_history`.

## Learning progress payload

```json
{
  "resource_type": "course",
  "resource_id": 1,
  "status": "in_progress",
  "completion_percent": 25,
  "learning_hours": 1.2
}
```

Valid statuses are `not_started`, `in_progress`, and `completed`. Completion status automatically forces percentage to `100`.

## Scoring notes

Gap severity is determined by the raw score difference:

- `>= 30`: critical
- `>= 20`: high
- `>= 10`: medium
- `< 10`: low

Recommendation ranking is deterministic and keeps a stable future AI-ranking contract:

`0.40 × competency gap match + 0.20 × role match + 0.15 × activity match + 0.10 × department priority + 0.10 × future demand + 0.05 × historical effectiveness`

Skill-gap priority uses the FRAC-aware factors:

`0.40 × gap score + 0.20 × role relevance + 0.15 × activity criticality + 0.15 × department priority + 0.10 × future demand`

Competency evidence uses configurable source weights. The current score is a confidence-weighted average of the latest evidence per source; formal assessment/quiz/course evidence is additive and score history is preserved.

Vector alignment normalizes scores to `[0,1]`, calculates weighted Euclidean distance `sqrt(Σ(wᵢ × (Tᵢ − Cᵢ)²))`, and calculates cosine similarity between current and target vectors.

## Other Phase 1 routes

- `GET /health` — unauthenticated process health check.
- `GET /bootstrap` — seeded counts, environment status, and controlled `demo_mode` flag.
- `POST /demo/reset` — admin-only reset available only when `DEMO_MODE=true` and `APP_ENV` is development, demo, or test. Recreates the synthetic seed and clears learner runtime state.
- `GET /admin/access-check` — admin RBAC smoke endpoint.
- `GET /admin/workforce-access-check` — admin RBAC smoke endpoint.
- `GET /admin/trainer-access-check` — trainer RBAC smoke endpoint.

## FRAC, evidence, and vector intelligence

- `GET /users/{user_id}/frac-profile` — position, role, role activities, required levels, and competency traceability.
- `GET /users/{user_id}/competency-vector` — normalized current/target vectors, weighted Euclidean distance, cosine similarity, alignment, and competency-specific gaps.
- `GET /users/{user_id}/evidence` — confidence-weighted evidence records by source.

Supported evidence types include `ASSESSMENT`, `QUIZ`, `COURSE_COMPLETION`, `PRACTICE`, `TRAINER_REVIEW`, `ROLE_ACTIVITY`, `TELEMETRY`, and `SELF_DECLARATION`. Assessment, quiz, and course signals do not overwrite history; they add evidence and recalculate the derived current score.

## Assessment studio and StatBot

- `POST /documents/upload` — trainer/admin-only multipart upload for PDF, DOCX, PPTX, and TXT with extension, MIME, filename, and size checks.
- `GET /documents` — caller-owned document list.
- `POST /documents/{document_id}/process` — extract, clean, chunk, and preserve page/slide metadata.
- `POST /assessment-items/generate` — deterministic source-grounded generation fallback. Every item has document/chunk provenance and starts as `PENDING_REVIEW`.
- `GET /assessment-items/review-queue` and `GET /assessment-items/{id}` — trainer/admin review views.
- `POST /assessment-items/{id}/approve`, `/reject`, and `/edit` — audited human review actions.
- `POST /quizzes/publish` — publish gate requiring all item IDs to be `APPROVED`.
- `GET /quizzes/{id}` and `POST /quizzes/{id}/submit` — learner quiz attempt/evaluation with quiz evidence.
- `POST /ai/chat` — general deterministic StatBot answer or document-grounded retrieval with source chunks.

Generated questions are checked with Pydantic and `QuestionQualityValidator`: exactly four unique options, valid answer index, allowed difficulty, non-empty explanation/source, competency existence, source support, duplicate detection, and answer-leakage heuristics.

## Telemetry

- `POST /telemetry/events` — validates and stores one Sunbird-compatible envelope.
- `POST /telemetry/batch` — validates up to 100 envelopes.
- `GET /telemetry/events/{user_id}` — caller-owned events, or any user for admin.
- `GET /telemetry/learner/{user_id}/velocity` — deterministic 30-day velocity and engagement metrics.
- `GET /telemetry/learner/{user_id}/skill-profile` — evidence-backed skill profile metrics.
- `GET /telemetry/organization/summary` — admin-only organization aggregates.

Envelope fields are `eid`, `ets`, `ver`, `mid`, `actor`, `context`, `object`, `edata`, and `tags`. Message IDs are deduplicated. Important assessment and learning-progress actions emit events automatically.

## Admin intelligence

- `GET /admin/overview`
- `GET /admin/departments`
- `GET /admin/skill-gaps`
- `GET /admin/training-effectiveness`
- `GET /admin/forecast`

These endpoints calculate aggregates from users, competencies, gaps, progress, assessment attempts, evidence, and prototype demand records. No KPI is intentionally hardcoded.

No live government API is connected in this prototype.
