from collections.abc import Mapping
from typing import Any, Protocol

import httpx

from .config import Settings


class SupabaseConfigurationError(RuntimeError):
    """Raised when a live Supabase operation is attempted without settings."""


class SupabaseAuthError(RuntimeError):
    """A structured error returned by Supabase Auth."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthProvider(Protocol):
    def sign_up(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        ...

    def sign_in(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        ...

    def sign_out(self, access_token: str) -> None:
        ...

    def get_user(self, access_token: str) -> Mapping[str, Any]:
        ...


class SupabaseAuthClient:
    """Small server-side adapter for Supabase Auth REST endpoints.

    Identity is verified by asking Supabase to resolve the presented access
    token. The API never treats locally decoded token claims as authoritative.
    """

    def __init__(self, settings: Settings, timeout_seconds: float = 10.0) -> None:
        if not settings.is_supabase_configured:
            raise SupabaseConfigurationError(
                "Supabase Auth is not configured. Set SUPABASE_URL and "
                "SUPABASE_PUBLISHABLE_KEY (or legacy SUPABASE_ANON_KEY)."
            )
        self._base_url = settings.supabase_url.rstrip("/")
        self._api_key = settings.supabase_api_key.get_secret_value()
        self._timeout = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        headers = {
            "apikey": self._api_key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        try:
            response = httpx.request(
                method,
                f"{self._base_url}/auth/v1/{path}",
                headers=headers,
                json=json,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise SupabaseAuthError(
                "Supabase Auth is unavailable.",
                status_code=503,
            ) from exc

        if response.is_error:
            message = "Supabase Auth request failed."
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    message = str(
                        payload.get("msg")
                        or payload.get("message")
                        or payload.get("error_description")
                        or payload.get("error")
                        or message
                    )
            except ValueError:
                pass
            raise SupabaseAuthError(message, response.status_code)

        if not response.content:
            return {}
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def sign_up(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        return self._request("POST", "signup", json=credentials)

    def sign_in(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        return self._request(
            "POST",
            "token?grant_type=password",
            json=credentials,
        )

    def sign_out(self, access_token: str) -> None:
        self._request("POST", "logout", access_token=access_token)

    def get_user(self, access_token: str) -> Mapping[str, Any]:
        return self._request("GET", "user", access_token=access_token)