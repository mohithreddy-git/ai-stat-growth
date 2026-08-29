# Phase 2 Validation

## Automated validation

From the repository root:

```bash
backend/.venv/bin/python -m pytest -q backend/tests
cd frontend && npm run build
```

The backend suite covers:

- authentication and demo login;
- API-backed Ananya Sharma profile and baseline competency values;
- severity thresholds and ranked weighted gaps;
- 20-question cross-domain assessment loading;
- complete server-side assessment submission;
- persisted competency score updates and history evidence;
- recommendation ordering and both prototype source types;
- explainability fields;
- learning progress persistence;
- cross-user employee RBAC blocking;
- missing-answer and invalid-option rejection.

## Manual smoke test

1. Start backend on port 8000 and frontend on port 5173.
2. Sign in as Employee demo.
3. Confirm profile loads without hardcoded profile values.
4. Confirm dashboard readiness and seeded progress are non-empty.
5. Confirm the competencies view shows GIS at 31%, Python at 45%, SQL at 64%, Artificial Intelligence at 38%, Data Visualization at 72%, and Statistics at 82% before any assessment.
6. Start the first assessment and confirm 20 questions and category labels.
7. Submit all first options; confirm result is 100% and competency deltas are shown.
8. Visit gaps and learning path; confirm refreshed API values and recommendations.
9. Start and complete a recommendation; reload and confirm the progress status.
10. Sign in as Admin and Trainer; confirm only their role homes are exposed.
11. Inspect browser console for critical errors and API network responses for unexpected failures.

## Known warning

The current test environment may emit a Starlette/httpx deprecation warning from the installed test client. It does not fail the suite and is unrelated to the application workflow.
