# Phase 2 Demo Flow

## Credentials

- Employee: `employee.demo@aistatgrowth.gov.in` / `Demo@123`
- Admin: `admin.demo@aistatgrowth.gov.in` / `Demo@123`
- Trainer: `trainer.demo@aistatgrowth.gov.in` / `Demo@123`

## Employee story

1. Sign in as Employee.
2. Open **My profile**. Dr. Ananya Sharma is loaded from `GET /api/users/{id}` with Assistant Director, National Statistical Office, five years' experience, assignment, education, previous training, and career goal.
3. Open **Competency profile**. The page loads 35 current competency rows and renders readiness, category bars, radar, strengths, development focus, current levels, and role targets.
4. Open **Assessment centre**. Start **Competency Intelligence Baseline**. It contains 20 questions across Statistical, Technical, Digital Governance, and Behavioural & Managerial categories.
5. Answer questions and submit. FastAPI validates every answer and calculates overall score, category scores, answer review, strengths, and weaknesses.
6. The response includes score changes. A perfect attempt increases assessed competency scores using the 65/35 evidence blend, writes history rows, and refreshes recommendations.
7. Open **Skill gaps**. GIS, Python, and Artificial Intelligence remain prominent but use the updated scores and recalculated gaps.
8. Open **Learning pathway**. Resources are grouped by priority and show iGOT or NSSTA/TPAC prototype source, current/target score, relevance, expected improvement, and the full “Why this recommendation?” explanation.
9. Start a resource. The action persists `in_progress` at 25% (or advances an existing row). Click again to mark it completed. Reload to verify persistence.
10. Return to dashboard. KPI cards and recent activity are API-backed and reflect the stored state.

## RBAC smoke check

Sign out and sign in as Admin or Trainer. Their workspace home is available, but employee routes are protected and redirect to their role home. An employee token attempting another employee's data returns `403` from the backend.

## What to say in the demo

“This is not a course catalogue. The platform starts with the official's context, measures evidence, compares it with the role target, ranks the gap using transparent signals, and turns that result into a source-labelled learning path. The score history and progress records make the loop ready for the next AI assessment slice.”

## Prototype boundary

All employee identities, learning resources, forecasts, and assessment content are synthetic. iGOT and NSSTA/TPAC are adapter-shaped prototype datasets. Do not describe them as live integrations.
