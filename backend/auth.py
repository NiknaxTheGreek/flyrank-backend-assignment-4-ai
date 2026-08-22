from collections.abc import Mapping
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .supabase import (
    AuthProvider,
    SupabaseAuthClient,
    SupabaseAuthError,
    SupabaseConfigurationError,
)


bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def get_auth_provider() -> AuthProvider:
    return SupabaseAuthClient(get_settings())


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Require one well-formed Bearer credential and normalize auth failures."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("A Bearer token is required.")

    token = credentials.credentials.strip()
    if not token or any(character.isspace() for character in token):
        raise _unauthorized("Malformed Bearer token.")
    return token


def get_current_user(
    access_token: str = Depends(get_bearer_token),
    provider: AuthProvider = Depends(get_auth_provider),
) -> Mapping[str, Any]:
    """Resolve identity with Supabase; never trust unverified client claims."""
    try:
        return provider.get_user(access_token)
    except SupabaseAuthError as exc:
        if exc.status_code in (401, 403):
            raise _unauthorized("Invalid or expired access token.") from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth is unavailable.",
        ) from exc
    except SupabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def require_admin(
    user: Mapping[str, Any] = Depends(get_current_user),
) -> Mapping[str, Any]:
    """Example authorization policy based on Supabase app metadata."""
    app_metadata = user.get("app_metadata")
    role = app_metadata.get("role") if isinstance(app_metadata, Mapping) else None
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission is required.",
        )
    return user