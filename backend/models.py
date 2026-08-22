from typing import Any

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class AuthSessionResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    user: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    supabase_configured: bool