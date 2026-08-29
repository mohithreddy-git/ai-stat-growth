# Telemetry and learner intelligence

The prototype exposes a Sunbird-compatible telemetry boundary without claiming a live Sunbird integration.

## Envelope

```json
{
  "eid": "COURSE_PROGRESS",
  "ets": 1787840000000,
  "ver": "3.0",
  "mid": "unique-message-id",
  "actor": {"id": "EMP-0001", "type": "User"},
  "context": {"channel": "AI_STAT_GROWTH"},
  "object": {"id": "course:2", "type": "course"},
  "edata": {"completion_percent": 50},
  "tags": ["prototype"]
}
```

Supported event IDs are `ASSESSMENT_START`, `RESPONSE`, `ASSESSMENT_END`, `COURSE_START`, `COURSE_PROGRESS`, `COURSE_COMPLETE`, `DOCUMENT_UPLOAD`, `CONTENT_VIEW`, `SEARCH`, `RECOMMENDATION_VIEW`, `RECOMMENDATION_ACCEPT`, `RECOMMENDATION_REJECT`, `FEEDBACK`, `SKILL_PROFILE_UPDATE`, and `ERROR`. The server emits `DOCUMENT_UPLOAD` for authenticated trainer/admin uploads and `CONTENT_VIEW` when an authenticated learner opens a published quiz.

The service overwrites the stored actor ID with the authenticated opaque employee ID and deduplicates messages by `mid`.

## Derived metrics

For a configurable 30-day window:

- `learning_velocity = (learning_hours + 2 × completed_resources + completed_assessments) / window_days`;
- `completion_velocity = completed_resources / window_days`;
- `assessment_accuracy = mean completed assessment score`;
- `engagement_rate = min(100, qualifying activity events / window_days × 100)`;
- `recommendation_acceptance_rate = accepted / (accepted + viewed + rejected) × 100`;
- `competency_improvement_rate = mean score delta from competency history`.

Telemetry is a low-confidence supporting signal. Formal assessment, quiz, course, trainer, and role evidence remains separately identified and weighted in competency aggregation.

## Production boundary

Production should validate the exact deployed Sunbird schema version against the target ecosystem, use durable event transport, encrypt sensitive fields, define retention and consent policy, and export to approved observability/analytics infrastructure.
