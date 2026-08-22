# Requirements audit

| Assignment requirement | Evidence |
| --- | --- |
| Python FastAPI service | `backend/main.py` defines the FastAPI application and routes. |
| Environment-based Supabase Auth | `backend/config.py` reads `SUPABASE_URL` and prefers modern `SUPABASE_PUBLISHABLE_KEY`, with legacy `SUPABASE_ANON_KEY` compatibility; `.env.example` documents both. |
| Public signup and login | `POST /auth/signup` and `POST /auth/login`. |
| Logout behavior | `POST /auth/logout` validates identity, then calls Supabase logout. |
| Reusable Bearer guard | `get_bearer_token` and `get_current_user` are FastAPI dependencies reused by protected routes. |
| Verified identity | `SupabaseAuthClient.get_user` asks Supabase `/auth/v1/user`; no JWT claims are decoded or trusted locally. |
| Authentication semantics | Missing, malformed, invalid, and expired credentials map to `401` with `WWW-Authenticate: Bearer`. |
| Authorization semantics | `require_admin` returns `403` for an authenticated non-admin. |
| Swagger/OpenAPI auth | `HTTPBearer(scheme_name="BearerAuth")` produces the security scheme and Swagger lock control. |
| Secrets out of source control | `.env` and `.env.*` are ignored; only `.env.example` is tracked. |
| Automated tests | `artifacts/web/tests/test_auth.py` uses a fake provider and covers each requested flow without live secrets. |
| README and evidence | `README.md` documents the API, commands, modern/legacy key behavior, and the separate mocked versus genuine local-runtime evidence. |

## Dependency audit

The root `pyproject.toml` and `uv.lock` contain the minimal runtime/test set:

- `fastapi` — API framework and generated Swagger/OpenAPI
- `uvicorn` — local/production ASGI server
- `httpx` — small Supabase Auth REST client and FastAPI test transport
- `pydantic-settings` — typed environment configuration
- `pytest` — local automated tests

No database, service-role key, local password hashing, or custom token issuer is
needed for this assignment.

## Verification record

- Replit automated suite: **15 tests passed** using the fake provider.
- Independent local artifact suite: **23 tests passed** against the official
  Supabase CLI local Auth stack.
- Genuine local app sequence: signup `201`, login `200`, protected
  `/auth/me` `200`, missing/malformed/invalid token `401`, authenticated
  non-admin `admin-check` `403`, logout `200`, token reuse after logout `401`,
  and OpenAPI Bearer security verified.
- No hosted Supabase account or committed secret was used for the local
  verification.