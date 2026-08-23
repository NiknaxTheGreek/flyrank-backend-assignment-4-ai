# FlyRank Backend Assignment 4 — Auth: Login & Protect

Minimal FastAPI authentication service backed by Supabase Auth. The service
keeps the public auth flows small, resolves every presented Bearer token with
Supabase's `/auth/v1/user` endpoint, and demonstrates the difference between
authentication (`401`) and authorization (`403`).

## Run locally

The checked-in `.env.example` documents the only live Supabase settings. Keep
real values in Replit Secrets or an ignored local `.env`; do not place them in
source control.

```bash
# Install/sync the pinned Python dependencies
uv sync

# Run the local fake-backed tests
uv run pytest artifacts/web/tests -q

# Run the web artifact (builds the React shell, then serves it from FastAPI)
pnpm --filter @workspace/web run dev
```

When the web artifact is running, inspect:

- `/docs` — Swagger UI with the `BearerAuth` lock control
- `/openapi.json` — generated OpenAPI document
- `/healthz` — reports whether Supabase settings are present without exposing them

## API surface

- `POST /auth/signup` — public Supabase signup
- `POST /auth/login` — public password login
- `POST /auth/logout` — validates and revokes the presented session
- `GET /auth/me` — protected identity lookup
- `GET /auth/admin-check` — protected example requiring `app_metadata.role=admin`

Missing, malformed, invalid, and expired Bearer credentials return `401` with a
Bearer challenge. An authenticated non-admin user reaches the authorization
policy but receives `403`.

## Verification evidence

The test suite uses a local fake provider and does not contact Supabase:

```text
uv run pytest artifacts/web/tests -q
```

Those tests cover signup success/failure, login success/invalid credentials,
missing and malformed headers, invalid and expired tokens, valid protected
access, authorization denial and success, logout, and the OpenAPI security
declaration.

The most recent local verification produced `15 passed` using that fake
provider. The running app also returned `200` from `/healthz` with
`supabase_configured: false`, returned `401` plus `WWW-Authenticate: Bearer`
for a protected request with no token, and exposed the `BearerAuth` security
scheme from `/openapi.json`.

No live Supabase verification is claimed unless real settings are intentionally
configured in the environment and the endpoint is exercised manually. With no
settings, the service still starts and `/healthz` reports
`supabase_configured: false`; live auth calls return `503` rather than silently
using fake data.