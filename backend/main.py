from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import get_auth_provider, get_bearer_token, get_current_user, require_admin
from .config import get_settings
from .models import AuthSessionResponse, Credentials, HealthResponse, MessageResponse
from .supabase import AuthProvider, SupabaseAuthError, SupabaseConfigurationError


app = FastAPI(
    title="FlyRank Assignment 4 Auth",
    description=(
        "Minimal signup, login, logout, and protected-route API. "
        "Supabase resolves the identity for every Bearer token."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _auth_response(payload: dict[str, Any]) -> AuthSessionResponse:
    return AuthSessionResponse(
        access_token=payload.get("access_token"),
        refresh_token=payload.get("refresh_token"),
        user=payload.get("user"),
    )


def _provider_failure(exc: SupabaseAuthError, *, authentication: bool = False) -> HTTPException:
    if authentication or exc.status_code in (401, 403):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if exc.status_code >= 500:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth is unavailable.",
        )
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


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


@app.post("/auth/logout", response_model=MessageResponse, tags=["auth"])
def logout(
    access_token: str = Depends(get_bearer_token),
    provider: AuthProvider = Depends(get_auth_provider),
) -> MessageResponse:
    # Validate the token before revoking the session, so logout has the same
    # 401 semantics as every other protected operation.
    try:
        provider.get_user(access_token)
        provider.sign_out(access_token)
    except SupabaseAuthError as exc:
        if exc.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
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
    return MessageResponse(message="Logged out.")


@app.get("/auth/me", tags=["protected"])
def protected_me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"user": user}


@app.get("/auth/admin-check", tags=["protected"])
def admin_check(user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    return {"message": "Admin access granted.", "user": user}


frontend_dir = Path(__file__).resolve().parents[1] / "dist" / "public"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")