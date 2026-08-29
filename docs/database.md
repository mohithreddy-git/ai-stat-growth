# Database — Phase 2

SQLite is the local default at `backend/data/ai_stat_growth.db`. SQLAlchemy models use portable column types and can migrate to PostgreSQL through a future migration tool.

## Core relationships

```text
roles ─┐
departments ─┐
           users
             ├── employee_competencies ── competencies
             ├── assessment_attempts ── assessments ── assessment_questions ── competencies
             │                              └── assessment_answers
             ├── competency_score_history ── competencies
             ├── recommendations ── competencies + resource id
             └── learning_progress ── course OR training_programme
```

`Course` and `TrainingProgramme` remain separate tables because their source metadata differs. `LearningProgress.resource_type/resource_id` is a deliberate lightweight polymorphic reference for the prototype; a production implementation can use a unified learning-resource table or explicit foreign keys.

## Phase 2 models

- `User`: employee profile and role/department ownership context.
- `Competency`: framework definition, level definitions, target level, and weight.
- `EmployeeCompetency`: current normalized 0–100 score, level, source, and last assessment timestamp.
- `Assessment`, `AssessmentQuestion`: published assessment content. Correct answers stay server-side in the response contract.
- `AssessmentAttempt`, `AssessmentAnswer`: user-owned attempt lifecycle and evaluated answer evidence.
- `CompetencyScoreHistory`: immutable evidence of previous score, new score, delta, source, and attempt id.
- `Course`: iGOT-shaped seeded learning resources.
- `TrainingProgramme`: NSSTA/TPAC-shaped seeded programmes.
- `Recommendation`: persisted ranking snapshot for auditability and future analytics.
- `LearningProgress`: status, completion percentage, learning hours, and activity timestamp.

The broader model also contains document, quiz, forecast, and audit tables. The forensic extension now exposes the document, review, quiz, telemetry, StatBot, and admin intelligence boundaries locally.

## Intelligence-layer models

- `CompetencyDomain`, `CompetencyLevel`: typed framework domains and 1–5 proficiency definitions.
- `Position`, `PositionRole`, `EmployeeRole`: FRAC-compatible position and role ownership.
- `Activity`, `RoleActivity`, `ActivityCompetency`, `RoleCompetencyRequirement`: role-to-activity-to-competency requirements and criticality.
- `CompetencyEvidence`: confidence-weighted assessment, quiz, course, telemetry, practice, trainer, role, or self-declaration evidence.
- `CompetencyVectorSnapshot`: normalized current/target vectors and alignment metrics.
- `FutureSkillDemand`: configurable demand, growth, period, source, and confidence records.
- `AssessmentItem`, `AssessmentItemReview`, `PublishedQuiz`, `QuizItemAnswer`: structured source-grounded item generation, human review, publishing, and attempt evidence.
- `TelemetryEvent`: deduplicated Sunbird-compatible envelope storage.
- `CompetencyUpdateAudit`, `RecommendationSnapshot`: reconstructable score and recommendation decisions.

The prototype uses additive startup upgrades instead of a full migration framework. Existing databases receive missing columns before new tables are created; production should use versioned Alembic migrations.

## Seed expectations

A clean seed creates:

- 3 roles
- 5 departments
- 50 synthetic users
- 35 competencies
- 35 iGOT-style course records
- 15 NSSTA/TPAC-style programmes
- 11 assessments, including a 20-question cross-domain baseline
- 7 prototype skill forecasts
- initial learning progress for the demo employee

Seeding is idempotent for normal local use. Recreate the local database only when intentionally resetting demo data.
