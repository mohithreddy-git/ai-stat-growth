# Phase 2 forensic audit and rectification

## Existing capabilities retained

The repository already had a working FastAPI/SQLAlchemy + React/Vite vertical slice for employee profile, competency baseline, server-side assessment scoring, gap ranking, recommendation retrieval, seeded iGOT/NSSTA-shaped resources, progress persistence, and demo JWT/RBAC.

## Reused components

The existing `Competency`, `EmployeeCompetency`, `Assessment*`, `LearningProgress`, `Recommendation`, `Course`, `TrainingProgramme`, `skill_gaps.py`, `recommendations.py`, `assessments.py`, seeded adapters, API client, AppShell, and employee pages were retained. No V2 duplicate business services were introduced.

## Findings before rectification

- Competencies were effectively `User → Competency → Score`; no first-class position, role, activity, or requirement graph existed.
- There was no confidence-weighted `CompetencyEvidence` source ledger.
- Score history lacked evidence linkage and calculation provenance.
- No normalized competency-vector/alignment service existed.
- Role and department relevance were hardcoded maps rather than database-derived FRAC activity relationships.
- Recommendation explanations were human-readable only and persisted ranking factors were absent.
- Existing document/quiz tables were not exposed through a guarded source-grounded review workflow.
- The LLM boundary only returned a placeholder string and had no Ollama/OpenAI-compatible implementations or structured validation.
- No Sunbird-compatible telemetry envelope, deduplication, velocity, or telemetry-to-intelligence boundary existed.
- Admin routes were RBAC smoke checks rather than real aggregation APIs.
- No versioned migrations existed; local schema evolution relied on `create_all`.
- Test coverage did not include FRAC, evidence, vectors, question quality, studio review, telemetry, or organization aggregates.

## Rectifications implemented

- Added additive FRAC entities: positions, position roles, activities, role activities, activity competencies, role requirements, employee roles, competency domains, and competency levels.
- Added evidence ledger, confidence/evidence counts, vector snapshots, recommendation factors, audit records, and future-demand records.
- Refactored gap and recommendation services to consume role/activity relationships and expose machine-readable factors.
- Added normalized vectors, weighted distance, cosine similarity, and profile alignment endpoint.
- Added mock/Ollama/OpenAI-compatible provider abstraction with Pydantic structured parsing.
- Added local PDF/DOCX/PPTX/TXT extraction, page/slide-preserving chunks, deterministic source-grounded MCQs, quality validation, review states, approval gates, quiz publication, and quiz evidence.
- Added StatBot general/document mode with source chunk citations.
- Added Sunbird-compatible telemetry envelope storage, batching, deduplication, automatic assessment/learning events, velocity, skill profile, and admin summary.
- Replaced admin placeholders with server-calculated overview, department, gap, training-effectiveness, and forecast endpoints/pages.
- Added additive schema upgrades for existing local databases.
- Added forensic integration tests; existing Phase 2 tests remain green.

## Risks and boundaries

The prototype remains synthetic and local. FRAC, iGOT, NSSTA/TPAC, Sunbird, future demand, and workforce data are not live official integrations. Additive migrations must become versioned Alembic migrations for production. Uploads require malware scanning, object storage, OCR, retention/consent governance, and stronger tenant isolation before deployment.
