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
# Install/sync the pinned dependencies
uv sync
pnpm install --frozen-lockfile

# Run the local fake-backed tests
uv run pytest tests -q

# Run the web artifact (builds the React shell, then serves it from FastAPI)
pnpm run dev
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

The complete evidence package, including explicit PASS statuses and the direct
local Supabase/Auth results, is in
[`VERIFICATION_EVIDENCE.md`](./VERIFICATION_EVIDENCE.md).

### Replit automated suite

The checked-in test suite uses a local fake provider and does not contact
Supabase:

```text
uv run pytest tests -q
```

Those tests cover signup success/failure, login success/invalid credentials,
missing and malformed headers, invalid and expired tokens, valid protected
access, authorization denial and success, logout, and the OpenAPI security
declaration.

The Replit automated suite passed **15 tests** using that fake provider, with
one non-failing TestClient/HTTPX deprecation warning.

### Genuine local Supabase runtime

The genuine local runtime verification used the official Supabase CLI with a
temporary `/tmp` project and a minimal Postgres, GoTrue/Auth, and Kong stack.
The CLI health check was ignored because its Auth/Kong health classification was
misleading even while the services were reachable. No hosted Supabase account
or committed secrets were used.

Direct Supabase Auth results:

- settings → `200`
- signup → `200`
- password login → `200`
- authenticated user lookup → `200`, with the same identity as signup/login
- logout → `204`
- settings after logout → `200`; Auth remained reachable

Application-level results:

- `GET /healthz` → `200`, with Supabase configured
- `POST /auth/signup` → `201`
- `POST /auth/login` → `200`
- `GET /auth/me` with the returned Bearer token → `200`
- Missing, malformed, and invalid Bearer tokens → `401`
- Authenticated non-admin `GET /auth/admin-check` → `403`
- `POST /auth/logout` → `200`
- Reusing the token after logout → `401`
- `GET /openapi.json` → `200`, with the `BearerAuth` HTTP bearer scheme

The signup, login, and protected identity responses resolved to the same user.

### Separate preserved local AI artifact

The separate preserved local AI artifact reported **23 tests passed**. This is
not the Replit workspace's automated suite and is not being presented as
additional local-Supabase runtime evidence.