# Phase 1 deployment

## Local

Run the backend with `uvicorn app.main:app --reload --port 8000` from `backend` and the frontend with `npm run dev` from `frontend`.

## Docker

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

The frontend is served on `http://localhost:4173`; the API is on `http://localhost:8000`.

## Production migration checklist

- Replace demo login with government-approved SSO/OAuth/SAML.
- Move `DATABASE_URL` to PostgreSQL and add migrations (Alembic).
- Use an external secret manager for `JWT_SECRET` and any LLM credentials.
- Build and serve the frontend with the production API URL; restrict CORS to known origins.
- Add TLS termination, centralized logs, metrics, tracing, backups, and retention controls.
- Connect official iGOT and NSSTA/TPAC APIs only after credentials, contracts, and data-governance review.
