# FlyRank Backend Assignment 4 — Auth: Login & Protect

Minimal FastAPI authentication service backed by Supabase Auth. The service
keeps the public auth flows small, resolves every presented Bearer token with
Supabase's `/auth/v1/user` endpoint, and demonstrates the difference between
authentication (`401`) and authorization (`403`).

## Run locally

The checked-in `.env.example` documents the live Supabase settings. Set
`SUPABASE_PUBLISHABLE_KEY` for modern Supabase projects; the legacy
`SUPABASE_ANON_KEY` remains supported as a fallback when no publishable key is
provided. Keep real values in Replit Secrets or an ignored local `.env`; do not
place them in source control.

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

### Replit automated suite

The checked-in test suite uses a local fake provider and does not contact
Supabase:

```text
uv run pytest artifacts/web/tests -q
```

Those tests cover signup success/failure, login success/invalid credentials,
missing and malformed headers, invalid and expired tokens, valid protected
access, authorization denial and success, logout, and the OpenAPI security
declaration.

The Replit automated suite passed **15 tests** using that fake provider.

### Independent local artifact suite

The independent local artifact suite passed **23 tests** against the official
Supabase CLI local Auth stack. This was a local-only verification using a
temporary `/tmp` project and process-scoped configuration; it did not use a
hosted Supabase account or committed secrets.

The genuine end-to-end sequence was run through the FastAPI app and produced:

- `GET /healthz` → `200`, with `supabase_configured: true`
- `POST /auth/signup` → `201`
- `POST /auth/login` → `200`
- `GET /auth/me` with the returned Bearer token → `200`
- Missing, malformed, and invalid Bearer tokens → `401`
- Authenticated non-admin `GET /auth/admin-check` → `403`
- `POST /auth/logout` → `200`
- Reusing the token after logout → `401`
- `GET /openapi.json` → `200`, with the `BearerAuth` HTTP bearer scheme

The signup, login, and protected identity responses resolved to the same user.
No hosted Supabase verification is claimed. With no settings, the service
still starts and `/healthz` reports `supabase_configured: false`; live auth
calls return `503` rather than silently using fake data.