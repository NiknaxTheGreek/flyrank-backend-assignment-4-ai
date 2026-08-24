from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import get_auth_provider, get_bearer_token, get_current_user, require_admin
from .config import get_settings
from .models import AuthSessionResponse, Credentials, HealthResponse
from .supabase import AuthProvider, SupabaseAuthError, SupabaseConfigurationError


app = FastAPI(
    title="FlyRank Assignment 4 Auth",
    description=(
        "Minimal signup, login, logout, public, and protected-route API. "
        "Supabase resolves the identity for every Bearer token."
    ),
    version="1.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid request", "detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
        headers=exc.headers,
    )


def _auth_response(payload: dict[str, Any]) -> AuthSessionResponse:
    return AuthSessionResponse(
        access_token=payload.get("access_token"),
        refresh_token=payload.get("refresh_token"),
        user=payload.get("user"),
    )


def _provider_failure(exc: SupabaseAuthError, *, authentication: bool = False) -> HTTPException:
    if exc.status_code >= 500:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth is unavailable.",
        )
    if authentication or exc.status_code in (401, 403):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
        )
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


def _safe_user(user: Mapping[str, Any]) -> dict[str, Any]:
    app_metadata = user.get("app_metadata")
    role = app_metadata.get("role") if isinstance(app_metadata, Mapping) else None
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "role": role,
    }


@app.get("/healthz", response_model=HealthResponse, tags=["system"])
def healthz() -> HealthResponse:
    return HealthResponse(
        status="ok",
        supabase_configured=get_settings().is_supabase_configured,
    )


@app.post(
    "/auth/signup",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
def signup(
    credentials: Credentials,
    provider: AuthProvider = Depends(get_auth_provider),
) -> AuthSessionResponse:
    try:
        payload = dict(provider.sign_up(credentials.model_dump()))
        return _auth_response(payload)
    except SupabaseAuthError as exc:
        raise _provider_failure(exc) from exc
    except SupabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@app.post(
    "/auth/login",
    response_model=AuthSessionResponse,
    tags=["auth"],
)
def login(
    credentials: Credentials,
    provider: AuthProvider = Depends(get_auth_provider),
) -> AuthSessionResponse:
    try:
        payload = dict(provider.sign_in(credentials.model_dump()))
        return _auth_response(payload)
    except SupabaseAuthError as exc:
        raise _provider_failure(exc, authentication=True) from exc
    except SupabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["auth"])
def logout(
    access_token: str = Depends(get_bearer_token),
    provider: AuthProvider = Depends(get_auth_provider),
) -> Response:
    try:
        provider.get_user(access_token)
        provider.sign_out(access_token)
    except SupabaseAuthError as exc:
        if exc.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth is unavailable.",
        ) from exc
    except SupabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/public/info", tags=["public"])
def public_info() -> dict[str, str]:
    return {"message": "This route is public."}


@app.get("/auth/me", include_in_schema=False)
@app.get("/protected/profile", tags=["protected"])
def protected_profile(
    user: Mapping[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {"user": _safe_user(user)}


@app.get("/protected/dashboard", tags=["protected"])
def protected_dashboard(
    user: Mapping[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "message": "Protected dashboard access granted.",
        "user": _safe_user(user),
    }


@app.get("/auth/admin-check", tags=["protected"])
def admin_check(user: Mapping[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    return {"message": "Admin access granted.", "user": _safe_user(user)}


frontend_dir = Path(__file__).resolve().parents[1] / "dist" / "public"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
