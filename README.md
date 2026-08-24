# FlyRank Backend Assignment 4 — Auth: Login & Protect

A FastAPI authentication service backed by Supabase Auth. The application delegates identity/password handling to Supabase, verifies every presented Bearer token with the provider, keeps authentication logic reusable, and exposes the public/protected route contract required by recovered S3.

## Required API surface

| Route | Auth | Required behavior |
| --- | --- | --- |
| `POST /auth/signup` | public | missing fields `400`; success `201` |
| `POST /auth/login` | public | missing fields `400`; bad credentials `401`; success `200` with access + refresh tokens |
| `POST /auth/logout` | Bearer | verified token; success `204` with empty body |
| `GET /public/info` | public | accessible without a token |
| `GET /protected/profile` | Bearer | valid verified identity required |
| `GET /protected/dashboard` | Bearer | second route reusing the same auth dependency |
| `GET /auth/admin-check` | Bearer + role | additional authorization example; authenticated non-admin receives `403` |

`GET /auth/me` remains as a hidden compatibility alias for `/protected/profile` and is not part of the public OpenAPI contract.

Missing/malformed Bearer headers and invalid/expired/tampered tokens return `401` with a Bearer challenge. A Supabase service outage is surfaced as `503` rather than being misreported as bad credentials.

## Configuration

Copy `.env.example` values into an ignored local `.env` or runtime secret store. Modern Supabase projects can use `SUPABASE_PUBLISHABLE_KEY`; `SUPABASE_ANON_KEY` remains supported as a compatibility fallback.

Never commit real credentials.

## Install and run

Python 3.12+:

```bash
python -m pip install .
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

Use the **Authorize** control with the access token returned by `/auth/login`, then call the protected routes through **Try it out**.

## Automated verification

```bash
python -m pytest -q
```

GitHub Actions run **32713258765** executed the current repaired branch and passed:

- clean `pip install .`;
- **26 tests passed**;
- public route without authentication;
- signup `201` and login `200`;
- missing-field `400` behavior;
- invalid/expired/tampered/malformed/missing credential `401` behavior;
- reusable authentication on `/protected/profile` and `/protected/dashboard`;
- non-admin authorization `403`;
- logout `204` with an empty body and rejected token reuse;
- provider-outage `503` behavior;
- OpenAPI Bearer security declarations;
- a real command-line `curl` lifecycle against the current FastAPI contract;
- a browser-driven Swagger UI Bearer authorization + `/protected/profile` **Try it out** returning `200`.

The run printed:

```text
A4_CURL_AUTH_FLOW=PASS
A4_LOGOUT_204_AND_REUSE_401=PASS
A4_SWAGGER_BEARER_TRY_IT_OUT=PASS
```

The run uploaded the complete curl headers/bodies, server logs and the Swagger screenshot as GitHub Actions artifact **`assignment-4-auth-evidence` (artifact 9514918717)**. The screenshot visibly shows Swagger's protected-route lock and a successful `200` response for `/protected/profile` after Bearer authorization.

The browser/curl acceptance gate uses an explicit evidence-only dependency override so no secret is required in CI. It proves the current HTTP/OpenAPI contract. Separately, preserved genuine local Supabase CLI evidence verifies that the production provider path performs real signup/login/user lookup/logout against Supabase Auth. Those two evidence types are intentionally not conflated.

See [`VERIFICATION_EVIDENCE.md`](VERIFICATION_EVIDENCE.md) and [`REQUIREMENTS_AUDIT.md`](REQUIREMENTS_AUDIT.md) for the exact evidence boundary and S3 mapping.

## AI Rematch boundary

Recovered S3/S1 makes the Assignment 4 AI Rematch a separate project-required comparison stage after the human-led Assignment 4 implementation exists and is understood. This repository is the isolated AI-generated implementation; it does not claim that the later human-vs-AI comparison has already been completed.
