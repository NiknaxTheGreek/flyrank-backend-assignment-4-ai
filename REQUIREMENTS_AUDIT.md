# Assignment 4 recovered-S3 requirements audit

| S3 requirement | Current implementation/evidence | Status |
| --- | --- | --- |
| Supabase Auth identity provider | Production `SupabaseAuthClient` handles signup/login/user verification/logout; preserved local Supabase CLI runtime evidence exercises the real provider path | PASS |
| `POST /auth/signup` | public; missing fields become `400`; success `201` | PASS |
| `POST /auth/login` | public; missing fields `400`; invalid credentials `401`; success returns access + refresh tokens | PASS |
| Public route | `GET /public/info` requires no token | PASS |
| Protected profile | `GET /protected/profile` uses reusable `get_current_user` dependency | PASS |
| Second protected route reuses guard | `GET /protected/dashboard` uses the same dependency | PASS |
| Real token verification | `get_current_user` resolves the presented token through the configured Supabase provider; JWT claims are not blindly trusted locally | PASS |
| Missing/malformed token | controlled `401` + `WWW-Authenticate: Bearer` | PASS |
| Invalid/expired/tampered token | controlled `401` | PASS |
| Logout | verifies token, calls provider logout, returns `204` with empty body | PASS |
| Safe metadata | protected routes return only selected identity fields | PASS |
| Swagger Bearer auth | `HTTPBearer` produces protected-route locks and the Authorize flow; current browser gate successfully calls `/protected/profile` via Swagger Try it out | PASS |
| Required Swagger screenshot | current GitHub Actions artifact `assignment-4-auth-evidence` contains `swagger-auth.png`; visual inspection shows Bearer lock + protected-profile `200` response | PASS |
| Curl flow | current CI performs signup/login/protected routes/invalid token/logout/reuse checks with curl and records headers/bodies | PASS |
| No manual password/crypto implementation | password/session/token cryptography remains delegated to Supabase | PASS |
| Secrets excluded | `.env`/`.env.*` ignored; `.env.example` contains configuration names/placeholders only | PASS |
| Provider failure semantics | upstream service outage maps to `503`, not invalid-credential `401` | PASS |
| Automated tests | GitHub Actions run `32713258765`: **26 passed** | PASS |
| Git history | existing history plus isolated repair/evidence commits exceeds S3's minimum of six commits without rewriting history | PASS |
| README | setup, environment, routes, Bearer usage, verification and evidence boundary documented | PASS |

## Current-code checkpoint

GitHub Actions run **32713258765** passed the repaired implementation and produced these explicit markers:

```text
A4_CURL_AUTH_FLOW=PASS
A4_LOGOUT_204_AND_REUSE_401=PASS
A4_SWAGGER_BEARER_TRY_IT_OUT=PASS
```

The associated Actions artifact is **`assignment-4-auth-evidence`**, artifact ID **9514918717**. It contains the curl request/response evidence, local evidence-server logs, and `swagger-auth.png`.

## Evidence boundary

The CI curl/Swagger gate deliberately overrides only the auth-provider dependency with a deterministic provider. This lets the public HTTP contract and Swagger Bearer behavior be reproduced without committing or injecting a live account secret. It is **not** presented as proof of hosted Supabase.

Separate preserved local Supabase CLI evidence covers the production provider path: Supabase Auth settings, signup, password login, authenticated user lookup and logout were exercised against a real local Supabase Auth stack. The deterministic CI and real-provider evidence are kept distinct.

## Additional authorization example

`GET /auth/admin-check` uses `require_admin` and returns `403` for an authenticated non-admin. S3 lists explicit `403` work as stretch/example material rather than a required replacement for the two normal protected routes; this endpoint is retained as a useful extra.

## Project completion boundary

The isolated AI implementation is technically S3-compliant for the code/evidence requirements above. Under S1/S3, Assignment 4's **AI Rematch comparison** remains a separate project-required stage after the human-created implementation exists and is understood. This audit does not fabricate that later comparison.
