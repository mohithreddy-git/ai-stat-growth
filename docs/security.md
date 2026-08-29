# Phase 2 prototype security posture

Implemented for the prototype:

- PBKDF2-SHA256 password hashing with per-password random salts.
- Signed HS256 JWT access tokens with expiry.
- Server-side role checks on protected API routes.
- Pydantic validation for login input.
- CORS configured from environment variables.
- No secrets committed; `.env` is ignored.
- Demo data marked synthetic and demo identities marked `is_demo`.
- SQLAlchemy parameters are bound rather than string-concatenated.
- Document uploads enforce sanitized filenames, allowed extensions/MIME types, and configurable byte limits.
- Trainer/admin-only assessment authoring and approval endpoints are protected by server-side RBAC.
- Assessment-item edits, approvals, rejections, and quiz publication create audit records.
- Telemetry actor identity is replaced by the authenticated opaque employee ID; passwords, tokens, and API keys are not logged.
- Every competency update stores source, evidence ID, old/new score, calculation, and timestamp.

Prototype limitations:

- Demo credentials are intentionally known and must never be used in production.
- The browser stores the demo token in localStorage for a simple local flow; production should prefer an SSO session or hardened httpOnly cookie strategy.
- Upload malware scanning, content disarm/reconstruction, rate limiting, CSRF protection, TLS termination, encryption at rest, consent/retention policy, and centralized observability remain production work.
- The lightweight additive schema upgrader must be replaced by reviewed versioned migrations before deployment.
