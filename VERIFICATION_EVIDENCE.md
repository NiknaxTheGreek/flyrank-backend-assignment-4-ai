# Assignment 4 Verification Evidence

## Final status

| Area | Status | Evidence |
| --- | --- | --- |
| FastAPI/Supabase implementation | **PASS** | Signup, login, logout, reusable Bearer guard, protected identity route, admin authorization example, 401/403 semantics, and Swagger/OpenAPI Bearer security are implemented. |
| Replit automated tests | **PASS** | Complete Replit-discovered suite: **15 passed**, with one non-failing TestClient/HTTPX deprecation warning. |
| Genuine local Supabase integration | **PASS** | The local Supabase CLI Auth stack completed direct Auth checks and the FastAPI app completed the full application-level sequence below. |

## Runtime boundary

This is genuine local-only evidence from this Replit environment. The official
Supabase CLI used a temporary project under `/tmp` with a minimal stack of:

- Postgres
- GoTrue/Auth
- Kong

The stack was started with the unrelated services excluded and
`--ignore-health-check` enabled because the CLI's Auth/Kong health classification
was misleading even though the services were reachable. No hosted Supabase
account, hosted project, or committed secret was used.

The local API URL came from `supabase status`:

```text
http://127.0.0.1:54321
```

The local anon/publishable key was also obtained from `supabase status` and
used only in process-scoped verification. It is intentionally not recorded
here.

## Direct local Supabase Auth results

These requests were made directly to the local Supabase Auth endpoint:

| Request | Result |
| --- | --- |
| `GET /auth/v1/settings` | `200` |
| `POST /auth/v1/signup` | `200` |
| `POST /auth/v1/token?grant_type=password` | `200` |
| `GET /auth/v1/user` with the returned Bearer token | `200`; same user identity as signup/login |
| `POST /auth/v1/logout` | `204` |
| `GET /auth/v1/settings` after logout | `200`; Auth remained reachable |

## FastAPI application results

The FastAPI app was run with temporary process environment values pointing to
the running local Supabase stack. The following results were observed through
the application routes:

| Request/check | Result |
| --- | --- |
| Public `GET /healthz` | `200`; Supabase reported configured |
| `POST /auth/signup` | `201` |
| `POST /auth/login` | `200` |
| `GET /auth/me` with returned Bearer token | `200` |
| `GET /auth/me` with no token | `401` |
| `GET /auth/me` with malformed `Bearer` header | `401` |
| `GET /auth/me` with invalid token | `401` |
| Authenticated non-admin `GET /auth/admin-check` | `403` |
| `POST /auth/logout` | `200` |
| Reusing the logged-out token at `GET /auth/me` | `401` |
| `GET /openapi.json` | `200`; `BearerAuth` HTTP bearer security declared |

Signup, login, and protected identity responses resolved to the same user.

## Automated test evidence

The complete Replit-discovered automated suite was run with:

```text
uv run pytest -q
```

Observed result:

```text
15 passed, 1 warning
```

The warning was non-failing and came from the FastAPI/Starlette TestClient
integration using HTTPX.

The separate preserved local AI artifact reported **23 tests passed**. That
23-test result is intentionally kept distinct from this Replit workspace's
15-test automated suite and from the genuine local-Supabase runtime evidence
above.

## Secret and provenance statement

No hosted Supabase verification is claimed. Real credentials were not committed
to the repository. The implementation and evidence package are the AI-created
Assignment 4 project in this Replit workspace; no human-created Assignment 4
implementation was inspected or reused.