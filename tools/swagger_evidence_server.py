"""Reproducible evidence-only server for curl and Swagger UI checkpoints.

The production app is unchanged. This process overrides only the AuthProvider
dependency so the CI browser can exercise the real FastAPI/OpenAPI/Bearer route
contract without storing or requiring a Supabase secret. Separate preserved
runtime evidence covers the real local Supabase verification path.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import uvicorn

from backend.auth import get_auth_provider
from backend.main import app
from backend.supabase import SupabaseAuthError


class EvidenceAuthProvider:
    def __init__(self) -> None:
        self.logged_out_tokens: set[str] = set()

    def sign_up(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        return {
            "access_token": "signup-token",
            "refresh_token": "signup-refresh",
            "user": {"id": "swagger-user", "email": credentials["email"]},
        }

    def sign_in(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        if credentials["password"] != "correct-password":
            raise SupabaseAuthError("Invalid login credentials", 400)
        return {
            "access_token": "valid-token",
            "refresh_token": "refresh-token",
            "user": {"id": "swagger-user", "email": credentials["email"]},
        }

    def sign_out(self, access_token: str) -> None:
        self.logged_out_tokens.add(access_token)

    def get_user(self, access_token: str) -> Mapping[str, Any]:
        if access_token in self.logged_out_tokens:
            raise SupabaseAuthError("Invalid token", 401)
        if access_token == "valid-token":
            return {
                "id": "swagger-user",
                "email": "person@example.com",
                "app_metadata": {"role": "member"},
            }
        raise SupabaseAuthError("Invalid token", 401)


provider = EvidenceAuthProvider()
app.dependency_overrides[get_auth_provider] = lambda: provider


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8040, access_log=False)
