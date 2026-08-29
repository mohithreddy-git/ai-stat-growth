# Phase 3 verification and hardening

## Scope

This pass verified the existing Phase 3+ implementation rather than rebuilding it. Existing services for documents, retrieval, assessment items, quizzes, telemetry, evidence, recommendations, and StatBot were retained.

## Reality check

| Capability | Finding |
| --- | --- |
| PDF/DOCX/PPTX/TXT processing | Implemented and tested; extraction preserves page/slide metadata where available. |
| Chunking and local embeddings | Implemented and tested; chunks retain document and source metadata. |
| Source-grounded MCQ generation | Implemented; deterministic fallback works without an external model. |
| Structured LLM output | Implemented; Pydantic parsing retries once and falls back safely. |
| MCQ quality validation | Implemented and expanded with malformed-output tests. |
| Human review | Implemented; approval gate prevents unreviewed or rejected publication. |
| Quiz evaluation | Implemented server-side; score is not accepted from the frontend. |
| Quiz competency evidence | Implemented; quiz results append evidence and score history. |
| StatBot general mode | Implemented and tested. |
| StatBot document mode | Implemented and tested; zero-relevance questions now fail instead of receiving an unrelated answer. |
| Telemetry envelope and deduplication | Implemented and tested. |
| Automatic document upload telemetry | Missing before this pass; fixed. |
| Automatic content-view telemetry | Missing before this pass; fixed for published quiz retrieval. |
| Complete review transition audit | Final queue status existed before this pass; intermediate `GENERATED`, `VALIDATED`, and `PENDING_REVIEW` actions are now recorded. |
| Post-publication item mutation | Previously insufficiently restricted; published items are now immutable and approved/published items cannot be rejected. |
| iGOT and NSSTA/TPAC | Prototype adapter-backed seeded data only; no live government integration is claimed. |
| FRAC | Synthetic relational prototype mappings; no official FRAC catalogue integration is claimed. |
| Future demand | Prototype seed forecasts; no official MoSPI forecasting is claimed. |

## Hardening changes

- Added `DOCUMENT_UPLOAD` to the supported telemetry contract.
- Emitted `DOCUMENT_UPLOAD` after authenticated document storage.
- Emitted `CONTENT_VIEW` when an authenticated learner retrieves a published quiz.
- Added conservative retrieval relevance gating using lexical overlap and stored deterministic embeddings.
- Document-grounded StatBot now returns no-source failure for unsupported questions instead of confidently quoting an unrelated chunk.
- Generated and edited assessment items now write review-ledger actions for `GENERATED`, `VALIDATED`, and `PENDING_REVIEW`.
- Rejected, unreviewed, and duplicate item publication is blocked.
- Published assessment items cannot be edited or rejected.
- Added tests for malformed MCQs, provider retry/failure, provenance, review transitions, rejection gates, upload validation, RBAC, telemetry, grounding, and the 10-item quiz workflow.

## Acceptance evidence

The isolated live backend acceptance run passed without restarting between workflow steps:

1. Trainer login.
2. PDF upload.
3. Document processing.
4. Page-preserving chunk creation.
5. Ten-plus source-grounded item generation.
6. Schema and quality validation.
7. Review queue entry.
8. Trainer approval.
9. Quiz publication.
10. Employee quiz retrieval.
11. Server-side quiz evaluation.
12. Quiz evidence and competency update.
13. Gap and recommendation recalculation.
14. Telemetry emission and deduplication.
15. Admin analytics and telemetry summary.

The automated suite passed 29 tests. The frontend TypeScript/Vite production build also passed.

## Remaining prototype limitations

- SQLite and synchronous SQLAlchemy are retained for the zero-cost prototype.
- Document processing and LLM work are in-process; production should use workers and durable job state.
- Uploads still need malware scanning, object storage, retention controls, OCR, and stronger tenant isolation.
- The deterministic embedding seam should be replaced with an approved production embedding service or model.
- Production requires official authentication/SSO, live approved learning-source connectors, official FRAC governance, and an exact deployed Sunbird schema review.
