from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    supabase_url: str | None = Field(
        default=None,
        validation_alias="SUPABASE_URL",
    )
    supabase_publishable_key: SecretStr | None = Field(
        default=None,
        validation_alias="SUPABASE_PUBLISHABLE_KEY",
    )
    supabase_anon_key: SecretStr | None = Field(
        default=None,
        validation_alias="SUPABASE_ANON_KEY",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def supabase_api_key(self) -> SecretStr | None:
        """Prefer modern publishable keys while accepting legacy anon keys."""
        return self.supabase_publishable_key or self.supabase_anon_key

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()