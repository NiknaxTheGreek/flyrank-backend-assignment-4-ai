from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.auth import get_auth_provider
from backend.main import app
from backend.supabase import SupabaseAuthError


class FakeAuthProvider:
    def __init__(self) -> None:
        self.logged_out_tokens: list[str] = []

    def sign_up(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        if credentials["email"] == "taken@example.com":
            raise SupabaseAuthError("User already registered", 400)
        return {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "user": {"id": "new-user", "email": credentials["email"]},
        }

    def sign_in(self, credentials: Mapping[str, str]) -> Mapping[str, Any]:
        if credentials["password"] != "correct-password":
            raise SupabaseAuthError("Invalid login credentials", 400)
        return {
            "access_token": "valid-token",
            "refresh_token": "refresh-token",
            "user": {"id": "user-123", "email": credentials["email"]},
        }

    def sign_out(self, access_token: str) -> None:
        self.logged_out_tokens.append(access_token)

    def get_user(self, access_token: str) -> Mapping[str, Any]:
        if access_token == "valid-token":
            return {
                "id": "user-123",
                "email": "person@example.com",
                "app_metadata": {"role": "member"},
            }
        if access_token == "admin-token":
            return {
                "id": "admin-123",
                "email": "admin@example.com",
                "app_metadata": {"role": "admin"},
            }
        if access_token == "expired-token":
            raise SupabaseAuthError("Token has expired", 401)
        raise SupabaseAuthError("Invalid token", 401)


@pytest.fixture
def fake_provider() -> FakeAuthProvider:
    return FakeAuthProvider()


@pytest.fixture
def client(fake_provider: FakeAuthProvider):
    app.dependency_overrides[get_auth_provider] = lambda: fake_provider
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_signup_success(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={"email": "new@example.com", "password": "correct-password"},
    )
    assert response.status_code == 201
    assert response.json()["access_token"] == "new-access-token"


def test_signup_failure_is_bad_request(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={"email": "taken@example.com", "password": "correct-password"},
    )
    assert response.status_code == 400


def test_login_success(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "correct-password"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"] == "valid-token"


def test_login_invalid_credentials_are_unauthorized(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "authorization",
    [None, "Basic abc123", "Bearer", "Bearer one two"],
)
def test_missing_or_malformed_bearer_header_is_401(
    client: TestClient, authorization: str | None
) -> None:
    headers = {} if authorization is None else {"Authorization": authorization}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token", ["invalid-token", "expired-token"])
def test_invalid_or_expired_token_is_401(client: TestClient, token: str) -> None:
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_valid_token_reaches_protected_route(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user-123"


def test_authenticated_user_without_permission_gets_403(client: TestClient) -> None:
    response = client.get(
        "/auth/admin-check",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 403


def test_admin_user_can_reach_authorized_route(client: TestClient) -> None:
    response = client.get(
        "/auth/admin-check",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert response.status_code == 200


def test_logout_validates_and_revokes_token(
    client: TestClient, fake_provider: FakeAuthProvider
) -> None:
    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out."}
    assert fake_provider.logged_out_tokens == ["valid-token"]


def test_openapi_declares_bearer_security(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
    }
    assert schema["paths"]["/auth/me"]["get"]["security"] == [
        {"BearerAuth": []}
    ]